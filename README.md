<p align="center">
  <img src="https://raw.githubusercontent.com/catppuccin/catppuccin/main/assets/palette/macchiato.png" width="600" />
</p>

<h1 align="center">cosyTerm</h1>

<p align="center">
  <strong>Your terminal, but make it cozy.</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/cosyterm/"><img src="https://img.shields.io/pypi/v/cosyterm?color=cba6f7&style=for-the-badge&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="https://github.com/JoshuaHarris391/cosyterm/actions"><img src="https://img.shields.io/github/actions/workflow/status/JoshuaHarris391/cosyterm/ci.yml?style=for-the-badge&logo=github&logoColor=white&color=a6e3a1" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/github/license/JoshuaHarris391/cosyterm?style=for-the-badge&color=89b4fa" alt="License"></a>
  <a href="#"><img src="https://img.shields.io/badge/macOS_%7C_Linux-supported-f5c2e7?style=for-the-badge&logo=apple&logoColor=white" alt="Platform"></a>
</p>

<p align="center">
  <sub>You want a beautiful terminal. You don't want to spend a weekend configuring one.<br/><b>cosyTerm</b> gives you the whole thing in one command.</sub>
</p>

<p align="center">
  <img src="assets/img/screenshot.png" width="800" alt="cosyTerm screenshot" />
</p>

---

## The idea

Most developers know their terminal *could* look better. Fewer want to spend hours reading dotfile repos, debugging shell configs, and cross-referencing theme ports across six different tools.

**cosyTerm** is for you if:

- You've seen those gorgeous terminal screenshots and thought *"I want that but I don't want to do all… that"*
- You'd rather run one command than hand-wire configs for a weekend
- You want everything to match — prompt, editor, multiplexer, file listings — without hunting down theme ports yourself
- You care about how your tools look and feel, but terminal customisation isn't your hobby

Two commands. Done.

```bash
pip install cosyterm
cosyterm
```

## What you get

A curated, cohesive terminal — every piece themed with **[Catppuccin Mocha](https://catppuccin.com)**.

| Tool | What it does |
|---|---|
| **[Nerd Font](https://www.nerdfonts.com/)** | Your choice of 10 patched fonts — JetBrains Mono, Commit Mono, Cascadia Code, and more |
| **[Ghostty](https://ghostty.org)** | GPU-accelerated terminal emulator by Mitchell Hashimoto |
| **[Fish](https://fishshell.com/) or [Zsh](https://www.zsh.org/)** | Fish (recommended) or Zsh (POSIX-compatible) |
| **[Starship](https://starship.rs)** | Cross-shell prompt — git, language versions, right-aligned and clean |
| **[eza](https://eza.rocks)** | `ls` with icons, colors, git status, and tree views |
| **[tmux](https://github.com/tmux/tmux)** | Terminal multiplexer with pastel status bar at top |
| **[NeoVim](https://neovim.io) + [LazyVim](https://lazyvim.github.io)** | IDE-grade editor, pre-configured, zero setup |
| **Claude Code** | AI assistance inside NeoVim |

## How it works

```bash
cosyterm
```

An interactive installer walks you through 8 steps. Every step asks before doing anything. Skip what you don't want. Nothing is installed silently.

```
╔═══════════════════════════════════════════════════════════════╗
║           cosyTerm — your terminal, but make it cozy         ║
╚═══════════════════════════════════════════════════════════════╝

Step 1/8 ▶ Pick a font
Step 2/8 ▶ Ghostty terminal
Step 3/8 ▶ Shell (Zsh default)
Step 4/8 ▶ Starship prompt
Step 5/8 ▶ eza (better ls)
Step 6/8 ▶ tmux + Catppuccin
Step 7/8 ▶ NeoVim + LazyVim
Step 8/8 ▶ Claude Code plugin
```

When it's done, close your terminal, open Ghostty, and everything just works.

## Something feel off?

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

## Safety

This isn't a script that silently overwrites your dotfiles and hopes for the best.

- **Backups** — every config is copied to `~/.terminal-setup-backups/<timestamp>/` before being touched
- **Confirmations** — every install and config write asks `[y/N]` first
- **Verification** — after each install, the binary is confirmed on PATH before writing any config that references it
- **Mismatch detection** — a final check catches configs pointing to tools that aren't installed
- **PATH migration** — if you switch to Fish, your Zsh/Bash PATH exports are scanned and translated
- **Full log** — everything is recorded in `~/terminal-setup.log`

## Recovering

Everything is reversible. Your backups are timestamped:

```bash
ls ~/.terminal-setup-backups/
cp ~/.terminal-setup-backups/20250415_143022/.zshrc ~/.zshrc
```

## Python API

```python
import cosyterm

cosyterm.setup()        # run the interactive installer
cosyterm.doctor()       # check for issues
```

## Requirements

macOS or Linux · Python 3.8+ · bash · git · Homebrew (macOS) or apt/dnf/pacman (Linux)

---

## Design philosophy

**cosyTerm is a curated product, not a framework.**

The tool selection is intentional and limited. I don't offer 15 theme options, 8 prompt engines, or 4 terminal emulators. I picked one cohesive set of tools that work well together, themed them consistently, and made the whole thing installable in one command.

This is opinionated by design. The constraint is the feature.


### What I will add

- New tools that improve the curated experience (e.g., better git UIs, fuzzy finders)
- Platform support (more Linux distros, WSL)
- Additional Nerd Font options
- Quality-of-life improvements to the installer flow

### What I won't add

- Multiple competing themes or colour schemes
- Alternative tools that do the same thing as an existing pick
- Options that require the user to understand terminal internals
- Anything that makes the "just run it" experience more complicated

## Contributing

Open source contributions are welcome. Whether it's bug fixes, installer improvements, new platform support, or better defaults — I'd love the help.

Before adding a new tool or feature, open an issue to discuss it. I want to keep the curated feel, so not everything will be a fit, but the conversation is always welcome.

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Credits

- Setup guide by **[Guillaume Moigneu](https://devcenter.upsun.com/posts/my-terminal-setup-mac-linux/)** at Upsun
- Theme: **[Catppuccin](https://catppuccin.com)** by the Catppuccin community
- Prompt: **[Starship](https://starship.rs)**
- Terminal: **[Ghostty](https://ghostty.org)** by Mitchell Hashimoto
- Editor: **[NeoVim](https://neovim.io)** + **[LazyVim](https://lazyvim.github.io)**

## License

[MIT](LICENSE)
