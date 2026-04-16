# Recovery

Every cosyTerm run writes a manifest of what it changed, so diagnosing problems and reversing a run are first-class commands.

## Diagnose with `doctor`

```bash
cosyterm doctor
```

```
━━━ cosyTerm doctor ━━━

  ✓ Ghostty          /opt/homebrew/bin/ghostty
  ✓ Starship         /opt/homebrew/bin/starship
  ✓ Starship config  ~/.config/starship.toml
  ✓ eza              /opt/homebrew/bin/eza
  ✓ tmux             /opt/homebrew/bin/tmux
  ✓ Catppuccin tmux  ~/.config/tmux/plugins/catppuccin/tmux
  ✓ NeoVim           /opt/homebrew/bin/nvim
  ✓ LazyVim config   ~/.config/nvim

  ✓ No config/binary mismatches found
```

Checks for missing binaries, orphaned configs, PATH issues, and font problems.

## Undo

```bash
# See what's available
cosyterm restore --list

# Preview what a restore would do — changes nothing on disk
cosyterm restore --latest --dry-run

# Reverse the most recent install completely
cosyterm restore --latest

# Reverse just one step (e.g. bring your NeoVim config back)
cosyterm restore --latest --only neovim

# Restore from a specific backup by timestamp
cosyterm restore --from 20250415_143022

# Verify a backup's integrity without restoring
cosyterm restore --verify --latest
```

### Preview with `--dry-run`

Pair `--dry-run` with any restore target (`--latest`, `--from <timestamp>`, `--only <step>`) to see exactly which paths would move back, in the order they'd be restored, without touching a single file.

```
Restoring from: ~/.terminal-setup-backups/20250415_143022
Entries: 3  (filtered to step 'neovim')

  [would move back]  ~/.terminal-setup-backups/20250415_143022/.local/state/nvim  →  ~/.local/state/nvim
  [would move back]  ~/.terminal-setup-backups/20250415_143022/.local/share/nvim  →  ~/.local/share/nvim
  [would move back]  ~/.terminal-setup-backups/20250415_143022/.config/nvim       →  ~/.config/nvim

(no changes made — --dry-run)
```

Use it to sanity-check a restore — especially when combining `--from` with `--only` — before committing to the real run.

## Under the hood

`restore` reads `manifest.tsv` from the chosen backup dir, stashes your current post-install state into a `pre-restore-<timestamp>/` subdir (so a restore is itself reversible), then moves every backed-up path back where it came from. Backups are plain directories — if the CLI isn't handy, `cp ~/.terminal-setup-backups/<timestamp>/.zshrc ~/.zshrc` works too.

See also: [Safety model](safety.md) for what's backed up and why.
