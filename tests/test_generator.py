"""Tests for changelog generator."""

import gc
import time
from datetime import datetime
from pathlib import Path

import git
import pytest

from changelog_maestro.core.config import Config
from changelog_maestro.core.generator import ChangelogGenerator
from changelog_maestro.core.git import GitRepository
from changelog_maestro.utils.exceptions import ChangelogError


class TestChangelogGenerator:
    """Test cases for ChangelogGenerator."""

    def test_init(self, temp_repo: Path):
        """Test initializing generator."""
        config = Config()
        generator = ChangelogGenerator(temp_repo, config)

        assert generator.repo_path == temp_repo
        assert generator.config == config
        assert isinstance(generator.git_repo, GitRepository)

    def test_generate_with_conventional_commits(self, temp_repo: Path):
        """Test generating changelog with conventional commits."""
        # Add conventional commits to repository
        repo = git.Repo(temp_repo)

        try:
            # Add feature commit
            feature_file = temp_repo / "feature.txt"
            feature_file.write_text("new feature")
            repo.index.add([str(feature_file)])
            repo.index.commit("feat: add new feature")

            # Add bug fix commit
            bug_file = temp_repo / "bug.txt"
            bug_file.write_text("bug fix")
            repo.index.add([str(bug_file)])
            repo.index.commit("fix: resolve critical bug")

            # Generate changelog
            generator = ChangelogGenerator(temp_repo)
            result = generator.generate()

            assert "# Changelog" in result
            assert "Unreleased" in result
            assert "Features" in result
            assert "Bug Fixes" in result
            assert "add new feature" in result
            assert "resolve critical bug" in result
        finally:
            repo.close()
            gc.collect()
            time.sleep(0.1)

    def test_generate_with_tags(self, temp_repo: Path):
        """Test generating changelog with version tags."""
        repo = git.Repo(temp_repo)

        try:
            # Add feature and create tag
            feature_file = temp_repo / "feature.txt"
            feature_file.write_text("new feature")
            repo.index.add([str(feature_file)])
            repo.index.commit("feat: add new feature")
            repo.create_tag("v1.0.0")

            # Add bug fix
            bug_file = temp_repo / "bug.txt"
            bug_file.write_text("bug fix")
            repo.index.add([str(bug_file)])
            repo.index.commit("fix: resolve bug")

            # Generate changelog
            generator = ChangelogGenerator(temp_repo)
            result = generator.generate()

            assert "## [1.0.0]" in result
            assert "add new feature" in result
            assert "resolve bug" in result
        finally:
            repo.close()
            gc.collect()
            time.sleep(0.1)

    def test_generate_no_commits(self, temp_repo: Path):
        """Test generating changelog with no valid commits."""
        repo = git.Repo(temp_repo)

        try:
            # Add non-conventional commit
            test_file = temp_repo / "test.txt"
            test_file.write_text("test")
            repo.index.add([str(test_file)])
            repo.index.commit("not a conventional commit")

            generator = ChangelogGenerator(temp_repo)

            with pytest.raises(
                ChangelogError, match="No valid conventional commits found"
            ):
                generator.generate()
        finally:
            repo.close()
            gc.collect()
            time.sleep(0.1)

    def test_generate_with_breaking_changes(self, temp_repo: Path):
        """Test generating changelog with breaking changes."""
        repo = git.Repo(temp_repo)

        try:
            # Add breaking change commit
            breaking_file = temp_repo / "breaking.txt"
            breaking_file.write_text("breaking change")
            repo.index.add([str(breaking_file)])
            repo.index.commit("feat!: breaking change in API")

            generator = ChangelogGenerator(temp_repo)
            result = generator.generate()

            assert "⚠ BREAKING CHANGES" in result
            assert "breaking change in API" in result
        finally:
            repo.close()
            gc.collect()
            time.sleep(0.1)

    def test_generate_with_exclude_patterns(self, temp_repo: Path):
        """Test generating changelog with exclude patterns."""
        repo = git.Repo(temp_repo)

        try:
            # Add commits using proper file operations
            feature_file = temp_repo / "feature.txt"
            feature_file.write_text("feature")
            repo.index.add([str(feature_file)])
            repo.index.commit("feat: add feature")

            bug_file = temp_repo / "bug.txt"
            bug_file.write_text("bug fix")
            repo.index.add([str(bug_file)])
            repo.index.commit("fix: resolve bug")

            chore_file = temp_repo / "chore.txt"
            chore_file.write_text("chore")
            repo.index.add([str(chore_file)])
            repo.index.commit("chore: update dependencies")

            # Configure to exclude chore commits
            config = Config(exclude_patterns=["chore"])
            generator = ChangelogGenerator(temp_repo, config)
            result = generator.generate()

            assert "add feature" in result
            assert "resolve bug" in result
            assert "update dependencies" not in result
        finally:
            repo.close()
            gc.collect()
            time.sleep(0.1)

    def test_generate_with_custom_sections(self, temp_repo: Path):
        """Test generating changelog with custom sections."""
        repo = git.Repo(temp_repo)

        try:
            # Add commits of different types
            feature_file = temp_repo / "feature.txt"
            feature_file.write_text("feature")
            repo.index.add([str(feature_file)])
            repo.index.commit("feat: add feature")

            bug_file = temp_repo / "bug.txt"
            bug_file.write_text("bug fix")
            repo.index.add([str(bug_file)])
            repo.index.commit("fix: resolve bug")

            docs_file = temp_repo / "docs.txt"
            docs_file.write_text("docs")
            repo.index.add([str(docs_file)])
            repo.index.commit("docs: update documentation")

            # Configure to only include features and fixes
            config = Config(sections=["feat", "fix"])
            generator = ChangelogGenerator(temp_repo, config)
            result = generator.generate()

            assert "add feature" in result
            assert "resolve bug" in result
            assert "update documentation" not in result
        finally:
            repo.close()
            gc.collect()
            time.sleep(0.1)

    def test_generate_json_format(self, temp_repo: Path):
        """Test generating changelog in JSON format."""
        repo = git.Repo(temp_repo)

        try:
            # Add conventional commit
            feature_file = temp_repo / "feature.txt"
            feature_file.write_text("feature")
            repo.index.add([str(feature_file)])
            repo.index.commit("feat: add new feature")

            # Configure JSON output
            config = Config(output_style="json")
            generator = ChangelogGenerator(temp_repo, config)
            result = generator.generate()

            assert '"changelog"' in result
            assert '"type": "feat"' in result
            assert '"description": "add new feature"' in result
        finally:
            repo.close()
            gc.collect()
            time.sleep(0.1)

    def test_generate_yaml_format(self, temp_repo: Path):
        """Test generating changelog in YAML format."""
        repo = git.Repo(temp_repo)

        try:
            # Add conventional commit
            feature_file = temp_repo / "feature.txt"
            feature_file.write_text("feature")
            repo.index.add([str(feature_file)])
            repo.index.commit("feat: add new feature")

            # Configure YAML output
            config = Config(output_style="yaml")
            generator = ChangelogGenerator(temp_repo, config)
            result = generator.generate()

            assert "changelog:" in result
            assert "type: feat" in result
            assert "description: add new feature" in result
        finally:
            repo.close()
            gc.collect()
            time.sleep(0.1)
