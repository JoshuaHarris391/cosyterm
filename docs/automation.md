# Automation

## Scripted install

For dotfiles-bootstrap, devcontainers, or onboarding scripts:

```bash
COSYTERM_YES=1 COSYTERM_NVIM_CHOICE=sidebyside cosyterm --classic
```

Setting the full choice surface non-interactively:

```bash
COSYTERM_YES=1 \
COSYTERM_STEPS=font,ghostty,shell,starship,eza,tmux,neovim \
COSYTERM_FONT_CHOICE=0xProto \
COSYTERM_SHELL_CHOICE=fish \
COSYTERM_FISH_METHOD=chsh \
COSYTERM_NVIM_CHOICE=sidebyside \
cosyterm --classic
```

(The curses wizard auto-falls-back to the classic path when stdin/stdout is not a TTY — so the `--classic` flag is mostly for explicitness.)

| Variable | Effect |
|---|---|
| `COSYTERM_YES=1` | Auto-answer every `[y/N]` with yes. |
| `COSYTERM_STEPS=<csv>` | CSV subset of `font,ghostty,shell,starship,eza,tmux,neovim`. Default: all seven. Skipped steps run no commands. |
| `COSYTERM_FONT_CHOICE=<key>` | Font key (`JetBrainsMono`, `CommitMono`, `CascadiaCode`, `Hack`, `FiraCode`, `0xProto`, `Monofur`, `OpenDyslexic`, `Agave`, `Hasklig`) or `skip`. Bypasses the font picker. |
| `COSYTERM_SHELL_CHOICE=fish\|zsh\|skip` | Pre-answer the shell picker. |
| `COSYTERM_FISH_METHOD=chsh\|ghostty\|none` | Pre-answer the fish-method picker. Only consulted when shell is `fish`. |
| `COSYTERM_NVIM_CHOICE=skip\|sidebyside\|replace` | Pre-answer the NeoVim prompt. With `COSYTERM_YES=1` but this unset, NeoVim defaults to `skip` so your config is never silently replaced. |
| `COSYTERM_PLAN=1` | Dry-run. Emits tab-delimited `CMD` / `WRITE` / `SECTION` / `NOTE` lines on stdout and executes nothing. The wizard uses this to populate its review screen; you can use it in CI to assert on what a given config would do. |
| `COSYTERM_BACKUP_DIR=<path>` | Override `~/.terminal-setup-backups`. |
| `COSYTERM_LOG_FILE=<path>` | Override `~/terminal-setup.log`. |

## Re-run a single step

```bash
cosyterm install <step>
```

Step names: `font`, `ghostty`, `shell`, `starship`, `eza`, `tmux`, `neovim`.

Useful when `cosyterm doctor` surfaces a single missing piece, or inside a dotfile pipeline that only wants to update one tool.

## Python API

```python
import cosyterm

cosyterm.setup()        # run the interactive installer
cosyterm.doctor()       # check for issues
```

See also: [Recovery](recovery.md) for `doctor` output and the restore flow.
