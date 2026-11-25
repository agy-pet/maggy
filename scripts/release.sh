#!/usr/bin/env bash
# Cut a release and update the Homebrew formula.
#
#   scripts/release.sh 0.4.0 [path/to/homebrew-tap]
#
# 1. writes VERSION, commits and tags v<version>, pushes the tag
# 2. builds maggy-<version>.tar.gz from the tag and publishes a GitHub release
#    with it and install.sh (pinned to the tag) attached
# 3. writes the formula with the new url/sha256 into packaging/homebrew/
#    and, if a tap checkout is given, into <tap>/Formula/ (commit + push it yourself)
set -euo pipefail

VERSION="${1:?usage: scripts/release.sh <version> [tap-dir]}"
TAP_DIR="${2:-}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="agy-pet/maggy"
FORMULA="$ROOT/packaging/homebrew/maggy.rb"
TARBALL="maggy-$VERSION.tar.gz"
URL="https://github.com/$REPO/releases/download/v$VERSION/$TARBALL"

cd "$ROOT"
[ -z "$(git status --porcelain)" ] || { echo "working tree not clean" >&2; exit 1; }

echo "$VERSION" > VERSION
python3 scripts/build_docs.py   # JSON-LD softwareVersion, llms.txt, llms-full.txt
git add VERSION docs
git commit -qm "chore(release): v$VERSION" || true
git tag -a "v$VERSION" -m "v$VERSION"
git push origin HEAD "v$VERSION"

DIST="$(mktemp -d)"
trap 'rm -rf "$DIST"' EXIT
git archive --format=tar.gz --prefix="maggy-$VERSION/" -o "$DIST/$TARBALL" "v$VERSION"
SHA="$(shasum -a 256 "$DIST/$TARBALL" | cut -d' ' -f1)"
echo "==> $TARBALL sha256 $SHA"

# The uploaded install.sh installs this tag, not whatever master is at install time.
sed -E 's|^REF="\$\{MAGGY_REF:-master\}"$|REF="${MAGGY_REF:-v'"$VERSION"'}"|' install.sh > "$DIST/install.sh"
grep -q "^REF=\"\${MAGGY_REF:-v$VERSION}\"$" "$DIST/install.sh" || { echo "failed to pin install.sh to v$VERSION" >&2; exit 1; }

echo "==> creating GitHub release v$VERSION with $TARBALL and install.sh (pinned to v$VERSION)"
gh release create "v$VERSION" "$DIST/$TARBALL" "$DIST/install.sh" \
    --repo "$REPO" --title "v$VERSION" --generate-notes --latest

echo "==> verifying $URL"
[ "$(curl -fsSL "$URL" | shasum -a 256 | cut -d' ' -f1)" = "$SHA" ] || { echo "uploaded tarball sha mismatch" >&2; exit 1; }

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
