"""
Lidl Receipt Data Updater - Entry Point

This is the main entry point for the shopping analyzer application.
For first-time setup or complete refresh, use the 'initial' command.
For monthly updates (adds only new data and sorts by date), use the 'update' command.

Usage:
    python get_data.py                             # Interactive menu
    python get_data.py initial --browser firefox   # Non-interactive initial setup
    python get_data.py update --browser chromium   # Non-interactive update
    python get_data.py initial --cookies-file cookies.json  # Use cookie file
    python get_data.py update --country bg --browser chromium  # Bulgaria
"""

import argparse
import sys

from cli import main
from config import LidlConfig
from workflows import initial_setup, update_data


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="get_data.py",
        description="Extract and manage Lidl receipt data from your online purchase history.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Common arguments for both subcommands
    def add_common_args(subparser: argparse.ArgumentParser) -> None:
        group = subparser.add_mutually_exclusive_group()
        group.add_argument(
            "--browser",
            choices=["firefox", "chrome", "chromium"],
            help="Browser to extract cookies from (non-interactive mode)",
        )
        group.add_argument(
            "--cookies-file",
            metavar="FILE",
            help="Path to cookies JSON file (non-interactive mode)",
        )
        subparser.add_argument(
            "--country",
            metavar="CODE",
            help="Two-letter country code (e.g., 'de', 'bg', 'nl'). Default: de",
        )

    # Initial setup subcommand
    initial_parser = subparsers.add_parser(
        "initial",
        help="Extract all historical receipt data (first-time setup)",
    )
    add_common_args(initial_parser)

    # Update subcommand
    update_parser = subparsers.add_parser(
        "update",
        help="Add only new receipts since last run",
    )
    add_common_args(update_parser)

    return parser


def run_workflow(args: argparse.Namespace, workflow_func) -> bool:
    """Run a workflow with the appropriate auth method."""
    # Set country if provided
    if args.country:
        LidlConfig.set_country(args.country)

    if args.browser:
        return workflow_func(auth_method=args.browser)
    elif args.cookies_file:
        return workflow_func(auth_method="file", cookies_file=args.cookies_file)
    else:
        # Interactive mode
        return workflow_func()


if __name__ == "__main__":
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "initial":
        success = run_workflow(args, initial_setup)
        if success:
            print("✓ Initial Setup erfolgreich abgeschlossen!")
        else:
            print("✗ Initial Setup fehlgeschlagen!")
            sys.exit(1)

    elif args.command == "update":
        success = run_workflow(args, update_data)
        if success:
            print("✓ Update erfolgreich abgeschlossen!")
        else:
            print("✗ Update fehlgeschlagen!")
            sys.exit(1)

    else:
        # No subcommand - run interactive menu
        main()
