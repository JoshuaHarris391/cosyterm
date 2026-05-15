"""Basic tests for cosyterm."""



def test_version():
    from cosyterm import __version__
    assert __version__ == "0.4.0"


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
    """_check_bash must return an executable bash path whose major version
    meets MIN_BASH_MAJOR. If no bash at all exists on the machine, it returns
    "" and the caller prints an actionable hint."""
    import shutil

    from cosyterm.core import MIN_BASH_MAJOR, _bash_major_version, _check_bash

    if shutil.which("bash") is None and not _bash_major_version("/bin/bash"):
        import pytest
        pytest.skip("no bash on PATH and /bin/bash absent")

    bash = _check_bash()
    assert bash, "bash should be discoverable"
    assert _bash_major_version(bash) >= MIN_BASH_MAJOR


def test_issue_2_check_bash_accepts_bash_3_on_macos():
    """Regression test for #2: macOS /bin/bash 3.2 must not be rejected.

    Before the fix, MIN_BASH_MAJOR=4 caused cosyterm to refuse to run on a
    stock macOS install, even though setup.sh is authored to be bash-3.2
    compatible. This test asserts that when /bin/bash exists and reports a
    major version >= 3, _check_bash returns a usable path rather than the
    empty string.
    """
    import os

    from cosyterm.core import _bash_major_version, _check_bash

    if not (os.path.isfile("/bin/bash") and os.access("/bin/bash", os.X_OK)):
        import pytest
        pytest.skip("/bin/bash not present — test only meaningful where it is")

    system_major = _bash_major_version("/bin/bash")
    if system_major < 3:
        import pytest
        pytest.skip(f"/bin/bash reports major version {system_major}")

    bash = _check_bash()
    assert bash, (
        "On a machine where /bin/bash exists and is >= 3.x, _check_bash must "
        "return a usable bash path — pre-fix it returned '' because the gate "
        "required bash 4+."
    )


def test_setup_script_parses_under_bin_bash():
    """setup.sh must pass `bash -n` under the system /bin/bash so that macOS
    users running 3.2 don't hit a parse error mid-install.

    Skipped if /bin/bash isn't present (non-Unix CI, sandboxed envs)."""
    import os
    import subprocess

    from cosyterm.core import _get_script_path

    if not (os.path.isfile("/bin/bash") and os.access("/bin/bash", os.X_OK)):
        import pytest
        pytest.skip("/bin/bash not present")

    result = subprocess.run(
        ["/bin/bash", "-n", str(_get_script_path())],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"setup.sh failed bash 3.2 syntax check under /bin/bash:\n{result.stderr}"
    )


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
