#!/usr/bin/env python3
"""Mark grouped clients so Picom joins their edges to the i3 tab strip."""
import fcntl
import json
import os
from pathlib import Path
import select
import subprocess


def grouped_clients(node, grouped=False):
    children = node.get("nodes", [])
    grouped = grouped or (
        node.get("layout") in {"tabbed", "stacked"} and len(children) > 1
    )
    result = {}
    if node.get("window"):
        result[node["window"]] = int(grouped)
    for child in children:
        result.update(grouped_clients(child, grouped))
    for child in node.get("floating_nodes", []):
        result.update(grouped_clients(child))
    return result


def synchronize(previous):
    tree = json.loads(subprocess.check_output(["i3-msg", "-t", "get_tree"], text=True))
    current = grouped_clients(tree)
    for window, grouped in current.items():
        if previous.get(window) != grouped:
            # A client may close between the tree query and this property update.
            result = subprocess.run(
                ["xprop", "-id", str(window), "-f", "_I3_GROUPED", "32c",
                 "-set", "_I3_GROUPED", str(grouped)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            if result.returncode:
                current[window] = None
    return current


def main():
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/tmp/i3-bar-{os.getuid()}"))
    runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (runtime / "i3-grouped-windows.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        with subprocess.Popen(
            ["i3-msg", "-m", "-t", "subscribe", '["window", "workspace", "output"]'],
            stdout=subprocess.PIPE, text=True,
        ) as subscription:
            try:
                previous = synchronize({})
                while subscription.poll() is None:
                    # Layout changes do not always emit a window event in i3.
                    ready, _, _ = select.select([subscription.stdout], [], [], 1.0)
                    if ready and not subscription.stdout.readline():
                        break
                    previous = synchronize(previous)
            finally:
                if subscription.poll() is None:
                    subscription.terminate()


if __name__ == "__main__":
    main()
