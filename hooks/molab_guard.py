"""Forward agent writes, shell commands, and session stop to molab.

The same events arrive from Claude Code, Grok, Codex (its hooks speak the
same protocol; a file edit is an ``apply_patch`` patch), and DeepSeek Harness
(the harness's DSH plugin in ``dsh/`` translates its tool calls into these
events).

This file holds no layout rule. It turns a hook event into `molab check`
calls and turns molab's verdict back into the hook's answer. A file write
goes to `molab check path`. A shell command goes whole to `molab check
command`; molab reads the destinations. Without molab installed, a path it
can see is allowed. A write whose path cannot be read is denied, because
there is nothing to forward.

When molab is installed but gives no verdict (a timeout, a crash, output that
is not JSON) the change still goes ahead, since a broken checker must not
stop the agent, but the hook says so in a ``systemMessage`` the user sees.
Every molab call shares one time budget, kept below the hook timeout in
hooks.json, so a slow workspace cannot get the hook killed mid-answer.
"""

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time

#: Seconds all molab calls of one hook run may take together; hooks.json
#: allows 120.
BUDGET = float(os.environ.get("MOLAB_GUARD_BUDGET", "100"))
_STARTED = time.monotonic()
#: Why a molab call gave no verdict; reported once in ``systemMessage``.
_PROBLEMS = []
_UNCHECKED = {
    "pre": "This change went ahead without a molab check.",
    "start": "No snapshot was taken, so the stop check falls back to the workspace baseline.",
    "stop": "The workspace was not checked before stopping; run `molab validate --new-only`.",
}

def _tool_inventory():
    """Host tool names. ``hooks/tools.json`` is the one list; this file only reads it."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools.json")
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


_INVENTORY = _tool_inventory()
WRITE_TOOLS = set(_INVENTORY["write"])
SHELL_TOOLS = set(_INVENTORY["shell"])
#: Codex edits files with one patch naming every file it adds, updates, deletes or moves.
PATCH_TOOLS = set(_INVENTORY["patch"])
PATH_KEYS = (
    "file_path",
    "filePath",
    "path",
    "notebook_path",
    "notebookPath",
    "target_notebook",
    "targetNotebook",
)
CONTENT_KEYS = ("content", "contents")
EDIT_TOOLS = {"Edit", "MultiEdit", "search_replace", "hashline_edit", "StrReplace"}


def molab(*args):
    """Run `molab check …` and return its JSON verdict, or None without one.

    molab not installed is silent. Any other missing verdict is recorded in
    ``_PROBLEMS`` for the hook's ``systemMessage``.
    """
    exe = shutil.which("molab")
    if exe is None:
        return None
    what = f"`molab check {args[0]}`" if args else "`molab check`"
    left = BUDGET - (time.monotonic() - _STARTED)
    if left < 1:
        _PROBLEMS.append(f"{what} was skipped: the hook's {BUDGET:.0f} s budget was used up")
        return None
    limit = min(110.0, left)
    try:
        done = subprocess.run(
            [exe, "check", *args, "--json"], capture_output=True, text=True, timeout=limit
        )
    except subprocess.TimeoutExpired:
        _PROBLEMS.append(f"{what} timed out after {limit:.0f} s")
        return None
    except (OSError, subprocess.SubprocessError) as exc:
        _PROBLEMS.append(f"{what} could not run ({exc})")
        return None
    try:
        verdict = json.loads(done.stdout)
    except ValueError:
        verdict = None
    if not isinstance(verdict, dict):
        lines = (done.stderr or done.stdout or "").strip().splitlines()
        tail = f": {lines[-1][:200]}" if lines else ""
        _PROBLEMS.append(f"{what} gave no verdict (exit {done.returncode}){tail}")
        return None
    return verdict


def _event_value(event, snake, camel, default=None):
    if snake in event:
        return event[snake]
    if camel in event:
        return event[camel]
    return default


def _input(event):
    data = _event_value(event, "tool_input", "toolInput", {})
    return data if isinstance(data, dict) else {}


def _tool(event):
    return str(_event_value(event, "tool_name", "toolName", "") or "")


def _session(event):
    raw = _event_value(event, "session_id", "sessionId", None) or "default"
    return re.sub(r"[^A-Za-z0-9_-]", "_", str(raw))[:80] or "default"


def _truncated(event):
    return bool(_event_value(event, "tool_input_truncated", "toolInputTruncated", False))


def _state_path(session):
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    return os.path.join(base, "molab-guard", f"{session}.json")


def _load_roots(session):
    try:
        with open(_state_path(session), encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return []
    roots = data.get("roots") if isinstance(data, dict) else None
    return [item for item in roots if isinstance(item, str)] if isinstance(roots, list) else []


def _save_roots(session, roots):
    """Merge *roots* into the session's list; atomic, so parallel hooks lose nothing they wrote."""
    path = _state_path(session)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    merged = list(dict.fromkeys([*_load_roots(session), *roots]))
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".roots-")
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump({"roots": merged}, handle)
    os.replace(tmp, path)


def _note(session, verdict):
    """Snapshot a workspace the first time this session sees it."""
    if not verdict or not verdict.get("in_workspace"):
        return
    root = verdict.get("root")
    if not isinstance(root, str) or not root:
        return
    roots = _load_roots(session)
    if root in roots:
        return
    if molab("tree", root, "--snapshot", session) is None:
        return
    roots.append(root)
    _save_roots(session, roots)


_PATCH_FILE = re.compile(r"^\*\*\* (Add|Update|Delete) File: (.+)$")
_PATCH_MOVE = re.compile(r"^\*\*\* Move to: (.+)$")


def _patch_text(data):
    """The patch body of an apply_patch call, wherever the agent put it."""
    for value in data.values():
        if isinstance(value, str) and "*** Begin Patch" in value:
            return value
    return None


def _apply_hunks(text, hunk_lines):
    """*text* after an Update File section's hunks, or None when a hunk does not match exactly once."""
    lines = text.split("\n")
    cursor = 0
    hunks, current = [], None
    for line in hunk_lines:
        if line.startswith("@@"):
            current = []
            hunks.append(current)
        elif line == "*** End of File":
            continue
        else:
            if current is None:
                current = []
                hunks.append(current)
            current.append(line)
    for hunk in hunks:
        old = [line[1:] for line in hunk if line[:1] in (" ", "-")]
        new = [line[1:] for line in hunk if line[:1] in (" ", "+")]
        if any(line[:1] not in (" ", "-", "+") for line in hunk if line):
            return None
        if not old:
            lines[len(lines):] = new
            continue
        found = [i for i in range(cursor, len(lines) - len(old) + 1) if lines[i : i + len(old)] == old]
        if len(found) != 1:
            return None
        start = found[0]
        lines[start : start + len(old)] = new
        cursor = start + len(new)
    return "\n".join(lines)


def patch_changes(patch, base=None):
    """(path, op, content) for every file a patch touches.

    An added file's content is its ``+`` lines. An updated file's content is
    its current text with the hunks applied, when *base* (the directory the
    patch's paths are relative to) is given and every hunk matches exactly
    once; otherwise it is None and molab judges the path alone. A deleted
    file, and a move's destination, carry no content.
    """
    changes = []
    current = None
    for line in patch.splitlines():
        found = _PATCH_FILE.match(line)
        moved = _PATCH_MOVE.match(line)
        if found:
            kind, path = found.group(1), found.group(2).strip()
            current = {"path": path, "kind": kind, "lines": []}
            changes.append(current)
        elif moved:
            current = {"path": moved.group(1).strip(), "kind": "Move", "lines": None}
            changes.append(current)
        elif line.startswith("*** ") and line != "*** End of File":
            current = None
        elif current is not None and current["lines"] is not None:
            current["lines"].append(line)
    result = []
    for item in changes:
        content = None
        if item["kind"] == "Add":
            content = "\n".join(line[1:] for line in item["lines"] if line.startswith("+")) + "\n"
        elif item["kind"] == "Update" and base is not None:
            try:
                with open(_absolute(item["path"], base), encoding="utf-8") as handle:
                    content = _apply_hunks(handle.read(), item["lines"])
            except OSError:
                content = None
        result.append((item["path"], "write" if item["kind"] in ("Add", "Move") else "edit", content))
    return result


def _trace(mode, event):
    """Append the raw event to $MOLAB_GUARD_TRACE, when set (debugging a new agent's events)."""
    target = os.environ.get("MOLAB_GUARD_TRACE")
    if not target:
        return
    try:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"mode": mode, "event": event}) + "\n")
    except OSError:
        pass


def _file_path(data):
    for key in PATH_KEYS:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _full_content(data):
    for key in CONTENT_KEYS:
        value = data.get(key)
        if isinstance(value, str):
            return value
    return None


def proposed(tool, data, path):
    """The file's full content after the edit, or None when it cannot be known."""
    if tool in {"Write", "write"}:
        return _full_content(data)
    edits = data.get("edits") if tool == "MultiEdit" else [data] if tool in EDIT_TOOLS else None
    if edits is None:
        return _full_content(data)
    if not isinstance(edits, list) or not all(isinstance(edit, dict) for edit in edits):
        return None
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except OSError:
        return _full_content(data)
    for edit in edits:
        if "old_string" not in edit:
            return None
        old, new = edit.get("old_string", ""), edit.get("new_string", "")
        text = text.replace(old, new) if edit.get("replace_all") else text.replace(old, new, 1)
    return text


def _absolute(path, cwd):
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(cwd, path)
    return os.path.normpath(path)


def _command_cwd(event, data):
    raw = data.get("cwd") if isinstance(data.get("cwd"), str) else None
    raw = raw or _event_value(event, "cwd", "cwd") or os.getcwd()
    return _absolute(str(raw), _event_value(event, "cwd", "cwd") or os.getcwd())


def _check_path(path, op, content):
    args = ["path", path, "--op", op]
    tmp = None
    if content is not None:
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as handle:
            handle.write(content)
            tmp = handle.name
        args += ["--content-file", tmp]
    try:
        return molab(*args)
    finally:
        if tmp:
            os.unlink(tmp)


def deny(text):
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": text,
        }
    }


def reason(verdict):
    lines = [verdict.get("reason") or "molab refused this change."]
    if verdict.get("command"):
        lines.append(f"Use: {verdict['command']}")
    for issue in verdict.get("issues", [])[:20]:
        lines.append(f"- [{issue.get('rule')}] {issue.get('path')}: {issue.get('hint', '')}")
    return "\n".join(lines)


def _refusal(verdict):
    if not verdict or verdict.get("allowed", True):
        return None
    return deny(reason(verdict))


def pre_write(event, data):
    if _truncated(event):
        return deny("This edit was truncated, so molab cannot check it.")
    path = _file_path(data)
    if path is None:
        return deny("This edit has no file path molab can check.")
    tool = _tool(event)
    content = _full_content(data)
    if content is None and tool not in {"Write", "write"}:
        content = proposed(tool, data, path)
    op = "write" if tool in {"Write", "write"} else "edit"
    verdict = _check_path(path, op, content)
    _note(_session(event), verdict)
    return _refusal(verdict)


def pre_shell(event, data):
    command = data.get("command")
    if isinstance(command, list) and all(isinstance(part, str) for part in command):
        command = shlex.join(command)
    if not isinstance(command, str) or not command.strip():
        return None
    if _truncated(event):
        return deny("This command was truncated, so molab cannot check its paths.")
    cwd = _command_cwd(event, data)
    verdict = molab("command", "--cwd", cwd, "--command", command)
    _note(_session(event), verdict)
    return _refusal(verdict)


def pre_patch(event, data):
    if _truncated(event):
        return deny("This patch was truncated, so molab cannot check it.")
    patch = _patch_text(data)
    if patch is None:
        return deny("This patch has no body molab can check.")
    base = _event_value(event, "cwd", "cwd") or os.getcwd()
    changes = patch_changes(patch, base)
    if not changes:
        return deny("This patch names no file molab can check.")
    session = _session(event)
    for path, op, content in changes:
        verdict = _check_path(_absolute(path, base), op, content)
        _note(session, verdict)
        refusal = _refusal(verdict)
        if refusal is not None:
            return refusal
    return None


def pre(event):
    tool = _tool(event)
    data = _input(event)
    if tool in SHELL_TOOLS:
        return pre_shell(event, data)
    if tool in PATCH_TOOLS:
        return pre_patch(event, data)
    if tool in WRITE_TOOLS:
        return pre_write(event, data)
    return None


def start(event):
    session = _session(event)
    cwd = _event_value(event, "cwd", "cwd") or os.getcwd()
    verdict = molab("tree", cwd, "--snapshot", session)
    if verdict and isinstance(verdict.get("root"), str):
        roots = _load_roots(session)
        root = verdict["root"]
        if root not in roots:
            roots.append(root)
            _save_roots(session, roots)
    return None


def stop(event):
    session = _session(event)
    cwd = _event_value(event, "cwd", "cwd") or os.getcwd()
    targets = []
    for item in [*_load_roots(session), cwd]:
        if item and item not in targets:
            targets.append(item)
    refused = None
    for target in targets:
        verdict = molab("tree", target, "--since", session)
        if refused is None and verdict and not verdict.get("allowed", True):
            refused = verdict
    if refused is None:
        return None
    if event.get("stop_hook_active"):
        # Blocked once already: let the agent stop, but show the user what is left.
        return {"systemMessage": "molab: errors remain after the stop check.\n" + reason(refused)}
    return {"decision": "block", "reason": reason(refused)}


def main():
    event = json.load(sys.stdin)
    mode = sys.argv[1]
    _trace(mode, event)
    answer = {"pre": pre, "start": start, "stop": stop}[mode](event)
    if _PROBLEMS:
        note = "molab guard: " + "; ".join(dict.fromkeys(_PROBLEMS)) + ". " + _UNCHECKED[mode]
        print(note, file=sys.stderr)
        answer = dict(answer or {})
        answer["systemMessage"] = "\n".join(filter(None, [answer.get("systemMessage"), note]))
    if answer:
        print(json.dumps(answer))


if __name__ == "__main__":
    main()
