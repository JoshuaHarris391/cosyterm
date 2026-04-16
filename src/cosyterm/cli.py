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
from cosyterm.core import setup, doctor, install_step, INSTALL_STEPS
import cosyterm.restore as restore_mod


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
        "-v", "--version",
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

    install_parser = subparsers.add_parser(
        "install",
        help="Re-run a specific setup step",
    )
    install_parser.add_argument(
        "step",
        choices=INSTALL_STEPS,
        help="Step to install (e.g. font, ghostty, starship)",
    )

    restore_parser = subparsers.add_parser(
        "restore",
        help="Undo a previous install by restoring from a backup",
    )
    restore_parser.add_argument(
        "--list", action="store_true",
        help="List available backups",
    )
    restore_parser.add_argument(
        "--latest", action="store_true",
        help="Restore from the most recent backup",
    )
    restore_parser.add_argument(
        "--from", dest="from_ts", metavar="TIMESTAMP",
        help="Restore from the backup with this timestamp (e.g. 20260416_140523)",
    )
    restore_parser.add_argument(
        "--only", metavar="STEP",
        help="Only restore entries for this step (e.g. neovim)",
    )
    restore_parser.add_argument(
        "--verify", action="store_true",
        help="Verify a backup's integrity without restoring",
    )
    restore_parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would happen without touching anything",
    )

    args = parser.parse_args()

    # Print the banner
    print(BANNER)
    print(f"  \033[90mv{__version__} — https://github.com/JoshuaHarris391/cosyterm\033[0m")
    print()

    if args.command == "doctor":
        issues = doctor()
        sys.exit(1 if issues > 0 else 0)
    elif args.command == "install":
        sys.exit(install_step(args.step))
    elif args.command == "restore":
        if args.list:
            sys.exit(restore_mod.print_list())
        if args.verify:
            sys.exit(restore_mod.verify(latest=args.latest, timestamp=args.from_ts))
        if not args.latest and not args.from_ts:
            print(
                "cosyterm restore: specify --latest, --from <timestamp>, or --list",
                file=sys.stderr,
            )
            sys.exit(2)
        sys.exit(restore_mod.restore(
            latest=args.latest,
            timestamp=args.from_ts,
            only=args.only,
            dry_run=args.dry_run,
        ))
    else:
        # Default action: run setup
        sys.exit(setup())


if __name__ == "__main__":
    main()
