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
            # Get commits from repository
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
        # Get tags from repository
        tags = self.git_repo.get_tags()

        if not tags:
            # No tags, create single "Unreleased" entry
            return self._create_unreleased_entry(parsed_commits)

        # Sort tags by date (newest first)
        tags.sort(key=lambda t: t.date, reverse=True)

        entries = []
        remaining_commits = parsed_commits.copy()

        # Process each tag
        for i, tag in enumerate(tags):
            # Get commits for this version
            if i == 0:
                # Latest tag - commits up to and including the tag
                # Include commits that are at or before the tag date
                version_commits = [
                    (commit, parsed)
                    for commit, parsed in remaining_commits
                    if commit.date <= tag.date
                ]
            else:
                # Previous tag - commits between previous tag and this tag
                next_tag = tags[i - 1]
                version_commits = [
                    (commit, parsed)
                    for commit, parsed in remaining_commits
                    if next_tag.date < commit.date <= tag.date
                ]

            if version_commits:
                entry = self._create_version_entry(tag.name, tag.date, version_commits)
                entries.append(entry)

                # Remove processed commits
                for commit_tuple in version_commits:
                    if commit_tuple in remaining_commits:
                        remaining_commits.remove(commit_tuple)

        # Add unreleased commits if any (commits newer than the latest tag)
        if remaining_commits:
            # Only include commits that are actually newer than the latest tag
            latest_tag_date = tags[0].date if tags else datetime.min
            truly_unreleased = [
                (commit, parsed)
                for commit, parsed in remaining_commits
                if commit.date > latest_tag_date
            ]

            if truly_unreleased:
                unreleased_entry = self._create_unreleased_entry(truly_unreleased)
                entries.insert(0, unreleased_entry[0])  # Add at the beginning

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
