"""One inventory of host tool names: hooks/tools.json."""

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / "hooks" / "molab_guard.py"


def _guard():
    spec = importlib.util.spec_from_file_location("molab_guard_under_test", GUARD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _matcher(path, key_path):
    data = json.loads(path.read_text())
    node = data
    for key in key_path:
        node = node[key]
    return node.split("|")


class ToolNameTests(unittest.TestCase):
    def test_host_matchers_are_the_inventory(self):
        names = json.loads((ROOT / "hooks" / "tools.json").read_text())
        covered = set(names["write"]) | set(names["shell"]) | set(names["patch"])
        claude = _matcher(ROOT / "hooks" / "hooks.json", ("hooks", "PreToolUse", 0, "matcher"))
        codex = _matcher(ROOT / "hooks" / "codex.json", ("hooks", "PreToolUse", 0, "matcher"))
        self.assertEqual(claude, names["hosts"]["claude"])
        self.assertEqual(codex, names["hosts"]["codex"])
        advertised = [*claude, *codex, *names["hosts"]["dsh"].values()]
        self.assertTrue(set(advertised) <= covered)
        self.assertIn("search_replace", names["write"])
        self.assertIn("hashline_edit", names["write"])
        self.assertIn("run_terminal_command", names["shell"])
        guard = _guard()
        self.assertEqual(guard.WRITE_TOOLS, set(names["write"]))
        self.assertEqual(guard.SHELL_TOOLS, set(names["shell"]))
        self.assertEqual(guard.PATCH_TOOLS, set(names["patch"]))


if __name__ == "__main__":
    unittest.main()
