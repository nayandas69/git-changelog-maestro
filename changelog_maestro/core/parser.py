"""Conventional Commits parser."""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..utils.exceptions import ParseError


@dataclass
class ParsedCommit:
    """Represents a parsed conventional commit."""

    type: str
    scope: Optional[str]
    description: str
    body: Optional[str]
    footer: Optional[str]
    is_breaking: bool
    breaking_change_description: Optional[str] = None

    @property
    def is_feature(self) -> bool:
        """Check if commit is a feature."""
        return self.type == "feat"

    @property
    def is_fix(self) -> bool:
        """Check if commit is a bug fix."""
        return self.type == "fix"

    @property
    def formatted_scope(self) -> str:
        """Get formatted scope for display."""
        return f"({self.scope})" if self.scope else ""

    @property
    def short_description(self) -> str:
        """Get short description (first line of description)."""
        return self.description.split("\n")[0] if self.description else ""


class ConventionalCommitParser:
    """Parser for Conventional Commits specification."""

    # Regex pattern for conventional commit format
    COMMIT_PATTERN = re.compile(
        r"^(?P<type>\w+)"
        r"(?:\((?P<scope>[^)]+)\))?"
        r"(?P<breaking>!)?"
        r": (?P<description>.+?)(?:\n\n(?P<body>.*))?$",
        re.DOTALL,
    )

    # Breaking change footer patterns
    BREAKING_CHANGE_PATTERNS = [
        re.compile(r"^BREAKING CHANGE:\s*(.+)", re.MULTILINE | re.IGNORECASE),
        re.compile(r"^BREAKING-CHANGE:\s*(.+)", re.MULTILINE | re.IGNORECASE),
    ]

    def __init__(self, breaking_change_indicators: Optional[List[str]] = None) -> None:
        """Initialize parser with optional custom breaking change indicators."""
        self.breaking_change_indicators = breaking_change_indicators or [
            "BREAKING CHANGE",
            "BREAKING-CHANGE",
        ]

    def parse(self, commit_message: str) -> ParsedCommit:
        """Parse a commit message according to Conventional Commits spec."""
        if not commit_message.strip():
            raise ParseError("Empty commit message")

        # Clean up the commit message
        message = commit_message.strip()

        # Try to match the conventional commit pattern
        match = self.COMMIT_PATTERN.match(message)
        if not match:
            raise ParseError(
                f"Commit message does not follow Conventional Commits format: {message[:50]}..."
            )

        groups = match.groupdict()

        # Extract basic components
        commit_type = groups["type"].lower()
        scope = groups.get("scope")
        description = groups["description"].strip()
        body = groups.get("body", "").strip() if groups.get("body") else None

        # Check for breaking change indicator in type (!)
        is_breaking_from_type = bool(groups.get("breaking"))

        # Parse body and footer
        body_parts = self._parse_body_and_footer(body) if body else (None, None)
        parsed_body, footer = body_parts

        # Check for breaking changes in footer
        breaking_change_desc = self._extract_breaking_change(footer or "")
        is_breaking_from_footer = bool(breaking_change_desc)

        is_breaking = is_breaking_from_type or is_breaking_from_footer

        return ParsedCommit(
            type=commit_type,
            scope=scope,
            description=description,
            body=parsed_body,
            footer=footer,
            is_breaking=is_breaking,
            breaking_change_description=breaking_change_desc,
        )

    def _parse_body_and_footer(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """Parse body and footer from commit message text."""
        if not text:
            return None, None

        # Split on double newlines to separate body from footer
        parts = text.split("\n\n")

        if len(parts) == 1:
            # Only body, no footer
            return parts[0].strip(), None

        # Check if last part looks like footer (contains colons)
        potential_footer = parts[-1]
        if ":" in potential_footer and any(
            line.strip() and ":" in line for line in potential_footer.split("\n")
        ):
            # Last part is footer
            body_parts = parts[:-1]
            body = "\n\n".join(body_parts).strip() if body_parts else None
            footer = potential_footer.strip()
            return body, footer
        else:
            # All parts are body
            return text.strip(), None

    def _extract_breaking_change(self, footer: str) -> Optional[str]:
        """Extract breaking change description from footer."""
        if not footer:
            return None

        for pattern in self.BREAKING_CHANGE_PATTERNS:
            match = pattern.search(footer)
            if match:
                return match.group(1).strip()

        return None

    def is_valid_commit_type(self, commit_type: str) -> bool:
        """Check if commit type is valid."""
        # Common conventional commit types
        valid_types = {
            "feat",
            "fix",
            "docs",
            "style",
            "refactor",
            "perf",
            "test",
            "build",
            "ci",
            "chore",
            "revert",
        }
        return commit_type.lower() in valid_types

    def parse_multiple(self, commit_messages: List[str]) -> List[ParsedCommit]:
        """Parse multiple commit messages."""
        parsed_commits = []
        for message in commit_messages:
            try:
                parsed_commit = self.parse(message)
                parsed_commits.append(parsed_commit)
            except ParseError:
                # Skip invalid commits
                continue
        return parsed_commits
