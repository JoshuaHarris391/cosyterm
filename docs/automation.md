# Automation

## Scripted install

For dotfiles-bootstrap, devcontainers, or onboarding scripts:

```bash
COSYTERM_YES=1 COSYTERM_NVIM_CHOICE=sidebyside cosyterm
```

| Variable | Effect |
|---|---|
| `COSYTERM_YES=1` | Auto-answer every `[y/N]` with yes. |
| `COSYTERM_NVIM_CHOICE=skip\|sidebyside\|replace` | Pre-answer the NeoVim prompt. With `COSYTERM_YES=1` but this unset, NeoVim defaults to `skip` so your config is never silently replaced. |
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
