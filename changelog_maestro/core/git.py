"""Git repository operations."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, List, Optional

import git
from git import Commit as GitCommit
from git import Repo

from ..utils.exceptions import GitError


@dataclass
class Commit:
    """Represents a Git commit."""

    hash: str
    message: str
    author: str
    email: str
    date: datetime
    is_merge: bool = False

    @classmethod
    def from_git_commit(cls, git_commit: GitCommit) -> "Commit":
        """Create Commit from GitPython commit object."""
        return cls(
            hash=git_commit.hexsha,
            message=(
                git_commit.message.strip().decode()
                if isinstance(git_commit.message, bytes)
                else git_commit.message.strip()
            ),
            author=git_commit.author.name or "Unknown",
            email=git_commit.author.email or "unknown@example.com",
            date=datetime.fromtimestamp(git_commit.committed_date),
            is_merge=len(git_commit.parents) > 1,
        )


@dataclass
class Tag:
    """Represents a Git tag."""

    name: str
    hash: str
    date: datetime
    message: Optional[str] = None

    @classmethod
    def from_git_tag(cls, git_tag: Any) -> "Tag":
        """Create Tag from GitPython tag object."""
        commit = git_tag.commit
        return cls(
            name=git_tag.name,
            hash=commit.hexsha,
            date=datetime.fromtimestamp(commit.committed_date),
            message=(
                git_tag.tag.message if hasattr(git_tag, "tag") and git_tag.tag else None
            ),
        )


class GitRepository:
    """Git repository operations."""

    def __init__(self, repo_path: Path) -> None:
        """Initialize Git repository."""
        self.repo_path = repo_path
        try:
            self.repo = Repo(repo_path)
        except git.InvalidGitRepositoryError:
            raise GitError(f"Not a valid Git repository: {repo_path}")
        except git.NoSuchPathError:
            raise GitError(f"Repository path does not exist: {repo_path}")

    def get_commits(
        self,
        since: Optional[str] = None,
        until: Optional[str] = None,
        include_merges: bool = False,
    ) -> List[Commit]:
        """Get commits from the repository."""
        try:
            # Build revision range
            rev_range = self._build_revision_range(since, until)

            # Get commits
            git_commits = list(self.repo.iter_commits(rev_range))
            commits = [Commit.from_git_commit(gc) for gc in git_commits]

            # Filter merge commits if requested
            if not include_merges:
                commits = [c for c in commits if not c.is_merge]

            return commits

        except git.GitCommandError as e:
            raise GitError(f"Failed to get commits: {e}")

    def get_tags(self) -> List[Tag]:
        """Get all tags from the repository."""
        try:
            git_tags = self.repo.tags
            return [Tag.from_git_tag(gt) for gt in git_tags]
        except git.GitCommandError as e:
            raise GitError(f"Failed to get tags: {e}")

    def get_latest_tag(self) -> Optional[Tag]:
        """Get the latest tag by commit date (not tag creation date)."""
        tags = self.get_tags()
        if not tags:
            return None

        # Sort by commit date (when the commit was made, not when tag was created)
        # This is more reliable than tag creation time
        return max(tags, key=lambda t: t.date)

    def tag_exists(self, tag_name: str) -> bool:
        """Check if a tag exists."""
        try:
            # Check if tag exists in the repository
            for tag in self.repo.tags:
                if tag.name == tag_name:
                    return True
            return False
        except Exception:
            return False

    def get_commits_between_tags(
        self,
        from_tag: Optional[str] = None,
        to_tag: Optional[str] = None,
        include_merges: bool = False,
    ) -> List[Commit]:
        """Get commits between two tags."""
        return self.get_commits(
            since=from_tag,
            until=to_tag,
            include_merges=include_merges,
        )

    def _build_revision_range(
        self,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> str:
        """Build revision range for git log."""
        if since and until:
            return f"{since}..{until}"
        elif since:
            return f"{since}..HEAD"
        elif until:
            return until
        else:
            return "HEAD"

    @property
    def current_branch(self) -> str:
        """Get current branch name."""
        try:
            return self.repo.active_branch.name
        except TypeError:
            # Detached HEAD
            return "HEAD"

    @property
    def remote_url(self) -> Optional[str]:
        """Get remote origin URL."""
        try:
            return self.repo.remotes.origin.url
        except AttributeError:
            return None

    def close(self) -> None:
        """Close the repository to release resources."""
        try:
            if hasattr(self.repo, "close"):
                self.repo.close()
        except Exception:
            pass
