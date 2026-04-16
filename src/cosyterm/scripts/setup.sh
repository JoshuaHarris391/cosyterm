#!/usr/bin/env bash
# =============================================================================
# Terminal Setup Installer
# Based on: https://devcenter.upsun.com/posts/my-terminal-setup-mac-linux/
# Author of original guide: Guillaume Moigneu (Upsun)
#
# What this script installs & configures:
#   1. Nerd Font (your choice)     — Monospace font with icons for terminal use
#   2. Ghostty                     — GPU-accelerated terminal emulator
#   3. Fish shell                  — Friendly interactive shell (optional, vs Zsh)
#   4. Starship                    — Cross-shell prompt with git/language context
#   5. eza                         — Modern replacement for 'ls'
#   6. tmux + Catppuccin           — Terminal multiplexer with Mocha theme
#   7. NeoVim + LazyVim            — Terminal-based editor with IDE features
#
# Safety features:
#   - Backs up all existing config files before overwriting
#   - Prompts for confirmation before every critical/destructive step
#   - Detects OS (macOS vs Linux) and adapts install commands
#   - Falls back gracefully if a tool can't be installed
#   - Never runs 'sudo' without telling you first
#   - Logs everything to ~/terminal-setup.log
#
# Usage:
#   chmod +x terminal-setup.sh
#   ./terminal-setup.sh
#
# To run a specific section only, set the environment variable:
#   SKIP_TO=starship ./terminal-setup.sh
# =============================================================================

set -euo pipefail

# =============================================================================
# CONFIGURATION — edit these if you want different defaults
# =============================================================================
CATPPUCCIN_MOCHA_URL="https://raw.githubusercontent.com/catppuccin/ghostty/main/themes/catppuccin-mocha.conf"

# Font selection — these will be set interactively in install_nerd_font()
FONT_NAME=""
FONT_URL=""
FONT_BREW_CASK=""
FONT_FAMILY=""   # the exact font-family string for terminal configs
FONT_FILE_GLOB="" # glob pattern to check if already installed on Linux

# ── Font lookup ──
# Uses a function instead of associative arrays for bash 3.2 (macOS default) compatibility.
# Each font has: display text, Homebrew cask name, font-family string, file glob.
#
# Nerd Fonts releases: https://github.com/ryanoasis/nerd-fonts/releases
DEFAULT_FONTS=(
    "JetBrainsMono"
    "CommitMono"
    "CascadiaCode"
    "Hack"
    "FiraCode"
)

FUN_FONTS=(
    "Monofur"
    "OpenDyslexic"
    "Agave"
    "0xProto"
    "Hasklig"
)

FONT_OPTIONS=("${FUN_FONTS[@]}" "${DEFAULT_FONTS[@]}")

# Usage: font_lookup <key> <field>
# Fields: display, cask, family, glob
font_lookup() {
    local key="$1"
    local field="$2"
    case "${key}:${field}" in
        JetBrainsMono:display)  echo "JetBrains Mono    — designed for developers, excellent readability" ;;
        JetBrainsMono:cask)     echo "font-jetbrains-mono-nerd-font" ;;
        JetBrainsMono:family)   echo "JetBrainsMono Nerd Font Mono" ;;
        JetBrainsMono:glob)     echo "*JetBrainsMono*" ;;

        CommitMono:display)     echo "Commit Mono       — clean, neutral, open-source by Eigil Nikolajsen" ;;
        CommitMono:cask)        echo "font-commit-mono-nerd-font" ;;
        CommitMono:family)      echo "CommitMono Nerd Font Mono" ;;
        CommitMono:glob)        echo "*CommitMono*" ;;

        CascadiaCode:display)   echo "Cascadia Code     — Microsoft's terminal font, ligature support" ;;
        CascadiaCode:cask)      echo "font-caskaydia-cove-nerd-font" ;;
        CascadiaCode:family)    echo "CaskaydiaCove Nerd Font Mono" ;;
        CascadiaCode:glob)      echo "*CaskaydiaCove*" ;;

        Hack:display)           echo "Hack              — optimised for source code, no-nonsense design" ;;
        Hack:cask)              echo "font-hack-nerd-font" ;;
        Hack:family)            echo "Hack Nerd Font Mono" ;;
        Hack:glob)              echo "*Hack*" ;;

        FiraCode:display)       echo "Fira Code         — clean, modern, with programming ligatures" ;;
        FiraCode:cask)          echo "font-fira-code-nerd-font" ;;
        FiraCode:family)        echo "FiraCode Nerd Font Mono" ;;
        FiraCode:glob)          echo "*FiraCode*" ;;

        OpenDyslexic:display)   echo "OpenDyslexic Mono — designed to improve readability for dyslexic readers" ;;
        OpenDyslexic:cask)      echo "font-opendyslexic-nerd-font" ;;
        OpenDyslexic:family)    echo "OpenDyslexicM Nerd Font Mono" ;;
        OpenDyslexic:glob)      echo "*OpenDyslexic*" ;;

        Monofur:display)        echo "Monofur           — playful, rounded, hand-drawn character" ;;
        Monofur:cask)           echo "font-monofur-nerd-font" ;;
        Monofur:family)         echo "Monofur Nerd Font Mono" ;;
        Monofur:glob)           echo "*Monofur*" ;;

        Agave:display)          echo "Agave             — small, compact, minimal with a retro feel" ;;
        Agave:cask)             echo "font-agave-nerd-font" ;;
        Agave:family)           echo "Agave Nerd Font Mono" ;;
        Agave:glob)             echo "*Agave*" ;;

        0xProto:display)        echo "0xProto           — coding font focused on character distinction" ;;
        0xProto:cask)           echo "font-0xproto-nerd-font" ;;
        0xProto:family)         echo "0xProto Nerd Font Mono" ;;
        0xProto:glob)           echo "*0xProto*" ;;

        Hasklig:display)        echo "Hasklig           — Source Code Pro with ligatures (Hasklug in Nerd Fonts)" ;;
        Hasklig:cask)           echo "font-hasklug-nerd-font" ;;
        Hasklig:family)         echo "Hasklug Nerd Font Mono" ;;
        Hasklig:glob)           echo "*Hasklug*" ;;

        *) echo "" ;;
    esac
}
LAZYVIM_REPO="https://github.com/LazyVim/starter"
BACKUP_DIR="${COSYTERM_BACKUP_DIR:-$HOME/.terminal-setup-backups/$(date +%Y%m%d_%H%M%S)}"
MANIFEST_FILE="$BACKUP_DIR/manifest.tsv"
LOG_FILE="${COSYTERM_LOG_FILE:-$HOME/terminal-setup.log}"
SHELL_CHOICE=""  # will be set interactively: "fish" or "zsh"

# Dev-mode / non-interactive overrides (for tests and scripted installs):
#   COSYTERM_YES=1            auto-confirm every [y/N] prompt
#   COSYTERM_DEV=1            dev sandbox — still writes to $HOME, but tests
#                             pre-populate HOME and shim PATH so no real network
#                             / real sudo is hit. Used by the test harness.
#   COSYTERM_BACKUP_DIR=...   override the backup dir (useful for tests)
#   COSYTERM_LOG_FILE=...     override the log file path
#   COSYTERM_NVIM_CHOICE=...  pre-answer the nvim pre-flight menu:
#                             skip | sidebyside | replace

# =============================================================================
# LOGGING & DISPLAY HELPERS
# =============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

log() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${CYAN}[$timestamp]${NC} $1"
    echo "[$timestamp] $(echo "$1" | sed 's/\x1b\[[0-9;]*m//g')" >> "$LOG_FILE"
}

log_success() {
    log "${GREEN}✓${NC} $1"
}

log_warn() {
    log "${YELLOW}⚠${NC} $1"
}

log_error() {
    log "${RED}✗${NC} $1"
}

log_section() {
    echo ""
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${BLUE}  $1${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "========== $1 ==========" >> "$LOG_FILE"
}

# Prompt the user for yes/no confirmation.
# Returns 0 (true) if user says yes, 1 (false) if no.
# COSYTERM_YES=1 auto-answers yes (for scripted installs and tests).
# Usage: if confirm "Do the thing?"; then ... fi
confirm() {
    local prompt="$1"
    local response
    if [[ "${COSYTERM_YES:-}" == "1" ]]; then
        echo ""
        echo -e "${BOLD}${YELLOW}▶ $prompt${NC}  ${GREEN}[auto-yes]${NC}"
        return 0
    fi
    echo ""
    echo -e "${BOLD}${YELLOW}▶ $prompt${NC}"
    read -rp "  [y/N]: " response
    case "$response" in
        [yY]|[yY][eE][sS]) return 0 ;;
        *) return 1 ;;
    esac
}

# Prompt the user to type an exact word — used as an extra gate before
# destructive operations (replacing an existing nvim config, etc.).
# Returns 0 if user types the expected word exactly, 1 otherwise.
# Usage: if confirm_typed "This will delete X. Type 'replace' to continue" replace; then ...
confirm_typed() {
    local prompt="$1"
    local expected="$2"
    local response
    if [[ "${COSYTERM_YES:-}" == "1" ]]; then
        echo ""
        echo -e "${BOLD}${RED}▶ $prompt${NC}  ${GREEN}[auto-yes]${NC}"
        return 0
    fi
    echo ""
    echo -e "${BOLD}${RED}▶ $prompt${NC}"
    read -rp "  type '$expected' to confirm: " response
    [[ "$response" == "$expected" ]]
}

# Append an entry to the run's manifest.tsv. Each entry records a reversible
# operation: a move (mv source -> backup) or a copy (cp source -> backup).
# The restore command reads this file and does the inverse moves.
# Format (tab-separated):  step<TAB>action<TAB>source<TAB>backup<TAB>timestamp
manifest_append() {
    local step="$1"
    local action="$2"
    local source="$3"
    local backup="$4"
    mkdir -p "$BACKUP_DIR"
    if [[ ! -f "$MANIFEST_FILE" ]]; then
        printf "# cosyterm manifest v1\n# step\taction\tsource\tbackup\ttimestamp\n" > "$MANIFEST_FILE"
    fi
    local ts
    ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    printf "%s\t%s\t%s\t%s\t%s\n" "$step" "$action" "$source" "$backup" "$ts" >> "$MANIFEST_FILE"
}

# Back up a file or directory by COPY. Skips if source doesn't exist.
# Use this for configs you want to keep in place (e.g. ~/.zshrc appended to).
backup_if_exists() {
    local src="$1"
    local step="${2:-unknown}"
    if [[ -e "$src" ]]; then
        mkdir -p "$BACKUP_DIR"
        local dest="$BACKUP_DIR/$(basename "$src")"
        cp -r "$src" "$dest"
        manifest_append "$step" "copy" "$src" "$dest"
        log_warn "Backed up ${BOLD}$src${NC} → ${BOLD}$dest${NC}"
    fi
}

# Back up a file or directory by MOVE. Safer and atomic — the original path
# is empty after this call, and restore is a single reverse-mv. Use this when
# the source will be recreated from scratch (e.g. nvim config replaced by
# LazyVim, where we want the old tree out of the way entirely).
backup_move() {
    local src="$1"
    local step="${2:-unknown}"
    if [[ -e "$src" ]]; then
        mkdir -p "$BACKUP_DIR"
        # Flatten the path into a safe filename so multiple dirs with the
        # same basename (e.g. .local/share/nvim and .local/state/nvim both
        # → "nvim") don't collide in the backup dir.
        local safe_name
        safe_name=$(echo "${src#$HOME/}" | tr '/' '_')
        local dest="$BACKUP_DIR/$safe_name"
        mv "$src" "$dest"
        manifest_append "$step" "move" "$src" "$dest"
        log_warn "Moved ${BOLD}$src${NC} → ${BOLD}$dest${NC} (reversible via 'cosyterm restore')"
    fi
}

# Check if a command exists on PATH.
has_cmd() {
    command -v "$1" &>/dev/null
}

# =============================================================================
# OS DETECTION
# =============================================================================
detect_os() {
    case "$(uname -s)" in
        Darwin*) OS="macos" ;;
        Linux*)  OS="linux" ;;
        *)       OS="unknown" ;;
    esac

    if [[ "$OS" == "linux" ]]; then
        if has_cmd apt; then
            PKG_MANAGER="apt"
        elif has_cmd dnf; then
            PKG_MANAGER="dnf"
        elif has_cmd pacman; then
            PKG_MANAGER="pacman"
        else
            PKG_MANAGER="unknown"
        fi
    elif [[ "$OS" == "macos" ]]; then
        PKG_MANAGER="brew"
    fi
}

# Install a package using the detected package manager.
# Usage: pkg_install <package_name> [optional_brew_name]
pkg_install() {
    local pkg="$1"
    local brew_pkg="${2:-$1}"

    case "$PKG_MANAGER" in
        brew)
            brew install "$brew_pkg"
            ;;
        apt)
            sudo apt-get install -y "$pkg"
            ;;
        dnf)
            sudo dnf install -y "$pkg"
            ;;
        pacman)
            sudo pacman -S --noconfirm "$pkg"
            ;;
        *)
            log_error "Unsupported package manager. Please install ${BOLD}$pkg${NC} manually."
            return 1
            ;;
    esac
}

# =============================================================================
# PRE-FLIGHT CHECKS
# =============================================================================
preflight() {
    log_section "Pre-flight checks"

    detect_os
    log "Detected OS: ${BOLD}$OS${NC}"
    log "Package manager: ${BOLD}$PKG_MANAGER${NC}"
    log "Backup directory: ${BOLD}$BACKUP_DIR${NC}"
    log "Log file: ${BOLD}$LOG_FILE${NC}"

    if [[ "$OS" == "unknown" ]]; then
        log_error "Unsupported operating system. This script supports macOS and Linux."
        exit 1
    fi

    # Ensure Homebrew is available on macOS
    if [[ "$OS" == "macos" ]] && ! has_cmd brew; then
        log_error "Homebrew is not installed. It's required for macOS package management."
        echo "  Install it from: https://brew.sh"
        echo "  Run: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi

    # Ensure git is available (needed for LazyVim, etc.)
    if ! has_cmd git; then
        log_error "git is not installed. Please install git first."
        exit 1
    fi

    # Ensure curl or wget is available
    if ! has_cmd curl && ! has_cmd wget; then
        log_error "Neither curl nor wget found. Please install one of them."
        exit 1
    fi

    # Ensure unzip is available (needed for font install)
    if ! has_cmd unzip; then
        log_warn "unzip not found. Will attempt to install it."
        pkg_install unzip || true
    fi

    log_success "Pre-flight checks passed"
}

# =============================================================================
# STEP 1: NERD FONT (choose your font)
# =============================================================================
install_nerd_font() {
    log_section "Step 1/7: Nerd Font"

    log "Nerd Fonts add icons and glyphs to monospace fonts. They're required"
    log "for Starship prompt icons and eza file icons to render properly."
    echo ""

    # ── Font selection menu ──
    echo -e "${BOLD}${YELLOW}▶ Which Nerd Font would you like to install?${NC}"
    echo ""
    local i=1

    echo -e "  ${BOLD}${CYAN}Fun fonts${NC}"
    for key in "${FUN_FONTS[@]}"; do
        echo -e "  ${BOLD}$i)${NC} $(font_lookup "$key" display)"
        ((i++))
    done

    echo ""
    echo -e "  ${BOLD}${CYAN}Developer fonts${NC}"
    for key in "${DEFAULT_FONTS[@]}"; do
        echo -e "  ${BOLD}$i)${NC} $(font_lookup "$key" display)"
        ((i++))
    done

    echo ""
    echo -e "  ${BOLD}$i)${NC} Skip — I'll install a Nerd Font myself"
    echo ""
    read -rp "  Choice [1-$i]: " font_choice

    # Validate choice
    if [[ "$font_choice" =~ ^[0-9]+$ ]] && (( font_choice >= 1 && font_choice <= ${#FONT_OPTIONS[@]} )); then
        local idx=$((font_choice - 1))
        local chosen="${FONT_OPTIONS[$idx]}"

        FONT_NAME="$chosen"
        FONT_URL="https://github.com/ryanoasis/nerd-fonts/releases/latest/download/${chosen}.zip"
        FONT_BREW_CASK="$(font_lookup "$chosen" cask)"
        FONT_FAMILY="$(font_lookup "$chosen" family)"
        FONT_FILE_GLOB="$(font_lookup "$chosen" glob)"

        local display_name
        display_name="$(font_lookup "$chosen" display)"
        log "Selected: ${BOLD}${display_name%%  —*}${NC}"
    else
        FONT_NAME=""
        log_warn "Skipped font installation. Icons may not render correctly without a Nerd Font."
        return 0
    fi

    # ── macOS install via Homebrew cask ──
    local font_installed=false
    if [[ "$OS" == "macos" ]]; then
        if brew list --cask "$FONT_BREW_CASK" &>/dev/null 2>&1; then
            log_success "$FONT_NAME Nerd Font is already installed via Homebrew"
            font_installed=true
        elif confirm "Install $FONT_NAME Nerd Font via Homebrew cask?"; then
            log "Installing $FONT_NAME Nerd Font..."
            brew install --cask "$FONT_BREW_CASK"
            log_success "Font installed"
            font_installed=true
        else
            log_warn "Skipped font installation."
        fi

    # ── Linux install via direct download ──
    else
        local font_dir="$HOME/.local/share/fonts"
        if ls "$font_dir"/$FONT_FILE_GLOB &>/dev/null 2>&1; then
            log_success "$FONT_NAME Nerd Font is already installed in $font_dir"
            font_installed=true
        elif confirm "Download and install $FONT_NAME Nerd Font to $font_dir?"; then
            local tmp_dir
            tmp_dir=$(mktemp -d)
            log "Downloading $FONT_NAME Nerd Font..."

            if curl -fsSL "$FONT_URL" -o "$tmp_dir/font.zip"; then
                mkdir -p "$font_dir"
                unzip -qo "$tmp_dir/font.zip" -d "$font_dir"
                rm -rf "$tmp_dir"

                # Rebuild font cache
                if has_cmd fc-cache; then
                    fc-cache -fv "$font_dir" >> "$LOG_FILE" 2>&1
                fi

                log_success "Font installed to $font_dir"
                font_installed=true
            else
                log_error "Failed to download font. Check your internet connection."
                rm -rf "$tmp_dir"
            fi
        else
            log_warn "Skipped font installation."
        fi
    fi

    # Update Ghostty config if it exists
    if $font_installed && [[ -n "$FONT_FAMILY" ]]; then
        local ghostty_config="$HOME/.config/ghostty/config"
        if [[ -f "$ghostty_config" ]]; then
            if grep -q "^font-family" "$ghostty_config"; then
                backup_if_exists "$ghostty_config"
                sed -i.bak "s/^font-family = .*/font-family = ${FONT_FAMILY}/" "$ghostty_config"
                rm -f "$ghostty_config.bak"
                log_success "Updated Ghostty config to use ${BOLD}$FONT_FAMILY${NC}"
            fi
        fi
    fi
}

# =============================================================================
# STEP 2: GHOSTTY
# =============================================================================
install_ghostty() {
    log_section "Step 2/7: Ghostty terminal emulator"

    log "Ghostty is a GPU-accelerated terminal emulator by Mitchell Hashimoto."
    log "It's fast, cross-platform, and has a simple config file."

    if has_cmd ghostty; then
        log_success "Ghostty is already installed"
    else
        if confirm "Install Ghostty? (If unavailable via package manager, you may need to build from source or download from ghostty.org)"; then
            local installed=false

            if [[ "$OS" == "macos" ]]; then
                if brew install --cask ghostty 2>>"$LOG_FILE"; then
                    installed=true
                fi
            elif [[ "$PKG_MANAGER" == "apt" ]]; then
                # Ghostty may not be in default repos — try, but don't fail hard
                if sudo apt-get install -y ghostty 2>>"$LOG_FILE"; then
                    installed=true
                fi
            elif [[ "$PKG_MANAGER" == "pacman" ]]; then
                if sudo pacman -S --noconfirm ghostty 2>>"$LOG_FILE"; then
                    installed=true
                fi
            fi

            if $installed; then
                log_success "Ghostty installed"
            else
                log_warn "Couldn't install Ghostty via package manager."
                log "  → Download manually from: https://ghostty.org/download"
                log "  → Or build from source: https://github.com/ghostty-org/ghostty"
            fi
        else
            log_warn "Skipped Ghostty installation."
        fi
    fi

    # Configure Ghostty (regardless of whether we just installed it)
    local ghostty_config_dir="$HOME/.config/ghostty"
    local ghostty_config="$ghostty_config_dir/config"
    local ghostty_themes_dir="$ghostty_config_dir/themes"

    if confirm "Write Ghostty config with Catppuccin Mocha theme and your chosen font?"; then
        backup_if_exists "$ghostty_config"

        mkdir -p "$ghostty_config_dir"
        mkdir -p "$ghostty_themes_dir"

        # Download Catppuccin Mocha theme
        log "Downloading Catppuccin Mocha theme for Ghostty..."
        if curl -fsSL "$CATPPUCCIN_MOCHA_URL" -o "$ghostty_themes_dir/catppuccin-mocha.conf" 2>>"$LOG_FILE"; then
            log_success "Theme downloaded"
        else
            log_warn "Could not download theme. You can add it manually later."
        fi

        # Determine font family for Ghostty config
        local ghostty_font="${FONT_FAMILY:-JetBrainsMono Nerd Font Mono}"

        cat > "$ghostty_config" << GHOSTTY_EOF
# Ghostty configuration
# Docs: https://ghostty.org/docs/config

theme = catppuccin-mocha.conf
font-size = 19
font-family = ${ghostty_font}
mouse-hide-while-typing = true
window-decoration = true
macos-option-as-alt = true
window-padding-x = 12
window-padding-y = 12
window-padding-balance = true
GHOSTTY_EOF

        log_success "Ghostty config written to $ghostty_config"
    fi
}

# =============================================================================
# STEP 3: SHELL (Fish or Zsh)
# =============================================================================
install_shell() {
    log_section "Step 3/7: Shell setup"

    log "The guide recommends Fish shell for its out-of-the-box experience"
    log "(autosuggestions, syntax highlighting, tab completions)."
    log "Zsh is the macOS default and a solid POSIX-compatible choice."
    echo ""
    log "${BOLD}Key trade-off:${NC} Fish is NOT POSIX-compatible. Bash one-liners,"
    log "venv activate scripts, and most online snippets won't work directly in Fish."

    echo ""
    echo -e "${BOLD}${YELLOW}▶ Which shell would you like to set up?${NC}"
    echo "  1) Fish  — modern, user-friendly, non-POSIX (recommended)"
    echo "  2) Zsh   — powerful, POSIX-compatible, widely supported"
    echo "  3) Skip  — keep your current shell"
    read -rp "  Choice [1/2/3] (default: 1): " shell_choice

    case "$shell_choice" in
        2) SHELL_CHOICE="zsh" ;;
        3)
            SHELL_CHOICE="skip"
            log_warn "Skipped shell installation. Starship will still work with your current shell."
            return 0
            ;;
        *) SHELL_CHOICE="fish" ;;
    esac

    # Install the chosen shell if not present
    if ! has_cmd "$SHELL_CHOICE"; then
        log "Installing $SHELL_CHOICE..."
        pkg_install "$SHELL_CHOICE" || {
            log_error "Failed to install $SHELL_CHOICE"
            SHELL_CHOICE="skip"
            return 1
        }
        log_success "$SHELL_CHOICE installed"
    else
        log_success "$SHELL_CHOICE is already installed"
    fi

    # Ask about default shell — this is the risky bit
    echo ""
    log "${YELLOW}Changing your default shell requires logging out and back in.${NC}"
    log "If something goes wrong, you can always recover by running:"
    log "  ${BOLD}chsh -s \$(which bash)${NC}   (from any TTY or recovery mode)"
    echo ""

    # The guide mentions an alternative: launch fish from within Ghostty
    # instead of changing the system default. Offer both options.
    if [[ "$SHELL_CHOICE" == "fish" ]]; then
        echo -e "${BOLD}${YELLOW}▶ How would you like to use Fish?${NC}"
        echo "  1) Set as default shell  (chsh — affects all terminals)"
        echo "  2) Launch from Ghostty only  (safer — Ghostty opens fish, everything else stays as-is)"
        echo "  3) Don't change anything  (just install it, I'll configure later)"
        read -rp "  Choice [1/2/3]: " fish_method

        case "$fish_method" in
            1)
                if confirm "Run 'chsh -s $(which fish)' to set Fish as your default shell?"; then
                    local fish_path
                    fish_path=$(which fish)

                    # Ensure fish is in /etc/shells (required for chsh)
                    if ! grep -qx "$fish_path" /etc/shells 2>/dev/null; then
                        log "Adding $fish_path to /etc/shells (requires sudo)..."
                        echo "$fish_path" | sudo tee -a /etc/shells > /dev/null
                    fi

                    chsh -s "$fish_path"
                    log_success "Default shell changed to Fish. Log out and back in to activate."
                fi
                ;;
            2)
                log "Adding Fish launch to Ghostty config..."
                local ghostty_config="$HOME/.config/ghostty/config"
                if [[ -f "$ghostty_config" ]]; then
                    # Only add if not already present
                    if ! grep -q "command.*fish" "$ghostty_config" 2>/dev/null; then
                        echo "" >> "$ghostty_config"
                        echo "# Launch Fish shell instead of default" >> "$ghostty_config"
                        echo "command = $(which fish)" >> "$ghostty_config"
                        log_success "Ghostty will now launch Fish. Other terminals keep your current shell."
                    else
                        log_success "Ghostty is already configured to launch Fish."
                    fi
                else
                    log_warn "Ghostty config not found. Set up Ghostty first, then re-run this section."
                fi
                ;;
            *)
                log_warn "No shell change made. You can run 'fish' anytime to try it."
                ;;
        esac
    elif [[ "$SHELL_CHOICE" == "zsh" ]]; then
        if confirm "Set Zsh as your default shell? (chsh -s $(which zsh))"; then
            chsh -s "$(which zsh)"
            log_success "Default shell changed to Zsh."
        fi
    fi

    # ── Migrate PATH exports from Bash/Zsh to Fish (only for Fish users) ──
    if [[ "$SHELL_CHOICE" == "fish" ]]; then
        _migrate_path_to_fish
    fi
}

# =============================================================================
# PATH MIGRATION — scan Bash/Zsh configs and translate to Fish syntax
# =============================================================================
_migrate_path_to_fish() {
    log_section "PATH migration (Bash/Zsh → Fish)"

    log "Fish doesn't read .zshrc, .bashrc, or .bash_profile. Any PATH exports"
    log "in those files (e.g. from Homebrew, nvm, pyenv, conda, cargo) won't"
    log "carry over automatically. Let's scan for them."
    echo ""

    # Collect all the shell config files that might contain PATH exports
    local -a source_files=()
    for f in "$HOME/.zshrc" "$HOME/.zprofile" "$HOME/.zshenv" \
             "$HOME/.bashrc" "$HOME/.bash_profile" "$HOME/.profile"; do
        [[ -f "$f" ]] && source_files+=("$f")
    done

    if [[ ${#source_files[@]} -eq 0 ]]; then
        log_warn "No Bash/Zsh config files found to scan."
        return 0
    fi

    # Extract PATH-related lines from all config files
    local -a path_lines=()
    local -a path_sources=()
    for f in "${source_files[@]}"; do
        while IFS= read -r line; do
            # Skip comments and empty lines
            [[ "$line" =~ ^[[:space:]]*# ]] && continue
            [[ -z "$line" ]] && continue
            path_lines+=("$line")
            path_sources+=("$(basename "$f")")
        done < <(grep -iE '(export.*PATH|PATH=|path.*=)' "$f" 2>/dev/null)
    done

    if [[ ${#path_lines[@]} -eq 0 ]]; then
        log_success "No PATH exports found in your Bash/Zsh configs. Nothing to migrate."
        return 0
    fi

    # Display what we found
    log "Found ${BOLD}${#path_lines[@]}${NC} PATH-related line(s) across your shell configs:"
    echo ""
    for i in "${!path_lines[@]}"; do
        echo -e "  ${CYAN}[${path_sources[$i]}]${NC} ${path_lines[$i]}"
    done
    echo ""

    if ! confirm "Translate these PATH exports to Fish syntax and add them to config.fish?"; then
        log_warn "Skipped PATH migration. You can add them manually later."
        log "  Fish syntax:  set -gx PATH /your/path \$PATH"
        return 0
    fi

    local fish_config="$HOME/.config/fish/config.fish"
    mkdir -p "$HOME/.config/fish"

    # Check if we've already added a migration block
    if grep -q "# PATH migration from Bash/Zsh" "$fish_config" 2>/dev/null; then
        log_warn "PATH migration block already exists in config.fish."
        if ! confirm "Replace existing PATH migration block with a fresh scan?"; then
            return 0
        fi
        # Remove the old block (between the markers)
        sed -i.bak '/# PATH migration from Bash\/Zsh — START/,/# PATH migration from Bash\/Zsh — END/d' "$fish_config"
    fi

    # Build the Fish PATH block
    local fish_block=""
    fish_block+=$'\n'"# PATH migration from Bash/Zsh — START"$'\n'
    fish_block+="# Auto-generated by terminal-setup.sh on $(date '+%Y-%m-%d %H:%M')"$'\n'
    fish_block+="# Original sources: ${source_files[*]}"$'\n'

    local added=0
    local skipped=0

    for line in "${path_lines[@]}"; do
        # Try to extract the path being added from common patterns:
        #   export PATH="/foo/bar:$PATH"
        #   export PATH="$PATH:/foo/bar"
        #   export PATH=$HOME/.local/bin:$PATH
        #   PATH="/foo/bar:${PATH}"
        #   eval "$(brew shellenv)"          — special case
        #   source "$HOME/.cargo/env"        — special case
        #   eval "$(pyenv init -)"           — special case

        local fish_line=""
        local original_comment="# from: $line"

        # ── Special case: brew shellenv ──
        if echo "$line" | grep -qE 'eval.*brew shellenv'; then
            # Homebrew on Apple Silicon
            if [[ -x /opt/homebrew/bin/brew ]]; then
                fish_line="/opt/homebrew/bin/brew shellenv | source"
            elif [[ -x /usr/local/bin/brew ]]; then
                fish_line="/usr/local/bin/brew shellenv | source"
            fi

        # ── Special case: cargo/rustup env ──
        elif echo "$line" | grep -qE 'source.*(\.cargo/env|cargo)'; then
            fish_line="set -gx PATH \$HOME/.cargo/bin \$PATH"

        # ── Special case: pyenv init ──
        elif echo "$line" | grep -qE 'eval.*(pyenv init|pyenv virtualenv)'; then
            fish_line="status is-login; and pyenv init --path | source"

        # ── Special case: nvm ──
        elif echo "$line" | grep -qiE '(NVM_DIR|nvm\.sh)'; then
            fish_line="# nvm: Fish users should use 'nvm.fish' or 'bass' plugin instead"
            fish_line+=$'\n'"# See: https://github.com/jorgebucaran/nvm.fish"

        # ── Special case: conda init ──
        elif echo "$line" | grep -qiE 'conda'; then
            fish_line="# conda: Run 'conda init fish' to set up conda for Fish"

        # ── General pattern: extract paths from export PATH="..." ──
        else
            # Strip: export, quotes, $PATH, ${PATH}, leading/trailing colons
            local extracted
            extracted=$(echo "$line" \
                | sed -E 's/^[[:space:]]*(export[[:space:]]+)?//' \
                | sed -E 's/^PATH[[:space:]]*=[[:space:]]*//' \
                | sed -E 's/["'\'']//g' \
                | sed -E 's/\$\{?PATH\}?//g' \
                | sed -E 's/^://;s/:$//' \
                | sed -E 's/:/ /g')

            if [[ -n "$extracted" && "$extracted" != " " ]]; then
                # Each space-separated token is a path to add
                for p in $extracted; do
                    # Expand $HOME references for the comment, keep variable for the actual line
                    local fish_path="$p"
                    # Convert $HOME to Fish-compatible form (Fish understands $HOME fine)
                    if [[ -n "$fish_path" && "$fish_path" != "\$PATH" ]]; then
                        fish_line+="set -gx PATH ${fish_path} \$PATH"$'\n'
                    fi
                done
                # Trim trailing newline
                fish_line="${fish_line%$'\n'}"
            fi
        fi

        if [[ -n "$fish_line" ]]; then
            fish_block+="$original_comment"$'\n'
            fish_block+="$fish_line"$'\n'
            ((added++))
        else
            fish_block+="# SKIPPED (couldn't parse): $line"$'\n'
            ((skipped++))
        fi
    done

    fish_block+="# PATH migration from Bash/Zsh — END"$'\n'

    # Append to fish config
    echo "$fish_block" >> "$fish_config"

    log_success "Added $added PATH export(s) to config.fish"
    if (( skipped > 0 )); then
        log_warn "Skipped $skipped line(s) that couldn't be auto-translated."
        log "  Check config.fish for lines marked SKIPPED and translate manually."
    fi

    echo ""
    log "Review the additions with: ${BOLD}cat ~/.config/fish/config.fish${NC}"
    log "You can edit or remove any lines between the START/END markers."
}

# =============================================================================
# STEP 4: STARSHIP PROMPT
# =============================================================================
install_starship() {
    log_section "Step 4/7: Starship prompt"

    log "Starship replaces your default shell prompt with a context-aware one."
    log "It shows git branch, language versions, cloud context, and more."
    log "Written in Rust — very fast. Works with any shell."

    if has_cmd starship; then
        log_success "Starship is already installed"
    else
        if confirm "Install Starship?"; then
            if [[ "$OS" == "macos" ]]; then
                brew install starship
            else
                # The official installer script — we show the user what's happening
                log "Installing via the official Starship installer script..."
                log "  Source: https://starship.rs/install.sh"

                if curl -sS https://starship.rs/install.sh -o /tmp/starship-install.sh 2>>"$LOG_FILE"; then
                    log "Downloaded installer to /tmp/starship-install.sh"
                    if confirm "Run the Starship installer? (You can inspect /tmp/starship-install.sh first)"; then
                        sh /tmp/starship-install.sh -y
                        rm -f /tmp/starship-install.sh
                    else
                        log_warn "Skipped. The installer is saved at /tmp/starship-install.sh if you want to inspect and run it."
                        return 0
                    fi
                else
                    log_error "Failed to download Starship installer."
                    return 1
                fi
            fi

            # ── Verify installation succeeded ──
            if has_cmd starship; then
                log_success "Starship installed and verified on PATH"
            else
                log_error "Starship install appeared to succeed but 'starship' is not on PATH."
                log_error "Shell configs will NOT be updated to avoid the error you'd get on startup."
                log "  Try: brew install starship   (or check the log at $LOG_FILE)"
                return 1
            fi
        else
            log_warn "Skipped Starship installation."
            log_warn "Shell configs will NOT reference Starship since it's not installed."
            return 0
        fi
    fi

    # Write Starship config (the toml is harmless without the binary, so always offer)
    local starship_config="$HOME/.config/starship.toml"

    if confirm "Write Starship config to $starship_config? (Catppuccin Mocha palette, git/node/python/docker context)"; then
        backup_if_exists "$starship_config"
        mkdir -p "$HOME/.config"

        cat > "$starship_config" << 'STARSHIP_EOF'
# Starship prompt configuration
# Docs: https://starship.rs/config/
#
# Layout: [os directory ❯]  ·····  [git_branch git_status | language | package]
# Left side = where you are. Right side = what's happening.
#
# To debug slow modules: env STARSHIP_LOG=trace starship timings

# ── Left prompt: single line, directory + prompt character ──
format = """$os$directory$character"""

# ── Right prompt: git, language versions, package ──
right_format = """$git_branch$git_status$nodejs$python$rust$golang$php$docker_context$package"""

# Blank line between prompts for readability
add_newline = true

# Use Catppuccin Mocha palette
palette = 'catppuccin_mocha'

[os]
disabled = false
style = "fg:text"

[os.symbols]
Macos = "  "
Linux = "  "
Ubuntu = "  "
Debian = "  "
Fedora = "  "
Arch = "  "

[username]
show_always = false
style_user = "fg:text"
format = '[$user]($style) '

[directory]
style = "fg:blue"
truncation_length = 3
truncate_to_repo = true
format = "[$path]($style)[$read_only]($read_only_style) "
read_only = " 🔒"

[git_branch]
style = "fg:green"
format = "[$symbol$branch]($style) "
symbol = " "

[git_status]
style = "fg:red"
format = '([$all_status$ahead_behind]($style) )'

[nodejs]
style = "fg:green"
format = "[$symbol($version)]($style) "
symbol = " "

[python]
style = "fg:yellow"
format = "[$symbol($version)( \\($virtualenv\\))]($style) "
symbol = " "

[rust]
style = "fg:peach"
format = "[$symbol($version)]($style) "
symbol = " "

[golang]
style = "fg:teal"
format = "[$symbol($version)]($style) "
symbol = " "

[php]
style = "fg:mauve"
format = "[$symbol($version)]($style) "
symbol = " "

[docker_context]
style = "fg:blue"
format = "[$symbol$context]($style) "
symbol = " "

[package]
style = "fg:peach"
format = "[$symbol$version]($style) "
symbol = "📦 "

[character]
success_symbol = "[❯](bold green)"
error_symbol = "[❯](bold red)"

# ── Catppuccin Mocha palette ──
[palettes.catppuccin_mocha]
rosewater = "#f5e0dc"
flamingo  = "#f2cdcd"
pink      = "#f5c2e7"
mauve     = "#cba6f7"
red       = "#f38ba8"
maroon    = "#eba0ac"
peach     = "#fab387"
yellow    = "#f9e2af"
green     = "#a6e3a1"
teal      = "#94e2d5"
sky       = "#89dceb"
sapphire  = "#74c7ec"
blue      = "#89b4fa"
lavender  = "#b4befe"
text      = "#cdd6f4"
subtext1  = "#bac2de"
subtext0  = "#a6adc8"
overlay2  = "#9399b2"
overlay1  = "#7f849c"
overlay0  = "#6c7086"
surface2  = "#585b70"
surface1  = "#45475a"
surface0  = "#313244"
base      = "#1e1e2e"
mantle    = "#181825"
crust     = "#11111b"
STARSHIP_EOF

        log_success "Starship config written"
    fi

    # Hook Starship into the chosen shell — but ONLY if the binary exists.
    # Writing 'starship init fish | source' without starship installed
    # causes an error on every shell startup.
    if has_cmd starship; then
        _hook_starship
    else
        log_warn "Starship binary not found — skipping shell hook to avoid startup errors."
        log "  Install Starship first, then re-run this script to add the shell hook."
    fi
}

_hook_starship() {
    if [[ "$SHELL_CHOICE" == "fish" ]]; then
        local fish_config="$HOME/.config/fish/config.fish"
        mkdir -p "$HOME/.config/fish"

        # ── Ensure Homebrew is on Fish's PATH ──
        # This is critical: Fish doesn't read .zprofile/.zshrc, so Homebrew's
        # PATH won't be inherited. Without this, 'starship', 'eza', and any
        # Homebrew-installed tool will show "Unknown command" in Fish.
        if ! grep -q "homebrew\|/opt/homebrew" "$fish_config" 2>/dev/null; then
            local brew_path=""
            if [[ -x /opt/homebrew/bin/brew ]]; then
                brew_path="/opt/homebrew/bin/brew"
            elif [[ -x /usr/local/bin/brew ]]; then
                brew_path="/usr/local/bin/brew"
            fi

            if [[ -n "$brew_path" ]]; then
                echo "" >> "$fish_config"
                echo "# Homebrew PATH (required — Fish doesn't inherit this from Zsh/Bash)" >> "$fish_config"
                echo "$brew_path shellenv | source" >> "$fish_config"
                log_success "Homebrew PATH added to Fish config"
            fi
        else
            log_success "Homebrew PATH already in Fish config"
        fi

        if ! grep -q "starship init fish" "$fish_config" 2>/dev/null; then
            echo "" >> "$fish_config"
            echo "# Starship prompt" >> "$fish_config"
            echo "starship init fish | source" >> "$fish_config"
            log_success "Starship hooked into Fish config"
        else
            log_success "Starship is already hooked into Fish"
        fi
    elif [[ "$SHELL_CHOICE" == "zsh" ]]; then
        local zshrc="$HOME/.zshrc"
        if ! grep -q "starship init zsh" "$zshrc" 2>/dev/null; then
            echo "" >> "$zshrc"
            echo "# Starship prompt" >> "$zshrc"
            echo 'eval "$(starship init zsh)"' >> "$zshrc"
            log_success "Starship hooked into .zshrc"
        else
            log_success "Starship is already hooked into Zsh"
        fi
    else
        log_warn "No shell selected — you'll need to add the Starship init line manually."
        log "  Fish:  Add 'starship init fish | source' to ~/.config/fish/config.fish"
        log "  Zsh:   Add 'eval \"\$(starship init zsh)\"' to ~/.zshrc"
        log "  Bash:  Add 'eval \"\$(starship init bash)\"' to ~/.bashrc"
    fi
}

# =============================================================================
# STEP 5: EZA (modern ls replacement)
# =============================================================================
install_eza() {
    log_section "Step 5/7: eza (modern ls replacement)"

    log "eza replaces 'ls' with colored output, file icons, git status,"
    log "and tree views. Works best with a Nerd Font installed."

    if has_cmd eza; then
        log_success "eza is already installed"
    else
        if confirm "Install eza?"; then
            if [[ "$OS" == "macos" ]]; then
                brew install eza
            elif [[ "$PKG_MANAGER" == "apt" ]]; then
                # eza may need a PPA on older Ubuntu — try direct first
                if ! pkg_install eza 2>>"$LOG_FILE"; then
                    log_warn "eza not in default repos. Trying cargo install as fallback..."
                    if has_cmd cargo; then
                        cargo install eza
                    else
                        log_error "Could not install eza. Install Rust (rustup.rs) and run: cargo install eza"
                        return 1
                    fi
                fi
            else
                pkg_install eza || {
                    log_warn "Falling back to cargo install..."
                    if has_cmd cargo; then
                        cargo install eza
                    else
                        log_error "Could not install eza."
                        return 1
                    fi
                }
            fi

            # ── Verify installation succeeded ──
            if has_cmd eza; then
                log_success "eza installed and verified on PATH"
            else
                log_error "eza install appeared to succeed but 'eza' is not on PATH."
                log_error "Shell aliases will NOT be added to avoid confusing errors."
                return 1
            fi
        else
            log_warn "Skipped eza installation."
            log_warn "Shell aliases will NOT be added since eza is not installed."
            return 0
        fi
    fi

    # Add aliases — only if eza is actually available
    if has_cmd eza; then
        _add_eza_aliases
    else
        log_warn "eza not found on PATH — skipping alias setup."
    fi
}

_add_eza_aliases() {
    if ! confirm "Add eza aliases (ls, lsa, lt, lta) to your shell config?"; then
        return 0
    fi

    if [[ "$SHELL_CHOICE" == "fish" ]]; then
        local fish_config="$HOME/.config/fish/config.fish"
        mkdir -p "$HOME/.config/fish"

        if ! grep -q "alias ls=" "$fish_config" 2>/dev/null; then
            cat >> "$fish_config" << 'FISH_EZA'

# eza aliases (modern ls replacement)
if command -v eza &> /dev/null
    alias ls='eza -lh --group-directories-first --icons=auto'
    alias lsa='ls -a'
    alias lt='eza --tree --level=2 --long --icons --git'
    alias lta='lt -a'
end
FISH_EZA
            log_success "eza aliases added to Fish config"
        else
            log_success "eza aliases already present in Fish config"
        fi

    elif [[ "$SHELL_CHOICE" == "zsh" ]]; then
        local zshrc="$HOME/.zshrc"

        if ! grep -q "alias ls=" "$zshrc" 2>/dev/null; then
            cat >> "$zshrc" << 'ZSH_EZA'

# eza aliases (modern ls replacement)
if command -v eza &> /dev/null; then
    alias ls='eza -lh --group-directories-first --icons=auto'
    alias lsa='ls -a'
    alias lt='eza --tree --level=2 --long --icons --git'
    alias lta='lt -a'
fi
ZSH_EZA
            log_success "eza aliases added to .zshrc"
        else
            log_success "eza aliases already present in .zshrc"
        fi
    else
        log_warn "No shell selected. Add these aliases manually to your shell config:"
        echo "  alias ls='eza -lh --group-directories-first --icons=auto'"
        echo "  alias lsa='ls -a'"
        echo "  alias lt='eza --tree --level=2 --long --icons --git'"
        echo "  alias lta='lt -a'"
    fi
}

# =============================================================================
# STEP 6/7: TMUX + CATPPUCCIN
# =============================================================================
install_tmux() {
    log_section "Step 6/7: tmux + Catppuccin Mocha"

    log "tmux is a terminal multiplexer — it lets you split panes, create"
    log "windows, and persist sessions that survive disconnects."
    log "We'll theme it with Catppuccin Mocha to match everything else."

    # ── Install tmux ──
    if has_cmd tmux; then
        log_success "tmux is already installed"
    else
        if confirm "Install tmux?"; then
            if [[ "$OS" == "macos" ]]; then
                brew install tmux
            else
                pkg_install tmux
            fi

            if has_cmd tmux; then
                log_success "tmux installed and verified on PATH"
            else
                log_error "tmux install failed. Skipping tmux setup."
                return 1
            fi
        else
            log_warn "Skipped tmux installation."
            return 0
        fi
    fi

    # ── Install TPM (Tmux Plugin Manager) ──
    local tpm_dir="$HOME/.tmux/plugins/tpm"

    if [[ -d "$tpm_dir" ]]; then
        log_success "TPM (Tmux Plugin Manager) is already installed"
    else
        if confirm "Install TPM (Tmux Plugin Manager)?"; then
            log "Cloning TPM from GitHub..."
            git clone https://github.com/tmux-plugins/tpm "$tpm_dir" 2>>"$LOG_FILE"
            if [[ -d "$tpm_dir" ]]; then
                log_success "TPM installed"
            else
                log_error "Failed to clone TPM."
                return 1
            fi
        else
            log_warn "Skipped TPM. You can install Catppuccin manually instead."
        fi
    fi

    # ── Install Catppuccin theme (manual clone method — avoids TPM naming conflicts) ──
    local catppuccin_dir="$HOME/.config/tmux/plugins/catppuccin/tmux"

    if [[ -d "$catppuccin_dir" ]]; then
        log_success "Catppuccin tmux theme is already installed"
    else
        if confirm "Install Catppuccin Mocha theme for tmux?"; then
            log "Cloning Catppuccin tmux theme..."
            mkdir -p "$HOME/.config/tmux/plugins/catppuccin"
            git clone -b v2.3.0 https://github.com/catppuccin/tmux.git "$catppuccin_dir" 2>>"$LOG_FILE"
            if [[ -d "$catppuccin_dir" ]]; then
                log_success "Catppuccin tmux theme installed"
            else
                log_error "Failed to clone Catppuccin theme."
            fi
        fi
    fi

    # ── Write tmux config ──
    local tmux_conf="$HOME/.tmux.conf"

    if confirm "Write tmux config with Catppuccin Mocha, mouse support, and status modules?"; then
        backup_if_exists "$tmux_conf"

        # Determine which shell tmux should use
        local tmux_shell=""
        if [[ "$SHELL_CHOICE" == "fish" ]] && has_cmd fish; then
            tmux_shell="$(which fish)"
        elif [[ "$SHELL_CHOICE" == "zsh" ]] && has_cmd zsh; then
            tmux_shell="$(which zsh)"
        fi

        cat > "$tmux_conf" << TMUX_EOF
# ─────────────────────────────────────────────────────────────
# tmux configuration — Catppuccin Mocha
# ─────────────────────────────────────────────────────────────

# ── General settings ──
set -g mouse on
set -g default-terminal "tmux-256color"
set -ag terminal-overrides ",xterm-256color:RGB"
${tmux_shell:+set -g default-shell ${tmux_shell}}
${tmux_shell:+set -g default-command ${tmux_shell}}
set -g base-index 1              # start window numbering at 1
setw -g pane-base-index 1        # start pane numbering at 1
set -g renumber-windows on       # renumber windows when one is closed
set -g history-limit 10000       # generous scrollback
set -g escape-time 0             # no delay after pressing Escape
set -g status-position top       # status bar at top

# ── Keybindings ──
# Easier splits (| and - are more intuitive than % and ")
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"
bind c new-window -c "#{pane_current_path}"

# Reload config with prefix + r
bind r source-file ~/.tmux.conf \; display-message "Config reloaded"

# Vim-style pane navigation
bind h select-pane -L
bind j select-pane -D
bind k select-pane -U
bind l select-pane -R

# ── Catppuccin theme ──
set -g @catppuccin_flavor "mocha"
set -g @catppuccin_window_status_style "rounded"

# Load Catppuccin (manual install method)
run ~/.config/tmux/plugins/catppuccin/tmux/catppuccin.tmux

# ── Status bar modules ──
set -g status-right-length 100
set -g status-left-length 100
set -g status-left ""
set -g status-right "#{E:@catppuccin_status_application}"
set -ag status-right "#{E:@catppuccin_status_session}"
set -ag status-right "#{E:@catppuccin_status_uptime}"

# ── TPM plugins ──
set -g @plugin 'tmux-plugins/tpm'
set -g @plugin 'tmux-plugins/tmux-sensible'

# Initialize TPM (keep this line at the very bottom)
run '~/.tmux/plugins/tpm/tpm'
TMUX_EOF

        log_success "tmux config written to $tmux_conf"
        echo ""
        log "To finish setup, open tmux and press ${BOLD}prefix + I${NC} (capital I)"
        log "to install TPM plugins. Default prefix is ${BOLD}Ctrl+b${NC}."
    fi
}

# =============================================================================
# STEP 7/7: NEOVIM + LAZYVIM
# =============================================================================
#
# Safety model:
#   1. Detect existing nvim config characteristics (lazy-lock.json, git repo,
#      file count, modified-recency) and surface them before any destructive op.
#   2. Offer four routes: skip / side-by-side / replace / quit. Default is
#      'skip' when a substantial non-LazyVim config is present.
#   3. 'replace' requires the user to type 'replace' — not a single keypress.
#   4. Backup uses mv (atomic, reversible) not cp+rm. The full nvim trifecta
#      is preserved: .config/nvim + .local/share/nvim + .local/state/nvim.
#      Cache is excluded (regenerable).
#   5. Every move is logged in the run manifest so 'cosyterm restore' can
#      reverse it exactly.
#
# Pre-answer the menu with COSYTERM_NVIM_CHOICE=skip|sidebyside|replace
# (used by tests and scripted installs).

# Detect and describe the existing nvim config. Prints a short summary line
# and sets globals for the caller:
#   NVIM_HAS_LAZYLOCK    — 1 if lazy-lock.json found (looks like LazyVim)
#   NVIM_IS_GITREPO      — 1 if .config/nvim is a git repo
#   NVIM_FILE_COUNT      — rough file count under .config/nvim
nvim_detect_existing() {
    local nvim_config="$HOME/.config/nvim"
    NVIM_HAS_LAZYLOCK=0
    NVIM_IS_GITREPO=0
    NVIM_FILE_COUNT=0

    [[ -d "$nvim_config" ]] || return 0

    [[ -f "$nvim_config/lazy-lock.json" ]] && NVIM_HAS_LAZYLOCK=1
    [[ -d "$nvim_config/.git" ]] && NVIM_IS_GITREPO=1
    NVIM_FILE_COUNT=$(find "$nvim_config" -type f 2>/dev/null | wc -l | tr -d ' ')

    log "Detected existing NeoVim config at $nvim_config:"
    if (( NVIM_HAS_LAZYLOCK == 1 )); then
        log "  · $NVIM_FILE_COUNT files · LazyVim (lazy-lock.json present)"
    else
        log "  · $NVIM_FILE_COUNT files · NOT LazyVim (no lazy-lock.json)"
    fi
    if (( NVIM_IS_GITREPO == 1 )); then
        log "  · git repo — your own dotfiles, most likely"
    fi
    if [[ -d "$HOME/.local/share/nvim" ]]; then
        local plugin_count
        plugin_count=$(find "$HOME/.local/share/nvim" -maxdepth 3 -type d 2>/dev/null | wc -l | tr -d ' ')
        log "  · plugin state: ~/.local/share/nvim ($plugin_count dirs)"
    fi
}

# Ask the user which route to take when an existing nvim config is found.
# Returns via echo: "skip" | "sidebyside" | "replace" | "quit"
nvim_preflight_choice() {
    # Environment override for tests / scripted installs.
    if [[ -n "${COSYTERM_NVIM_CHOICE:-}" ]]; then
        echo "${COSYTERM_NVIM_CHOICE}"
        return 0
    fi

    # When auto-yes is set without an explicit choice, play safe: skip.
    if [[ "${COSYTERM_YES:-}" == "1" ]]; then
        echo "skip"
        return 0
    fi

    # Menu goes to stderr so it stays visible when this function is called
    # via command substitution (choice=$(nvim_preflight_choice) at the caller).
    echo "" >&2
    echo -e "${BOLD}${YELLOW}How would you like to proceed?${NC}" >&2
    echo "  [s] skip          — leave your nvim config untouched (recommended)" >&2
    echo "  [i] side-by-side  — install LazyVim at ~/.config/nvim-cosy" >&2
    echo "                      (your existing config is NOT touched, no backup taken)" >&2
    echo "                      (try it with: NVIM_APPNAME=nvim-cosy nvim)" >&2
    echo "  [r] replace       — move your config to backup, install LazyVim here" >&2
    echo "                      (requires typing 'replace' to confirm)" >&2
    echo "  [q] quit          — exit without touching anything" >&2
    echo "" >&2
    local response
    read -rp "  choice [s/i/r/q]: " response
    case "$response" in
        s|S|skip) echo "skip" ;;
        i|I|sidebyside|side-by-side) echo "sidebyside" ;;
        r|R|replace) echo "replace" ;;
        q|Q|quit) echo "quit" ;;
        *) echo "skip" ;;
    esac
}

# Install LazyVim at $1 (the target config dir). Uses git clone.
nvim_install_lazyvim() {
    local target="$1"
    git clone "$LAZYVIM_REPO" "$target"
    rm -rf "$target/.git"
}

install_neovim() {
    log_section "Step 7/7: NeoVim + LazyVim"

    log "NeoVim is a modern fork of Vim. LazyVim is a pre-configured setup"
    log "that gives you IDE features out of the box: file explorer, fuzzy find,"
    log "LSP support, git integration, syntax highlighting."

    if has_cmd nvim; then
        log_success "NeoVim is already installed"
    else
        if confirm "Install NeoVim?"; then
            if [[ "$OS" == "macos" ]]; then
                brew install neovim
            else
                pkg_install neovim
            fi
            log_success "NeoVim installed"
        else
            log_warn "Skipped NeoVim installation."
            return 0
        fi
    fi

    local nvim_config="$HOME/.config/nvim"

    # No existing config — simple path, no risk.
    if [[ ! -d "$nvim_config" ]]; then
        if confirm "Install LazyVim (pre-configured NeoVim setup)?"; then
            nvim_install_lazyvim "$nvim_config"
            log_success "LazyVim installed. Run 'nvim' to complete plugin installation."
        else
            log_warn "Skipped LazyVim."
        fi
        return 0
    fi

    # Existing config — pre-flight, route the user.
    nvim_detect_existing
    local choice
    choice=$(nvim_preflight_choice)

    case "$choice" in
        skip)
            log_warn "Kept existing NeoVim config. Skipping LazyVim."
            log "  (re-run with a different choice via 'cosyterm install neovim')"
            ;;
        sidebyside)
            local cosy_config="$HOME/.config/nvim-cosy"
            if [[ -d "$cosy_config" ]]; then
                log_warn "Side-by-side target $cosy_config already exists. Skipping."
                return 0
            fi
            nvim_install_lazyvim "$cosy_config"
            log_success "LazyVim installed side-by-side at $cosy_config"
            log "Your existing $nvim_config is untouched."
            log "Try the new setup with:  ${BOLD}NVIM_APPNAME=nvim-cosy nvim${NC}"
            log "If you like it, move it into place yourself."
            ;;
        replace)
            log_warn "Replace mode will move these paths to the backup:"
            log "  · $nvim_config"
            log "  · $HOME/.local/share/nvim"
            log "  · $HOME/.local/state/nvim"
            log "and delete (regenerable cache):"
            log "  · $HOME/.cache/nvim"
            if ! confirm_typed "This replaces your NeoVim setup. Type 'replace' to continue." replace; then
                log_warn "Confirmation declined. No changes made."
                return 0
            fi
            # Atomic moves into the backup dir. Each recorded in the manifest.
            backup_move "$nvim_config" "neovim"
            backup_move "$HOME/.local/share/nvim" "neovim"
            backup_move "$HOME/.local/state/nvim" "neovim"
            # Cache is regenerable — delete without backup.
            rm -rf "$HOME/.cache/nvim"
            nvim_install_lazyvim "$nvim_config"
            log_success "LazyVim installed. Previous config is in ${BOLD}$BACKUP_DIR${NC}"
            log "To restore: ${BOLD}cosyterm restore --latest --only neovim${NC}"
            ;;
        quit)
            log_warn "Exiting NeoVim step without changes."
            return 0
            ;;
        *)
            log_error "Unknown choice '$choice'. No changes made."
            return 1
            ;;
    esac
}

# =============================================================================
# VERIFICATION — catch config-vs-binary mismatches
# =============================================================================
verify_setup() {
    log_section "Verifying setup"

    log "Checking that configs only reference tools that are actually installed..."
    local issues=0

    # ── Check: shell config references starship, but starship not installed ──
    local shell_config=""
    if [[ "$SHELL_CHOICE" == "fish" ]]; then
        shell_config="$HOME/.config/fish/config.fish"
    elif [[ "$SHELL_CHOICE" == "zsh" ]]; then
        shell_config="$HOME/.zshrc"
    fi

    if [[ -n "$shell_config" && -f "$shell_config" ]]; then
        if grep -q "starship init" "$shell_config" 2>/dev/null && ! has_cmd starship; then
            log_error "MISMATCH: $shell_config references 'starship' but it's not installed!"
            log "  This will cause an error every time your shell starts."
            log "  Fix: brew install starship"
            log "  Or remove the starship line from $shell_config"
            ((issues++))
        fi

        if grep -q "eza" "$shell_config" 2>/dev/null && ! has_cmd eza; then
            log_error "MISMATCH: $shell_config references 'eza' but it's not installed!"
            log "  The aliases won't work. Fix: brew install eza"
            ((issues++))
        fi
    fi

    # ── Check: Ghostty config references fish, but fish not installed ──
    local ghostty_config="$HOME/.config/ghostty/config"
    if [[ -f "$ghostty_config" ]]; then
        if grep -q "command.*fish" "$ghostty_config" 2>/dev/null && ! has_cmd fish; then
            log_error "MISMATCH: Ghostty config launches Fish but Fish is not installed!"
            log "  Ghostty may fail to open or fall back to your default shell."
            log "  Fix: brew install fish"
            log "  Or remove the 'command' line from $ghostty_config"
            ((issues++))
        fi

        # Check the font referenced in Ghostty config is likely installed
        local configured_font
        configured_font=$(grep "^font-family" "$ghostty_config" 2>/dev/null | sed 's/font-family *= *//')
        if [[ -n "$configured_font" ]]; then
            local font_found=false
            if [[ "$OS" == "macos" ]]; then
                # Check macOS font list
                if system_profiler SPFontsDataType 2>/dev/null | grep -qi "$(echo "$configured_font" | cut -d' ' -f1)"; then
                    font_found=true
                fi
                # Also check Homebrew cask list as a fallback
                if ! $font_found && brew list --cask 2>/dev/null | grep -qi "nerd-font"; then
                    font_found=true  # approximate — at least some nerd font is installed
                fi
            else
                # Check Linux font directory
                local font_dir="$HOME/.local/share/fonts"
                if [[ -d "$font_dir" ]] && ls "$font_dir"/*Nerd* &>/dev/null 2>&1; then
                    font_found=true
                fi
            fi
            if ! $font_found; then
                log_warn "Ghostty config references font '$configured_font' but it may not be installed."
                log "  If icons show as boxes or ?, install a Nerd Font and restart Ghostty."
            fi
        fi
    fi

    # ── Check: tmux config references Catppuccin but theme not cloned ──
    if [[ -f "$HOME/.tmux.conf" ]]; then
        if grep -q "catppuccin" "$HOME/.tmux.conf" 2>/dev/null && [[ ! -d "$HOME/.config/tmux/plugins/catppuccin/tmux" ]]; then
            log_error "MISMATCH: .tmux.conf references Catppuccin but theme is not installed!"
            log "  Fix: mkdir -p ~/.config/tmux/plugins/catppuccin"
            log "       git clone -b v2.3.0 https://github.com/catppuccin/tmux.git ~/.config/tmux/plugins/catppuccin/tmux"
            ((issues++))
        fi

        if grep -q "tpm/tpm" "$HOME/.tmux.conf" 2>/dev/null && [[ ! -d "$HOME/.tmux/plugins/tpm" ]]; then
            log_error "MISMATCH: .tmux.conf references TPM but it's not installed!"
            log "  Fix: git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm"
            ((issues++))
        fi
    fi

    # ── Check: LazyVim config exists but nvim not installed ──
    if [[ -d "$HOME/.config/nvim" ]] && ! has_cmd nvim; then
        log_warn "LazyVim config directory exists but NeoVim is not installed."
        ((issues++))
    fi

    # ── Results ──
    if (( issues == 0 )); then
        log_success "All checks passed — configs match installed tools"
    else
        echo ""
        log_error "$issues issue(s) found. Your shell may show errors on startup."
        log "Install the missing tools above, or remove the config lines that reference them."
    fi
}

# =============================================================================
# SUMMARY
# =============================================================================
print_summary() {
    log_section "Setup complete!"

    echo -e "${GREEN}${BOLD}Here's what was done:${NC}"
    echo ""

    has_cmd ghostty   && echo -e "  ${GREEN}✓${NC} Ghostty terminal emulator"     || echo -e "  ${YELLOW}○${NC} Ghostty (not installed)"
    [[ -f "$HOME/.config/ghostty/config" ]] \
                      && echo -e "  ${GREEN}✓${NC} Ghostty config (Catppuccin)"    || echo -e "  ${YELLOW}○${NC} Ghostty config"
    has_cmd fish      && echo -e "  ${GREEN}✓${NC} Fish shell"                     || echo -e "  ${YELLOW}○${NC} Fish shell (not installed)"
    has_cmd zsh       && echo -e "  ${GREEN}✓${NC} Zsh shell"                      || echo -e "  ${YELLOW}○${NC} Zsh shell"
    has_cmd starship  && echo -e "  ${GREEN}✓${NC} Starship prompt"                || echo -e "  ${YELLOW}○${NC} Starship (not installed)"
    [[ -f "$HOME/.config/starship.toml" ]] \
                      && echo -e "  ${GREEN}✓${NC} Starship config (Catppuccin)"   || echo -e "  ${YELLOW}○${NC} Starship config"
    has_cmd eza       && echo -e "  ${GREEN}✓${NC} eza (ls replacement)"           || echo -e "  ${YELLOW}○${NC} eza (not installed)"
    has_cmd tmux      && echo -e "  ${GREEN}✓${NC} tmux"                             || echo -e "  ${YELLOW}○${NC} tmux (not installed)"
    [[ -f "$HOME/.tmux.conf" ]] \
                      && echo -e "  ${GREEN}✓${NC} tmux config (Catppuccin Mocha)"   || echo -e "  ${YELLOW}○${NC} tmux config"
    [[ -d "$HOME/.config/tmux/plugins/catppuccin/tmux" ]] \
                      && echo -e "  ${GREEN}✓${NC} Catppuccin tmux theme"            || echo -e "  ${YELLOW}○${NC} Catppuccin tmux theme"
    has_cmd nvim      && echo -e "  ${GREEN}✓${NC} NeoVim"                           || echo -e "  ${YELLOW}○${NC} NeoVim (not installed)"
    [[ -d "$HOME/.config/nvim" ]] \
                      && echo -e "  ${GREEN}✓${NC} LazyVim config"                 || echo -e "  ${YELLOW}○${NC} LazyVim"

    echo ""

    if [[ -d "$BACKUP_DIR" ]]; then
        echo -e "${YELLOW}Backups saved to:${NC} $BACKUP_DIR"
    fi

    echo -e "${YELLOW}Full log:${NC} $LOG_FILE"
    echo ""
    echo -e "${BOLD}Next steps:${NC}"
    echo "  1. If you changed your default shell, log out and back in"
    echo "  2. Open Ghostty (or your terminal) — you should see the new prompt"
    echo "  3. Run 'nvim' once to let LazyVim install its plugins"
    echo "  4. Run 'tmux' then press Ctrl+b, I (capital I) to install tmux plugins"
    echo "  5. Select '${FONT_FAMILY:-your chosen Nerd Font}' as your terminal font"
    echo "  6. If anything went wrong, restore from $BACKUP_DIR"
    echo ""
}

# =============================================================================
# MAIN
# =============================================================================
main() {
    local step="${1:-}"

    # Single-step mode: run just one install step
    if [[ -n "$step" ]]; then
        mkdir -p "$(dirname "$LOG_FILE")"
        echo "=== cosyterm install $step — $(date) ===" > "$LOG_FILE"
        preflight
        case "$step" in
            font)     install_nerd_font ;;
            ghostty)  install_ghostty ;;
            shell)    install_shell ;;
            starship) install_starship ;;
            eza)      install_eza ;;
            tmux)     install_tmux ;;
            neovim)   install_neovim ;;
            *) echo "Unknown step: $step"
               echo "Available: font, ghostty, shell, starship, eza, tmux, neovim"
               exit 1 ;;
        esac
        if [[ -d "$BACKUP_DIR" ]]; then
            echo ""
            log "Backups saved to: ${BOLD}$BACKUP_DIR${NC}"
        fi
        return
    fi

    # Full setup mode
    echo ""
    echo -e "${BOLD}${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║           Terminal Setup Installer                           ║${NC}"
    echo -e "${BOLD}${CYAN}║   Based on the Upsun Dev Center guide by Guillaume Moigneu   ║${NC}"
    echo -e "${BOLD}${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "This script will walk you through installing and configuring:"
    echo "  • Nerd Font, Ghostty, Fish/Zsh, Starship, eza, tmux, NeoVim, LazyVim"
    echo ""
    echo "Every critical step will ask for your confirmation first."
    echo "All existing configs are backed up before being changed."
    echo ""

    if ! confirm "Ready to begin?"; then
        echo "No worries. Run this script again when you're ready."
        exit 0
    fi

    # Initialise log file
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "=== Terminal Setup Log — $(date) ===" > "$LOG_FILE"

    preflight
    install_nerd_font
    install_ghostty
    install_shell
    install_starship
    install_eza
    install_tmux
    install_neovim
    verify_setup
    print_summary
}

main "$@"
