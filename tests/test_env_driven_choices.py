"""
Regression tests for the wizard-era env-var gates in setup.sh.

Before this change, every menu (font, shell, fish method) blocked on
`read -rp`. Now each one checks its corresponding COSYTERM_*_CHOICE env var
first and only prompts when it's unset.

These tests prove the gates work by running with stdin=DEVNULL and a short
timeout: if the script still tries to `read`, it'll hang and the test will
time out with a clear failure message.
"""

import subprocess

import pytest


def test_font_choice_env_var_bypasses_prompt(sandbox_env, run_setup_sh_full):
    """COSYTERM_FONT_CHOICE=0xProto must skip the numeric menu entirely."""
    env = sandbox_env(
        plan=True,
        steps=["font"],
        choices={"font_choice": "0xProto"},
    )
    result = run_setup_sh_full(env)  # run_setup_sh_full already uses DEVNULL
    assert result.returncode == 0
    assert "CMD\tbrew install --cask font-0xproto-nerd-font" in result.stdout


def test_shell_choice_env_var_bypasses_prompt(sandbox_env, run_setup_sh_full):
    """COSYTERM_SHELL_CHOICE=fish must skip the shell menu and install fish."""
    env = sandbox_env(
        plan=True,
        steps=["shell"],
        choices={"shell_choice": "fish", "fish_method": "none"},
    )
    result = run_setup_sh_full(env)
    assert result.returncode == 0
    assert "CMD\tbrew install fish" in result.stdout


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
    # fired and no brew install was planned for a bogus font.
    assert "Unknown COSYTERM_FONT_CHOICE 'ComicSans'" in result.stdout + result.stderr
    assert "CMD\tbrew install --cask font-comicsans" not in result.stdout
