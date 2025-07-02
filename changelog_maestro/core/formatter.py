"""Changelog formatting utilities."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, Template

from ..utils.exceptions import FormatterError
from .git import Commit, Tag
from .parser import ParsedCommit


class ChangelogEntry:
    """Represents a changelog entry for a version."""

    def __init__(self, version: str, date: Optional[datetime] = None) -> None:
        self.version = version
        self.date = date or datetime.now()
        self.sections: Dict[str, List[ParsedCommit]] = {}
        self.breaking_changes: List[ParsedCommit] = []

    def add_commit(self, commit: ParsedCommit, section_name: str) -> None:
        """Add a commit to the appropriate section."""
        if section_name not in self.sections:
            self.sections[section_name] = []

        self.sections[section_name].append(commit)

        if commit.is_breaking:
            self.breaking_changes.append(commit)

    def has_changes(self) -> bool:
        """Check if this entry has any changes."""
        return bool(self.sections) or bool(self.breaking_changes)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "version": self.version,
            "date": self.date.isoformat(),
            "sections": {
                section: [
                    {
                        "type": commit.type,
                        "scope": commit.scope,
                        "description": commit.description,
                        "body": commit.body,
                        "is_breaking": commit.is_breaking,
                        "breaking_change_description": commit.breaking_change_description,
                    }
                    for commit in commits
                ]
                for section, commits in self.sections.items()
            },
            "breaking_changes": [
                {
                    "type": commit.type,
                    "scope": commit.scope,
                    "description": commit.description,
                    "breaking_change_description": commit.breaking_change_description,
                }
                for commit in self.breaking_changes
            ],
        }


class ChangelogFormatter:
    """Formats changelog entries into various output formats."""

    def __init__(self, template_path: Optional[Path] = None) -> None:
        """Initialize formatter with optional custom template."""
        self.template_path = template_path
        self._setup_jinja_env()

    def _setup_jinja_env(self) -> None:
        """Setup Jinja2 environment."""
        if self.template_path and self.template_path.exists():
            # Use custom template
            template_dir = self.template_path.parent
            template_name = self.template_path.name
            self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
            self.template_name = template_name
        else:
            # Use built-in templates
            templates_dir = Path(__file__).parent.parent / "templates"
            self.jinja_env = Environment(loader=FileSystemLoader(templates_dir))
            self.template_name = "default.md.j2"

        # Add custom filters
        self.jinja_env.filters["format_date"] = self._format_date
        self.jinja_env.filters["format_scope"] = self._format_scope

    def format_markdown(self, entries: List[ChangelogEntry]) -> str:
        """Format changelog entries as Markdown."""
        try:
            template = self.jinja_env.get_template(self.template_name)
            return template.render(entries=entries, now=datetime.now())
        except Exception as e:
            raise FormatterError(f"Failed to format Markdown: {e}")

    def format_json(self, entries: List[ChangelogEntry]) -> str:
        """Format changelog entries as JSON."""
        try:
            data = {
                "changelog": [entry.to_dict() for entry in entries],
                "generated_at": datetime.now().isoformat(),
            }
            return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception as e:
            raise FormatterError(f"Failed to format JSON: {e}")

    def format_yaml(self, entries: List[ChangelogEntry]) -> str:
        """Format changelog entries as YAML."""
        try:
            import yaml
        except ImportError:
            raise FormatterError("PyYAML is required for YAML output format")

        try:
            data = {
                "changelog": [entry.to_dict() for entry in entries],
                "generated_at": datetime.now().isoformat(),
            }
            result = yaml.dump(data, default_flow_style=False, allow_unicode=True)
            assert isinstance(result, str)
            return result
        except Exception as e:
            raise FormatterError(f"Failed to format YAML: {e}")

    def format(self, entries: List[ChangelogEntry], output_format: str) -> str:
        """Format changelog entries in the specified format."""
        formatters = {
            "markdown": self.format_markdown,
            "json": self.format_json,
            "yaml": self.format_yaml,
        }

        formatter = formatters.get(output_format.lower())
        if not formatter:
            raise FormatterError(f"Unsupported output format: {output_format}")

        return formatter(entries)

    @staticmethod
    def _format_date(date: datetime) -> str:
        """Format date for display."""
        return date.strftime("%Y-%m-%d")

    @staticmethod
    def _format_scope(scope: Optional[str]) -> str:
        """Format scope for display."""
        return f"({scope})" if scope else ""
