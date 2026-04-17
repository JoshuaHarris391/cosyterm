<p align="center">
  <img src="https://raw.githubusercontent.com/catppuccin/catppuccin/main/assets/palette/macchiato.png" width="600" />
</p>

<h1 align="center">cosyTerm</h1>

<p align="center">
  <strong>Your whole terminal stack, themed in one command.</strong><br/>
  <sub>Ghostty, your shell, Starship, eza, tmux, NeoVim — all Catppuccin Mocha, fully reversible.</sub>
</p>

<p align="center">
  <a href="https://pypi.org/project/cosyterm/"><img src="https://img.shields.io/pypi/v/cosyterm?color=cba6f7&style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://github.com/JoshuaHarris391/cosyterm/actions"><img src="https://img.shields.io/github/actions/workflow/status/JoshuaHarris391/cosyterm/ci.yml?style=for-the-badge&logo=github&logoColor=white&color=a6e3a1" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/JoshuaHarris391/cosyterm?style=for-the-badge&color=89b4fa" alt="License"></a>
  <a href="#"><img src="https://img.shields.io/badge/macOS_%7C_Linux-supported-f5c2e7?style=for-the-badge&logo=apple&logoColor=white" alt="Platform"></a>
</p>

<p align="center">
  <img src="assets/img/screenshot.png" width="800" alt="cosyTerm screenshot" />
</p>

---

## Install

```bash
pip install cosyterm
cosyterm
```

Launches an interactive wizard. Pick which tools to install, choose your font and shell, then review **every shell command that will run** before a single thing happens. One final Enter executes the whole plan. About two minutes. Existing configs are moved to a timestamped backup first, so `cosyterm restore --latest` reverses the whole run.

Prefer the old step-by-step prompts (or running in a non-TTY environment like CI)? `cosyterm --classic`.

## What you get

| Tool | What it does |
|---|---|
| **[Nerd Font](https://www.nerdfonts.com/)** | 10 patched fonts — JetBrains Mono, Commit Mono, Cascadia Code, and more |
| **[Ghostty](https://ghostty.org)** | GPU-accelerated terminal emulator by Mitchell Hashimoto |
| **[Fish](https://fishshell.com/) or [Zsh](https://www.zsh.org/)** | Fish (recommended) or Zsh (POSIX-compatible) |
| **[Starship](https://starship.rs)** | Cross-shell prompt — git, language versions, right-aligned and clean |
| **[eza](https://eza.rocks)** | `ls` with icons, colors, git status, and tree views |
| **[tmux](https://github.com/tmux/tmux)** | Terminal multiplexer with pastel status bar at top |
| **[NeoVim](https://neovim.io) + [LazyVim](https://lazyvim.github.io)** | IDE-grade editor, pre-configured, zero setup |

## Docs

- **[Safety model](docs/safety.md)** — every command that runs, every URL fetched, every `sudo` — plus backups and blast-radius guarantees.
- **[Recovery](docs/recovery.md)** — `cosyterm doctor`, `cosyterm restore`, and the `--dry-run` preview.
- **[Automation](docs/automation.md)** — scripted installs (`COSYTERM_YES=1`, `COSYTERM_NVIM_CHOICE`), re-running a single step, and the Python API.
- **[Design philosophy](docs/philosophy.md)** — why cosyTerm is opinionated and what it won't add.

---

**Try it. If it's not for you, `cosyterm restore --latest` puts everything back.**

## Requirements

macOS or Linux · Python 3.8+ · bash · git · Homebrew (macOS) or apt/dnf/pacman (Linux)

## Contributing

Open source contributions are welcome. Before adding a new tool or feature, open an issue to discuss it — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Credits

- Setup guide by **[Guillaume Moigneu](https://devcenter.upsun.com/posts/my-terminal-setup-mac-linux/)** at Upsun
- Theme: **[Catppuccin](https://catppuccin.com)** by the Catppuccin community
- Prompt: **[Starship](https://starship.rs)**
- Terminal: **[Ghostty](https://ghostty.org)** by Mitchell Hashimoto
- Editor: **[NeoVim](https://neovim.io)** + **[LazyVim](https://lazyvim.github.io)**

## License

[MIT](LICENSE)
