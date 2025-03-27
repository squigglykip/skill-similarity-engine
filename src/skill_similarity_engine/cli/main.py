"""
Command-line interface for the Skill Similarity Engine.

This module provides the main CLI entry point and command registration.
"""

import click

from .config_cmd import register_commands as register_config_commands


@click.group()
@click.version_option()
def cli():
    """Skill Similarity Engine - A tool for analyzing skill similarities and gaps."""
    pass


# Register commands from modules
register_config_commands(cli)


def main():
    """Main entry point for the CLI."""
    cli() 