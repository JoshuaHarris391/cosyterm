"""
Shared test fixtures for cosyterm.

Design goal: run the real setup.sh + the real cosyterm CLI end-to-end,
but inside a sandbox `$HOME` and with PATH shimmed so no real network,
no real sudo, and no real package manager is ever touched.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pytest

TESTS_DIR = Path(__file__).parent
FAKEBIN_DIR = TESTS_DIR / "fakebin"
FIXTURES_DIR = TESTS_DIR / "fixtures"
REPO_ROOT = TESTS_DIR.parent
SETUP_SH = REPO_ROOT / "src" / "cosyterm" / "scripts" / "setup.sh"
SRC_DIR = REPO_ROOT / "src"


@pytest.fixture
def tmp_home(tmp_path: Path) -> Path:
    """A clean $HOME for a single test — everything happens inside this dir."""
    home = tmp_path / "home"
    home.mkdir()
    (home / ".config").mkdir()
    (home / ".local" / "share").mkdir(parents=True)
    (home / ".local" / "state").mkdir(parents=True)
    return home


def _install_fixture(name: str, tmp_home: Path) -> None:
    """Copy a fixture's tree into $HOME at the mapped locations.

    Fixture dirs are named after their target path with '_' separators:
      dot_config_nvim        -> ~/.config/nvim
      dot_local_share_nvim   -> ~/.local/share/nvim
      dot_local_state_nvim   -> ~/.local/state/nvim
    """
    src_root = FIXTURES_DIR / name
    if not src_root.is_dir():
        raise FileNotFoundError(f"fixture not found: {src_root}")

    mapping = {
        "dot_config_nvim": tmp_home / ".config" / "nvim",
        "dot_local_share_nvim": tmp_home / ".local" / "share" / "nvim",
        "dot_local_state_nvim": tmp_home / ".local" / "state" / "nvim",
    }
    for sub, target in mapping.items():
        src = src_root / sub
        if src.is_dir():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, target)


@pytest.fixture
def install_fixture() -> Callable[[str, Path], None]:
    """Return the _install_fixture helper — parameterised by test body."""
    return _install_fixture


def _sandbox_env(
    tmp_home: Path,
    *,
    extra: dict | None = None,
    plan: bool = False,
    steps: list[str] | None = None,
    choices: dict[str, str] | None = None,
) -> dict:
    """Environment for running setup.sh or the CLI inside a sandbox.

    - HOME points at tmp_home.
    - PATH prepends the test fakebin dir so curl/git/brew/sudo/etc. are
      intercepted, but real coreutils (mkdir, mv, cp, rm, find, grep, sed,
      date, wc, tr, basename) still resolve normally.
    - COSYTERM_YES auto-answers all confirm prompts.
    - COSYTERM_LOG_FILE redirects the log inside the sandbox.
    - COSYTERM_FAKE_LOG captures every fake-bin invocation for assertions.
    - PYTHONPATH lets the CLI run without `pip install`.

    Wizard-era knobs:
    - plan=True sets COSYTERM_PLAN=1 (dry-run, prints CMD/WRITE lines).
    - steps=["ghostty", "eza"] sets COSYTERM_STEPS to that CSV.
    - choices={"font_choice": "0xProto", "shell_choice": "fish"} maps to
      COSYTERM_FONT_CHOICE / COSYTERM_SHELL_CHOICE / etc.
    """
    env = {
        "HOME": str(tmp_home),
        "PATH": f"{FAKEBIN_DIR}:{os.environ.get('PATH', '')}",
        "COSYTERM_YES": "1",
        "COSYTERM_DEV": "1",
        "COSYTERM_LOG_FILE": str(tmp_home / "terminal-setup.log"),
        "COSYTERM_FAKE_LOG": str(tmp_home / "fake-bin.log"),
        "PYTHONPATH": str(SRC_DIR),
        # Keep these so bash / python can find themselves and their libs.
        "LANG": os.environ.get("LANG", "en_US.UTF-8"),
        "TERM": os.environ.get("TERM", "dumb"),
    }
    if plan:
        env["COSYTERM_PLAN"] = "1"
    if steps:
        env["COSYTERM_STEPS"] = ",".join(steps)
    if choices:
        for k, v in choices.items():
            env[f"COSYTERM_{k.upper()}"] = v
    if extra:
        env.update(extra)
    return env


@pytest.fixture
def sandbox_env(tmp_home: Path) -> Callable[..., dict]:
    """Factory: build the sandbox env, optionally with extra vars merged in."""
    def build(
        *,
        plan: bool = False,
        steps: list[str] | None = None,
        choices: dict[str, str] | None = None,
        **extra: str,
    ) -> dict:
        return _sandbox_env(
            tmp_home, extra=extra, plan=plan, steps=steps, choices=choices
        )
    return build


@dataclass
class RunResult:
    returncode: int
    stdout: str
    stderr: str


def _run_setup_sh(step: str, env: dict) -> RunResult:
    """Invoke setup.sh <step> with the given env. Returns merged output."""
    r = subprocess.run(
        ["bash", str(SETUP_SH), step],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return RunResult(r.returncode, r.stdout, r.stderr)


def _run_setup_sh_full(env: dict) -> RunResult:
    """Invoke setup.sh without a step arg — exercises the main flow.

    Used by plan-mode tests that need to see SECTION markers and
    step-gating via COSYTERM_STEPS.
    """
    r = subprocess.run(
        ["bash", str(SETUP_SH)],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        stdin=subprocess.DEVNULL,  # detects blocking `read -rp` regressions
    )
    return RunResult(r.returncode, r.stdout, r.stderr)


def _run_cli(args: list[str], env: dict) -> RunResult:
    """Invoke the cosyterm CLI as a module. Returns merged output."""
    r = subprocess.run(
        [sys.executable, "-m", "cosyterm.cli", *args],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return RunResult(r.returncode, r.stdout, r.stderr)


@pytest.fixture
def run_setup_sh() -> Callable[[str, dict], RunResult]:
    return _run_setup_sh


@pytest.fixture
def run_setup_sh_full() -> Callable[[dict], RunResult]:
    return _run_setup_sh_full


@pytest.fixture
def run_cli() -> Callable[[list[str], dict], RunResult]:
    return _run_cli


def _sha256_tree(*roots: Path) -> str:
    """A deterministic content hash for a set of directory trees.

    The hash covers every regular file's relative path + its bytes. Missing
    roots are included as explicit '(missing)' markers so a disappeared tree
    changes the hash. Symlinks are recorded by link target, not by contents.

    This is the equality oracle for the gate test: sha256_tree(before) must
    equal sha256_tree(after) for restore to be "truly reversible".
    """
    h = hashlib.sha256()
    for root in roots:
        if not root.exists():
            h.update(f"(missing:{root})\n".encode())
            continue
        # Walk in sorted order so hash is deterministic.
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            dirnames.sort()
            filenames.sort()
            for fname in filenames:
                p = Path(dirpath) / fname
                rel = p.relative_to(root)
                h.update(f"{root.name}/{rel}\n".encode())
                if p.is_symlink():
                    h.update(f"->{os.readlink(p)}\n".encode())
                else:
                    with p.open("rb") as fh:
                        for chunk in iter(lambda: fh.read(65536), b""):
                            h.update(chunk)
    return h.hexdigest()


@pytest.fixture
def sha256_tree() -> Callable[..., str]:
    return _sha256_tree
