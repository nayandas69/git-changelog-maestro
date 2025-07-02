"""Configuration management for Git Changelog Maestro."""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        import tomllib


class Config(BaseModel):
    """Configuration for changelog generation."""

    output_file: str = Field(default="CHANGELOG.md", description="Output file path")
    template_path: Optional[Path] = Field(
        default=None, description="Custom template file"
    )
    version_prefix: str = Field(default="v", description="Version prefix")
    output_style: str = Field(default="markdown", description="Output format")
    since_tag: Optional[str] = Field(
        default=None, description="Generate from specific tag"
    )
    until_tag: Optional[str] = Field(
        default=None, description="Generate until specific tag"
    )
    sections: List[str] = Field(
        default_factory=list, description="Custom sections to include"
    )
    exclude_patterns: List[str] = Field(
        default_factory=list, description="Patterns to exclude"
    )
    include_merges: bool = Field(default=False, description="Include merge commits")

    # Commit type mappings
    commit_types: Dict[str, str] = Field(
        default_factory=lambda: {
            "feat": "Features",
            "fix": "Bug Fixes",
            "docs": "Documentation",
            "style": "Styles",
            "refactor": "Code Refactoring",
            "perf": "Performance Improvements",
            "test": "Tests",
            "build": "Builds",
            "ci": "Continuous Integration",
            "chore": "Chores",
            "revert": "Reverts",
        },
        description="Mapping of commit types to section names",
    )

    # Breaking change indicators
    breaking_change_indicators: List[str] = Field(
        default_factory=lambda: ["BREAKING CHANGE", "BREAKING-CHANGE"],
        description="Indicators for breaking changes",
    )

    @classmethod
    def load_from_file(cls, config_path: Path) -> "Config":
        """Load configuration from pyproject.toml file."""
        if not config_path.exists():
            return cls()

        try:
            with open(config_path, "rb") as f:
                data = tomllib.load(f)

            changelog_config = data.get("tool", {}).get("changelog-maestro", {})
            return cls(**changelog_config)

        except Exception:
            # If config loading fails, return default config
            return cls()

    def get_section_name(self, commit_type: str) -> str:
        """Get section name for a commit type."""
        return self.commit_types.get(commit_type, commit_type.title())

    def should_include_commit_type(self, commit_type: str) -> bool:
        """Check if a commit type should be included in the changelog."""
        if self.sections:
            return commit_type in self.sections
        return commit_type in self.commit_types
