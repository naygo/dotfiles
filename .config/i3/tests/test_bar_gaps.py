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

        with patch.object(bar_gaps.subprocess, "check_output", side_effect=ipc), \
                patch.object(bar_gaps, "bar_monitors", return_value="all"):
            bar_gaps.apply_gaps(False)
        self.assertEqual(events, [], "Gap update destroyed/recreated the empty workspace: " + str(events))
        self.assertEqual(focused, "6")
        self.assertIn("6", existing)

    def test_hidden_bar_uses_outer_gap(self):
        self.assertEqual(bar_gaps.build_command([
            {"name": "1", "output": "eDP-1", "focused": True},
        ], hidden=True), "gaps top current set 2")

    def test_every_monitor_has_a_bar(self):
        self.assertEqual(bar_gaps.build_command([
            {"name": "1", "output": "eDP-1", "focused": False, "visible": True},
            {"name": "6", "output": "HDMI-1", "focused": True},
        ]), "gaps top current set 38")

    def test_primary_only_bar_ignores_other_monitors(self):
        workspaces = [
            {"name": "1", "output": "HDMI-0", "focused": False, "visible": True},
            {"name": "7", "output": "DP-0", "focused": True},
        ]
        self.assertEqual(bar_gaps.build_command(workspaces, bar_output="HDMI-0"), "")
        workspaces[0]["focused"], workspaces[1]["focused"] = True, False
        self.assertEqual(bar_gaps.build_command(workspaces, bar_output="HDMI-0"), "gaps top current set 38")

    def test_bar_monitors_reads_machine_env(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / "machine.env"
            with patch.object(bar_gaps, "MACHINE_ENV", env):
                self.assertEqual(bar_gaps.bar_monitors(), "all")
                env.write_text("# comentário\nBAR_MONITORS=primary\nPRIMARY_MONITOR=HDMI-0\n")
                self.assertEqual(bar_gaps.bar_monitors(), "primary")
                self.assertEqual(bar_gaps.primary_output(), "HDMI-0")


if __name__ == "__main__":
    unittest.main()
