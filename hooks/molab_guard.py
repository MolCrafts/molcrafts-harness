"""Forward Claude Code file writes, session start, and stop to molab's own checks.

This file holds no layout rule. It turns a hook event into one `molab check`
call and turns molab's verdict back into the hook's answer. Without molab
installed, or outside a molab workspace, everything is allowed.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile


def molab(*args):
    """Run `molab check …` and return its JSON verdict, or None when unavailable."""
    exe = shutil.which("molab")
    if exe is None:
        return None
    try:
        done = subprocess.run(
            [exe, "check", *args, "--json"], capture_output=True, text=True, timeout=110
        )
        return json.loads(done.stdout)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None


def proposed(tool, data):
    """The file's full content after the edit, or None when it cannot be known."""
    if tool == "Write":
        return data.get("content")
    edits = data.get("edits") if tool == "MultiEdit" else [data] if tool == "Edit" else None
    if edits is None:
        return None
    try:
        with open(data["file_path"], encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, KeyError):
        return None
    for edit in edits:
        old, new = edit.get("old_string", ""), edit.get("new_string", "")
        text = text.replace(old, new) if edit.get("replace_all") else text.replace(old, new, 1)
    return text


def pre(event):
    tool, data = event.get("tool_name", ""), event.get("tool_input", {})
    path = data.get("file_path") or data.get("notebook_path")
    if not path:
        return None
    op = "write" if tool == "Write" else "edit"
    content = proposed(tool, data)
    args = ["path", path, "--op", op]
    tmp = None
    if content is not None:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as handle:
            handle.write(content)
            tmp = handle.name
        args += ["--content-file", tmp]
    try:
        verdict = molab(*args)
    finally:
        if tmp:
            os.unlink(tmp)
    if not verdict or verdict.get("allowed", True):
        return None
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason(verdict),
        }
    }


def start(event):
    molab("tree", event.get("cwd") or os.getcwd(), "--snapshot", session(event))
    return None


def stop(event):
    verdict = molab("tree", event.get("cwd") or os.getcwd(), "--since", session(event))
    if not verdict or verdict.get("allowed", True):
        return None
    if event.get("stop_hook_active"):
        print(reason(verdict), file=sys.stderr)
        return None
    return {"decision": "block", "reason": reason(verdict)}


def session(event):
    return event.get("session_id") or "default"


def reason(verdict):
    lines = [verdict.get("reason") or "molab refused this change."]
    if verdict.get("command"):
        lines.append(f"Use: {verdict['command']}")
    for issue in verdict.get("issues", [])[:20]:
        lines.append(f"- [{issue.get('rule')}] {issue.get('path')}: {issue.get('hint', '')}")
    return "\n".join(lines)


def main():
    event = json.load(sys.stdin)
    answer = {"pre": pre, "start": start, "stop": stop}[sys.argv[1]](event)
    if answer:
        print(json.dumps(answer))


if __name__ == "__main__":
    main()
