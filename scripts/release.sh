#!/usr/bin/env bash
# Cut a release and update the Homebrew formula.
#
#   scripts/release.sh 0.4.0 [path/to/homebrew-tap]
#
# 1. writes VERSION, commits and tags v<version>, pushes the tag
# 2. downloads the GitHub tarball and computes its sha256
# 3. writes the formula with the new url/sha256 into packaging/homebrew/
#    and, if a tap checkout is given, into <tap>/Formula/ (commit + push it yourself)
set -euo pipefail

VERSION="${1:?usage: scripts/release.sh <version> [tap-dir]}"
TAP_DIR="${2:-}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="agy-pet/maggy"
FORMULA="$ROOT/packaging/homebrew/maggy.rb"
URL="https://github.com/$REPO/archive/refs/tags/v$VERSION.tar.gz"

cd "$ROOT"
[ -z "$(git status --porcelain)" ] || { echo "working tree not clean" >&2; exit 1; }

echo "$VERSION" > VERSION
python3 scripts/build_docs.py   # JSON-LD softwareVersion, llms.txt, llms-full.txt
git add VERSION docs
git commit -qm "chore(release): v$VERSION" || true
git tag -a "v$VERSION" -m "v$VERSION"
git push origin HEAD "v$VERSION"

echo "==> fetching $URL"
SHA="$(curl -fsSL "$URL" | shasum -a 256 | cut -d' ' -f1)"
echo "==> sha256 $SHA"

sed -i '' -E \
    -e "s|^  url \".*\"|  url \"$URL\"|" \
    -e "s|^  sha256 \".*\"|  sha256 \"$SHA\"|" \
    "$FORMULA"
git commit -qm "chore(brew): formula v$VERSION" "$FORMULA"
git push origin HEAD

if [ -n "$TAP_DIR" ]; then
    mkdir -p "$TAP_DIR/Formula"
    cp "$FORMULA" "$TAP_DIR/Formula/maggy.rb"
    echo "==> copied formula to $TAP_DIR/Formula; review, commit and push the tap"
fi
