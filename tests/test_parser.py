"""Tests for the conventional commits parser."""

import pytest

from changelog_maestro.core.parser import ConventionalCommitParser, ParsedCommit
from changelog_maestro.utils.exceptions import ParseError


class TestConventionalCommitParser:
    """Test cases for ConventionalCommitParser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ConventionalCommitParser()

    def test_parse_simple_commit(self):
        """Test parsing a simple conventional commit."""
        message = "feat: add new feature"
        result = self.parser.parse(message)

        assert result.type == "feat"
        assert result.scope is None
        assert result.description == "add new feature"
        assert result.body is None
        assert result.footer is None
        assert not result.is_breaking

    def test_parse_commit_with_scope(self):
        """Test parsing commit with scope."""
        message = "fix(parser): resolve parsing issue"
        result = self.parser.parse(message)

        assert result.type == "fix"
        assert result.scope == "parser"
        assert result.description == "resolve parsing issue"
        assert not result.is_breaking

    def test_parse_breaking_change_with_exclamation(self):
        """Test parsing breaking change with exclamation mark."""
        message = "feat!: breaking change in API"
        result = self.parser.parse(message)

        assert result.type == "feat"
        assert result.scope is None
        assert result.description == "breaking change in API"
        assert result.is_breaking

    def test_parse_breaking_change_with_scope(self):
        """Test parsing breaking change with scope and exclamation."""
        message = "feat(api)!: breaking change in API"
        result = self.parser.parse(message)

        assert result.type == "feat"
        assert result.scope == "api"
        assert result.description == "breaking change in API"
        assert result.is_breaking

    def test_parse_commit_with_body(self):
        """Test parsing commit with body."""
        message = "feat: add new feature\n\nThis is a detailed description of the feature.\nIt spans multiple lines."
        result = self.parser.parse(message)

        assert result.type == "feat"
        assert result.description == "add new feature"
        assert "detailed description" in result.body
        assert not result.is_breaking

    def test_parse_commit_with_breaking_change_footer(self):
        """Test parsing commit with breaking change in footer."""
        message = "feat: add new feature\n\nThis adds a new feature to the system.\n\nBREAKING CHANGE: This changes the API interface."
        result = self.parser.parse(message)

        assert result.type == "feat"
        assert result.description == "add new feature"
        assert result.is_breaking
        assert "changes the API interface" in result.breaking_change_description

    def test_parse_invalid_commit_format(self):
        """Test parsing invalid commit format."""
        message = "This is not a conventional commit"

        with pytest.raises(ParseError):
            self.parser.parse(message)

    def test_parse_empty_commit(self):
        """Test parsing empty commit message."""
        message = ""

        with pytest.raises(ParseError):
            self.parser.parse(message)

    def test_parse_multiple_commits(self):
        """Test parsing multiple commit messages."""
        messages = [
            "feat: add feature A",
            "fix: resolve bug B",
            "invalid commit message",
            "docs: update documentation",
        ]

        results = self.parser.parse_multiple(messages)

        # Should skip invalid commit
        assert len(results) == 3
        assert results[0].type == "feat"
        assert results[1].type == "fix"
        assert results[2].type == "docs"

    def test_is_valid_commit_type(self):
        """Test commit type validation."""
        assert self.parser.is_valid_commit_type("feat")
        assert self.parser.is_valid_commit_type("fix")
        assert self.parser.is_valid_commit_type("docs")
        assert not self.parser.is_valid_commit_type("invalid")

    def test_parsed_commit_properties(self):
        """Test ParsedCommit properties."""
        commit = ParsedCommit(
            type="feat",
            scope="api",
            description="add new endpoint",
            body=None,
            footer=None,
            is_breaking=False,
        )

        assert commit.is_feature
        assert not commit.is_fix
        assert commit.formatted_scope == "(api)"
        assert commit.short_description == "add new endpoint"

    def test_parsed_commit_without_scope(self):
        """Test ParsedCommit without scope."""
        commit = ParsedCommit(
            type="fix",
            scope=None,
            description="resolve issue",
            body=None,
            footer=None,
            is_breaking=False,
        )

        assert not commit.is_feature
        assert commit.is_fix
        assert commit.formatted_scope == ""
