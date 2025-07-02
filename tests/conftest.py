"""Pytest configuration and fixtures."""

import gc
import os
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Generator

import git
import pytest

from changelog_maestro.core.config import Config
from changelog_maestro.core.git import Commit, GitRepository


def force_remove_readonly(func, path, exc):
    """Force remove readonly files on Windows."""
    if os.path.exists(path):
        os.chmod(path, 0o777)
        func(path)


@pytest.fixture
def temp_repo() -> Generator[Path, None, None]:
    """Create a temporary Git repository for testing."""
    temp_dir = tempfile.mkdtemp()
    repo_path = Path(temp_dir)
    repo = None

    try:
        # Initialize Git repository
        repo = git.Repo.init(repo_path)

        # Configure Git user
        repo.config_writer().set_value("user", "name", "Test User").release()
        repo.config_writer().set_value("user", "email", "test@example.com").release()

        # Create initial commit
        readme_file = repo_path / "README.md"
        readme_file.write_text("# Test Repository\n")
        repo.index.add([str(readme_file)])
        repo.index.commit("Initial commit")

        yield repo_path

    finally:
        # Aggressive cleanup for Windows
        try:
            if repo is not None:
                repo.close()
                del repo
            gc.collect()
            time.sleep(0.2)  # Give Windows more time

            # Force remove the directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, onerror=force_remove_readonly)
        except Exception:
            # If cleanup fails, try again after a longer delay
            try:
                time.sleep(0.5)
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, onerror=force_remove_readonly)
            except Exception:
                pass  # Give up if we still can't clean up


@pytest.fixture
def sample_commits() -> list[Commit]:
    """Sample commits for testing."""
    return [
        Commit(
            hash="abc123",
            message="feat: add new feature",
            author="Test User",
            email="test@example.com",
            date=datetime(2023, 1, 1, 12, 0, 0),
        ),
        Commit(
            hash="def456",
            message="fix: resolve bug in parser",
            author="Test User",
            email="test@example.com",
            date=datetime(2023, 1, 2, 12, 0, 0),
        ),
        Commit(
            hash="ghi789",
            message="feat!: breaking change in API",
            author="Test User",
            email="test@example.com",
            date=datetime(2023, 1, 3, 12, 0, 0),
        ),
    ]


@pytest.fixture
def default_config() -> Config:
    """Default configuration for testing."""
    return Config()


@pytest.fixture
def git_repo(temp_repo: Path) -> GitRepository:
    """GitRepository instance for testing."""
    return GitRepository(temp_repo)
