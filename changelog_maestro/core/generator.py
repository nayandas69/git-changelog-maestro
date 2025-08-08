"""Main changelog generator."""

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..utils.exceptions import ChangelogError
from .config import Config
from .formatter import ChangelogEntry, ChangelogFormatter
from .git import Commit, GitRepository
from .parser import ConventionalCommitParser, ParsedCommit


class ChangelogGenerator:
    """Main changelog generator class."""

    def __init__(self, repo_path: Path, config: Optional[Config] = None) -> None:
        """Initialize changelog generator."""
        self.repo_path = repo_path
        self.config = config or Config()

        # Initialize components
        self.git_repo = GitRepository(repo_path)
        self.parser = ConventionalCommitParser(
            breaking_change_indicators=self.config.breaking_change_indicators
        )
        self.formatter = ChangelogFormatter(template_path=self.config.template_path)

    def generate(self) -> str:
        """Generate changelog content."""
        try:
            # Get commits from repository using the improved method
            commits = self.git_repo.get_commits(
                since=self.config.since_tag,
                until=self.config.until_tag,
                include_merges=self.config.include_merges,
            )

            if not commits:
                raise ChangelogError("No commits found in the specified range")

            # Parse commits
            parsed_commits = self._parse_commits(commits)

            if not parsed_commits:
                raise ChangelogError("No valid conventional commits found")

            # Group commits by version/tag
            entries = self._group_commits_by_version(parsed_commits)

            # Format changelog
            return self.formatter.format(entries, self.config.output_style)

        except Exception as e:
            if isinstance(e, ChangelogError):
                raise
            raise ChangelogError(f"Failed to generate changelog: {e}")

    def _parse_commits(
        self, commits: List[Commit]
    ) -> List[tuple[Commit, ParsedCommit]]:
        """Parse commits using conventional commits parser."""
        parsed_commits = []

        for commit in commits:
            # Skip commits that match exclude patterns
            if self._should_exclude_commit(commit):
                continue

            try:
                parsed_commit = self.parser.parse(commit.message)

                # Only include commits of specified types
                if self.config.should_include_commit_type(parsed_commit.type):
                    parsed_commits.append((commit, parsed_commit))

            except Exception:
                # Skip commits that don't follow conventional format
                continue

        return parsed_commits

    def _should_exclude_commit(self, commit: Commit) -> bool:
        """Check if commit should be excluded based on patterns."""
        if not self.config.exclude_patterns:
            return False

        message = commit.message.lower()
        for pattern in self.config.exclude_patterns:
            if pattern.lower() in message:
                return True

        return False

    def _group_commits_by_version(
        self, parsed_commits: List[tuple[Commit, ParsedCommit]]
    ) -> List[ChangelogEntry]:
        """Group commits by version/tag."""
        # If we have specific since/until tags, handle them differently
        if self.config.since_tag or self.config.until_tag:
            return self._group_commits_by_tag_range(parsed_commits)
        else:
            return self._group_commits_by_all_tags(parsed_commits)

    def _group_commits_by_tag_range(
        self, parsed_commits: List[tuple[Commit, ParsedCommit]]
    ) -> List[ChangelogEntry]:
        """Group commits when specific tag range is provided."""
        # For tag ranges, we want to show all commits in that range
        # grouped by the tags that exist within that range

        # Get all tags
        all_tags = self.git_repo.get_tags()

        if not all_tags:
            # No tags, create single "Unreleased" entry
            return self._create_unreleased_entry(parsed_commits)

        # Sort tags by date (newest first for display)
        all_tags.sort(key=lambda t: t.date, reverse=True)

        # If we have both since and until, create a single entry for that range
        if self.config.since_tag and self.config.until_tag:
            version_name = f"{self.config.since_tag}..{self.config.until_tag}"
            entry = ChangelogEntry(version_name, datetime.now())

            for commit, parsed_commit in parsed_commits:
                section_name = self.config.get_section_name(parsed_commit.type)
                entry.add_commit(parsed_commit, section_name)

            return [entry] if entry.has_changes() else []

        # Otherwise, group by individual tags in the range
        entries = []

        # Find relevant tags based on the range
        relevant_tags = []
        for tag in all_tags:
            include_tag = True

            # Check if tag is within our range
            if self.config.since_tag:
                since_tag = next(
                    (t for t in all_tags if t.name == self.config.since_tag), None
                )
                if since_tag and tag.date <= since_tag.date:
                    include_tag = False

            if self.config.until_tag:
                until_tag = next(
                    (t for t in all_tags if t.name == self.config.until_tag), None
                )
                if until_tag and tag.date > until_tag.date:
                    include_tag = False

            if include_tag:
                relevant_tags.append(tag)

        # Create entries for relevant tags
        for tag in relevant_tags:
            # For now, include all commits for each tag in range
            # This is a simplified approach - in practice you might want
            # to be more precise about which commits belong to which tag
            if parsed_commits:
                entry = self._create_version_entry(tag.name, tag.date, parsed_commits)
                if entry.has_changes():
                    entries.append(entry)
                    break  # Only create one entry to avoid duplication

        # If no relevant tags found, create unreleased entry
        if not entries and parsed_commits:
            entries = self._create_unreleased_entry(parsed_commits)

        return entries

    def _group_commits_by_all_tags(
        self, parsed_commits: List[tuple[Commit, ParsedCommit]]
    ) -> List[ChangelogEntry]:
        """Group commits by all tags when no specific range is provided."""
        # Get tags from repository
        tags = self.git_repo.get_tags()

        if not tags:
            # No tags, create single "Unreleased" entry
            return self._create_unreleased_entry(parsed_commits)

        # Sort tags by date (oldest first)
        tags.sort(key=lambda t: t.date)

        entries = []
        processed_commits = set()

        # Process each tag (oldest to newest)
        for i, tag in enumerate(tags):
            # Get the date range for this tag
            if i == 0:
                # First tag - all commits up to this tag
                start_date = datetime.min
            else:
                # Subsequent tags - commits after previous tag
                start_date = tags[i - 1].date

            end_date = tag.date

            # Get commits for this version
            version_commits = [
                (commit, parsed)
                for commit, parsed in parsed_commits
                if start_date < commit.date <= end_date
                and (commit.hash, parsed.type) not in processed_commits
            ]

            if version_commits:
                entry = self._create_version_entry(tag.name, tag.date, version_commits)
                entries.append(entry)

                # Mark commits as processed
                for commit, parsed in version_commits:
                    processed_commits.add((commit.hash, parsed.type))

        # Add unreleased commits (commits newer than the latest tag)
        if tags:
            latest_tag_date = max(tag.date for tag in tags)
            unreleased_commits = [
                (commit, parsed)
                for commit, parsed in parsed_commits
                if commit.date > latest_tag_date
                and (commit.hash, parsed.type) not in processed_commits
            ]

            if unreleased_commits:
                unreleased_entry = self._create_unreleased_entry(unreleased_commits)
                entries = unreleased_entry + entries

        # Sort entries by version (newest first for display)
        entries.sort(key=lambda e: e.date, reverse=True)

        return entries

    def _create_version_entry(
        self, version: str, date: datetime, commits: List[tuple[Commit, ParsedCommit]]
    ) -> ChangelogEntry:
        """Create a changelog entry for a specific version."""
        # Remove version prefix if present
        clean_version = version
        if version.startswith(self.config.version_prefix):
            clean_version = version[len(self.config.version_prefix) :]

        entry = ChangelogEntry(clean_version, date)

        # Group commits by type
        for commit, parsed_commit in commits:
            section_name = self.config.get_section_name(parsed_commit.type)
            entry.add_commit(parsed_commit, section_name)

        return entry

    def _create_unreleased_entry(
        self, commits: List[tuple[Commit, ParsedCommit]]
    ) -> List[ChangelogEntry]:
        """Create changelog entry for unreleased commits."""
        if not commits:
            return []

        entry = ChangelogEntry("Unreleased", datetime.now())

        # Group commits by type
        for commit, parsed_commit in commits:
            section_name = self.config.get_section_name(parsed_commit.type)
            entry.add_commit(parsed_commit, section_name)

        return [entry]
