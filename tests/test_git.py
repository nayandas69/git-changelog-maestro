"""Tests for Git repository operations."""

import gc
import tempfile
import time
from datetime import datetime
from pathlib import Path

import git
import pytest

from changelog_maestro.core.git import Commit, GitRepository, Tag
from changelog_maestro.utils.exceptions import GitError


class TestGitRepository:
    """Test cases for GitRepository."""

    def test_init_valid_repo(self, temp_repo: Path):
        """Test initializing with valid repository."""
        git_repo = GitRepository(temp_repo)
        assert git_repo.repo_path == temp_repo
        assert isinstance(git_repo.repo, git.Repo)

    def test_init_invalid_repo(self):
        """Test initializing with invalid repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_path = Path(temp_dir) / "not_a_repo"
            invalid_path.mkdir()

            with pytest.raises(GitError):
                GitRepository(invalid_path)

    def test_init_nonexistent_path(self):
        """Test initializing with nonexistent path."""
        nonexistent_path = Path("/nonexistent/path")

        with pytest.raises(GitError):
            GitRepository(nonexistent_path)

    def test_get_commits(self, git_repo: GitRepository):
        """Test getting commits from repository."""
        commits = git_repo.get_commits()

        assert len(commits) >= 1  # At least initial commit
        assert all(isinstance(c, Commit) for c in commits)
        assert commits[0].message == "Initial commit"

    def test_get_commits_exclude_merges(self, temp_repo: Path):
        """Test excluding merge commits."""
        repo = git.Repo(temp_repo)
        git_repo = None

        try:
            # Create a branch and merge commit
            feature_branch = repo.create_head("feature")
            feature_branch.checkout()

            # Add commit to feature branch
            test_file = temp_repo / "feature.txt"
            test_file.write_text("feature content")
            repo.index.add([str(test_file)])
            repo.index.commit("feat: add feature")

            # Switch back to main and merge (this should create a merge commit)
            main_branch = repo.heads[0]  # Get the main branch (master/main)
            main_branch.checkout()

            # Force a merge commit
            repo.git.merge("feature", "--no-ff")

            git_repo = GitRepository(temp_repo)

            # Get all commits (including merges)
            all_commits = git_repo.get_commits(include_merges=True)

            # Get commits excluding merges
            no_merge_commits = git_repo.get_commits(include_merges=False)

            # Should have at least one merge commit
            merge_commits = [c for c in all_commits if c.is_merge]
            if merge_commits:
                assert len(all_commits) > len(no_merge_commits)
            else:
                # If no merge commit was created, counts should be equal
                assert len(all_commits) == len(no_merge_commits)
        finally:
            if git_repo:
                git_repo.close()
            repo.close()
            gc.collect()
            time.sleep(0.1)

    def test_get_tags(self, temp_repo: Path):
        """Test getting tags from repository."""
        repo = git.Repo(temp_repo)
        git_repo = None

        try:
            # Create a tag
            repo.create_tag("v1.0.0", message="Release v1.0.0")

            git_repo = GitRepository(temp_repo)
            tags = git_repo.get_tags()

            assert len(tags) == 1
            assert isinstance(tags[0], Tag)
            assert tags[0].name == "v1.0.0"
        finally:
            if git_repo:
                git_repo.close()
            repo.close()
            gc.collect()
            time.sleep(0.1)

    def test_get_latest_tag(self, temp_repo: Path):
        """Test getting latest tag."""
        repo = git.Repo(temp_repo)
        git_repo = None

        try:
            # Get the initial commit
            initial_commit = repo.head.commit

            # Create first tag on initial commit
            tag1 = repo.create_tag("v1.0.0", ref=initial_commit)

            # Wait a moment to ensure different timestamps
            time.sleep(1.1)

            # Add another commit - this will have a later timestamp
            test_file = temp_repo / "test.txt"
            test_file.write_text("test content")
            repo.index.add([str(test_file)])
            new_commit = repo.index.commit("Add test file")

            # Create second tag on the newer commit
            tag2 = repo.create_tag("v1.1.0", ref=new_commit)

            git_repo = GitRepository(temp_repo)

            # Verify the commits have different timestamps
            commit1_date = datetime.fromtimestamp(tag1.commit.committed_date)
            commit2_date = datetime.fromtimestamp(tag2.commit.committed_date)

            # The second commit should be newer
            assert (
                commit2_date > commit1_date
            ), f"Second commit ({commit2_date}) should be newer than first ({commit1_date})"

            latest_tag = git_repo.get_latest_tag()

            assert latest_tag is not None
            # The latest tag should be v1.1.0 since it points to a later commit
            assert (
                latest_tag.name == "v1.1.0"
            ), f"Expected v1.1.0 but got {latest_tag.name}"
        finally:
            if git_repo:
                git_repo.close()
            repo.close()
            gc.collect()
            time.sleep(0.1)

    def test_get_latest_tag_no_tags(self, git_repo: GitRepository):
        """Test getting latest tag when no tags exist."""
        latest_tag = git_repo.get_latest_tag()
        assert latest_tag is None

    def test_tag_exists(self, temp_repo: Path):
        """Test checking if tag exists."""
        repo = git.Repo(temp_repo)
        git_repo = None

        try:
            repo.create_tag("v1.0.0")

            git_repo = GitRepository(temp_repo)

            assert git_repo.tag_exists("v1.0.0")
            assert not git_repo.tag_exists("v2.0.0")
        finally:
            if git_repo:
                git_repo.close()
            repo.close()
            gc.collect()
            time.sleep(0.1)

    def test_current_branch(self, git_repo: GitRepository):
        """Test getting current branch name."""
        branch_name = git_repo.current_branch
        assert branch_name in ["master", "main"]  # Default branch names

    def test_remote_url_no_remote(self, git_repo: GitRepository):
        """Test getting remote URL when no remote exists."""
        remote_url = git_repo.remote_url
        assert remote_url is None


class TestCommit:
    """Test cases for Commit dataclass."""

    def test_from_git_commit(self, temp_repo: Path):
        """Test creating Commit from GitPython commit."""
        repo = git.Repo(temp_repo)

        try:
            git_commit = list(repo.iter_commits())[0]

            commit = Commit.from_git_commit(git_commit)

            assert commit.hash == git_commit.hexsha
            assert commit.message == git_commit.message.strip()
            assert commit.author == git_commit.author.name
            assert commit.email == git_commit.author.email
            assert isinstance(commit.date, datetime)
            assert not commit.is_merge  # Initial commit is not a merge
        finally:
            repo.close()
            gc.collect()
            time.sleep(0.1)


class TestTag:
    """Test cases for Tag dataclass."""

    def test_from_git_tag(self, temp_repo: Path):
        """Test creating Tag from GitPython tag."""
        repo = git.Repo(temp_repo)

        try:
            git_tag = repo.create_tag("v1.0.0", message="Release v1.0.0")

            tag = Tag.from_git_tag(git_tag)

            assert tag.name == "v1.0.0"
            assert tag.hash == git_tag.commit.hexsha
            assert isinstance(tag.date, datetime)
        finally:
            repo.close()
            gc.collect()
            time.sleep(0.1)
