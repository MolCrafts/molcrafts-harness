"""Forward Claude Code and Grok writes, shell moves, and session stop to molab.

This file holds no layout rule. It turns a hook event into `molab check`
calls and turns molab's verdict back into the hook's answer. Without molab
installed, a path it can see is allowed. A write whose path cannot be read
is denied, because there is nothing to forward.

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

WRITE_TOOLS = {
    "Write",
    "write",
    "Edit",
    "MultiEdit",
    "NotebookEdit",
    "search_replace",
    "hashline_edit",
    "StrReplace",
    "EditNotebook",
}
SHELL_TOOLS = {"Bash", "run_terminal_command", "Shell"}
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
# Options that take the next token. -t / --target-directory is the destination.
_ARG_FLAGS = {
    "mv": {"-t", "--target-directory", "-S", "--suffix"},
    "cp": {"-t", "--target-directory", "-S", "--suffix"},
    "ln": {"-t", "--target-directory", "-S", "--suffix"},
    "install": {
        "-t",
        "--target-directory",
        "-m",
        "--mode",
        "-o",
        "--owner",
        "-g",
        "--group",
        "-S",
        "--suffix",
    },
    "mkdir": {"-m", "--mode", "-Z", "--context"},
    "touch": {"-d", "--date", "-r", "--reference", "-t"},
    "tee": set(),
    "rsync": {"-e", "--rsh"},
}
_TARGET_FLAGS = {"-t", "--target-directory"}
# Only these read -t as the destination; touch -t is a time stamp.
_TARGET_COMMANDS = {"mv", "cp", "ln", "install"}
_LAST_DEST = {"mv", "cp", "ln", "install", "rsync"}
# Words that run the command after them.
_WRAPPERS = {"env", "command", "nohup", "time", "exec", "sudo", "builtin"}
_WRAPPER_ARGS = {"sudo": {"-u", "-g", "-C", "-h", "-p"}, "env": {"-u", "-C", "-S"}}
_ALL_DEST = {"mkdir", "touch", "tee"}
_NOT_A_FILE = {"/dev/null", "/dev/stdout", "/dev/stderr", "/dev/fd/1", "/dev/fd/2"}
_REDIRECT = re.compile(r"\d*&>>|\d*&>|\d*>>|\d*>\||\d*>")


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


def _under(path, roots):
    real = os.path.realpath(path)
    return any(real == root or real.startswith(root.rstrip("/") + "/") for root in roots)


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


_HEREDOC = re.compile(r"<<(-?)\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")


def _skip_heredocs(command, i, pending):
    """Index after the bodies of *pending* here-documents, which start at *i* (after a newline)."""
    n = len(command)
    for strip_tabs, word in pending:
        while i < n:
            end = command.find("\n", i)
            end = n if end < 0 else end
            line = command[i:end]
            i = end + 1
            if (line.lstrip("\t") if strip_tabs else line) == word:
                break
    return i


def _split_segments(command):
    parts = []
    buf = []
    i = 0
    n = len(command)
    quote = None
    pending = []  # here-documents whose bodies start after the next newline
    while i < n:
        char = command[i]
        if not quote and command.startswith("<<", i) and not command.startswith("<<<", i):
            heredoc = _HEREDOC.match(command, i)
            if heredoc:
                pending.append((heredoc.group(1) == "-", heredoc.group(3)))
                buf.append(command[i : heredoc.end()])
                i = heredoc.end()
                continue
        if not quote and char == "\n" and pending:
            # the body is data for the command, not commands: skip it
            parts.append("".join(buf))
            buf = []
            i = _skip_heredocs(command, i + 1, pending)
            pending = []
            continue
        if quote:
            buf.append(char)
            if char == "\\" and quote == '"' and i + 1 < n:
                buf.append(command[i + 1])
                i += 2
                continue
            if char == quote:
                quote = None
            i += 1
            continue
        if char in "'\"":
            quote = char
            buf.append(char)
            i += 1
            continue
        if char == "\\" and i + 1 < n:
            buf.append(char)
            buf.append(command[i + 1])
            i += 2
            continue
        if command.startswith("&&", i) or command.startswith("||", i):
            parts.append("".join(buf))
            buf = []
            i += 2
            continue
        if char in ";\n|&":
            parts.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(char)
        i += 1
    if quote:
        return None
    parts.append("".join(buf))
    return parts


def _read_word(text, i):
    n = len(text)
    while i < n and text[i].isspace():
        i += 1
    if i >= n:
        return "", i
    buf = []
    quote = None
    while i < n:
        char = text[i]
        if quote:
            if char == quote:
                quote = None
                i += 1
                continue
            if char == "\\" and quote == '"' and i + 1 < n:
                buf.append(text[i + 1])
                i += 2
                continue
            buf.append(char)
            i += 1
            continue
        if char.isspace() or char in ";&|<>()":
            break
        if char in "'\"":
            quote = char
            i += 1
            continue
        if char == "\\" and i + 1 < n:
            buf.append(text[i + 1])
            i += 2
            continue
        buf.append(char)
        i += 1
    if quote:
        return None
    return "".join(buf), i


def _peel_redirects(segment):
    cleaned = []
    targets = []
    i = 0
    n = len(segment)
    quote = None
    while i < n:
        char = segment[i]
        if quote:
            cleaned.append(char)
            if char == "\\" and quote == '"' and i + 1 < n:
                cleaned.append(segment[i + 1])
                i += 2
                continue
            if char == quote:
                quote = None
            i += 1
            continue
        if char in "'\"":
            quote = char
            cleaned.append(char)
            i += 1
            continue
        if char == "\\" and i + 1 < n:
            cleaned.append(char)
            cleaned.append(segment[i + 1])
            i += 2
            continue
        matched = _REDIRECT.match(segment, i)
        boundary = i == 0 or segment[i - 1].isspace() or segment[i - 1] in ";&|(){}"
        # `echo hi>f` redirects too; only digits inside a word (`a2>f`) are no fd.
        if matched and (boundary or not char.isdigit()):
            j = matched.end()
            if j < n and segment[j] == "&":
                i = j + 1
                while i < n and not segment[i].isspace():
                    i += 1
                continue
            word = _read_word(segment, j)
            if word is None:
                return None
            target, i = word
            if target and target not in _NOT_A_FILE:
                targets.append(target)
            cleaned.append(" ")
            continue
        cleaned.append(char)
        i += 1
    if quote:
        return None
    return "".join(cleaned), targets


def _split_args(args, takes_arg, target_flags=frozenset()):
    positional = []
    targeted = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--":
            positional.extend(args[i + 1 :])
            break
        if arg.startswith("--"):
            name, eq, value = arg.partition("=")
            if name in takes_arg:
                got = value if eq else (args[i + 1] if not eq and i + 1 < len(args) else None)
                if name in target_flags and got:
                    targeted.append(got)
                i += 1 if eq or got is None else 2
                continue
            i += 1
            continue
        if arg.startswith("-") and arg != "-":
            letters = arg[1:]
            consume = False
            for index, letter in enumerate(letters):
                flag = "-" + letter
                if flag not in takes_arg:
                    continue
                rest = letters[index + 1 :]
                if flag in target_flags:
                    if rest:
                        targeted.append(rest)
                    elif i + 1 < len(args):
                        targeted.append(args[i + 1])
                        consume = True
                elif not rest:
                    consume = True
                break
            i += 2 if consume else 1
            continue
        positional.append(arg)
        i += 1
    return positional, targeted


def _inplace_files(args, script_letters, arg_letters, long_script, long_arg):
    """Files a ``sed -i`` / ``perl -i`` edits in place; [] without ``-i``.

    Without an ``-e``/``-f`` style script the first operand is the script.
    """
    files = []
    in_place = False
    script_given = False
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--":
            files.extend(args[i + 1 :])
            break
        if arg.startswith("--"):
            name, eq, _value = arg.partition("=")
            if name == "--in-place":
                in_place = True
            elif name in long_script:
                script_given = True
                i += 0 if eq else 1
            elif name in long_arg and not eq:
                i += 1
        elif arg.startswith("-") and arg != "-":
            for index, letter in enumerate(arg[1:]):
                last = index == len(arg) - 2
                if letter == "i":  # the rest is a backup suffix
                    in_place = True
                    break
                if letter in script_letters:
                    script_given = True
                    i += 1 if last else 0
                    break
                if letter in arg_letters:
                    i += 1 if last else 0
                    break
        else:
            files.append(arg)
        i += 1
    if not in_place:
        return []
    return files if script_given else files[1:]


_VAR = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))")


def _expand(path, variables):
    """*path* with ``$NAME`` / ``${NAME}`` filled in, or None when something stays unknown.

    Names come from assignments earlier in the same command, then the hook's
    environment. A path still holding ``$`` or a backtick cannot be checked
    before the command runs; the stop check sees what it made.
    """

    def fill(match):
        name = match.group(1) or match.group(2)
        value = variables.get(name, os.environ.get(name))
        return match.group(0) if value is None else value

    expanded = _VAR.sub(fill, path)
    return None if "$" in expanded or "`" in expanded else expanded


def _unwrap(argv):
    """*argv* without leading ``VAR=value`` words and wrappers (``env``, ``sudo``, ``nohup`` …)."""
    argv = list(argv)
    while argv:
        word = argv[0]
        if "=" in word and not word.startswith(("-", "=")) and word.split("=", 1)[0].isidentifier():
            argv.pop(0)
            continue
        base = os.path.basename(word)
        if base not in _WRAPPERS:
            break
        argv.pop(0)
        takes = _WRAPPER_ARGS.get(base, set())
        while argv and argv[0].startswith("-") and argv[0] != "-":
            flag = argv.pop(0)
            if flag in takes and argv:
                argv.pop(0)
    return argv


def _command_dests(argv):
    argv = _unwrap(argv)
    if not argv:
        return []
    base = os.path.basename(argv[0])
    args = argv[1:]
    if base == "sed":
        return _inplace_files(args, "ef", "l", {"--expression", "--file"}, {"--line-length"})
    if base == "perl":
        return _inplace_files(args, "eE", "", set(), set())
    if base not in _ARG_FLAGS:
        return []
    targets = _TARGET_FLAGS if base in _TARGET_COMMANDS else frozenset()
    positional, targeted = _split_args(args, _ARG_FLAGS[base], targets)
    if targeted:
        return targeted
    if base in _ALL_DEST:
        return positional
    if base in _LAST_DEST and len(positional) >= 2:
        return [positional[-1]]
    return []


def _next_cwd(argv, cwd):
    positional, _targeted = _split_args(argv[1:], set())
    chosen = [item for item in positional if item != "-"]
    if len(chosen) != 1:
        return cwd
    return _absolute(chosen[0], cwd)


def destinations(command, cwd):
    """Destination paths of a shell command, or None when the command cannot be parsed.

    Only paths that receive a file are returned. ``cd`` changes the base for
    the following segment. A command with no such path returns an empty list.
    """
    segments = _split_segments(command)
    if segments is None:
        return None
    found = []
    here = cwd
    outer = []  # cwd to restore when a `( … )` subshell closes
    variables = {}  # NAME=value set earlier in this command
    for segment in segments:
        peeled = _peel_redirects(segment)
        if peeled is None:
            return None
        cleaned, targets = peeled
        try:
            argv = shlex.split(cleaned, posix=True)
        except ValueError:
            return None
        for target in targets:
            found.append((target, here))
        while argv and argv[0].startswith(("(", "{")):
            if argv[0].startswith("("):
                outer.append(here)
            argv[0] = argv[0][1:]
            if not argv[0]:
                argv.pop(0)
        closing = 0
        while argv and argv[-1].endswith((")", "}")):
            closing += argv[-1].endswith(")")
            argv[-1] = argv[-1][:-1]
            if not argv[-1]:
                argv.pop()
        assigned = 0
        for word in argv:
            name, eq, value = word.partition("=")
            if not eq or not name.isidentifier():
                break
            variables[name] = _expand(value, variables) or value
            assigned += 1
        if argv[assigned:] and os.path.basename(argv[assigned]) == "export":
            for word in argv[assigned + 1 :]:
                name, eq, value = word.partition("=")
                if eq and name.isidentifier():
                    variables[name] = _expand(value, variables) or value
        argv = _unwrap(argv)
        if not argv:
            for _ in range(closing):
                here = outer.pop() if outer else here
            continue
        if os.path.basename(argv[0]) in ("cd", "pushd"):
            moved = [_expand(word, variables) for word in argv]
            here = _next_cwd(moved, here) if None not in moved else here
            for _ in range(closing):
                here = outer.pop() if outer else here
            continue
        if os.path.basename(argv[0]) == "git":
            base = here
            args = argv[1:]
            index = 0
            while index < len(args) and args[index] != "mv":
                if args[index] == "-C" and index + 1 < len(args):
                    base = _absolute(args[index + 1], here)
                    index += 2
                    continue
                index += 1
            if index < len(args) and args[index] == "mv":
                for target in _command_dests(["mv", *args[index + 1 :]]):
                    found.append((target, base))
            continue
        for target in _command_dests(argv):
            found.append((target, here))
        for _ in range(closing):
            here = outer.pop() if outer else here
    seen = set()
    unique = []
    for target, base in found:
        expanded = _expand(target, variables)
        if expanded is None:
            continue
        path = _absolute(expanded, base)
        if path not in seen:
            seen.add(path)
            unique.append(path)
    return unique


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
    if not isinstance(command, str) or not command.strip():
        return None
    if _truncated(event):
        return deny("This command was truncated, so molab cannot check its paths.")
    session = _session(event)
    cwd = _command_cwd(event, data)
    if not _under(cwd, _load_roots(session)):  # one molab call fewer per command
        _note(session, _check_path(cwd, "write", None))
    found = destinations(command, cwd)
    if found is None:
        return None
    refused = None
    for path in found:
        verdict = _check_path(path, "write", None)
        _note(session, verdict)
        if refused is None and verdict and not verdict.get("allowed", True):
            refused = verdict
    return _refusal(refused)


def pre(event):
    tool = _tool(event)
    data = _input(event)
    if tool in SHELL_TOOLS:
        return pre_shell(event, data)
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
