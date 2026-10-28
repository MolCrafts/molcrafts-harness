"""The guard forwards to `molab check` and holds no rule of its own."""

import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest

GUARD = Path(__file__).resolve().parents[2] / "hooks" / "molab_guard.py"

FAKE = """#!{python}
import json, sys
args = sys.argv[1:]
content = None
if "--content-file" in args:
    content = open(args[args.index("--content-file") + 1]).read()
open({log!r}, "w").write(json.dumps({{"args": args, "content": content}}))
print(open({verdict!r}).read())
"""


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.log = self.dir / "log.json"
        self.verdict = self.dir / "verdict.json"
        self.verdict.write_text(json.dumps({"allowed": True}))
        fake = self.dir / "bin" / "molab"
        fake.parent.mkdir()
        fake.write_text(FAKE.format(python=sys.executable, log=str(self.log), verdict=str(self.verdict)))
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
        self.env = {**os.environ, "PATH": f"{fake.parent}{os.pathsep}{os.environ['PATH']}"}

    def run_guard(self, mode, event, env=None):
        done = subprocess.run(
            [sys.executable, str(GUARD), mode], input=json.dumps(event),
            capture_output=True, text=True, env=env or self.env, check=True,
        )
        return json.loads(done.stdout) if done.stdout.strip() else None

    def test_write_sends_the_full_content_and_allows(self):
        event = {"tool_name": "Write", "tool_input": {"file_path": "/ws/a.md", "content": "hi"}}
        self.assertIsNone(self.run_guard("pre", event))
        sent = json.loads(self.log.read_text())
        self.assertEqual(sent["args"][:4], ["check", "path", "/ws/a.md", "--op"])
        self.assertIn("--json", sent["args"])
        self.assertEqual(sent["content"], "hi")

    def test_edit_sends_the_content_after_the_edit(self):
        target = self.dir / "index.md"
        target.write_text("---\ntype: run\n---\nold body\n")
        event = {"tool_name": "Edit", "tool_input": {
            "file_path": str(target), "old_string": "old", "new_string": "new"}}
        self.run_guard("pre", event)
        self.assertEqual(json.loads(self.log.read_text())["content"], "---\ntype: run\n---\nnew body\n")

    def test_a_refusal_becomes_a_deny_with_molabs_reason(self):
        self.verdict.write_text(json.dumps({
            "allowed": False, "reason": "run.json is not a file in molab.",
            "command": "molab runs create P E --params '{...}'"}))
        event = {"tool_name": "Write", "tool_input": {"file_path": "/ws/x", "content": ""}}
        out = self.run_guard("pre", event)["hookSpecificOutput"]
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertIn("molab runs create", out["permissionDecisionReason"])

    def test_stop_blocks_on_new_issues_once(self):
        self.verdict.write_text(json.dumps({"allowed": False, "reason": "new layout errors", "issues": [
            {"rule": "layout.stray", "path": "projects/p/x.py", "hint": "move it to scratch/"}]}))
        out = self.run_guard("stop", {"cwd": "/ws", "session_id": "s1"})
        self.assertEqual(out["decision"], "block")
        self.assertIn("layout.stray", out["reason"])
        self.assertEqual(json.loads(self.log.read_text())["args"][:5], ["check", "tree", "/ws", "--since", "s1"])
        self.assertIsNone(self.run_guard("stop", {"cwd": "/ws", "session_id": "s1", "stop_hook_active": True}))

    def test_session_start_takes_a_snapshot(self):
        self.assertIsNone(self.run_guard("start", {"cwd": "/ws", "session_id": "s1"}))
        self.assertEqual(json.loads(self.log.read_text())["args"][:5], ["check", "tree", "/ws", "--snapshot", "s1"])

    def test_without_molab_everything_is_allowed(self):
        env = {**os.environ, "PATH": str(self.dir / "empty")}
        event = {"tool_name": "Write", "tool_input": {"file_path": "/ws/run.json", "content": "{}"}}
        self.assertIsNone(self.run_guard("pre", event, env=env))
        self.assertIsNone(self.run_guard("stop", {"cwd": "/ws"}, env=env))


if __name__ == "__main__":
    unittest.main()
