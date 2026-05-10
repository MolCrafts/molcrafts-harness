---
description: Frontend runtime evaluator. Reads `<slug>.acceptance.md` from `.claude/specs/`, filters criteria of `type: ui_runtime`, starts the project's dev server via `mol_project.dev.command`, parses the URL from its ready banner, then verifies each criterion by driving the running web app through whatever Playwright MCP server / browser-automation plugin the user has installed. Returns a verdict per the evaluator-protocol contract. Read-only on source code; writes only artifact files (screenshots, console dumps) under `.claude/specs/<slug>.artifacts/`. Skip cleanly when no Playwright tools are available.
argument-hint: "<spec-slug> [<criterion-id>]"
---

# /mol:web — Frontend Runtime Evaluator

Verify `ui_runtime` acceptance criteria against a running
application. This is the runtime half of the harness — `/mol:review`
covers the static half — so projects that ship a UI can close the
loop end-to-end.

## Detect (run only when applicable)

This skill is meaningful only when **both** of the following hold:

- The spec has at least one `ui_runtime` criterion in
  `<slug>.acceptance.md`.
- A Playwright-capable MCP server is reachable in this session.
  Look for any of these tool prefixes: `mcp__plugin_playwright_*`,
  `mcp__claude-in-chrome__*`, or any other browser-automation MCP
  the user has installed. **`mol` does not bundle one** — the user
  installs whichever Playwright MCP / plugin they prefer.

If no `ui_runtime` criteria exist, return *"no `ui_runtime`
criteria for `<slug>` — nothing to do"* and stop.

If `ui_runtime` criteria exist but no Playwright MCP is available,
return *"no browser-automation MCP installed; install one (e.g.
the official Playwright MCP) and re-run, or verify these
criteria manually"* — list the criteria — and stop. Do not try to
shell out to `npx playwright`; this skill operates strictly through
MCP.

## Procedure

### 1. Resolve the slug

`$ARGUMENTS` parses as `<slug> [<criterion-id>]`. Read CLAUDE.md
to resolve `$META.specs_path` (default `.claude/specs/`).

Read:

- `{$META.specs_path}{slug}.md` — the spec.
- `{$META.specs_path}{slug}.acceptance.md` — the contract.

If either is missing, stop. Tell the user the spec is not approved
yet — they should run `/mol:spec <slug>`.

### 2. Filter criteria

Parse `criteria:` from the acceptance frontmatter. Build the
working set:

- if `<criterion-id>` given: only that one (refuse if its `type`
  is not `ui_runtime`; explain that this skill handles only that
  type).
- otherwise: every criterion with `type: ui_runtime`.

If the working set is empty, see § Detect above.

### 3. Start the dev server and resolve the URL from its banner

This skill always boots its own dev server. There is no "probe a
URL the user might already have running" shortcut — that path is
ambiguous (you can't tell whose process answered) and the printed
banner is the only source of truth for the actual URL anyway
(many dev servers fall back to a different port when the
configured one is busy, e.g. "port 3000 in use, using port 3001").

Read the `mol_project.dev` block from CLAUDE.md (defined below
under § Project configuration). If `command` + `ready_pattern` +
`url_pattern` are not all set, stop and tell the user to declare
them. Do not invent a command — CLAUDE.md is the source of truth
for project-specific HOW.

Show the user the working set (id + summary + pass_when, one line
each) and the configured `dev.command`. Then:

1. Run `dev.command` in the background, capturing combined
   stdout/stderr to a log file under `/tmp/mol-web-<slug>.log`.
   Record the PID for Step 6 cleanup.
2. Tail the log every 1 s; consider the server ready as soon as
   the configured `ready_pattern` appears, bounded by
   `ready_timeout` (default 90 s).
3. Parse the actual URL from the ready line using the configured
   `url_pattern` regex.
4. Probe the parsed URL with the browser-automation MCP
   `navigate` tool, 5 s timeout. On success, continue to Step 4.
   On failure or `ready_timeout`, kill the PID, stop, and tell
   the user the auto-start command did not produce a reachable
   URL — point them at the captured log file for triage.

> **Remote dev server.** This skill is for dev servers it owns
> end-to-end. For a long-running dev server started outside `mol`
> (remote box, `tmux` session, sidecar container), use the browser
> MCP directly, or add a `mol_project.dev.remote_url` mode in a
> future iteration.

## Project configuration

This skill is project-agnostic; everything project-specific lives
in CLAUDE.md under `mol_project.dev`. A project that wants
`/mol:web` to work must declare `command` + `ready_pattern` +
`url_pattern` — all three are required.

```yaml
mol_project:
  dev:
    # required: the shell command that boots the dev server.
    # the skill never invents commands.
    command: <project-specific shell command that boots the dev server>

    # required: log line substring that means "the server is now listening"
    ready_pattern: <project-specific marker, e.g. a server's banner string>

    # required: regex with one capture group that extracts the actual
    # URL from the ready line (the dev server, not CLAUDE.md, decides
    # the URL — it may pick a different port than configured)
    url_pattern: <project-specific regex>

    # optional: seconds to wait for ready_pattern before giving up
    ready_timeout: 90
```

Per-project because dev-server stacks, workspace layouts, banner
strings, and mock-vs-live backends all vary; the skill states the
intent (start, parse banner, navigate, evaluate, clean up) and
each project spells out its own HOW.

### 4. Delegate per criterion

For each criterion in the working set, delegate to the
`playwright-evaluator` agent with the criterion verbatim plus the
target URL. The agent translates `pass_when` into a navigate /
interact / observe / assert sequence and returns:

- a verdict (`✅ pass` / `❌ fail` / `⏭ skip`)
- one-line evidence
- artifact paths (screenshots, console dump) under
  `.claude/specs/<slug>.artifacts/<criterion-id>/`

Run the per-criterion delegations **sequentially** (not in
parallel) — Playwright sessions interfere when run concurrently
against the same target.

### 5. Aggregate, emit, and update the acceptance ledger

Print the verdict in the evaluator-protocol shape:

```markdown
## /mol:web — <slug>

| Criterion | Verdict | Evidence |
|-----------|---------|----------|
| ac-004    | ✅ pass | first paint at 142ms (target <200ms) → screenshot |
| ac-005    | ❌ fail | error toast did not appear after save 500 → screenshot + console |

### Artifacts

- `.claude/specs/<slug>.artifacts/ac-004/state.png`
- `.claude/specs/<slug>.artifacts/ac-005/before.png`
- `.claude/specs/<slug>.artifacts/ac-005/after.png`
- `.claude/specs/<slug>.artifacts/ac-005/console.log`
```

Then **update `acceptance.md`** for each criterion this run
verified (the carved-out exception in
`plugins/mol/rules/evaluator-protocol.md` § *Field semantics*):

- `✅ pass` → set `status: verified`
- `❌ fail` → set `status: failed`
- `⏭ skip` → leave `status` unchanged (this skill did not
  produce a verdict for that criterion)

Set `last_checked: <today's ISO date>` alongside any flipped
status. **Touch only `status` and `last_checked`** on the
criteria handled in this run — every other field (`id`,
`summary`, `type`, `evaluator_hint`, `pass_when`) and every
criterion this skill did not handle are immutable. Do not
rewrite the spec body, do not reorder criteria, do not add or
remove ids.

End with a one-line user-facing summary: *"<slug>: 4 ui_runtime
criteria, 3 pass, 1 fail. acceptance.md updated. Re-run
`/mol:impl <slug>` to advance to `done` (or fix the failure
first). See artifacts under .claude/specs/<slug>.artifacts/."*

### 6. Cleanup

Stop the dev server started in Step 3:

```
kill <PID>
```

Always run cleanup, even on a skip / fail verdict, so a
half-finished evaluation does not leave a zombie dev server. The
skill is the sole owner of this PID — Step 3 always starts its
own server, so there is no "user's server, leave it alone" branch
to worry about.

## Guardrails

- **Read-only on source.** This skill never edits code. If a
  verdict is `fail`, it is the user's (or orchestrator's) job to
  decide whether to feed the failure back into `/mol:fix` or
  `/mol:spec` (refine the criterion).
- **Write-narrow on `acceptance.md`.** This skill MAY only
  update `status` and `last_checked` on the criteria it just
  evaluated, per the evaluator-protocol exception. Never edit
  the spec body, never touch other fields. Never delete the
  acceptance file — that is `/mol:impl`'s job at `done`.
- **Artifacts under specs/, not docs/.** Artifacts are scratch —
  delete them when the spec is closed (`/mol:impl` Step 7 deletes
  the spec; deleting `.artifacts/` is a manual cleanup the user
  can run, since impl does not know about runtime artifacts by
  design).
- **Do not auto-loop.** If a criterion fails, do not re-run after
  a code change. The harness pattern explicitly leaves the
  loop-back decision to the orchestrator.
- **Browser dialog hazard.** Per the Playwright MCP guidance,
  avoid clicking elements that trigger native `alert/confirm/prompt`
  dialogs without first acknowledging the user — they block the
  session and break the next criterion.

## Why this lives in `mol`

`mol:web` doesn't bundle Playwright (it consumes whatever
browser-automation MCP the user installed), so its only asset is
this procedure plus the `playwright-evaluator` agent — fits
inside `mol` as a sibling to `/mol:review`, behind a self-detect
gate. Other runtime evaluators planned under the same shape
(future `/mol:bench`, future `/mol:numeric`, …) follow
`plugins/mol/rules/evaluator-protocol.md`.
