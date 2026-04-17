"""Basic tests for cosyterm."""



def test_version():
    from cosyterm import __version__
    assert __version__ == "0.3.1"


def test_script_exists():
    from cosyterm.core import _get_script_path
    script = _get_script_path()
    assert script.exists(), f"Setup script not found at {script}"
    assert script.suffix == ".sh"


def test_script_is_valid_bash():
    """Verify the bundled script passes bash syntax check."""
    import subprocess

    from cosyterm.core import _get_script_path

    script = _get_script_path()
    result = subprocess.run(
        ["bash", "-n", str(script)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Bash syntax error: {result.stderr}"


def test_check_bash():
    """_check_bash must refuse bash < 4 (macOS /bin/bash) and return a path
    otherwise. If nothing suitable is installed, it returns "" — the caller
    prints an actionable hint. On dev machines without Homebrew bash this
    test is skipped rather than fabricating a fake bash 4+ binary."""
    import shutil

    from cosyterm.core import _bash_major_version, _check_bash

    if not any(
        shutil.which(p) or None
        for p in ("/opt/homebrew/bin/bash", "/usr/local/bin/bash")
    ):
        # Also accept system bash if it's 4+.
        system_bash = shutil.which("bash")
        if not (system_bash and _bash_major_version(system_bash) >= 4):
            import pytest
            pytest.skip("no bash >= 4 on this machine; install via brew install bash")

    bash = _check_bash()
    assert bash, "bash >= 4 should be discoverable"
    assert _bash_major_version(bash) >= 4


def test_doctor_runs():
    from cosyterm.core import doctor
    # doctor() should return an int (number of issues)
    result = doctor()
    assert isinstance(result, int)


def test_path_helper_safety_net_emitted():
    """Both generated fish conf.d files must emit the path_helper safety net.

    Without it, tmux's `default-command` spawns fish non-login, macOS
    path_helper is skipped, /usr/bin is missing from PATH, and starship's
    init crashes because fish's psub can't find mktemp.

    This test guards against regressions that drop the safety line from
    either _hook_starship (10-cosyterm-init.fish) or _migrate_path_to_fish
    (00-cosyterm-path.fish).
    """
    from cosyterm.core import _get_script_path

    script_text = _get_script_path().read_text()
    safety_line = (
        'fish_add_path --append --path /usr/local/bin /usr/bin /bin /usr/sbin /sbin'
    )

    # At minimum: one occurrence in _hook_starship, one in _migrate_path_to_fish
    # main header, one in the minimal-file writer. Require >= 3.
    count = script_text.count(safety_line)
    assert count >= 3, (
        f"expected safety-net line to appear at least 3 times in setup.sh, "
        f"found {count}. Missing emission site?"
    )

    # Also assert both containing function names are in the script — if one
    # is renamed without updating this test, the count check catches it, but
    # failing loudly here gives a clearer error.
    assert "_hook_starship" in script_text
    assert "_migrate_path_to_fish" in script_text
