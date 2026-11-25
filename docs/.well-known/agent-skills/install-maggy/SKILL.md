---
name: install-maggy
description: Install, verify, update or remove Maggy, the animated agy pet and custom statusline for Antigravity CLI (agy) showing usage, quota limits, and reset countdowns, on macOS or Linux. Use when a user asks to set up Maggy, an agy pet/animation, or a custom agy statusline.
---

# Install Maggy

Maggy is an animated agy pet and custom statusline for Antigravity CLI (`agy`), displaying a dancing Antigravity logo animation beside the live model, context window usage %, 5-hour & weekly quota limit bars with reset countdowns, workspace, and git branch. Python 3 standard library only, no telemetry.

## Install (non-interactive)

Prefer Homebrew when `brew` is available:

```bash
brew install agy-pet/tap/maggy && maggy setup
```

Otherwise (needs `git` and `python3`; clones to `~/.maggy`, links `maggy` into `~/.local/bin`):

```bash
curl -fsSL https://agy-pet.github.io/install.sh | bash
```

Pass `maggy setup` options after `bash -s --`, e.g. `| bash -s -- --theme xmas --no-mood`.

`maggy setup` only sets the `statusLine` key in `~/.gemini/antigravity-cli/settings.json` and backs up the previous file to `settings.json.bak`. Other settings are untouched.

## Verify

```bash
maggy doctor       # checks the install and the agy settings
maggy status -q    # setup state and settings, without the sample render
```

Then tell the user to restart `agy` or run `/statusline enable` inside it.

## Configure

- Prefer `maggy config set KEY VALUE` over editing `~/.config/maggy/config.json`.
- `maggy theme list` / `maggy theme NAME` switch themes (`auto`, `default`, `xmas`, `halloween`, `cny`, or a custom one).
- `maggy preview` animates until Ctrl+C; use `maggy preview working --once` in scripts.
- `maggy stats --json` prints machine-readable usage stats.

## Update or remove

```bash
brew upgrade maggy        # or: maggy update
maggy uninstall --purge   # removes Maggy's statusLine from agy settings, plus its config, cache and stats
```

`uninstall` leaves the program itself: then run `brew uninstall maggy`, or `rm -rf ~/.maggy ~/.local/bin/maggy` for the one-line install.

Full docs: https://agy-pet.github.io/llms-full.txt
