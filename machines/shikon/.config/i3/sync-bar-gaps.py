#!/usr/bin/env python3
"""Keep workspace clearance synchronized with Polybar visibility."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess


def runtime_dir():
    directory = Path(os.environ.get("XDG_RUNTIME_DIR", f"/tmp/i3-bar-{os.getuid()}"))
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    return directory


def build_command(workspaces, hidden=False):
    # Visiting other workspaces destroys an empty focused workspace. Restoring
    # it then emits "init", causing the listener to repeat forever. Only change
    # the current workspace; the listener updates the others as they gain focus.
    for workspace in workspaces:
        if workspace.get("focused") and workspace["output"] == "HDMI-0":
            return f"gaps top current set {2 if hidden else 38}"
    return ""


def apply_gaps(hidden):
    workspaces = json.loads(subprocess.check_output(["i3-msg", "-t", "get_workspaces"], text=True))
    command = build_command(workspaces, hidden)
    if command:
        results = json.loads(subprocess.check_output(["i3-msg", command], text=True))
        if not all(result.get("success") for result in results):
            raise SystemExit("Não foi possível aplicar todas as margens: " + str(results))


def synchronize(toggle=False, reset=False):
    directory = runtime_dir()
    state = directory / "i3-topbar-hidden"
    with (directory / "i3-topbar-gaps.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        hidden = state.exists()
        if toggle:
            hidden = not hidden
            subprocess.run(["polybar-msg", "cmd", "hide" if hidden else "show"], check=True)
        elif reset:
            hidden = False
        apply_gaps(hidden)
        if hidden:
            state.touch(mode=0o600)
        else:
            state.unlink(missing_ok=True)


def watch():
    # Keep a single listener across i3 reloads.
    with (runtime_dir() / "i3-topbar-watch.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        with subprocess.Popen(
            ["i3-msg", "-m", "-t", "subscribe", '["workspace", "output"]'],
            stdout=subprocess.PIPE, text=True,
        ) as subscription:
            try:
                synchronize()
                for line in subscription.stdout:
                    event = json.loads(line)
                    # Gap commands do not change focus or create workspaces.
                    # Apply the current bar state when the user enters a workspace.
                    if isinstance(event, dict) and event.get("change") in {"init", "focus", "move", "unspecified"}:
                        synchronize()
            finally:
                if subscription.poll() is None:
                    subscription.terminate()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--toggle", action="store_true")
    mode.add_argument("--reset", action="store_true")
    mode.add_argument("--watch", action="store_true")
    args = parser.parse_args()
    if args.watch:
        watch()
    else:
        synchronize(toggle=args.toggle, reset=args.reset)


if __name__ == "__main__":
    main()
