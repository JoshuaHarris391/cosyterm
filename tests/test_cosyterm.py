"""Basic tests for cosyterm."""



def test_version():
    from cosyterm import __version__
    assert __version__ == "0.2.0"


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
