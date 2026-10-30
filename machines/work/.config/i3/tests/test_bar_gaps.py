"""Regression for the captured empty-workspace focus loop."""
import importlib.util
import json
from pathlib import Path
import shlex
import unittest
from unittest.mock import patch

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("bar_gaps", HERE.parent / "sync-bar-gaps.py")
bar_gaps = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bar_gaps)


class BarGapsTests(unittest.TestCase):
    def test_recreated_empty_workspace_survives_gap_update(self):
        fixture = json.loads((HERE / "empty-workspace.json").read_text())
        workspaces = fixture["visible"]
        focused = next(w["name"] for w in workspaces if w["focused"])
        empty = {str(w["num"]) for w in fixture["tree"] if not w["windows"]}
        existing = {w["name"] for w in workspaces}
        events = []

        def ipc(args, **kwargs):
            nonlocal focused
            if args[2:] == ["get_workspaces"]:
                return json.dumps(workspaces)
            results = []
            for command in args[1].split(";"):
                words = shlex.split(command)
                if words[0] == "workspace":
                    target = words[-1]
                    if target not in existing:
                        existing.add(target)
                        events.append("init")
                    if target != focused:
                        events.append("focus")
                        if focused in empty:
                            existing.remove(focused)
                            events.append("empty")
                        focused = target
                elif words[:4] != ["gaps", "top", "current", "set"]:
                    self.fail("Unexpected IPC command: " + command)
                results.append({"success": True})
            return json.dumps(results)

        with patch.object(bar_gaps.subprocess, "check_output", side_effect=ipc):
            bar_gaps.apply_gaps(False)
        self.assertEqual(events, [], "Gap update destroyed/recreated the empty workspace: " + str(events))
        self.assertEqual(focused, "6")
        self.assertIn("6", existing)

    def test_hidden_bar_uses_outer_gap(self):
        self.assertEqual(bar_gaps.build_command([
            {"name": "6", "output": "HDMI-0", "focused": True},
        ], hidden=True), "gaps top current set 2")

    def test_secondary_monitor_does_not_steal_focus(self):
        self.assertEqual(bar_gaps.build_command([
            {"name": "1", "output": "HDMI-0", "focused": False, "visible": True},
            {"name": "7", "output": "DP-0", "focused": True},
        ]), "")


if __name__ == "__main__":
    unittest.main()
