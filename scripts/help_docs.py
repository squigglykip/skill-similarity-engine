#!/usr/bin/env python3
"""
Script to generate comprehensive help documentation for the Skill Similarity Engine CLI.

This script outputs markdown documentation for all CLI commands in the skill
similarity engine, which can be incorporated into the project's README or docs.
"""

import os
import sys
import io
import click
from pathlib import Path
from contextlib import redirect_stdout

# Add the src directory to the path
src_path = str(Path(__file__).parent.parent / 'src')
sys.path.insert(0, src_path)

# Import the main CLI
sys.path.append(str(Path(__file__).parent))
from skillsim import cli


def generate_command_help(command, parent_name="skillsim"):
    """Generate help text for a command in markdown format."""
    ctx = click.Context(command, info_name=command.name, parent=click.Context(cli, info_name=parent_name))
    
    # Get command help text
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        click.echo(command.get_help(ctx))
    help_text = buffer.getvalue()
    
    markdown = f"## {parent_name} {command.name}\n\n"
    markdown += f"```\n{help_text}\n```\n\n"
    
    # Add information about options
    markdown += "### Options\n\n"
    for param in command.params:
        if isinstance(param, click.Option):
            opts = ", ".join(f"`{opt}`" for opt in param.opts)
            markdown += f"- {opts}: {param.help}\n"
    markdown += "\n"
    
    return markdown


def generate_cli_documentation():
    """Generate comprehensive documentation for the CLI."""
    markdown = "# Skill Similarity Engine CLI Documentation\n\n"
    markdown += "This document provides comprehensive documentation for the command-line interface of the Skill Similarity Engine.\n\n"
    
    # Main CLI help
    ctx = click.Context(cli, info_name="skillsim")
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        click.echo(cli.get_help(ctx))
    help_text = buffer.getvalue()
    markdown += "## Main Command\n\n"
    markdown += f"```\n{help_text}\n```\n\n"
    
    # Document each command
    markdown += "# Commands\n\n"
    for command in cli.commands.values():
        markdown += generate_command_help(command)
    
    return markdown


def main():
    """Generate CLI documentation and write to a file."""
    docs_dir = Path(__file__).parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    doc_path = docs_dir / "cli_documentation.md"
    
    markdown = generate_cli_documentation()
    
    with open(doc_path, "w") as f:
        f.write(markdown)
    
    print(f"CLI documentation generated at {doc_path}")


if __name__ == "__main__":
    main() 