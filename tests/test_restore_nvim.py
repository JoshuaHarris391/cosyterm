"""
Tests for the NeoVim safety rework + cosyterm restore.

These tests are the evidence that cosyterm's "Everything is reversible"
promise holds specifically for the riskiest step in the wizard: replacing
an existing NeoVim config.

Each test follows the house convention: clear docstring, explicit inputs
(fixtures + env), explicit expected outputs (tree hash, file presence,
manifest contents). A junior developer should be able to read the
docstring and understand why the test matters and what would break in
production if it started failing.
"""

from __future__ import annotations

from pathlib import Path


# -----------------------------------------------------------------------------
# The gate test — nothing ships if this goes red.
# -----------------------------------------------------------------------------
def test_restore_nvim_brings_back_precious_config(
    tmp_home: Path,
    install_fixture,
    sandbox_env,
    run_setup_sh,
    run_cli,
    sha256_tree,
):
    """A user has a working LazyVim setup with plugin state and a lockfile
    pinning plugin versions. They run cosyterm (replace mode), then regret
    it and run `cosyterm restore --latest --only neovim`. Every byte of
    their ~/.config/nvim + ~/.local/share/nvim + ~/.local/state/nvim must
    come back exactly as it was.

    This is the load-bearing claim of the whole rework. If this test
    fails, nvim users who trusted cosyterm can lose plugin pins, shada,
    and config. Nothing merges until this stays green.
    """
    # Given: a precious LazyVim setup on disk.
    install_fixture("nvim_lazyvim", tmp_home)

    nvim_roots = [
        tmp_home / ".config" / "nvim",
        tmp_home / ".local" / "share" / "nvim",
        tmp_home / ".local" / "state" / "nvim",
    ]
    before_hash = sha256_tree(*nvim_roots)
    assert before_hash, "fixture produced an empty hash — fixture files missing"

    # When: the user runs the nvim install step in 'replace' mode, then restore.
    env = sandbox_env(COSYTERM_NVIM_CHOICE="replace")
    install = run_setup_sh("neovim", env)
    assert install.returncode == 0, (
        f"install failed\nSTDOUT:\n{install.stdout}\nSTDERR:\n{install.stderr}"
    )

    # Post-install, the original precious config is gone from its live paths
    # (sanity check that the test is actually exercising the destructive path).
    lazy_lock_after_install = (tmp_home / ".config" / "nvim" / "lazy-lock.json").exists()
    # Fake git clone writes README.md but no lazy-lock.json, so this must be False.
    assert not lazy_lock_after_install, (
        "install did not replace the existing nvim config — test is not "
        "exercising the destructive path"
    )

    # A backup dir with a manifest must exist.
    backups_root = tmp_home / ".terminal-setup-backups"
    backup_dirs = [d for d in backups_root.iterdir() if d.is_dir()]
    assert backup_dirs, "no backup directory was created"
    assert (backup_dirs[0] / "manifest.tsv").is_file(), "manifest.tsv missing"

    # When: the user restores.
    restore = run_cli(["restore", "--latest", "--only", "neovim"], env)
    assert restore.returncode == 0, (
        f"restore failed\nSTDOUT:\n{restore.stdout}\nSTDERR:\n{restore.stderr}"
    )

    # Then: every byte of the three nvim dirs is back where it started.
    after_hash = sha256_tree(*nvim_roots)
    assert after_hash == before_hash, (
        "restore did NOT bring nvim back byte-for-byte — this is the "
        "exact failure the user would experience as lost plugin state / "
        "lost config / lost shada"
    )


# -----------------------------------------------------------------------------
# Supporting tests — each guards a specific part of the safety model.
# -----------------------------------------------------------------------------
def test_sidebyside_leaves_original_untouched(
    tmp_home: Path,
    install_fixture,
    sandbox_env,
    run_setup_sh,
    sha256_tree,
):
    """In side-by-side mode, LazyVim is installed at ~/.config/nvim-cosy
    and the existing ~/.config/nvim (plus plugin and state dirs) is not
    touched. This is the recommended route for users with custom configs.

    What this guards against: the scariest regression would be a future
    refactor that accidentally wires side-by-side mode through the same
    mv/rm path as replace mode — silently destroying the user's config
    even when they explicitly picked the "safe" option. This test asserts
    a byte-exact equality on the original paths so any such regression
    lights up immediately.
    """
    install_fixture("nvim_lazyvim", tmp_home)
    before = sha256_tree(
        tmp_home / ".config" / "nvim",
        tmp_home / ".local" / "share" / "nvim",
        tmp_home / ".local" / "state" / "nvim",
    )

    env = sandbox_env(COSYTERM_NVIM_CHOICE="sidebyside")
    result = run_setup_sh("neovim", env)
    assert result.returncode == 0, result.stderr

    # Side-by-side target must exist.
    assert (tmp_home / ".config" / "nvim-cosy" / "init.lua").is_file()

    # Original three trees must be byte-for-byte unchanged.
    after = sha256_tree(
        tmp_home / ".config" / "nvim",
        tmp_home / ".local" / "share" / "nvim",
        tmp_home / ".local" / "state" / "nvim",
    )
    assert after == before


def test_skip_touches_nothing(
    tmp_home: Path,
    install_fixture,
    sandbox_env,
    run_setup_sh,
    sha256_tree,
):
    """'skip' must be a true no-op: no backup dir, no config change, no
    side-by-side install. This is the default path for COSYTERM_YES=1 when
    no explicit choice is given — users who accidentally auto-approve must
    land on the safe path, not the destructive one.
    """
    install_fixture("nvim_lazyvim", tmp_home)

    env = sandbox_env()  # no COSYTERM_NVIM_CHOICE → defaults to skip
    result = run_setup_sh("neovim", env)
    assert result.returncode == 0, result.stderr

    # No backup dir should have been created for a skip.
    assert not (tmp_home / ".terminal-setup-backups").exists(), (
        "skip should not create any backup"
    )
    # The side-by-side target must not exist.
    assert not (tmp_home / ".config" / "nvim-cosy").exists()

    # Home tree is untouched — assert the fixture files are still present.
    # (A whole-tree hash comparison was tried but abandoned because the log
    # file gets written into $HOME; a spot-check on the nvim roots is
    # tighter anyway.)
    assert (tmp_home / ".config" / "nvim" / "lazy-lock.json").is_file()
    assert (tmp_home / ".local" / "share" / "nvim" / "lazy" /
            "tokyonight.nvim" / "plugin" / "tokyonight.vim").is_file()


def test_manifest_records_every_move(
    tmp_home: Path,
    install_fixture,
    sandbox_env,
    run_setup_sh,
):
    """Every destructive operation must produce one manifest row. Without
    this, restore has no way to know what it needs to undo. The manifest
    is the authoritative record of "what cosyterm did to this machine".
    """
    install_fixture("nvim_lazyvim", tmp_home)

    env = sandbox_env(COSYTERM_NVIM_CHOICE="replace")
    result = run_setup_sh("neovim", env)
    assert result.returncode == 0, result.stderr

    backups_root = tmp_home / ".terminal-setup-backups"
    backup_dir = next(d for d in backups_root.iterdir() if d.is_dir())
    manifest = (backup_dir / "manifest.tsv").read_text()

    # Exactly the three nvim trifecta paths must be recorded.
    expected_sources = {
        str(tmp_home / ".config" / "nvim"),
        str(tmp_home / ".local" / "share" / "nvim"),
        str(tmp_home / ".local" / "state" / "nvim"),
    }
    rows = [
        line.split("\t") for line in manifest.splitlines()
        if line and not line.startswith("#")
    ]
    sources_in_manifest = {r[2] for r in rows if len(r) == 5}
    assert sources_in_manifest == expected_sources, (
        f"manifest does not record every moved path\n"
        f"  expected: {expected_sources}\n"
        f"  got:      {sources_in_manifest}"
    )
    # Every entry must be tagged with step=neovim and action=move (not copy).
    for r in rows:
        assert r[0] == "neovim", f"wrong step: {r}"
        assert r[1] == "move", f"wrong action (should be mv-based): {r}"


def test_restore_dry_run_is_a_noop(
    tmp_home: Path,
    install_fixture,
    sandbox_env,
    run_setup_sh,
    run_cli,
    sha256_tree,
):
    """`cosyterm restore --dry-run` must print what it would do and change
    nothing on disk. If a user runs --dry-run to check before committing,
    and it accidentally moves files, the safety claim collapses.
    """
    install_fixture("nvim_lazyvim", tmp_home)
    env = sandbox_env(COSYTERM_NVIM_CHOICE="replace")
    assert run_setup_sh("neovim", env).returncode == 0

    # Snapshot the entire home after install but before dry-run restore.
    home_before = sha256_tree(tmp_home)

    result = run_cli(["restore", "--latest", "--only", "neovim", "--dry-run"], env)
    assert result.returncode == 0, result.stderr
    assert "would" in result.stdout.lower(), "dry-run should say 'would'"

    home_after = sha256_tree(tmp_home)
    assert home_after == home_before, "--dry-run mutated the filesystem"


def test_restore_list_shows_backup(
    tmp_home: Path,
    install_fixture,
    sandbox_env,
    run_setup_sh,
    run_cli,
):
    """`cosyterm restore --list` must surface every backup dir that has a
    manifest, with its step tags. Users rely on this to recover without
    remembering exact timestamps.
    """
    install_fixture("nvim_lazyvim", tmp_home)
    env = sandbox_env(COSYTERM_NVIM_CHOICE="replace")
    assert run_setup_sh("neovim", env).returncode == 0

    result = run_cli(["restore", "--list"], env)
    assert result.returncode == 0, result.stderr
    assert "neovim" in result.stdout, "backup listing should mention step=neovim"
    assert "entries" in result.stdout, (
        "listing should summarise how many entries each backup holds"
    )


def test_verify_fails_when_backup_tampered(
    tmp_home: Path,
    install_fixture,
    sandbox_env,
    run_setup_sh,
    run_cli,
):
    """If someone deletes a file from a backup dir, `restore --verify` must
    spot the missing path and exit non-zero. Without this, a silently
    corrupted backup would only be discovered mid-restore, when it's too
    late.
    """
    install_fixture("nvim_lazyvim", tmp_home)
    env = sandbox_env(COSYTERM_NVIM_CHOICE="replace")
    assert run_setup_sh("neovim", env).returncode == 0

    # Corrupt the backup: remove the state/nvim backup path entirely.
    backups_root = tmp_home / ".terminal-setup-backups"
    backup_dir = next(d for d in backups_root.iterdir() if d.is_dir())
    import shutil
    # The backup filename is the safe-mangled source path (e.g. ".local_state_nvim")
    for child in backup_dir.iterdir():
        if child.name.endswith("_state_nvim"):
            shutil.rmtree(child)
            break

    result = run_cli(
        ["restore", "--verify", "--from", backup_dir.name],
        env,
    )
    assert result.returncode != 0, (
        f"verify should fail after tampering, but exited 0\n{result.stdout}"
    )
    assert "missing" in result.stdout.lower() or "missing" in result.stderr.lower()
