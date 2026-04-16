# Contributing to cosyTerm

Thanks for your interest in contributing. cosyTerm is a curated tool, so we're thoughtful about what goes in — but we genuinely welcome help making it better.

## What we're looking for

- **Bug fixes** — if something breaks on your OS, distro, or shell, we want to know
- **Installer improvements** — better error handling, clearer prompts, smarter fallbacks
- **Platform support** — WSL, new Linux distros, edge cases on older macOS versions
- **Documentation** — typos, unclear instructions, missing context
- **Better defaults** — if a config value could be smarter, suggest it

## Before adding a new tool

cosyTerm is intentionally limited. We pick one tool per job and theme it consistently. Before proposing a new tool, open an issue to discuss:

- What problem does it solve that the current setup doesn't?
- Does it fit the "run and go" philosophy — zero config needed from the user?
- Does it have a Catppuccin port?
- Does it add complexity to the installer flow?

We won't merge additions that make the user think harder. The whole point is they don't have to.

## How to contribute

1. Fork the repo
2. Create a branch (`git checkout -b fix/your-fix`)
3. Make your changes
4. Test on macOS and/or Linux if possible
5. Run `bash -n src/cosyterm/scripts/setup.sh` to verify script syntax
6. Open a PR with a clear description of what changed and why

## Code style

- **Bash**: `set -euo pipefail`, functions prefixed with `install_` or `_helper`, log everything
- **Python**: standard library only, no third-party dependencies, type hints where useful
- Keep it simple. If a change needs a paragraph to explain, it might be too complex.

## Be kind

This is a small project. We review PRs as time allows. Be patient, be respectful, and assume good intent.
