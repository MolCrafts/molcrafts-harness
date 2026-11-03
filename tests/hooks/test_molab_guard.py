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
with open({log!r}, "a") as handle:
    handle.write(json.dumps({{"args": args, "content": content}}) + "\\n")
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
        self.env = {
            **os.environ,
            "PATH": f"{fake.parent}{os.pathsep}{os.environ['PATH']}",
            "XDG_CACHE_HOME": str(self.dir / "cache"),
        }

    def run_guard(self, mode, event, env=None):
        done = subprocess.run(
            [sys.executable, str(GUARD), mode], input=json.dumps(event),
            capture_output=True, text=True, env=env or self.env, check=True,
        )
        return json.loads(done.stdout) if done.stdout.strip() else None

    def calls(self):
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines() if line.strip()]

    def paths(self):
        found = []
        for call in self.calls():
            args = call["args"]
            if len(args) >= 3 and args[1] == "path":
                found.append(args[2])
        return found

    def test_write_sends_the_full_content_and_allows(self):
        event = {"tool_name": "Write", "tool_input": {"file_path": "/ws/a.md", "content": "hi"}}
        self.assertIsNone(self.run_guard("pre", event))
        sent = self.calls()[-1]
        self.assertEqual(sent["args"][:4], ["check", "path", "/ws/a.md", "--op"])
        self.assertIn("--json", sent["args"])
        self.assertEqual(sent["content"], "hi")

    def test_edit_sends_the_content_after_the_edit(self):
        target = self.dir / "index.md"
        target.write_text("---\ntype: run\n---\nold body\n")
        event = {"tool_name": "Edit", "tool_input": {
            "file_path": str(target), "old_string": "old", "new_string": "new"}}
        self.run_guard("pre", event)
        self.assertEqual(self.calls()[-1]["content"], "---\ntype: run\n---\nnew body\n")

    def test_grok_path_and_contents_are_sent(self):
        event = {"tool_name": "search_replace", "tool_input": {"path": "/ws/a.md", "contents": "hi"}}
        self.assertIsNone(self.run_guard("pre", event))
        sent = self.calls()[-1]
        self.assertEqual(sent["args"][2], "/ws/a.md")
        self.assertEqual(sent["content"], "hi")

    def test_a_write_with_no_path_is_denied(self):
        event = {"tool_name": "Write", "tool_input": {"content": "hi"}}
        out = self.run_guard("pre", event)["hookSpecificOutput"]
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertEqual(self.calls(), [])

    def test_a_write_with_no_path_is_denied_without_molab(self):
        env = {**os.environ, "PATH": str(self.dir / "empty"), "XDG_CACHE_HOME": str(self.dir / "cache")}
        event = {"tool_name": "write", "tool_input": {}}
        out = self.run_guard("pre", event, env=env)["hookSpecificOutput"]
        self.assertEqual(out["permissionDecision"], "deny")

    def test_a_refusal_becomes_a_deny_with_molabs_reason(self):
        self.verdict.write_text(json.dumps({
            "allowed": False, "reason": "run.json is not a file in molab.",
            "command": "molab runs create P E --params '{...}'"}))
        event = {"tool_name": "Write", "tool_input": {"file_path": "/ws/x", "content": ""}}
        out = self.run_guard("pre", event)["hookSpecificOutput"]
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertIn("molab runs create", out["permissionDecisionReason"])

    def test_shell_move_beside_the_experiment_is_denied(self):
        self.verdict.write_text(json.dumps({
            "allowed": False, "in_workspace": True, "root": "/ws",
            "reason": "not a legal file at the experiment level.",
            "command": "molab runs adopt P E R"}))
        event = {
            "tool_name": "Bash", "cwd": "/ws", "session_id": "s1",
            "tool_input": {"command": "mv /tmp/a.py projects/p/experiments/e/plot.py"},
        }
        out = self.run_guard("pre", event)["hookSpecificOutput"]
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertIn("molab runs adopt", out["permissionDecisionReason"])
        self.assertIn("/ws/projects/p/experiments/e/plot.py", self.paths())

    def test_shell_move_into_scratch_is_allowed(self):
        self.verdict.write_text(json.dumps({"allowed": True, "in_workspace": True, "root": "/ws"}))
        event = {
            "tool_name": "run_terminal_command", "cwd": "/ws", "session_id": "s1",
            "tool_input": {"command": "mv /tmp/a.py projects/p/experiments/e/scratch/plot.py"},
        }
        self.assertIsNone(self.run_guard("pre", event))
        self.assertIn("/ws/projects/p/experiments/e/scratch/plot.py", self.paths())

    def test_cd_then_move_uses_the_new_directory(self):
        self.verdict.write_text(json.dumps({"allowed": True, "in_workspace": True, "root": "/ws"}))
        event = {
            "tool_name": "Bash", "cwd": "/ws", "session_id": "s1",
            "tool_input": {"command": "cd projects/p/experiments/e && mv /tmp/a.py plot.py"},
        }
        self.run_guard("pre", event)
        self.assertIn("/ws/projects/p/experiments/e/plot.py", self.paths())

    def test_redirect_to_a_file_is_checked_and_a_dup_is_not(self):
        self.verdict.write_text(json.dumps({"allowed": True}))
        event = {
            "tool_name": "Bash", "cwd": "/ws", "session_id": "s1",
            "tool_input": {"command": "echo hi > projects/p/experiments/e/out.py 2>&1"},
        }
        self.run_guard("pre", event)
        self.assertIn("/ws/projects/p/experiments/e/out.py", self.paths())
        self.assertNotIn("/ws/1", self.paths())

    def test_an_unparsed_command_is_allowed(self):
        event = {
            "tool_name": "Bash", "cwd": "/ws", "session_id": "s1",
            "tool_input": {"command": "mv 'unterminated"},
        }
        self.assertIsNone(self.run_guard("pre", event))
        self.assertNotIn("/ws/unterminated", self.paths())

    def test_a_workspace_is_snapshotted_once(self):
        self.verdict.write_text(json.dumps({"allowed": True, "in_workspace": True, "root": "/ws"}))
        event = {
            "tool_name": "Bash", "cwd": "/ws", "session_id": "s1",
            "tool_input": {"command": "mkdir -p scratch/a scratch/b"},
        }
        self.assertIsNone(self.run_guard("pre", event))
        self.assertIsNone(self.run_guard("pre", event))
        snaps = [call for call in self.calls() if "--snapshot" in call["args"]]
        self.assertEqual(len(snaps), 1)
        self.assertIn("/ws", snaps[0]["args"])
        self.assertIn("/ws/scratch/a", self.paths())
        self.assertIn("/ws/scratch/b", self.paths())

    def test_start_records_the_root_so_a_later_command_does_not_snapshot_again(self):
        self.verdict.write_text(json.dumps({"allowed": True, "in_workspace": True, "root": "/ws"}))
        self.run_guard("start", {"cwd": "/ws", "session_id": "s1"})
        self.run_guard("pre", {
            "tool_name": "Bash", "cwd": "/ws", "session_id": "s1",
            "tool_input": {"command": "mv /tmp/a.py scratch/a.py"},
        })
        snaps = [call for call in self.calls() if "--snapshot" in call["args"]]
        self.assertEqual(len(snaps), 1)

    def test_stop_checks_every_workspace_the_session_touched(self):
        self.verdict.write_text(json.dumps({"allowed": True, "in_workspace": True, "root": "/lab"}))
        self.run_guard("pre", {
            "tool_name": "Bash", "cwd": "/repo", "session_id": "s9",
            "tool_input": {"command": "mv /tmp/a.py /lab/projects/p/experiments/e/a.py"},
        })
        self.log.write_text("")
        self.verdict.write_text(json.dumps({"allowed": False, "reason": "new layout errors", "issues": [
            {"rule": "layout.stray", "path": "projects/p/experiments/e/a.py", "hint": "move it to scratch/"}]}))
        out = self.run_guard("stop", {"cwd": "/repo", "session_id": "s9"})
        self.assertEqual(out["decision"], "block")
        self.assertIn("layout.stray", out["reason"])
        checked = [call["args"][:5] for call in self.calls()]
        self.assertIn(["check", "tree", "/lab", "--since", "s9"], checked)
        self.assertIn(["check", "tree", "/repo", "--since", "s9"], checked)

    def test_stop_blocks_on_new_issues_once(self):
        self.verdict.write_text(json.dumps({"allowed": False, "reason": "new layout errors", "issues": [
            {"rule": "layout.stray", "path": "projects/p/x.py", "hint": "move it to scratch/"}]}))
        out = self.run_guard("stop", {"cwd": "/ws", "session_id": "s1"})
        self.assertEqual(out["decision"], "block")
        self.assertIn("layout.stray", out["reason"])
        self.assertEqual(self.calls()[-1]["args"][:5], ["check", "tree", "/ws", "--since", "s1"])
        again = self.run_guard("stop", {"cwd": "/ws", "session_id": "s1", "stop_hook_active": True})
        self.assertNotIn("decision", again)
        self.assertIn("layout.stray", again["systemMessage"])

    def test_session_start_takes_a_snapshot(self):
        self.assertIsNone(self.run_guard("start", {"cwd": "/ws", "session_id": "s1"}))
        self.assertEqual(self.calls()[-1]["args"][:5], ["check", "tree", "/ws", "--snapshot", "s1"])

    def test_without_molab_a_known_path_is_allowed(self):
        env = {**os.environ, "PATH": str(self.dir / "empty"), "XDG_CACHE_HOME": str(self.dir / "cache")}
        event = {"tool_name": "Write", "tool_input": {"file_path": "/ws/run.json", "content": "{}"}}
        self.assertIsNone(self.run_guard("pre", event, env=env))
        self.assertIsNone(self.run_guard("pre", {
            "tool_name": "Bash", "cwd": "/ws", "tool_input": {"command": "mv a b"},
        }, env=env))
        self.assertIsNone(self.run_guard("stop", {"cwd": "/ws"}, env=env))

    def test_git_mv_in_another_directory_uses_that_directory(self):
        self.verdict.write_text(json.dumps({"allowed": True, "in_workspace": True, "root": "/ws"}))
        event = {
            "tool_name": "Bash", "cwd": "/ws", "session_id": "s1",
            "tool_input": {"command": "git -C projects/p/experiments/e mv a.py plot.py"},
        }
        self.run_guard("pre", event)
        self.assertIn("/ws/projects/p/experiments/e/plot.py", self.paths())

    def shell(self, command, session="s1"):
        self.verdict.write_text(json.dumps({"allowed": True, "in_workspace": True, "root": "/ws"}))
        self.run_guard("pre", {
            "tool_name": "Bash", "cwd": "/ws", "session_id": session, "tool_input": {"command": command}})
        return self.paths()

    def test_a_redirect_without_spaces_is_checked(self):
        self.assertIn("/ws/projects/p/index.md", self.shell("echo hi>projects/p/index.md"))

    def test_touch_t_is_a_time_stamp_not_a_destination(self):
        found = self.shell("touch -t 202601011200 projects/p/index.md")
        self.assertIn("/ws/projects/p/index.md", found)
        self.assertNotIn("/ws/202601011200", found)

    def test_sed_in_place_edits_are_checked(self):
        self.assertIn("/ws/projects/p/index.md", self.shell("sed -i 's/a/b/' projects/p/index.md"))
        self.assertIn("/ws/b.md", self.shell("sed -i.bak -e 's/a/b/' -e 's/c/d/' b.md"))
        self.assertNotIn("/ws/c.md", self.shell("sed 's/a/b/' c.md"))
        self.assertIn("/ws/d.md", self.shell("perl -pi -e 's/a/b/' d.md"))

    def test_wrappers_and_assignments_are_seen_through(self):
        self.assertIn("/ws/x/a.py", self.shell("FOO=1 env -u BAR sudo -u me cp /tmp/a.py x/a.py"))

    def test_a_subshell_cd_does_not_leak(self):
        found = self.shell("(cd projects/p && touch a.txt) && touch b.txt")
        self.assertIn("/ws/projects/p/a.txt", found)
        self.assertIn("/ws/b.txt", found)

    def test_variables_are_expanded_or_the_path_is_left_to_stop(self):
        found = self.shell("S=/tmp/x; mkdir -p $S/deck && touch ${HOME}/a && cp a $UNSET_GUARD_VAR/b")
        self.assertIn("/tmp/x/deck", found)
        self.assertIn(os.path.join(os.environ["HOME"], "a"), found)
        self.assertFalse(any("$" in path for path in found))
        self.assertIn("/ws/d/e.txt", self.shell("D=d; cd $D && touch e.txt"))

    def test_a_heredoc_body_is_data_not_commands(self):
        found = self.shell("cat > /tmp/x.js <<'EOF'\n// a -> deck/index.html\necho hi > body.txt\nEOF\ntouch after.txt")
        self.assertIn("/tmp/x.js", found)
        self.assertIn("/ws/after.txt", found)
        self.assertNotIn("/ws/deck/index.html", found)
        self.assertNotIn("/ws/body.txt", found)
        self.assertIn("/ws/t.txt", self.shell("cat <<-END > t.txt\n\tline > no.txt\n\tEND"))

    def test_a_known_workspace_cwd_is_not_checked_again(self):
        self.shell("mkdir scratch/a")
        self.log.write_text("")
        self.shell("mkdir scratch/b")
        self.assertNotIn("/ws", self.paths())

    def test_a_timeout_is_reported_and_the_change_goes_ahead(self):
        slow = self.dir / "slowbin" / "molab"
        slow.parent.mkdir()
        slow.write_text(f"#!{sys.executable}\nimport time\ntime.sleep(5)\n")
        slow.chmod(slow.stat().st_mode | stat.S_IXUSR)
        env = {**self.env, "PATH": f"{slow.parent}{os.pathsep}{os.environ['PATH']}",
               "MOLAB_GUARD_BUDGET": "1.5"}
        event = {"tool_name": "Write", "tool_input": {"file_path": "/ws/a.md", "content": "hi"}}
        out = self.run_guard("pre", event, env=env)
        self.assertNotIn("hookSpecificOutput", out)
        self.assertIn("timed out", out["systemMessage"])
        self.assertIn("without a molab check", out["systemMessage"])
        stop = self.run_guard("stop", {"cwd": "/ws", "session_id": "s1"}, env=env)
        self.assertIn("molab validate --new-only", stop["systemMessage"])

    def test_output_that_is_not_a_verdict_is_reported(self):
        self.verdict.write_text("Traceback: boom")
        out = self.run_guard("start", {"cwd": "/ws", "session_id": "s1"})
        self.assertIn("gave no verdict", out["systemMessage"])
        self.assertIn("baseline", out["systemMessage"])

    def test_molab_not_installed_stays_silent(self):
        env = {**os.environ, "PATH": str(self.dir / "empty"), "XDG_CACHE_HOME": str(self.dir / "cache")}
        self.assertIsNone(self.run_guard("start", {"cwd": "/ws", "session_id": "s1"}, env=env))


if __name__ == "__main__":
    unittest.main()
