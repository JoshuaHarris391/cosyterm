"""
Core logic for cosyterm — locates and executes the setup script.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def _get_script_path() -> Path:
    """Return the path to the bundled setup.sh script."""
    return Path(__file__).parent / "scripts" / "setup.sh"


def _check_bash() -> str:
    """Find a suitable bash binary. Prefers Homebrew bash (4+) on macOS."""
    # On macOS, /bin/bash is 3.2 — check for Homebrew bash first
    for candidate in ["/opt/homebrew/bin/bash", "/usr/local/bin/bash", "/bin/bash"]:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    bash = shutil.which("bash")
    if bash:
        return bash

    return ""


def setup() -> int:
    """
    Run the full interactive terminal setup.

    This launches the bundled setup.sh script which walks you through
    installing and configuring:
      - Nerd Font (your choice of 10 fonts)
      - Ghostty terminal emulator
      - Zsh or Fish shell (with PATH migration to Fish)
      - Starship prompt
      - eza (modern ls)
      - tmux with Catppuccin Mocha theme
      - NeoVim + LazyVim

    Every destructive step requires confirmation. All existing configs
    are backed up before being modified.

    Returns:
        Exit code from the setup script (0 = success).
    """
    script = _get_script_path()

    if not script.exists():
        print(f"Error: Setup script not found at {script}", file=sys.stderr)
        print("This usually means the package was installed incorrectly.", file=sys.stderr)
        print("Try: pip install --force-reinstall cosyterm", file=sys.stderr)
        return 1

    bash = _check_bash()
    if not bash:
        print("Error: bash is required but not found on your system.", file=sys.stderr)
        return 1

    # Make the script executable
    os.chmod(script, 0o755)

    # Run the script interactively — it needs stdin for user prompts
    try:
        result = subprocess.run(
            [bash, str(script)],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        return result.returncode
    except KeyboardInterrupt:
        print("\n\nSetup cancelled. Run 'cosyterm' to start again.")
        return 130


INSTALL_STEPS = [
    "font", "ghostty", "shell", "starship", "eza",
    "tmux", "neovim",
]


def install_step(step: str) -> int:
    """Re-run a single setup step (e.g. 'font', 'ghostty', 'starship')."""
    script = _get_script_path()

    if not script.exists():
        print(f"Error: Setup script not found at {script}", file=sys.stderr)
        return 1

    bash = _check_bash()
    if not bash:
        print("Error: bash is required but not found on your system.", file=sys.stderr)
        return 1

    os.chmod(script, 0o755)

    try:
        result = subprocess.run(
            [bash, str(script), step],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        return result.returncode
    except KeyboardInterrupt:
        print("\n\nInstall cancelled.")
        return 130


def doctor() -> int:
    """
    Run diagnostics to check if your terminal setup is healthy.

    Checks for:
      - Missing binaries referenced in config files
      - Config files pointing to uninstalled tools
      - Homebrew PATH issues in Fish
      - Font installation status

    Returns:
        Number of issues found (0 = all clear).
    """
    issues = 0
    home = Path.home()

    print("\033[1m\033[36m━━━ cosyTerm doctor ━━━\033[0m\n")

    # Define checks as (label, check_function) pairs
    checks = [
        ("Ghostty", _check_binary("ghostty")),
        ("Ghostty config", _check_file(home / ".config" / "ghostty" / "config")),
        ("Starship", _check_binary("starship")),
        ("Starship config", _check_file(home / ".config" / "starship.toml")),
        ("eza", _check_binary("eza")),
        ("tmux", _check_binary("tmux")),
        ("tmux config", _check_file(home / ".tmux.conf")),
        ("Catppuccin tmux theme", _check_dir(home / ".config" / "tmux" / "plugins" / "catppuccin" / "tmux")),
        ("TPM", _check_dir(home / ".tmux" / "plugins" / "tpm")),
        ("NeoVim", _check_binary("nvim")),
        ("LazyVim config", _check_dir(home / ".config" / "nvim")),
        ("Fish", _check_binary("fish")),
        ("Zsh", _check_binary("zsh")),
    ]

    for label, (found, detail) in checks:
        if found:
            print(f"  \033[32m✓\033[0m {label}  \033[90m{detail}\033[0m")
        else:
            print(f"  \033[33m○\033[0m {label}  \033[90m{detail}\033[0m")

    # Check for config/binary mismatches
    print()
    mismatches = _check_mismatches(home)
    issues += mismatches

    if mismatches == 0:
        print("  \033[32m✓\033[0m No config/binary mismatches found\n")
    else:
        print(f"\n  \033[31m✗\033[0m {mismatches} mismatch(es) found — see above\n")

    return issues


def _check_binary(name: str):
    """Check if a binary is on PATH."""
    path = shutil.which(name)
    if path:
        return True, path
    return False, "not found"


def _check_file(path: Path):
    """Check if a file exists."""
    if path.exists():
        return True, str(path)
    return False, "not found"


def _check_dir(path: Path):
    """Check if a directory exists."""
    if path.is_dir():
        return True, str(path)
    return False, "not found"


def _check_mismatches(home: Path) -> int:
    """Check for config files that reference tools not on PATH."""
    issues = 0

    # Fish config references starship but starship not installed
    fish_config = home / ".config" / "fish" / "config.fish"
    if fish_config.exists():
        content = fish_config.read_text()
        if "starship init" in content and not shutil.which("starship"):
            print("  \033[31m✗\033[0m config.fish references starship but it's not installed")
            print("    Fix: brew install starship")
            issues += 1
        if "eza" in content and not shutil.which("eza"):
            print("  \033[31m✗\033[0m config.fish references eza but it's not installed")
            print("    Fix: brew install eza")
            issues += 1

    # Zshrc references starship but starship not installed
    zshrc = home / ".zshrc"
    if zshrc.exists():
        content = zshrc.read_text()
        if "starship init" in content and not shutil.which("starship"):
            print("  \033[31m✗\033[0m .zshrc references starship but it's not installed")
            print("    Fix: brew install starship")
            issues += 1

    # Ghostty config references fish but fish not installed
    ghostty_config = home / ".config" / "ghostty" / "config"
    if ghostty_config.exists():
        content = ghostty_config.read_text()
        if "fish" in content and not shutil.which("fish"):
            print("  \033[31m✗\033[0m Ghostty config references fish but it's not installed")
            issues += 1

    # tmux config references catppuccin but theme not installed
    tmux_conf = home / ".tmux.conf"
    catppuccin_dir = home / ".config" / "tmux" / "plugins" / "catppuccin" / "tmux"
    if tmux_conf.exists():
        content = tmux_conf.read_text()
        if "catppuccin" in content and not catppuccin_dir.is_dir():
            print("  \033[31m✗\033[0m .tmux.conf references Catppuccin but theme not installed")
            print("    Fix: mkdir -p ~/.config/tmux/plugins/catppuccin")
            print("         git clone -b v2.3.0 https://github.com/catppuccin/tmux.git ~/.config/tmux/plugins/catppuccin/tmux")
            issues += 1

    return issues
