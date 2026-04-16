"""
cosyTerm — Your terminal, but make it cozy.

One command to install and configure a beautiful, cohesive terminal
setup: Ghostty, Starship, eza, tmux, NeoVim + LazyVim — all themed
with Catppuccin Mocha. No effort required.

Usage:
    $ pip install cosyterm
    $ cosyterm

Or from Python:
    >>> import cosyterm
    >>> cosyterm.setup()
"""

__version__ = "0.1.0"

from cosyterm.core import setup, doctor, install_step, INSTALL_STEPS

__all__ = ["setup", "doctor", "install_step", "INSTALL_STEPS", "__version__"]
