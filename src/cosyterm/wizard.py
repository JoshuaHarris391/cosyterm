"""
Interactive curses wizard for cosyterm.

Flow:
    1. Welcome screen.
    2. Multi-select checklist of the 7 install steps.
    3. Font picker (single-select, only if "font" was selected).
    4. Shell picker (single-select, only if "shell" was selected).
    5. Fish method picker (only if shell_choice == "fish").
    6. NeoVim pre-flight picker (only if "neovim" was selected).
    7. Plan dry-run: spawn setup.sh with COSYTERM_PLAN=1 and the collected
       choices, parse CMD / WRITE / SECTION / NOTE lines.
    8. Review screen: scrollable pager showing the literal commands.
    9. Confirm → caller spawns setup.sh for real.

Pure logic (WizardConfig, parse_plan_output) lives above render_* functions so
it can be unit-tested without a TTY.
"""

from __future__ import annotations

import curses
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

INSTALL_STEPS: list[tuple[str, str]] = [
    ("font",     "Nerd Font         — code font patched with icons/symbols so prompts and file listings show glyphs, not boxes"),
    ("ghostty",  "Ghostty           — the terminal app window itself; a modern replacement for Terminal.app / gnome-terminal"),
    ("shell",    "Shell (Fish/Zsh)  — the program that reads your commands; Fish autocompletes and syntax-highlights as you type"),
    ("starship", "Starship prompt   — the info line before your cursor: current folder, git branch, language version, etc."),
    ("eza",      "eza               — a nicer 'ls': colors, file icons, git status, and a handy tree view"),
    ("tmux",     "tmux + Catppuccin — split one terminal into panes and keep sessions alive after you close the window"),
    ("neovim",   "NeoVim + LazyVim  — a modern Vim with IDE features (file tree, fuzzy search, LSP autocomplete) pre-configured"),
]

FUN_FONTS: list[tuple[str, str]] = [
    ("0xProto",      "0xProto           — coding font focused on character distinction"),
    ("Monofur",      "Monofur           — playful, rounded, hand-drawn character"),
    ("OpenDyslexic", "OpenDyslexic Mono — designed to improve readability for dyslexic readers"),
    ("Agave",        "Agave             — small, compact, minimal with a retro feel"),
    ("Hasklig",      "Hasklig           — Source Code Pro with ligatures"),
]
DEFAULT_FONTS: list[tuple[str, str]] = [
    ("JetBrainsMono", "JetBrains Mono    — designed for developers, excellent readability"),
    ("CommitMono",    "Commit Mono       — clean, neutral, open-source"),
    ("CascadiaCode",  "Cascadia Code     — Microsoft's terminal font, ligature support"),
    ("Hack",          "Hack              — optimised for source code, no-nonsense design"),
    ("FiraCode",      "Fira Code         — clean, modern, with programming ligatures"),
]
SKIP_FONT_KEY = "skip"

SHELL_OPTIONS: list[tuple[str, str]] = [
    ("fish", "Fish  — modern, user-friendly, non-POSIX (recommended)"),
    ("zsh",  "Zsh   — powerful, POSIX-compatible, widely supported"),
    ("skip", "Skip  — keep your current shell"),
]
FISH_METHOD_OPTIONS: list[tuple[str, str]] = [
    ("chsh",    "Set Fish as default shell (chsh — affects all terminals)"),
    ("ghostty", "Launch Fish from Ghostty only (safer)"),
    ("none",    "Just install it, I'll configure later"),
]
NVIM_OPTIONS: list[tuple[str, str]] = [
    ("skip",       "Skip        — leave existing NeoVim config untouched"),
    ("sidebyside", "Side-by-side — install LazyVim at ~/.config/nvim-cosy"),
    ("replace",    "Replace     — move current config to backup, install LazyVim"),
]


# =============================================================================
# Pure-logic layer (no curses, fully unit-testable)
# =============================================================================

@dataclass
class WizardConfig:
    steps: list[str] = field(default_factory=list)
    font_choice: str | None = None
    shell_choice: str | None = None
    fish_method: str | None = None
    nvim_choice: str | None = None

    def to_env(self) -> dict[str, str]:
        """Flatten wizard choices into COSYTERM_* env vars for setup.sh."""
        env: dict[str, str] = {"COSYTERM_STEPS": ",".join(self.steps)}
        if "font" in self.steps and self.font_choice is not None:
            env["COSYTERM_FONT_CHOICE"] = self.font_choice
        if "shell" in self.steps and self.shell_choice is not None:
            env["COSYTERM_SHELL_CHOICE"] = self.shell_choice
        if (
            "shell" in self.steps
            and self.shell_choice == "fish"
            and self.fish_method is not None
        ):
            env["COSYTERM_FISH_METHOD"] = self.fish_method
        if "neovim" in self.steps and self.nvim_choice is not None:
            env["COSYTERM_NVIM_CHOICE"] = self.nvim_choice
        return env


@dataclass
class PlanEntry:
    kind: str      # "CMD", "WRITE", "SECTION", "NOTE"
    payload: str   # full text after the tab
    detail: str = ""  # extra column (e.g. WRITE's hint)


def parse_plan_output(stdout: str) -> list[PlanEntry]:
    """Parse setup.sh plan-mode output into structured entries.

    Unknown / blank / log lines are dropped — plan-mode is supposed to be
    machine-parseable but log_section headers and confirm banners aren't
    fully suppressed on every code path, so we filter defensively.
    """
    entries: list[PlanEntry] = []
    for line in stdout.splitlines():
        if not line or "\t" not in line:
            continue
        head, _, rest = line.partition("\t")
        if head not in ("CMD", "WRITE", "SECTION", "NOTE"):
            continue
        if head == "WRITE" and "\t" in rest:
            payload, _, detail = rest.partition("\t")
            entries.append(PlanEntry(head, payload, detail))
        else:
            entries.append(PlanEntry(head, rest))
    return entries


def format_review_lines(entries: list[PlanEntry]) -> list[str]:
    """Render parsed plan entries into human-readable review lines."""
    out: list[str] = []
    for e in entries:
        if e.kind == "SECTION":
            if out:
                out.append("")
            out.append(f"── {e.payload} ──")
        elif e.kind == "CMD":
            out.append(f"  $ {e.payload}")
        elif e.kind == "WRITE":
            out.append(f"  » write {e.payload}  ({e.detail})")
        elif e.kind == "NOTE":
            out.append(f"  · {e.payload}")
    return out


# =============================================================================
# curses rendering
# =============================================================================

def _center(win, y: int, text: str, attr: int = 0) -> None:
    _, w = win.getmaxyx()
    x = max(0, (w - len(text)) // 2)
    try:
        win.addstr(y, x, text[: w - 1], attr)
    except curses.error:
        pass


def _safe_addstr(win, y: int, x: int, text: str, attr: int = 0) -> None:
    _, w = win.getmaxyx()
    try:
        win.addstr(y, x, text[: max(0, w - x - 1)], attr)
    except curses.error:
        pass


def _draw_box(win, title: str) -> None:
    """Draw a titled border around the whole window."""
    win.erase()
    win.border()
    if title:
        _safe_addstr(win, 0, 2, f" {title} ", curses.A_BOLD)


def _render_menu(
    win,
    title: str,
    options: list[tuple[str, str]],
    initial: int = 0,
    footer: str = "↑/↓ move   Enter select   Esc back",
) -> int | None:
    """Single-select menu. Returns index or None on Esc."""
    idx = initial
    while True:
        _draw_box(win, title)
        _, w = win.getmaxyx()
        for i, (_, label) in enumerate(options):
            y = 2 + i
            attr = curses.A_REVERSE if i == idx else 0
            line = f" {'▶' if i == idx else ' '} {label} "
            _safe_addstr(win, y, 2, line.ljust(max(10, w - 4)), attr)
        _safe_addstr(win, win.getmaxyx()[0] - 2, 2, footer, curses.A_DIM)
        win.refresh()
        ch = win.getch()
        if ch in (curses.KEY_UP, ord("k")):
            idx = (idx - 1) % len(options)
        elif ch in (curses.KEY_DOWN, ord("j")):
            idx = (idx + 1) % len(options)
        elif ch in (curses.KEY_ENTER, 10, 13):
            return idx
        elif ch == 27:  # Esc
            return None


def _render_checklist(
    win,
    title: str,
    options: list[tuple[str, str]],
    checked: set[int],
    footer: str = "↑/↓ move   Space toggle   Enter continue   Esc back",
) -> set[int] | None:
    """Multi-select checklist. Returns set of indices or None on Esc."""
    idx = 0
    selected = set(checked)
    while True:
        _draw_box(win, title)
        _, w = win.getmaxyx()
        for i, (_, label) in enumerate(options):
            y = 2 + i
            attr = curses.A_REVERSE if i == idx else 0
            mark = "[x]" if i in selected else "[ ]"
            line = f" {mark}  {label} "
            _safe_addstr(win, y, 2, line.ljust(max(10, w - 4)), attr)
        _safe_addstr(win, win.getmaxyx()[0] - 2, 2, footer, curses.A_DIM)
        win.refresh()
        ch = win.getch()
        if ch in (curses.KEY_UP, ord("k")):
            idx = (idx - 1) % len(options)
        elif ch in (curses.KEY_DOWN, ord("j")):
            idx = (idx + 1) % len(options)
        elif ch == ord(" "):
            if idx in selected:
                selected.remove(idx)
            else:
                selected.add(idx)
        elif ch in (curses.KEY_ENTER, 10, 13):
            return selected
        elif ch == 27:
            return None


def _render_pager(win, lines: list[str], title: str) -> bool:
    """Scrollable pager. Returns True (Enter = confirm) or False (Esc = back)."""
    top = 0
    while True:
        h, w = win.getmaxyx()
        _draw_box(win, title)
        body_h = h - 4
        for i, line in enumerate(lines[top : top + body_h]):
            attr = curses.A_BOLD if line.startswith("── ") else 0
            _safe_addstr(win, 2 + i, 2, line, attr)
        footer = "↑/↓ PgUp/PgDn scroll   Enter confirm & run   Esc back"
        _safe_addstr(win, h - 2, 2, footer, curses.A_DIM)
        win.refresh()
        ch = win.getch()
        if ch in (curses.KEY_DOWN, ord("j")):
            top = min(top + 1, max(0, len(lines) - body_h))
        elif ch in (curses.KEY_UP, ord("k")):
            top = max(0, top - 1)
        elif ch in (curses.KEY_NPAGE, ord(" ")):
            top = min(top + body_h, max(0, len(lines) - body_h))
        elif ch == curses.KEY_PPAGE:
            top = max(0, top - body_h)
        elif ch in (curses.KEY_ENTER, 10, 13):
            return True
        elif ch == 27:
            return False


def _render_welcome(win) -> bool:
    """Returns True on Enter (continue), False on Esc."""
    while True:
        _draw_box(win, "cosyTerm")
        h, _ = win.getmaxyx()
        lines = [
            "",
            "Welcome.",
            "",
            "This wizard will collect your preferences, then show you the",
            "exact shell commands it plans to run. Nothing is executed",
            "until you confirm on the final review screen.",
            "",
            "↑/↓ to navigate, Space to toggle checklists, Enter to continue,",
            "Esc to go back or cancel.",
            "",
        ]
        for i, line in enumerate(lines):
            _center(win, 2 + i, line)
        _center(win, h - 3, "[ Enter ] begin     [ Esc ] cancel", curses.A_BOLD)
        win.refresh()
        ch = win.getch()
        if ch in (curses.KEY_ENTER, 10, 13):
            return True
        if ch == 27:
            return False


# =============================================================================
# Orchestration
# =============================================================================

def _run_plan(script: Path, bash: str, env: dict[str, str]) -> tuple[int, str, str]:
    """Spawn setup.sh in plan mode and capture stdout/stderr."""
    plan_env = {**env, "COSYTERM_PLAN": "1", "COSYTERM_YES": "1"}
    r = subprocess.run(
        [bash, str(script)],
        env=plan_env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return r.returncode, r.stdout, r.stderr


def _driver(stdscr, script: Path, bash: str) -> WizardConfig | None:
    curses.curs_set(0)
    stdscr.keypad(True)

    if not _render_welcome(stdscr):
        return None

    # 1. Steps checklist — default: all selected.
    checked = set(range(len(INSTALL_STEPS)))
    result = _render_checklist(stdscr, "Which tools to install?", INSTALL_STEPS, checked)
    if result is None:
        return None
    config = WizardConfig(steps=[INSTALL_STEPS[i][0] for i in sorted(result)])
    if not config.steps:
        return None  # nothing selected — treat as cancel

    # 2. Font
    if "font" in config.steps:
        font_options = FUN_FONTS + DEFAULT_FONTS + [(SKIP_FONT_KEY, "Skip — I'll install a Nerd Font myself")]
        idx = _render_menu(stdscr, "Which Nerd Font?", font_options)
        if idx is None:
            return None
        config.font_choice = font_options[idx][0]

    # 3. Shell
    if "shell" in config.steps:
        idx = _render_menu(stdscr, "Which shell?", SHELL_OPTIONS)
        if idx is None:
            return None
        config.shell_choice = SHELL_OPTIONS[idx][0]

        # 4. Fish method
        if config.shell_choice == "fish":
            idx = _render_menu(stdscr, "How would you like to use Fish?", FISH_METHOD_OPTIONS)
            if idx is None:
                return None
            config.fish_method = FISH_METHOD_OPTIONS[idx][0]

    # 5. NeoVim
    if "neovim" in config.steps:
        idx = _render_menu(stdscr, "NeoVim pre-flight", NVIM_OPTIONS)
        if idx is None:
            return None
        config.nvim_choice = NVIM_OPTIONS[idx][0]

    # 6. Dry-run to produce review lines.
    stdscr.erase()
    _center(stdscr, stdscr.getmaxyx()[0] // 2, "Computing plan…", curses.A_BOLD)
    stdscr.refresh()
    env = {**os.environ, **config.to_env()}
    rc, stdout, stderr = _run_plan(script, bash, env)
    if rc != 0:
        _draw_box(stdscr, "Plan failed")
        _safe_addstr(stdscr, 2, 2, f"setup.sh exited {rc} in plan mode.", curses.A_BOLD)
        for i, line in enumerate((stderr or stdout).splitlines()[:20]):
            _safe_addstr(stdscr, 4 + i, 2, line)
        _safe_addstr(stdscr, stdscr.getmaxyx()[0] - 2, 2, "[ Esc ] back", curses.A_DIM)
        stdscr.refresh()
        while stdscr.getch() != 27:
            pass
        return None

    entries = parse_plan_output(stdout)
    review_lines = format_review_lines(entries)
    if not review_lines:
        review_lines = ["(no commands — setup.sh reported nothing to do)"]

    # 7. Review.
    confirmed = _render_pager(stdscr, review_lines, "Review — commands to be run")
    if not confirmed:
        return None
    return config


def run_wizard(script: Path, bash: str) -> WizardConfig | None:
    """Public entry. Returns None on cancel/abort.

    Falls back to None (caller should use --classic path) if stdout is not a
    TTY — curses can't initialise without one, and many CI environments pipe
    stdout.
    """
    if not sys.stdout.isatty() or not sys.stdin.isatty():
        return None
    try:
        return curses.wrapper(_driver, script, bash)
    except KeyboardInterrupt:
        return None
