"""Basic tests for cosyterm."""



def test_version():
    from cosyterm import __version__
    assert __version__ == "0.1.0"


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
    from cosyterm.core import _check_bash
    bash = _check_bash()
    assert bash, "No bash binary found"


def test_doctor_runs():
    from cosyterm.core import doctor
    # doctor() should return an int (number of issues)
    result = doctor()
    assert isinstance(result, int)
