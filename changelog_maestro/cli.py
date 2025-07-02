"""Command-line interface for Git Changelog Maestro."""

import sys
from pathlib import Path
from typing import List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .core.config import Config
from .core.generator import ChangelogGenerator
from .utils.exceptions import ChangelogError

console = Console()


def print_error(message: str) -> None:
    """Print error message with rich formatting."""
    console.print(f"[red]Error:[/red] {message}")


def print_success(message: str) -> None:
    """Print success message with rich formatting."""
    console.print(f"[green]✓[/green] {message}")


def print_info(message: str) -> None:
    """Print info message with rich formatting."""
    console.print(f"[blue]ℹ[/blue] {message}")


@click.group(invoke_without_command=True)
@click.option(
    "--repo-path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help="Git repository path [default: current directory]",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=Path("CHANGELOG.md"),
    help="Output file [default: CHANGELOG.md]",
)
@click.option(
    "--template",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Custom template file",
)
@click.option("--since", help="Generate from specific tag")
@click.option("--until", help="Generate until specific tag")
@click.option("--version-prefix", default="v", help="Version prefix [default: v]")
@click.option(
    "--style",
    type=click.Choice(["markdown", "json", "yaml"]),
    default="markdown",
    help="Output style [default: markdown]",
)
@click.option(
    "--sections",
    multiple=True,
    help="Custom sections to include (can be used multiple times)",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Patterns to exclude (can be used multiple times)",
)
@click.option("--no-merges", is_flag=True, help="Exclude merge commits")
@click.option("--verbose", "-v", is_flag=True, help="Increase output verbosity")
@click.pass_context
def cli(
    ctx: click.Context,
    repo_path: Path,
    output: Path,
    template: Optional[Path],
    since: Optional[str],
    until: Optional[str],
    version_prefix: str,
    style: str,
    sections: List[str],
    exclude: List[str],
    no_merges: bool,
    verbose: bool,
) -> None:
    """Generate elegant changelogs from Git commit history using Conventional Commits."""
    if ctx.invoked_subcommand is None:
        # Default behavior: generate changelog
        ctx.invoke(
            generate,
            repo_path=repo_path,
            output=output,
            template=template,
            since=since,
            until=until,
            version_prefix=version_prefix,
            style=style,
            sections=sections,
            exclude=exclude,
            no_merges=no_merges,
            verbose=verbose,
        )


@cli.command()
@click.option(
    "--repo-path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help="Git repository path [default: current directory]",
)
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    default=Path("CHANGELOG.md"),
    help="Output file [default: CHANGELOG.md]",
)
@click.option(
    "--template",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Custom template file",
)
@click.option("--since", help="Generate from specific tag")
@click.option("--until", help="Generate until specific tag")
@click.option("--version-prefix", default="v", help="Version prefix [default: v]")
@click.option(
    "--style",
    type=click.Choice(["markdown", "json", "yaml"]),
    default="markdown",
    help="Output style [default: markdown]",
)
@click.option(
    "--sections",
    multiple=True,
    help="Custom sections to include (can be used multiple times)",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Patterns to exclude (can be used multiple times)",
)
@click.option("--no-merges", is_flag=True, help="Exclude merge commits")
@click.option("--verbose", "-v", is_flag=True, help="Increase output verbosity")
def generate(
    repo_path: Path,
    output: Path,
    template: Optional[Path],
    since: Optional[str],
    until: Optional[str],
    version_prefix: str,
    style: str,
    sections: List[str],
    exclude: List[str],
    no_merges: bool,
    verbose: bool,
) -> None:
    """Generate changelog from Git commit history."""
    try:
        if verbose:
            print_info(f"Repository path: {repo_path}")
            print_info(f"Output file: {output}")
            print_info(f"Style: {style}")

        # Load configuration
        config = Config.load_from_file(repo_path / "pyproject.toml")

        # Override config with CLI options
        if template:
            config.template_path = template
        if since:
            config.since_tag = since
        if until:
            config.until_tag = until
        if version_prefix:
            config.version_prefix = version_prefix
        if style:
            config.output_style = style
        if sections:
            config.sections = list(sections)
        if exclude:
            config.exclude_patterns = list(exclude)
        if no_merges:
            config.include_merges = False

        # Generate changelog
        generator = ChangelogGenerator(repo_path, config)
        changelog_content = generator.generate()

        # Write output
        output.write_text(changelog_content, encoding="utf-8")

        print_success(f"Changelog generated successfully: {output}")

        if verbose:
            console.print(
                Panel(
                    Text(
                        changelog_content[:500] + "..."
                        if len(changelog_content) > 500
                        else changelog_content
                    ),
                    title="Generated Changelog Preview",
                    border_style="green",
                )
            )

    except ChangelogError as e:
        print_error(str(e))
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
@click.option(
    "--repo-path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help="Git repository path [default: current directory]",
)
def validate(repo_path: Path) -> None:
    """Validate commit messages against Conventional Commits specification."""
    try:
        from .core.git import GitRepository
        from .core.parser import ConventionalCommitParser

        git_repo = GitRepository(repo_path)
        parser = ConventionalCommitParser()

        commits = git_repo.get_commits()
        valid_count = 0
        invalid_commits = []

        for commit in commits:
            try:
                parser.parse(commit.message)
                valid_count += 1
            except Exception:
                invalid_commits.append(commit)

        total_commits = len(commits)

        console.print(f"\n[bold]Commit Validation Results[/bold]")
        console.print(f"Total commits: {total_commits}")
        console.print(f"[green]Valid commits: {valid_count}[/green]")
        console.print(f"[red]Invalid commits: {len(invalid_commits)}[/red]")

        if invalid_commits:
            console.print("\n[bold red]Invalid commits:[/bold red]")
            for commit in invalid_commits[:10]:  # Show first 10
                console.print(f"  {commit.hash[:8]}: {commit.message[:60]}...")

            if len(invalid_commits) > 10:
                console.print(f"  ... and {len(invalid_commits) - 10} more")

        if len(invalid_commits) > 0:
            sys.exit(1)
        else:
            print_success("All commits follow Conventional Commits specification!")

    except Exception as e:
        print_error(f"Validation failed: {e}")
        sys.exit(1)


@cli.command()
def init() -> None:
    """Initialize changelog configuration in current directory."""
    try:
        config_path = Path("pyproject.toml")

        if config_path.exists():
            # Read existing config and add changelog section
            content = config_path.read_text()
            if "[tool.changelog-maestro]" not in content:
                content += "\n\n[tool.changelog-maestro]\n"
                content += "# Changelog configuration\n"
                content += 'output_file = "CHANGELOG.md"\n'
                content += 'version_prefix = "v"\n'
                content += "include_merges = false\n"
                config_path.write_text(content)
                print_success(
                    "Added changelog configuration to existing pyproject.toml"
                )
            else:
                print_info("Changelog configuration already exists in pyproject.toml")
        else:
            # Create new pyproject.toml with changelog config
            content = """[tool.changelog-maestro]
# Changelog configuration
output_file = "CHANGELOG.md"
version_prefix = "v"
include_merges = false

# Commit types to include in changelog
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
"""
            config_path.write_text(content)
            print_success("Created pyproject.toml with changelog configuration")

    except Exception as e:
        print_error(f"Failed to initialize configuration: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
