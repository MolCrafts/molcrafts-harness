"""The import and command allowlist stays gone."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class NoPolicyTests(unittest.TestCase):
    def test_there_is_no_policy_file_and_no_second_guard(self):
        self.assertFalse((ROOT / "policy.toml").exists())
        self.assertFalse((ROOT / "hooks" / "policy_guard.py").exists())
        for rel in ("hooks/hooks.json", "hooks/codex.json", "dsh/index.js"):
            text = (ROOT / rel).read_text()
            self.assertNotIn("policy_guard", text, rel)
            self.assertNotIn("policy.toml", text, rel)
            self.assertIn("molab_guard.py", text, rel)
        guard = (ROOT / "hooks" / "molab_guard.py").read_text()
        self.assertNotIn("policy_guard", guard)
        self.assertNotIn("policy.toml", guard)
        self.assertIn('join(HOOKS, "molab_guard.py")', (ROOT / "dsh" / "index.js").read_text())
        self.assertEqual(list((ROOT / "hooks").glob("*guard*.py")), [ROOT / "hooks" / "molab_guard.py"])


if __name__ == "__main__":
    unittest.main()
