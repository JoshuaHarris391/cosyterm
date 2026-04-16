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

## Where cosyterm writes in fish

Starting with cosyTerm 0.3.0, fish integration lives entirely in `conf.d/` — cosyterm never touches `config.fish` on new installs:

| File | Purpose |
|---|---|
| `~/.config/fish/conf.d/00-cosyterm-path.fish` | PATH migration from bash/zsh (`fish_add_path` calls) |
| `~/.config/fish/conf.d/10-cosyterm-init.fish` | Homebrew `shellenv` + `starship init fish` |
| `~/.config/fish/conf.d/20-cosyterm-aliases.fish` | `eza` aliases (`ls`, `lsa`, `lt`, `lta`) |

All three honour `$XDG_CONFIG_HOME` — if you've set it, cosyterm writes to `$XDG_CONFIG_HOME/fish/conf.d/` instead.

Fish sources `conf.d/*.fish` alphabetically before `config.fish`, so cosyterm's stuff runs early and you retain full control of `config.fish`.

## Troubleshooting

### Fish starts with `Unknown command` errors referencing `.docker/completions` (or similar)

**Symptom.** On fish startup you see something like:

```
~/.config/fish/config.fish (line 1): Unknown command. '/Users/you/.docker/completions' exists but is not an executable file.
fish: Unknown command: mktemp
fish: Unknown command: uname
thread 'main' panicked ... failed printing to stdout: Broken pipe
```

**Cause.** Affects cosyTerm < 0.2.1. The PATH migration's scan regex was too broad and matched zsh `fpath=(...)` completion lines (e.g. Docker Desktop's). The mangled line wrote unbalanced parentheses into `config.fish`, which fish parses as a command substitution — that clobbers `$PATH`, so even `/bin` and `/usr/bin` fall off and basic commands vanish.

**Fix.** From a working shell (zsh works fine — it's not affected), remove the bad migration block:

```sh
sed -i.bak '/# PATH migration from Bash\/Zsh — START/,/# PATH migration from Bash\/Zsh — END/d' ~/.config/fish/config.fish
rm ~/.config/fish/config.fish.bak
# 0.3.0+ also put a copy in conf.d — remove that too if present:
rm -f ~/.config/fish/conf.d/00-cosyterm-path.fish
```

Then start fish, confirm it sources cleanly, and upgrade cosyTerm (`pip install -U cosyterm`) before re-running setup. If you'd prefer to roll back entirely, `cosyterm restore --latest` reverses the install.

### macOS: "bash >=4 is required" when running `cosyterm`

**Cause.** macOS ships `/bin/bash` 3.2 for GPL-v2 licensing reasons; cosyterm's installer uses bash 4+ features (associative arrays, pattern substitution, etc.) and refuses to run under 3.2 rather than fail cryptically mid-script.

**Fix.** Install a modern bash via Homebrew:

```sh
brew install bash
```

You don't need to change your login shell — cosyterm's Python wrapper picks up `/opt/homebrew/bin/bash` automatically.

### PATH migration skipped my `mise` / `asdf` / `rbenv` activation

**Cause.** cosyterm deliberately supports only the most common activation patterns (Homebrew, cargo, pyenv, nvm, conda). Version managers with shell-specific activation (`mise activate fish`, `asdf.fish` plugin, etc.) need their fish-native equivalents — cosyterm would emit bash syntax that fish can't run.

**Fix.** After install, add your version manager's fish integration to `~/.config/fish/conf.d/` yourself. Examples:

```fish
# ~/.config/fish/conf.d/50-mise.fish
mise activate fish | source
```

```fish
# ~/.config/fish/conf.d/50-asdf.fish
source ~/.asdf/asdf.fish
```

### Migrated PATH references `$GOPATH` / `$JAVA_HOME` / another shell var that doesn't exist in fish

**Cause.** Your bash/zsh rc file set `$GOPATH` and then used it in `PATH="$GOPATH/bin:$PATH"`. cosyterm translates the PATH line faithfully, but fish has no knowledge of `$GOPATH` because it never read your zshrc.

**Fix.** Define the variable in `~/.config/fish/conf.d/40-cosyterm-envs.fish` so both the variable and the `fish_add_path` reference work:

```fish
set -gx GOPATH $HOME/go
fish_add_path -g "$GOPATH/bin"
```

Leaving the original `fish_add_path -g "$GOPATH/bin"` in `00-cosyterm-path.fish` is harmless — fish expands the undefined var to empty and skips the add.

### Multi-line PATH assignments weren't migrated

**Cause.** The scan is line-based; PATH assignments that use a backslash continuation (`PATH="\ \n /foo:$PATH"`) are only partially captured.

**Fix.** Open the file cosyterm scanned (`~/.zshrc` and friends), combine the multi-line assignment into a single line, and re-run `cosyterm install shell`. Or add the missing path manually with `fish_add_path -g /your/path`.

### Conditional PATH (`[[ -d ~/.foo/bin ]] && PATH=...`) added even when the directory doesn't exist

**Cause.** cosyterm copies the path without re-evaluating the `[[ -d ... ]]` guard. Fish tolerates non-existent directories in `$PATH` — it's a no-op, not an error — so this is cosmetic. If it bothers you, delete the line from `00-cosyterm-path.fish`.

See also: [Safety model](safety.md) for what's backed up and why.
