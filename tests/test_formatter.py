"""Tests for changelog formatting."""

from datetime import datetime
from pathlib import Path

import pytest

from changelog_maestro.core.formatter import ChangelogEntry, ChangelogFormatter
from changelog_maestro.core.parser import ParsedCommit
from changelog_maestro.utils.exceptions import FormatterError


class TestChangelogEntry:
    """Test cases for ChangelogEntry."""

    def test_create_entry(self):
        """Test creating a changelog entry."""
        entry = ChangelogEntry("1.0.0", datetime(2023, 1, 1))

        assert entry.version == "1.0.0"
        assert entry.date == datetime(2023, 1, 1)
        assert entry.sections == {}
        assert entry.breaking_changes == []
        assert not entry.has_changes()

    def test_add_commit(self):
        """Test adding commits to entry."""
        entry = ChangelogEntry("1.0.0")

        commit = ParsedCommit(
            type="feat",
            scope=None,
            description="add new feature",
            body=None,
            footer=None,
            is_breaking=False,
        )

        entry.add_commit(commit, "Features")

        assert "Features" in entry.sections
        assert len(entry.sections["Features"]) == 1
        assert entry.sections["Features"][0] == commit
        assert entry.has_changes()

    def test_add_breaking_change(self):
        """Test adding breaking change commit."""
        entry = ChangelogEntry("1.0.0")

        commit = ParsedCommit(
            type="feat",
            scope=None,
            description="breaking change",
            body=None,
            footer=None,
            is_breaking=True,
            breaking_change_description="This breaks the API",
        )

        entry.add_commit(commit, "Features")

        assert len(entry.breaking_changes) == 1
        assert entry.breaking_changes[0] == commit

    def test_to_dict(self):
        """Test converting entry to dictionary."""
        entry = ChangelogEntry("1.0.0", datetime(2023, 1, 1))

        commit = ParsedCommit(
            type="feat",
            scope="api",
            description="add endpoint",
            body="Detailed description",
            footer=None,
            is_breaking=False,
        )

        entry.add_commit(commit, "Features")

        result = entry.to_dict()

        assert result["version"] == "1.0.0"
        assert result["date"] == "2023-01-01T00:00:00"
        assert "Features" in result["sections"]
        assert len(result["sections"]["Features"]) == 1

        commit_dict = result["sections"]["Features"][0]
        assert commit_dict["type"] == "feat"
        assert commit_dict["scope"] == "api"
        assert commit_dict["description"] == "add endpoint"


class TestChangelogFormatter:
    """Test cases for ChangelogFormatter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = ChangelogFormatter()

    def test_format_markdown(self):
        """Test formatting as Markdown."""
        entry = ChangelogEntry("1.0.0", datetime(2023, 1, 1))

        commit = ParsedCommit(
            type="feat",
            scope=None,
            description="add new feature",
            body=None,
            footer=None,
            is_breaking=False,
        )

        entry.add_commit(commit, "Features")

        result = self.formatter.format_markdown([entry])

        assert "# Changelog" in result
        assert "## [1.0.0] - 2023-01-01" in result
        assert "### Features" in result
        assert "add new feature" in result

    def test_format_json(self):
        """Test formatting as JSON."""
        entry = ChangelogEntry("1.0.0", datetime(2023, 1, 1))

        commit = ParsedCommit(
            type="feat",
            scope=None,
            description="add new feature",
            body=None,
            footer=None,
            is_breaking=False,
        )

        entry.add_commit(commit, "Features")

        result = self.formatter.format_json([entry])

        assert '"changelog"' in result
        assert '"version": "1.0.0"' in result
        assert '"type": "feat"' in result
        assert '"description": "add new feature"' in result

    def test_format_yaml(self):
        """Test formatting as YAML."""
        entry = ChangelogEntry("1.0.0", datetime(2023, 1, 1))

        commit = ParsedCommit(
            type="feat",
            scope=None,
            description="add new feature",
            body=None,
            footer=None,
            is_breaking=False,
        )

        entry.add_commit(commit, "Features")

        result = self.formatter.format_yaml([entry])

        assert "changelog:" in result
        assert "version: 1.0.0" in result
        assert "type: feat" in result
        assert "description: add new feature" in result

    def test_format_with_breaking_changes(self):
        """Test formatting with breaking changes."""
        entry = ChangelogEntry("2.0.0", datetime(2023, 2, 1))

        commit = ParsedCommit(
            type="feat",
            scope="api",
            description="breaking change",
            body=None,
            footer=None,
            is_breaking=True,
            breaking_change_description="This breaks the API",
        )

        entry.add_commit(commit, "Features")

        result = self.formatter.format_markdown([entry])

        assert "⚠ BREAKING CHANGES" in result
        assert "This breaks the API" in result

    def test_format_unsupported_format(self):
        """Test formatting with unsupported format."""
        entry = ChangelogEntry("1.0.0")

        with pytest.raises(FormatterError):
            self.formatter.format([entry], "unsupported")

    def test_format_date_filter(self):
        """Test date formatting filter."""
        date = datetime(2023, 12, 25, 15, 30, 45)
        result = ChangelogFormatter._format_date(date)
        assert result == "2023-12-25"

    def test_format_scope_filter(self):
        """Test scope formatting filter."""
        assert ChangelogFormatter._format_scope("api") == "(api)"
        assert ChangelogFormatter._format_scope(None) == ""
        assert ChangelogFormatter._format_scope("") == ""
