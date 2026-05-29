"""Click CLI entry point for brother-printer."""

import sys

import click

from brother_printer.transport import discover
from brother_printer.transport.errors import TransportError


@click.group()
@click.version_option(package_name="brother_printer")
def main() -> None:
    """Brother PT-E920BT label printer CLI."""


@main.command("discover")
def discover_cmd() -> None:
    """List connected Brother PT-E920BT printers on USB."""
    try:
        printers = discover()
    except TransportError as exc:
        click.echo(str(exc), err=True)
        sys.exit(1)

    if not printers:
        click.echo("No Brother PT-E920BT printers found.", err=True)
        sys.exit(1)

    for printer in printers:
        click.echo(
            f"{printer.identifier}\t{printer.product}\t{printer.bus}:{printer.address}"
        )
