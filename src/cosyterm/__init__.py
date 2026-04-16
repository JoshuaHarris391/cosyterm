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

from cosyterm.core import INSTALL_STEPS, doctor, install_step, setup

# Note: restore functionality lives in cosyterm.restore — import that module
# directly rather than re-exporting, so `cosyterm.restore` unambiguously
# resolves to the submodule.

__all__ = [
    "setup", "doctor", "install_step", "INSTALL_STEPS",
    "__version__",
]
