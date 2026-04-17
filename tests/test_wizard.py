"""
Unit tests for the pure-logic layer of cosyterm.wizard.

Curses rendering is deliberately not exercised here — curses needs a real TTY,
which pytest doesn't provide. These tests cover WizardConfig.to_env() and
parse_plan_output(), which are the two pieces of logic that can drift
between Python and the bash side.
"""

import pytest

from cosyterm.wizard import (
    PlanEntry,
    WizardConfig,
    format_review_lines,
    parse_plan_output,
)


def test_to_env_all_steps_all_choices():
    """Full wizard run: all 7 steps, font + shell + fish + nvim chosen.

    Every COSYTERM_* gate in setup.sh should be set, so running setup.sh
    with this env should not block on any interactive prompt.
    """
    cfg = WizardConfig(
        steps=["font", "ghostty", "shell", "starship", "eza", "tmux", "neovim"],
        font_choice="0xProto",
        shell_choice="fish",
        fish_method="chsh",
        nvim_choice="sidebyside",
    )
    assert cfg.to_env() == {
        "COSYTERM_STEPS": "font,ghostty,shell,starship,eza,tmux,neovim",
        "COSYTERM_FONT_CHOICE": "0xProto",
        "COSYTERM_SHELL_CHOICE": "fish",
        "COSYTERM_FISH_METHOD": "chsh",
        "COSYTERM_NVIM_CHOICE": "sidebyside",
    }


def test_to_env_omits_choices_for_deselected_steps():
    """If 'shell' isn't in the selected steps, COSYTERM_SHELL_CHOICE and
    COSYTERM_FISH_METHOD should not be emitted even if the fields are set.

    This mirrors how setup.sh gates each step behind COSYTERM_STEPS — an env
    var for a skipped step would be a confusing no-op.
    """
    cfg = WizardConfig(
        steps=["ghostty", "eza"],
        shell_choice="fish",      # should be ignored
        fish_method="chsh",        # should be ignored
        font_choice="JetBrainsMono",  # should be ignored (font not in steps)
    )
    env = cfg.to_env()
    assert env["COSYTERM_STEPS"] == "ghostty,eza"
    assert "COSYTERM_FONT_CHOICE" not in env
    assert "COSYTERM_SHELL_CHOICE" not in env
    assert "COSYTERM_FISH_METHOD" not in env


def test_to_env_fish_method_requires_fish():
    """COSYTERM_FISH_METHOD must only be set when the chosen shell is fish.

    Setting it when shell_choice='zsh' would be confusing and harmless, but
    noisy; the wizard keeps it out of the env entirely.
    """
    cfg = WizardConfig(
        steps=["shell"],
        shell_choice="zsh",
        fish_method="chsh",  # set but should be dropped
    )
    env = cfg.to_env()
    assert env["COSYTERM_SHELL_CHOICE"] == "zsh"
    assert "COSYTERM_FISH_METHOD" not in env


def test_parse_plan_output_happy_path():
    """CMD / WRITE / SECTION / NOTE lines are the contract setup.sh promises
    in plan mode. Anything else (blank lines, confirm banners, log output
    that leaked through) must be ignored so the wizard can render a clean
    review screen even if the bash side is chatty.
    """
    stdout = (
        "SECTION\tStep 2/7: Ghostty\n"
        "CMD\tbrew install --cask ghostty\n"
        "CMD\tmkdir -p /home/u/.config/ghostty\n"
        "WRITE\t/home/u/.config/ghostty/config\tghostty config (Catppuccin)\n"
        "NOTE\twill overwrite existing font-family line\n"
        "\n"
        "  some stray log line\n"
        "\x1b[1m[2026-04-17 12:00:00] ► Install Ghostty?\x1b[0m\n"
    )
    entries = parse_plan_output(stdout)
    kinds = [e.kind for e in entries]
    assert kinds == ["SECTION", "CMD", "CMD", "WRITE", "NOTE"]
    assert entries[3].detail == "ghostty config (Catppuccin)"
    assert entries[4].payload == "will overwrite existing font-family line"


def test_format_review_lines_groups_by_section():
    """The review screen should visually group commands by section so the
    user can see which step each line belongs to."""
    entries = [
        PlanEntry("SECTION", "Step 2/7: Ghostty"),
        PlanEntry("CMD", "brew install --cask ghostty"),
        PlanEntry("SECTION", "Step 5/7: eza"),
        PlanEntry("CMD", "brew install eza"),
    ]
    lines = format_review_lines(entries)
    # First section has no leading blank; subsequent ones do.
    assert lines[0].startswith("── Step 2/7:")
    assert lines[1] == "  $ brew install --cask ghostty"
    assert lines[2] == ""
    assert lines[3].startswith("── Step 5/7:")
    assert lines[4] == "  $ brew install eza"
