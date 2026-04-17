"""
Guard tests for setup.sh structure.

Plan-mode fidelity depends on every external command going through the
run / run_sh wrappers. If a future contributor adds a bare `brew install`
or `git clone`, it'll execute even during a dry run — silently lying to
the wizard's review screen.

These tests grep the script for known offender patterns and flag any
unwrapped usages.
"""

import re
from pathlib import Path

from cosyterm.core import _get_script_path


# Commands that must always be wrapped when they mutate the system.
# Each entry: (name, regex-that-matches-a-bare-use, regex-that-matches-the-wrapped-form)
GUARDS = [
    ("chsh", re.compile(r"^\s*chsh\s"), re.compile(r"^\s*run\s+chsh\s")),
    ("git clone", re.compile(r"^\s*git\s+clone\b"), re.compile(r"^\s*run\s+git\s+clone\b")),
]

# Lines where the pattern is allowed (help text, comments, error messages).
ALLOWED_SUBSTRINGS = (
    "# ",           # comments
    '"  ',          # help-text strings
    "log_",         # log_warn/log_error messages
    "chsh -s $(",   # log output describing a recovery command
    "chsh -s \\$",  # escaped form in a log string
    "echo",         # echoed help text
)


def test_no_unwrapped_destructive_commands():
    """Walk every line of setup.sh; for each GUARD, ensure any occurrence of
    the bare pattern is either in a comment / log message / heredoc, or
    prefixed with `run`.
    """
    script = _get_script_path().read_text().splitlines()
    offenders: list[str] = []

    in_heredoc = False
    heredoc_terminator = None
    for i, line in enumerate(script, start=1):
        # Track heredocs — anything inside is a literal data block, not
        # executable code.
        if in_heredoc:
            if line.strip() == heredoc_terminator:
                in_heredoc = False
            continue
        m = re.search(r"<<\s*['\"]?(\w+)['\"]?$", line)
        if m:
            in_heredoc = True
            heredoc_terminator = m.group(1)
            continue

        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        for name, bare_re, wrapped_re in GUARDS:
            if bare_re.match(line) and not wrapped_re.match(line):
                if any(sub in line for sub in ALLOWED_SUBSTRINGS):
                    continue
                offenders.append(f"  {script[0] and i}: [{name}] {line.rstrip()}")

    assert not offenders, (
        "Found destructive commands not routed through run/run_sh — these "
        "will execute during COSYTERM_PLAN=1 dry-runs, breaking the wizard "
        "review screen:\n" + "\n".join(offenders)
    )


def test_plan_mode_wrappers_are_defined():
    """Sanity check: the run / run_sh / is_plan_mode / note_write helpers
    that the rest of the script relies on are all defined.
    """
    text = _get_script_path().read_text()
    for helper in ("run()", "run_sh()", "is_plan_mode()", "note_write()"):
        assert helper in text, f"setup.sh is missing the {helper} wrapper"
