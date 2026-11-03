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


MACHINE_ENV = Path.home() / ".config/polybar/machine.env"


def machine_env():
    """KEY=VALUE pairs from machine.env (BAR_MONITORS, PRIMARY_MONITOR)."""
    values = {}
    try:
        for line in MACHINE_ENV.read_text().splitlines():
            key, sep, value = line.partition("=")
            if sep and not key.lstrip().startswith("#"):
                values[key.strip()] = value.strip().strip("'\"")
    except FileNotFoundError:
        pass
    return values


def bar_monitors():
    """"all" (default: every monitor has a bar) or "primary"."""
    return machine_env().get("BAR_MONITORS") or "all"


def primary_output():
    configured = machine_env().get("PRIMARY_MONITOR")
    if configured:
        return configured
    outputs = json.loads(subprocess.check_output(["i3-msg", "-t", "get_outputs"], text=True))
    return next((o["name"] for o in outputs if o.get("active") and o.get("primary")), None)


def build_command(workspaces, hidden=False, bar_output=None):
    # Visiting other workspaces destroys an empty focused workspace. Restoring
    # it then emits "init", causing the listener to repeat forever. Only change
    # the current workspace; the listener updates the others as they gain focus.
    # bar_output: only that monitor has a bar (None = every monitor has one).
    for workspace in workspaces:
        if workspace.get("focused") and bar_output in (None, workspace["output"]):
            return f"gaps top current set {2 if hidden else 38}"
    return ""


def apply_gaps(hidden):
    workspaces = json.loads(subprocess.check_output(["i3-msg", "-t", "get_workspaces"], text=True))
    bar_output = primary_output() if bar_monitors() == "primary" else None
    command = build_command(workspaces, hidden, bar_output)
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
