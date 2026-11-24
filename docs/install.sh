#!/usr/bin/env bash
# maggy installer: curl -fsSL https://agy-pet.github.io/install.sh | bash
# Runs install.sh from the latest release; see https://github.com/agy-pet/maggy
set -euo pipefail
main() {
    local script
    script="$(curl -fsSL https://github.com/agy-pet/maggy/releases/latest/download/install.sh 2>/dev/null)" ||
        script="$(curl -fsSL https://raw.githubusercontent.com/agy-pet/maggy/master/install.sh)"
    bash -c "$script" maggy-install "$@"
}
main "$@"
