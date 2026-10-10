#!/usr/bin/env python3
"""Apply the bar clearance to existing workspaces on the bar monitor."""
import json
import subprocess


def build_command(workspaces):
    affected = [w for w in workspaces if w["output"] == "HDMI-0"]
    if not affected:
        return ""
    commands = []
    def select(name):
        return "workspace --no-auto-back-and-forth " + json.dumps(name)
    for workspace in affected:
        commands.extend([select(workspace["name"]), "gaps top current set 38"])
    # Restore which workspace was visible on the main monitor, then input focus.
    for workspace in affected:
        if workspace.get("visible"):
            commands.append(select(workspace["name"]))
    for workspace in workspaces:
        if workspace.get("focused"):
            commands.append(select(workspace["name"]))
    return "; ".join(commands)


def main():
    workspaces = json.loads(subprocess.check_output(["i3-msg", "-t", "get_workspaces"], text=True))
    command = build_command(workspaces)
    if command:
        results = json.loads(subprocess.check_output(["i3-msg", command], text=True))
        if not all(result.get("success") for result in results):
            raise SystemExit("Não foi possível aplicar todas as margens: " + str(results))


if __name__ == "__main__":
    main()
