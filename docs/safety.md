# Safety model

cosyTerm modifies files in your home directory and, on Linux, runs `sudo` for package installs and for appending Fish to `/etc/shells`. Here's how it minimises blast radius.

- **Backups** — existing configs are backed up to `~/.terminal-setup-backups/<timestamp>/` before being touched. The NeoVim step **moves** (not copies) `~/.config/nvim`, `~/.local/share/nvim`, and `~/.local/state/nvim` into the backup so plugin state and your `lazy-lock.json` come back exactly if you restore. Cache (`~/.cache/nvim`) is regenerable and not backed up.
- **Manifest** — every move/copy is recorded in `<backup>/manifest.tsv` so `cosyterm restore` can undo them exactly.
- **Confirmations** — every install and config write asks `[y/N]` first. Replacing an existing NeoVim config requires typing `replace` — not a single keystroke.
- **NeoVim pre-flight** — if you already have a NeoVim config, you're offered `skip` / `side-by-side` (installs to `~/.config/nvim-cosy`, original untouched) / `replace`. The safe route is the default when auto-confirming.
- **Verification** — after each install, the binary is confirmed on PATH before writing any config that references it.
- **Mismatch detection** — a final check catches configs pointing to tools that aren't installed.
- **PATH migration (best-effort)** — PATH entries from Zsh/Bash are translated to `fish_add_path` and written to `~/.config/fish/conf.d/00-cosyterm-path.fish` (honours `$XDG_CONFIG_HOME`). Anything that can't be auto-translated (nvm, conda) is logged as a post-install TODO in `~/.terminal-setup-backups/<timestamp>/TODO.md`.
- **Full log** — everything is recorded in `~/terminal-setup.log`.

## What commands will run

Every command below runs only after you confirm its step. Line references point into [`src/cosyterm/scripts/setup.sh`](../src/cosyterm/scripts/setup.sh) so you can verify against the source.

- **Nerd Font**
  - macOS: `brew install --cask font-<name>-nerd-font` (setup.sh:442)
  - Linux: `curl -fsSL <font-url> -o /tmp/font.zip` then `unzip -qo /tmp/font.zip -d ~/.local/share/fonts` then `fc-cache -fv ~/.local/share/fonts` (setup.sh:461-468)
- **Ghostty**
  - macOS: `brew install --cask ghostty` (setup.sh:512)
  - apt: `sudo apt-get install -y ghostty` — often not in default repos; falls back to a manual-install hint (setup.sh:517)
  - pacman: `sudo pacman -S --noconfirm ghostty` (setup.sh:521)
- **Shell** (Fish or Zsh)
  - macOS: `brew install fish` / `brew install zsh` via `pkg_install` (setup.sh:620)
  - Linux: `sudo apt-get install -y <shell>` / `sudo dnf install -y <shell>` / `sudo pacman -S --noconfirm <shell>` (setup.sh:320-326)
  - `sudo tee -a /etc/shells` — only if you pick "set Fish as default" and Fish isn't already registered (setup.sh:655)
  - `chsh -s "$(which fish|zsh)"` — only on explicit confirmation (setup.sh:658, 685)
- **Starship**
  - macOS: `brew install starship` (setup.sh:898)
  - Linux: downloads `https://starship.rs/install.sh` to `/tmp/starship-install.sh`, then asks again before running `sh /tmp/starship-install.sh -y` — you can inspect the file first (setup.sh:902-908)
- **eza, tmux, NeoVim** — `brew install` on macOS, `pkg_install` on Linux (setup.sh:1147, 1262, 1503)
  - On Ubuntu without eza in apt, falls back to `cargo install eza` (setup.sh:1153) — requires rustup already installed
- **tmux plugins**
  - `git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm` (setup.sh:1287)
  - `git clone -b v2.3.0 https://github.com/catppuccin/tmux.git ~/.config/tmux/plugins/catppuccin/tmux` (setup.sh:1308)
- **LazyVim** — `git clone https://github.com/LazyVim/starter ~/.config/nvim` (setup.sh:130, 1487). `.git` is removed after clone so the result is yours to version however you like.

## Where downloads come from

Every remote source cosyTerm reaches out to, what it is, and when it gets fetched.

| Source | What | When |
|---|---|---|
| `github.com/ryanoasis/nerd-fonts/releases/latest` | Nerd Font `.zip` | Linux, step 1, if you pick a font |
| `raw.githubusercontent.com/catppuccin/ghostty` | Ghostty Mocha theme | Step 2, if you accept the Ghostty config |
| `starship.rs/install.sh` | Official Starship installer | Linux, step 4, only if Starship isn't already installed |
| `github.com/tmux-plugins/tpm` | Tmux Plugin Manager | Step 6 |
| `github.com/catppuccin/tmux` (tag `v2.3.0`) | tmux theme | Step 6 |
| `github.com/LazyVim/starter` | LazyVim starter repo | Step 7, only on `replace` or `side-by-side` |

## When sudo is used

cosyTerm will only ever call `sudo` in two situations:

- **Linux package installs** — `sudo apt-get install` / `sudo dnf install` / `sudo pacman -S` for each tool you accept (setup.sh:320-326). Never on macOS; Homebrew runs as your user.
- **Registering Fish in `/etc/shells`** — `sudo tee -a /etc/shells`, only if you chose "set Fish as default" and the binary isn't already listed (setup.sh:655).

Everything else — config writes, backups, git clones, font extraction — runs as your user inside your `$HOME`.

See also: [Recovery](recovery.md) for how to diagnose and undo a run.
