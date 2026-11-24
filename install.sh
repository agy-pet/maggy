#!/usr/bin/env bash
# One-line installer for maggy (Maggy). Prefer Homebrew if you have it:
#
#   brew install agy-pet/tap/maggy && maggy setup
#
# Otherwise:
#
#   curl -fsSL https://raw.githubusercontent.com/agy-pet/maggy/master/install.sh | bash
#
# Extra args are passed to `maggy setup`, e.g. `| bash -s -- --theme xmas --no-mood`.
#
# Env overrides:
#   MAGGY_DIR   install location   (default: ~/.maggy)
#   MAGGY_BIN_DIR          where to link maggy (default: ~/.local/bin)
#   AGY_SETTINGS           agy settings file  (default: ~/.gemini/antigravity-cli/settings.json)
set -euo pipefail

REPO_URL="https://github.com/agy-pet/maggy.git"
INSTALL_DIR="${MAGGY_DIR:-$HOME/.maggy}"
BIN_DIR="${MAGGY_BIN_DIR:-$HOME/.local/bin}"

say() { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31merror:\033[0m %s\n' "$*" >&2; exit 1; }

command -v git >/dev/null 2>&1 || die "git is required"
command -v python3 >/dev/null 2>&1 || die "python3 is required"

# 1. Fetch or update the code
if [ -d "$INSTALL_DIR/.git" ]; then
    say "Updating $INSTALL_DIR"
    git -C "$INSTALL_DIR" pull --ff-only --quiet
elif [ -e "$INSTALL_DIR" ]; then
    die "$INSTALL_DIR exists and is not a git clone; set MAGGY_DIR to another path"
else
    say "Cloning into $INSTALL_DIR"
    git clone --depth 1 --quiet "$REPO_URL" "$INSTALL_DIR"
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

# 3. Hook into agy (settings are backed up to settings.json.bak)
MAGGY_BIN="$BIN_DIR/maggy" "$BIN_DIR/maggy" setup "$@"
