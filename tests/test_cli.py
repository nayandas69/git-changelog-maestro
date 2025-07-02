"""Tests for CLI interface."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from changelog_maestro.cli import cli, generate, init, validate


class TestCLI:
    """Test cases for CLI interface."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test CLI help output."""
        result = self.runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Generate elegant changelogs" in result.output
        assert "--repo-path" in result.output
        assert "--output" in result.output

    @patch("changelog_maestro.cli.ChangelogGenerator")
    def test_generate_command(self, mock_generator_class):
        """Test generate command."""
        # Mock the generator
        mock_generator = MagicMock()
        mock_generator.generate.return_value = "# Changelog\n\n## [1.0.0]\n"
        mock_generator_class.return_value = mock_generator

        with self.runner.isolated_filesystem():
            # Create a dummy git repo directory
            Path("test_repo").mkdir()

            result = self.runner.invoke(
                generate,
                ["--repo-path", "test_repo", "--output", "CHANGELOG.md", "--verbose"],
            )

            assert result.exit_code == 0
            assert "Changelog generated successfully" in result.output

            # Check that changelog file was created
            assert Path("CHANGELOG.md").exists()

    def test_generate_command_error(self):
        """Test generate command with error."""
        with self.runner.isolated_filesystem():
            # Try to generate from non-existent repo
            result = self.runner.invoke(
                generate,
                [
                    "--repo-path",
                    "nonexistent",
                ],
            )

            # Should exit with error code 1, but Click might return 2 for usage errors
            assert result.exit_code in [1, 2]
            assert "Error:" in result.output or "Usage:" in result.output

    @patch("changelog_maestro.core.git.GitRepository")
    @patch("changelog_maestro.core.parser.ConventionalCommitParser")
    def test_validate_command(self, mock_parser_class, mock_git_class):
        """Test validate command."""
        # Mock git repository and parser
        mock_commit = MagicMock()
        mock_commit.message = "feat: add feature"
        mock_commit.hash = "abc123"

        mock_git = MagicMock()
        mock_git.get_commits.return_value = [mock_commit]
        mock_git_class.return_value = mock_git

        mock_parser = MagicMock()
        mock_parser.parse.return_value = MagicMock()
        mock_parser_class.return_value = mock_parser

        with self.runner.isolated_filesystem():
            Path("test_repo").mkdir()

            result = self.runner.invoke(validate, ["--repo-path", "test_repo"])

            assert result.exit_code == 0
            assert "All commits follow Conventional Commits" in result.output

    @patch("changelog_maestro.core.git.GitRepository")
    @patch("changelog_maestro.core.parser.ConventionalCommitParser")
    def test_validate_command_with_invalid_commits(
        self, mock_parser_class, mock_git_class
    ):
        """Test validate command with invalid commits."""
        # Mock git repository
        mock_commit = MagicMock()
        mock_commit.message = "not conventional"
        mock_commit.hash = "abc123"

        mock_git = MagicMock()
        mock_git.get_commits.return_value = [mock_commit]
        mock_git_class.return_value = mock_git

        # Mock parser to raise exception for invalid commit
        mock_parser = MagicMock()
        mock_parser.parse.side_effect = Exception("Invalid format")
        mock_parser_class.return_value = mock_parser

        with self.runner.isolated_filesystem():
            Path("test_repo").mkdir()

            result = self.runner.invoke(validate, ["--repo-path", "test_repo"])

            assert result.exit_code == 1
            assert "Invalid commits:" in result.output

    def test_init_command_new_file(self):
        """Test init command creating new pyproject.toml."""
        with self.runner.isolated_filesystem():
            result = self.runner.invoke(init)

            assert result.exit_code == 0
            assert "Created pyproject.toml" in result.output

            # Check that file was created with correct content
            config_file = Path("pyproject.toml")
            assert config_file.exists()

            content = config_file.read_text()
            assert "[tool.changelog-maestro]" in content
            assert "output_file" in content

    def test_init_command_existing_file(self):
        """Test init command with existing pyproject.toml."""
        with self.runner.isolated_filesystem():
            # Create existing pyproject.toml
            existing_content = """[build-system]
requires = ["setuptools"]
"""
            Path("pyproject.toml").write_text(existing_content)

            result = self.runner.invoke(init)

            assert result.exit_code == 0
            assert "Added changelog configuration" in result.output

            # Check that configuration was added
            content = Path("pyproject.toml").read_text()
            assert "[build-system]" in content  # Original content preserved
            assert "[tool.changelog-maestro]" in content  # New content added

    def test_init_command_existing_config(self):
        """Test init command with existing changelog config."""
        with self.runner.isolated_filesystem():
            # Create pyproject.toml with existing changelog config
            existing_content = """[tool.changelog-maestro]
output_file = "CHANGELOG.md"
"""
            Path("pyproject.toml").write_text(existing_content)

            result = self.runner.invoke(init)

            assert result.exit_code == 0
            assert "already exists" in result.output

    def test_cli_default_behavior(self):
        """Test CLI default behavior (should invoke generate)."""
        with patch("changelog_maestro.cli.ChangelogGenerator") as mock_generator_class:
            mock_generator = MagicMock()
            mock_generator.generate.return_value = "# Changelog\n"
            mock_generator_class.return_value = mock_generator

            with self.runner.isolated_filesystem():
                Path("test_repo").mkdir()

                result = self.runner.invoke(cli, ["--repo-path", "test_repo"])

                assert result.exit_code == 0
                assert "Changelog generated successfully" in result.output
