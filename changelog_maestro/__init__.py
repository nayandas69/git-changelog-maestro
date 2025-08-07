"""Git Changelog Maestro - Generate elegant changelogs from Git commit history."""

__version__ = "0.1.1"
__author__ = "petherldev"
__email__ = "petherl@protonmail.com"

from .core.formatter import ChangelogFormatter
from .core.generator import ChangelogGenerator
from .core.parser import ConventionalCommitParser

__all__ = ["ChangelogGenerator", "ConventionalCommitParser", "ChangelogFormatter"]
