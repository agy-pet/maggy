#!/usr/bin/env bash
# maggy installer: curl -fsSL https://agy-pet.github.io/install.sh | bash
# Runs install.sh from the latest release; see https://github.com/agy-pet/maggy
set -euo pipefail
main() {
    local script
    script="$(curl -fsSL https://github.com/agy-pet/maggy/releases/latest/download/install.sh)" || {
        echo "maggy: could not download the release installer; try again, or: brew install agy-pet/tap/maggy" >&2
        exit 1
    }
    bash -c "$script" maggy-install "$@"
}
main "$@"
