"""
Regression tests for the wizard-era env-var gates in setup.sh.

Before this change, every menu (font, shell, fish method) blocked on
`read -rp`. Now each one checks its corresponding COSYTERM_*_CHOICE env var
first and only prompts when it's unset.

These tests prove the gates work by running with stdin=DEVNULL and a short
timeout: if the script still tries to `read`, it'll hang and the test will
time out with a clear failure message.

CI runs on both macOS (brew) and Ubuntu (apt), so install-command assertions
use _matches_install() to accept either package manager's output.
"""

import sys


def _matches_install(stdout: str, pkg_brew: str, pkg_apt: str | None = None, cask: bool = False) -> bool:
    """True if stdout contains a CMD install line for the given package on
    the current platform. Tests don't care which package manager fired,
    only that the package was queued for install.
    """
    apt_pkg = pkg_apt or pkg_brew
    brew_line = f"CMD\tbrew install {'--cask ' if cask else ''}{pkg_brew}"
    apt_line = f"CMD\tsudo apt-get install -y {apt_pkg}"
    if sys.platform == "darwin":
        return brew_line in stdout
    return apt_line in stdout or brew_line in stdout


def test_font_choice_env_var_bypasses_prompt(sandbox_env, run_setup_sh_full):
    """COSYTERM_FONT_CHOICE=0xProto must skip the numeric menu entirely.

    On macOS the font installs via a Homebrew cask; on Linux it downloads
    the zip directly — either way, the key signal is that 0xProto is
    referenced in the plan and no interactive read fired.
    """
    env = sandbox_env(
        plan=True,
        steps=["font"],
        choices={"font_choice": "0xProto"},
    )
    result = run_setup_sh_full(env)  # run_setup_sh_full already uses DEVNULL
    assert result.returncode == 0
    if sys.platform == "darwin":
        assert "CMD\tbrew install --cask font-0xproto-nerd-font" in result.stdout
    else:
        # Linux path: direct curl of the 0xProto.zip release.
        assert "0xProto.zip" in result.stdout
        assert "CMD\tunzip" in result.stdout


def test_shell_choice_env_var_bypasses_prompt(sandbox_env, run_setup_sh_full):
    """COSYTERM_SHELL_CHOICE=fish must skip the shell menu and install fish."""
    env = sandbox_env(
        plan=True,
        steps=["shell"],
        choices={"shell_choice": "fish", "fish_method": "none"},
    )
    result = run_setup_sh_full(env)
    assert result.returncode == 0
    assert _matches_install(result.stdout, "fish"), (
        f"no fish install CMD in plan output:\n{result.stdout}"
    )


def test_fish_method_env_var_bypasses_prompt(sandbox_env, run_setup_sh_full):
    """COSYTERM_FISH_METHOD=chsh must skip the fish-method menu and emit
    the chsh / sudo-tee commands."""
    env = sandbox_env(
        plan=True,
        steps=["shell"],
        choices={"shell_choice": "fish", "fish_method": "chsh"},
    )
    result = run_setup_sh_full(env)
    assert result.returncode == 0
    assert "CMD\tchsh -s" in result.stdout


def test_invalid_font_choice_rejected(sandbox_env, run_setup_sh_full):
    """An unknown font key must fail loudly, not silently skip — typos
    in automation configs should surface as errors, not data loss."""
    env = sandbox_env(
        plan=True,
        steps=["font"],
        choices={"font_choice": "ComicSans"},
    )
    result = run_setup_sh_full(env)
    # Font step returns 1, but because subsequent steps in the CSV run,
    # the overall script may still exit 0. Key assertion: the error message
    # fired and no install was planned for a bogus font.
    assert "Unknown COSYTERM_FONT_CHOICE 'ComicSans'" in result.stdout + result.stderr
    assert "font-comicsans" not in result.stdout
