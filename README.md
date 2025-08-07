# Git Changelog Maestro

**Git Changelog Maestro** is a modern CLI tool that automatically generates changelogs from your Git commit history. It supports **Conventional Commits**, multiple output styles (Markdown, JSON, YAML), custom templates, and integrates perfectly with **CI/CD pipelines**. Built for **developers, teams, and open-source maintainers** who want clean, automated changelogs with minimal effort.

[![PyPI version](https://badge.fury.io/py/git-changelog-maestro.svg)](https://badge.fury.io/py/git-changelog-maestro)
[![Python Support](https://img.shields.io/pypi/pyversions/git-changelog-maestro.svg)](https://pypi.org/project/git-changelog-maestro/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/petherldev/git-changelog-maestro/workflows/Tests/badge.svg)](https://github.com/petherldev/git-changelog-maestro/actions)
[![Coverage](https://codecov.io/gh/petherldev/git-changelog-maestro/branch/main/graph/badge.svg)](https://codecov.io/gh/petherldev/git-changelog-maestro)


## Features

| Feature                 | Description                                                             |
| ----------------------- | ----------------------------------------------------------------------- |
| Conventional Commits | Parses Git commit messages using the Conventional Commits specification |
| Multi-format Output  | Outputs changelogs in Markdown, JSON, or YAML                           |
| Custom Templates     | Use or create templates with Jinja2                                     |
| Semantic Versioning | Detects versions automatically from Git tags                            |
| Rich CLI             | Colorful, structured CLI output using Rich                              |
| Fast & Modern         | Built with modern Python and fully tested                               |
| Configurable         | Easily customize behavior via `pyproject.toml`                          |
| CI/CD Ready          | Seamless integration in release pipelines                               |


## Quick Start

### Installation

```bash
pip install git-changelog-maestro
```

### Basic Usage

```bash
changelog-maestro
```

This creates a `CHANGELOG.md` file in your current directory with all changes from the full Git history.

> \[!TIP]
> Use `--since <tag>` to generate changelogs from a specific point in time.


### Advanced Usage

```bash
# Generate changelog from specific tag
changelog-maestro --since v1.0.0

# Generate changelog between two tags
changelog-maestro --since v1.0.0 --until v2.0.0

# Output in JSON format
changelog-maestro --style json --output changelog.json

# Use custom template
changelog-maestro --template my-template.md.j2

# Exclude merge commits and specific patterns
changelog-maestro --no-merges --exclude "chore" --exclude "docs"

# Verbose output with preview
changelog-maestro --verbose
```


## CLI Reference

```
changelog-maestro [OPTIONS] COMMAND [ARGS]...

Options:
  --repo-path PATH         Git repository path [default: current]
  --output FILE            Output file [default: CHANGELOG.md]
  --template PATH          Custom template file
  --since TAG              Generate from specific tag
  --until TAG              Generate until specific tag
  --version-prefix TEXT    Version prefix [default: v]
  --style TEXT             Output style [default: markdown]
  --sections TEXT          Custom sections to include
  --exclude TEXT           Patterns to exclude
  --no-merges              Exclude merge commits
  --verbose                Increase output verbosity

Commands:
  generate    Generate changelog from Git commit history
  validate    Validate commit messages against Conventional Commits
  init        Initialize changelog configuration
```


## Configuration

You can configure Git Changelog Maestro via `pyproject.toml`.

```toml
[tool.changelog-maestro]
output_file = "CHANGELOG.md"
version_prefix = "v"
include_merges = false

[tool.changelog-maestro.commit_types]
feat = "Features"
fix = "Bug Fixes"
docs = "Documentation"
style = "Styles"
refactor = "Code Refactoring"
perf = "Performance Improvements"
test = "Tests"
build = "Builds"
ci = "Continuous Integration"
chore = "Chores"
revert = "Reverts"

breaking_change_indicators = ["BREAKING CHANGE", "BREAKING-CHANGE"]
exclude_patterns = ["wip", "temp"]
```

Initialize configuration interactively:

```bash
changelog-maestro init
```


## Conventional Commits

This tool supports the [Conventional Commits](https://www.conventionalcommits.org/) specification.

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Examples

```bash
# Feature
git commit -m "feat: add user authentication"

# Bug fix
git commit -m "fix: resolve login validation issue"

# Breaking change
git commit -m "feat!: change API response format"

# With scope
git commit -m "feat(auth): add OAuth2 support"

# With body and footer
git commit -m "feat: add user profiles

Allow users to create and customize their profiles
with avatar upload and bio information.

Closes #123"
```


## Custom Templates

Use custom templates written in Jinja2 for changelog formatting.

```jinja2
# custom-template.md.j2
# My Project Changelog

{% for entry in entries %}
## Version {{ entry.version }} ({{ entry.date | format_date }})

{% if entry.breaking_changes %}
### 💥 Breaking Changes
{% for commit in entry.breaking_changes %}
- {{ commit.description }}
{% endfor %}
{% endif %}

{% for section_name, commits in entry.sections.items() %}
### {{ section_name }}
{% for commit in commits %}
- {{ commit.description }}{% if commit.scope %} ({{ commit.scope }}){% endif %}
{% endfor %}
{% endfor %}
{% endfor %}
```

Run with:

```bash
changelog-maestro --template custom-template.md.j2
```


## Validation

```bash
changelog-maestro validate
```

> \[!CAUTION]
> This will scan your Git history and report any commits that do not comply with the Conventional Commits format.


## CI/CD Integration

### GitHub Actions

```yaml
name: Generate Changelog

on:
  push:
    tags:
      - 'v*'

jobs:
  changelog:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install changelog-maestro
        run: pip install git-changelog-maestro
      
      - name: Generate changelog
        run: changelog-maestro --since $(git describe --tags --abbrev=0 HEAD^)
      
      - name: Commit changelog
        run: |
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git config user.name "github-actions[bot]"
          git add CHANGELOG.md
          git commit -m "docs: update changelog for ${{ github.ref_name }}" || exit 0
          git push
```


## Development

### Setup

```bash
git clone https://github.com/petherldev/git-changelog-maestro.git
cd git-changelog-maestro
pip install -e ".[dev]"
```

### Testing

```bash
pytest                      # Run tests
pytest --cov=changelog_maestro    # With coverage
pytest -v                   # Verbose output
pytest tests/test_parser.py       # Single file
```

### Code Quality

```bash
black changelog_maestro tests     # Format
isort changelog_maestro tests     # Sort imports
flake8 changelog_maestro tests    # Lint
mypy changelog_maestro            # Type check
```

### Pre-commit

```bash
pre-commit install
pre-commit run --all-files
```


## Output Examples

### Markdown

```markdown
## [1.2.0] - 2023-12-01

### ⚠ BREAKING CHANGES

### Bug Fixes


- correct scope formatting in changelog template `(template)`

### Features


- add GitHub Actions workflow to auto-generate changelog on new tag `(ci)`


  Introduces changelog.yml which triggers on version tags (v*), 

  installs git-changelog-maestro, generates CHANGELOG.md, and commits it back to the repository.
```

### JSON

```json
{
  "changelog": [
    {
      "version": "1.2.0",
      "date": "2023-12-01T00:00:00",
      "sections": {
        "Features": [
          {
            "type": "feat",
            "scope": "auth",
            "description": "add OAuth2 authentication support",
            "body": null,
            "is_breaking": false
          }
        ]
      },
      "breaking_changes": []
    }
  ],
  "generated_at": "2023-12-01T10:30:00"
}
```


## Contributing

> \[!NOTE]
> Please open an issue before starting major work.

- [x] Fork the repo
- [x] Create a branch (`git checkout -b feat/your-feature`)
- [x] Code and add tests
- [x] Ensure all tests pass
- [x] Commit changes (`git commit -m "feat: your feature"`)
- [x] Push (`git push origin feat/your-feature`)
- [x] Open a PR 🎉


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file.


## Acknowledgments

* [Conventional Commits](https://www.conventionalcommits.org/)
* [Keep a Changelog](https://keepachangelog.com/)
* [Semantic Versioning](https://semver.org/)
* [Rich](https://github.com/Textualize/rich)
* [Click](https://click.palletsprojects.com/)


## Support

> \[!TIP]
> Check existing issues or create a new one if you need help.

* [Search Issues](https://github.com/petherldev/git-changelog-maestro/issues)
* [Open Issue](https://github.com/petherldev/git-changelog-maestro/issues/new)


Made with ❤️ by [HErl](https://github.com/petherldev)
