# Safety model

cosyTerm modifies files in your home directory and, on Linux, runs `sudo` for package installs and for appending Fish to `/etc/shells`. Here's how it minimises blast radius.

- **Backups** — existing configs are backed up to `~/.terminal-setup-backups/<timestamp>/` before being touched. The NeoVim step **moves** (not copies) `~/.config/nvim`, `~/.local/share/nvim`, and `~/.local/state/nvim` into the backup so plugin state and your `lazy-lock.json` come back exactly if you restore. Cache (`~/.cache/nvim`) is regenerable and not backed up.
- **Manifest** — every move/copy is recorded in `<backup>/manifest.tsv` so `cosyterm restore` can undo them exactly.
- **Confirmations** — every install and config write asks `[y/N]` first. Replacing an existing NeoVim config requires typing `replace` — not a single keystroke.
- **NeoVim pre-flight** — if you already have a NeoVim config, you're offered `skip` / `side-by-side` (installs to `~/.config/nvim-cosy`, original untouched) / `replace`. The safe route is the default when auto-confirming.
- **Verification** — after each install, the binary is confirmed on PATH before writing any config that references it.
- **Mismatch detection** — a final check catches configs pointing to tools that aren't installed.
- **PATH migration (best-effort)** — PATH entries from Zsh/Bash are translated to `fish_add_path` where possible; review `~/.config/fish/config.fish` after install.
- **Full log** — everything is recorded in `~/terminal-setup.log`.

See also: [Recovery](recovery.md) for how to diagnose and undo a run.
