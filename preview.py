#!/usr/bin/env python3
"""Live terminal preview of the dancing Antigravity statusline.

Usage:
    maggy preview [working|tool_use|initializing|idle|reviewing|error] [--theme T] [--once]
    python3 preview.py [state]

Without --theme every theme plays at once, each under its name, so you can
pick one with `maggy theme NAME`.

`idle` simulates agy's sparse idle redraws: a "done!" pose, then a random
fidget every ~1.5 s, then dozing off.
"""

import os
import random
import sys
import tempfile
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from mascot import IDLE_FIDGETS, THEMES  # noqa: E402
from statusline import render_statusline  # noqa: E402

SAMPLE_DATA = {
    "cwd": os.getcwd(),
    "model": {
        "id": "Gemini Pro",
        "display_name": "Gemini Pro",
        "effort": "medium",
    },
    "context_window": {"used_percentage": 18},
    "quota": {
        "gemini-5h": {"remaining_fraction": 0.84, "reset_in_seconds": 14400},
        "gemini-weekly": {"remaining_fraction": 0.92, "reset_in_seconds": 432000},
        "3p-5h": {"remaining_fraction": 1.0, "reset_in_seconds": 18000},
    },
    "terminal_width": 120,
}


def _bold(text):
    return f"\033[1m{text}\033[0m" if sys.stdout.isatty() else text


def _render(data, frame, activity, themes):
    """One statusline per theme, each under its name (no heading for one theme)."""
    if len(themes) == 1:
        os.environ["MAGGY_THEME"] = themes[0]
        return render_statusline(data, frame_idx=frame, activity=activity)
    blocks = []
    for name in themes:
        os.environ["MAGGY_THEME"] = name
        blocks.append(_bold(name) + "\n" + render_statusline(data, frame_idx=frame, activity=activity))
    return "\n\n".join(blocks)


def main(state="working", once=False, width=120, themes=None):
    # Keep the sample quota data out of the user's real quota cache.
    os.environ["XDG_CACHE_HOME"] = tempfile.mkdtemp(prefix="maggy-preview-")
    data = dict(SAMPLE_DATA, agent_state=state, terminal_width=width)
    themes = list(themes or THEMES)
    frame = 0
    tick_n = 0
    first = True
    last_fidget = -1
    if once:
        activity = {"idle_for": 10, "fidget": 0} if state == "idle" else None
        print(_render(data, 0, activity, themes))
        if len(themes) > 1:
            print("\n" + "pick one with: maggy theme NAME")
        return
    try:
        sys.stdout.write("\033[?25l")  # hide cursor
        while True:
            activity = None
            if state == "idle":
                # One idle redraw every ~1.5 s: done -> 8 fidgets -> sleep.
                step = tick_n // 5
                if step > len(IDLE_FIDGETS):
                    activity = {"idle_for": 999}
                else:
                    if tick_n % 5 == 0:
                        last_fidget = random.choice([i for i in range(len(IDLE_FIDGETS)) if i != last_fidget])
                    activity = {"idle_for": 0 if step == 0 else 10,
                                "just_finished": step == 0, "fidget": last_fidget}
            rendered = _render(data, frame, activity, themes)
            lines = rendered.split("\n")
            if not first:
                sys.stdout.write(f"\033[{len(lines)}A")
            first = False
            for line in lines:
                sys.stdout.write(f"\033[2K{line}\n")
            sys.stdout.flush()
            tick_n += 1
            if state != "idle" or tick_n >= 45:
                frame += 1  # sleep frames still alternate (z / zZ)
            elif tick_n % 5 == 0:
                frame += 1
            time.sleep(0.28)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?25h")  # show cursor
        sys.stdout.flush()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "working")
