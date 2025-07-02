"""Git Changelog Maestro - Generate elegant changelogs from Git commit history."""

__version__ = "0.1.0"
__author__ = "petherldev"
__email__ = "petherl@protonmail.com"

from .core.generator import ChangelogGenerator
from .core.parser import ConventionalCommitParser
from .core.formatter import ChangelogFormatter

__all__ = ["ChangelogGenerator", "ConventionalCommitParser", "ChangelogFormatter"]
