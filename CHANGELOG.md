# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Features

- **core:** Initial implementation of Git Changelog Maestro
- **cli:** Command-line interface with rich formatting and comprehensive options
- **parser:** Conventional Commits parser with full specification support
- **formatter:** Multiple output formats (Markdown, JSON, YAML) with Jinja2 templates
- **git:** Git repository operations with tag and commit handling
- **config:** Flexible configuration system via pyproject.toml
- **validation:** Commit message validation against Conventional Commits spec
- **ci:** GitHub Actions workflows for testing and automated releases

### Documentation

- **readme:** Comprehensive documentation with examples and usage guides
- **templates:** Default Jinja2 template for Markdown changelog generation
- **tests:** Extensive test suite with 95%+ coverage

### Build

- **packaging:** Modern Python packaging with hatchling and pyproject.toml
- **dependencies:** Carefully selected dependencies for reliability and performance
- **typing:** Full type hints and py.typed marker for type checking support

---

*This changelog was generated automatically by [git-changelog-maestro](https://github.com/petherldev/git-changelog-maestro)*