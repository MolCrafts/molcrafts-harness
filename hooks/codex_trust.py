"""Trust the harness's Codex hooks, through Codex's own app-server.

Codex runs a hook only after a person has trusted its exact definition
(`hooks.state.<key>.trusted_hash` in the user's config.toml). An unattended
Codex — a subagent, `codex exec`, an app-server client — never asks, so an
untrusted guard is silently skipped. Run this once after installing or
updating the harness, from a directory inside the workspace:

    python3 hooks/codex_trust.py            # list the guard hooks and their trust
    python3 hooks/codex_trust.py --yes      # trust the ones that are not trusted

Only hooks whose command contains a ``--match`` (default ``molab_guard.py``)
are touched; nothing else in config.toml changes. The hash written is the
one Codex reports for the hook's current definition, so editing the hook
makes Codex ask again.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys


class AppServer:
    """A minimal JSON-RPC client for `codex app-server --stdio`."""

    def __init__(self, codex: str) -> None:
        self._process = subprocess.Popen(
            [codex, "app-server", "--stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        self._next = 0

    def request(self, method: str, params: dict) -> dict:
        self._next += 1
        ident = self._next
        self._send({"jsonrpc": "2.0", "id": ident, "method": method, "params": params})
        assert self._process.stdout is not None
        for line in self._process.stdout:
            message = json.loads(line)
            if message.get("id") != ident or "method" in message:
                continue
            if "error" in message:
                raise RuntimeError(f"{method}: {message['error'].get('message')}")
            return message.get("result") or {}
        raise RuntimeError(f"{method}: codex app-server closed the connection")

    def notify(self, method: str) -> None:
        self._send({"jsonrpc": "2.0", "method": method})

    def close(self) -> None:
        if self._process.stdin:
            self._process.stdin.close()
        self._process.wait(timeout=10)

    def _send(self, message: dict) -> None:
        assert self._process.stdin is not None
        self._process.stdin.write(json.dumps(message) + "\n")
        self._process.stdin.flush()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--cwd", action="append", help="directory whose hooks to inspect (repeatable; default: here)")
    parser.add_argument(
        "--match",
        action="append",
        help="trust only hooks whose command contains this (repeatable; default: molab_guard.py)",
    )
    parser.add_argument("--yes", action="store_true", help="write the trust; without it, only list")
    parser.add_argument("--codex", default=os.environ.get("CODEX_BIN") or shutil.which("codex"), help="codex executable")
    args = parser.parse_args()
    if not args.codex:
        print("codex is not on PATH; pass --codex or set CODEX_BIN", file=sys.stderr)
        return 2
    cwds = [os.path.abspath(path) for path in (args.cwd or [os.getcwd()])]
    matches = args.match or ["molab_guard.py"]

    server = AppServer(args.codex)
    try:
        server.request("initialize", {"clientInfo": {"name": "molab-guard", "title": None, "version": "1"}, "capabilities": {"experimentalApi": False, "requestAttestation": False}})
        server.notify("initialized")
        listed = server.request("hooks/list", {"cwds": cwds})
        guard = {}
        for entry in listed.get("data", []):
            for problem in entry.get("errors", []) + entry.get("warnings", []):
                print(f"codex: {problem}", file=sys.stderr)
            for hook in entry.get("hooks", []):
                if hook.get("handlerType") == "command" and any(match in hook.get("command", "") for match in matches):
                    guard[hook["key"]] = hook
        if not guard:
            print(f"no Codex hook runs any of {matches} here; install the harness plugin or project hooks first")
            return 1
        pending = {}
        for key, hook in sorted(guard.items()):
            print(f"{hook['trustStatus']:>9}  {hook['eventName']:<14} {key}")
            if hook["trustStatus"] in {"untrusted", "modified"}:
                pending[key] = {"trusted_hash": hook["currentHash"]}
        if not pending:
            print("every guard hook is trusted")
            return 0
        if not args.yes:
            print(f"{len(pending)} hook(s) not trusted; rerun with --yes to trust them")
            return 1
        server.request("config/value/write", {"keyPath": "hooks.state", "value": pending, "mergeStrategy": "upsert"})
        print(f"trusted {len(pending)} hook(s)")
        return 0
    finally:
        server.close()


if __name__ == "__main__":
    sys.exit(main())
