#!/usr/bin/env bash
# One-line installer for maggy (Maggy). Prefer Homebrew if you have it:
#
#   brew install agy-pet/tap/maggy && maggy setup
#
# Otherwise:
#
#   curl -fsSL https://agy-pet.github.io/install.sh | bash
#
# Extra args are passed to `maggy setup`, e.g. `| bash -s -- --theme xmas --no-mood`.
#
# Env overrides:
#   MAGGY_DIR   install location   (default: ~/.maggy)
#   MAGGY_BIN_DIR          where to link maggy (default: ~/.local/bin)
#   AGY_SETTINGS           agy settings file  (default: ~/.gemini/antigravity-cli/settings.json)
#   MAGGY_REF              tag or branch to install (default: the release this
#                          installer came from; master when run from the repo)
set -euo pipefail

REPO_URL="https://github.com/agy-pet/maggy.git"
# scripts/release.sh rewrites this default to the release tag in the copy it uploads.
REF="${MAGGY_REF:-master}"
INSTALL_DIR="${MAGGY_DIR:-$HOME/.maggy}"
BIN_DIR="${MAGGY_BIN_DIR:-$HOME/.local/bin}"

say() { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

command -v git >/dev/null 2>&1 || die "git is required"
command -v python3 >/dev/null 2>&1 || die "python3 is required"

# 1. Fetch or update the code
if [ -d "$INSTALL_DIR/.git" ]; then
    say "Updating $INSTALL_DIR to $REF"
    git -C "$INSTALL_DIR" fetch --depth 1 --quiet origin "$REF"
    git -C "$INSTALL_DIR" checkout --quiet --detach FETCH_HEAD
elif [ -e "$INSTALL_DIR" ]; then
    die "$INSTALL_DIR exists and is not a git clone; set MAGGY_DIR to another path"
else
    say "Cloning $REF into $INSTALL_DIR"
    git clone --depth 1 --quiet --branch "$REF" "$REPO_URL" "$INSTALL_DIR"
fi
chmod +x "$INSTALL_DIR/bin/maggy"

# 2. Put `maggy` on PATH
mkdir -p "$BIN_DIR"
ln -sf "$INSTALL_DIR/bin/maggy" "$BIN_DIR/maggy"
say "Linked $BIN_DIR/maggy"
case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *) printf '\033[1;33mnote:\033[0m %s is not on your PATH; add it to use `maggy` directly\n' "$BIN_DIR" ;;
esac

# 3. Shell completions (Homebrew does this for brew installs)
COMP_DIR="$INSTALL_DIR/completions"
FISH_COMP_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/fish/completions"
BASH_COMP_DIR="${BASH_COMPLETION_USER_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion}/completions"
if command -v fish >/dev/null 2>&1; then
    mkdir -p "$FISH_COMP_DIR"
    ln -sf "$COMP_DIR/maggy.fish" "$FISH_COMP_DIR/maggy.fish"
    say "Linked fish completions into $FISH_COMP_DIR"
fi
if command -v bash >/dev/null 2>&1; then
    mkdir -p "$BASH_COMP_DIR"
    ln -sf "$COMP_DIR/maggy.bash" "$BASH_COMP_DIR/maggy"
    say "Linked bash completions into $BASH_COMP_DIR (loaded by bash-completion 2)"
fi
if command -v zsh >/dev/null 2>&1; then
    printf '\033[1;33mnote:\033[0m for zsh completions, add to ~/.zshrc before compinit:  fpath=(%s $fpath)\n' "$COMP_DIR"
fi

# 4. Hook into agy (settings are backed up to settings.json.bak)
MAGGY_BIN="$BIN_DIR/maggy" "$BIN_DIR/maggy" setup "$@"
