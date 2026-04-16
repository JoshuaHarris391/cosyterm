"""
Restore logic — reads the TSV manifest written by setup.sh and reverses
every recorded move/copy, returning a user's home to its pre-install state.

The manifest is written by the bash helpers `backup_move` and `backup_if_exists`
in setup.sh. Format:

    # cosyterm manifest v1
    # step<TAB>action<TAB>source<TAB>backup<TAB>timestamp
    neovim	move	/Users/x/.config/nvim	/Users/x/.terminal-setup-backups/20260416_140523/.config_nvim	2026-04-16T14:05:24Z

Restore processes entries in reverse order. For each entry:
  - If something currently lives at the original `source`, it is moved to a
    `pre-restore-<ts>/` directory inside the backup first (so 'undo the undo'
    is possible).
  - The backup is moved (or copied, depending on action) back to `source`.

The module is stdlib-only and mirrors the "no external deps" stance of the
rest of the Python code.
"""

from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ManifestEntry:
    """One row from manifest.tsv — a reversible operation recorded by setup.sh."""
    step: str
    action: str  # "move" or "copy"
    source: Path
    backup: Path
    timestamp: str


def _backups_root(home: Path | None = None) -> Path:
    """The dir under which every run's timestamped backup lives."""
    home = home or Path.home()
    return home / ".terminal-setup-backups"


def list_backups(home: Path | None = None) -> list[Path]:
    """Return every backup dir under the root, newest first.

    A backup dir is a direct child of ~/.terminal-setup-backups/ that contains
    a manifest.tsv. Dirs without a manifest are ignored — they are legacy
    backups from the pre-manifest era and can't be auto-restored.
    """
    root = _backups_root(home)
    if not root.is_dir():
        return []
    dirs = [d for d in root.iterdir() if d.is_dir() and (d / "manifest.tsv").is_file()]
    # Timestamped dir names sort chronologically as strings.
    return sorted(dirs, key=lambda p: p.name, reverse=True)


def resolve_backup(
    *,
    latest: bool = False,
    timestamp: str | None = None,
    home: Path | None = None,
) -> Path | None:
    """Find the backup dir to restore from.

    Exactly one selector is expected: `latest=True` or `timestamp="..."`.
    Returns None if no matching backup exists.
    """
    backups = list_backups(home=home)
    if not backups:
        return None
    if latest:
        return backups[0]
    if timestamp:
        target = _backups_root(home) / timestamp
        return target if target.is_dir() and (target / "manifest.tsv").is_file() else None
    return None


def read_manifest(backup_dir: Path) -> list[ManifestEntry]:
    """Parse manifest.tsv. Comment lines (starting with #) and blank lines are skipped."""
    manifest = backup_dir / "manifest.tsv"
    entries: list[ManifestEntry] = []
    with manifest.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) != 5:
                # Malformed row — skip rather than crash. A real tool would
                # log this; for our purposes, dropping an unreadable row is
                # safer than failing mid-restore.
                continue
            step, action, source, backup, ts = parts
            entries.append(ManifestEntry(
                step=step,
                action=action,
                source=Path(source),
                backup=Path(backup),
                timestamp=ts,
            ))
    return entries


def _pre_restore_dir(backup_dir: Path) -> Path:
    """Where the pre-restore snapshot of the current-state files goes."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    d = backup_dir / f"pre-restore-{ts}"
    d.mkdir(exist_ok=True)
    return d


def _stash_current(source: Path, stash_root: Path) -> Path | None:
    """If `source` currently exists, move it into the stash dir and return
    the stashed path. Used so restore is reversible: if the user regrets
    the restore, the post-install state they just threw away is still there.
    Returns None if source didn't exist.
    """
    if not source.exists() and not source.is_symlink():
        return None
    safe_name = str(source).lstrip("/").replace("/", "_")
    dest = stash_root / safe_name
    shutil.move(str(source), str(dest))
    return dest


def restore(
    *,
    latest: bool = False,
    timestamp: str | None = None,
    only: str | None = None,
    home: Path | None = None,
    dry_run: bool = False,
) -> int:
    """Restore from a backup.

    Args:
        latest: use the most recent backup dir.
        timestamp: use the backup dir named <timestamp>.
        only: restore only entries for this step (e.g. "neovim").
        home: override $HOME (used by tests).
        dry_run: print what would happen without touching anything.

    Returns:
        0 on success, non-zero exit code otherwise.
    """
    backup_dir = resolve_backup(latest=latest, timestamp=timestamp, home=home)
    if backup_dir is None:
        print("cosyterm: no backup found to restore from.", file=sys.stderr)
        print("  Run 'cosyterm restore --list' to see available backups.", file=sys.stderr)
        return 1

    entries = read_manifest(backup_dir)
    if only:
        entries = [e for e in entries if e.step == only]
    if not entries:
        print(f"cosyterm: no matching entries in {backup_dir / 'manifest.tsv'}", file=sys.stderr)
        return 1

    print(f"Restoring from: {backup_dir}")
    print(f"Entries: {len(entries)}" + (f"  (filtered to step '{only}')" if only else ""))
    print()

    if dry_run:
        for e in reversed(entries):
            print(f"  [would {e.action} back]  {e.backup}  →  {e.source}")
        print("\n(no changes made — --dry-run)")
        return 0

    stash = _pre_restore_dir(backup_dir)
    # Reverse order so the most recent install is undone first.
    for e in reversed(entries):
        if not e.backup.exists():
            print(f"  [skip]  backup missing: {e.backup}", file=sys.stderr)
            continue

        stashed = _stash_current(e.source, stash)
        if stashed:
            print(f"  [stash] {e.source} → {stashed}")

        # For both 'move' and 'copy' actions, the reverse is the same: put
        # the backup tree back where the source was. Using move is safe now
        # because we've stashed any current content out of the way.
        e.source.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(e.backup), str(e.source))
        print(f"  [restore] {e.source}  ({e.action})")

    marker = backup_dir / ".restored"
    marker.write_text(datetime.now(timezone.utc).isoformat() + "\n")
    print(f"\nDone. Post-install state (if any) stashed at:  {stash}")
    return 0


def print_list(home: Path | None = None) -> int:
    """Print every available backup, newest first, with a short summary."""
    backups = list_backups(home=home)
    if not backups:
        print("No cosyterm backups found.")
        return 0

    print("Available backups:")
    for b in backups:
        entries = read_manifest(b)
        steps = sorted(set(e.step for e in entries))
        mark = " [restored]" if (b / ".restored").exists() else ""
        print(f"  {b.name}  —  {len(entries)} entries, steps: {', '.join(steps) or '-'}{mark}")
        print(f"    {b}")
    return 0


def verify(
    *,
    timestamp: str | None = None,
    latest: bool = False,
    home: Path | None = None,
) -> int:
    """Check that every backup path referenced in the manifest still exists."""
    backup_dir = resolve_backup(latest=latest, timestamp=timestamp, home=home)
    if backup_dir is None:
        print("cosyterm: no matching backup found.", file=sys.stderr)
        return 1

    entries = read_manifest(backup_dir)
    missing = [e for e in entries if not e.backup.exists()]
    if not missing:
        print(f"OK — all {len(entries)} backup paths present in {backup_dir}")
        return 0
    print(f"FAIL — {len(missing)}/{len(entries)} backup paths missing:")
    for e in missing:
        print(f"  missing: {e.backup}  (source: {e.source}, step: {e.step})")
    return 1
