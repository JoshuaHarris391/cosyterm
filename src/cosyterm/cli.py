"""
CLI entry point for cosyterm.

Usage:
    cosyterm          Run the full interactive setup
    cosyterm doctor   Check your setup for issues
    cosyterm --help   Show help
"""

import sys
import argparse

from cosyterm import __version__
from cosyterm.core import setup, doctor


BANNER = r"""
\033[38;5;183m
                        ______
  _________  _______  _/_  __/__  _________ ___
 / ___/ __ \/ ___/ / / // / / _ \/ ___/ __ `__ \
/ /__/ /_/ (__  ) /_/ // / /  __/ /  / / / / / /
\___/\____/____/\__, //_/  \___/_/  /_/ /_/ /_/
               /____/\033[0m
"""


def main():
    parser = argparse.ArgumentParser(
        prog="cosyterm",
        description="cosyTerm — your terminal, but make it cozy.",
        epilog="Run 'cosyterm' with no arguments to start the interactive setup.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"cosyterm {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "setup",
        help="Run the full interactive terminal setup (default)",
    )

    subparsers.add_parser(
        "doctor",
        help="Check your terminal setup for issues and mismatches",
    )

    args = parser.parse_args()

    # Print the banner
    print(BANNER)
    print(f"  \033[90mv{__version__} — https://github.com/JoshuaHarris391/cosyterm\033[0m")
    print()

    if args.command == "doctor":
        issues = doctor()
        sys.exit(1 if issues > 0 else 0)
    else:
        # Default action: run setup
        sys.exit(setup())


if __name__ == "__main__":
    main()
