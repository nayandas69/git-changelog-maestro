"""Custom exceptions for Git Changelog Maestro."""


class ChangelogError(Exception):
    """Base exception for changelog generation errors."""

    pass


class GitError(ChangelogError):
    """Exception for Git-related errors."""

    pass


class ParseError(ChangelogError):
    """Exception for commit parsing errors."""

    pass


class FormatterError(ChangelogError):
    """Exception for formatting errors."""

    pass


class ConfigError(ChangelogError):
    """Exception for configuration errors."""

    pass
