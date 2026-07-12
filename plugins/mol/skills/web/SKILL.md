---
description: "Frontend runtime evaluator — starts the project's dev server and verifies the spec body's non-binding `## UI verification` checks (plus legacy `type: ui_runtime` acceptance criteria from older specs) by driving the running app through whatever Playwright MCP is installed. Ad-hoc and advisory — UI checks no longer gate spec close; skips cleanly when no Playwright tools are available."
argument-hint: "<spec-slug> [<criterion-id>]"
---

# /mol:web — Frontend Runtime Evaluator

Verify UI checks against a running app. Runtime half of the harness (`/mol:review` covers static). Since 2026-06, UI checks live in the spec body's **`## UI verification`** section and are **non-binding** — they never appear in `acceptance.md` and never park a spec at `code-complete`; this skill is run ad hoc. Legacy specs (pre-2026-06) may still carry `type: ui_runtime` acceptance criteria; those are handled too, with the old ledger semantics.

## Detect (run only when applicable)

Both must hold:

- spec has ≥1 UI check — a `## UI verification` section in `<slug>.md`, or legacy `type: ui_runtime` criteria in `<slug>.acceptance.md`
- a Playwright-capable MCP server is reachable. Tool prefixes: `mcp__plugin_playwright_*`, `mcp__claude-in-chrome__*`, or any other browser-automation MCP. **`mol` does not bundle one.**

No UI checks anywhere → *"no UI verification checks for `<slug>` — nothing to do"* and stop.

UI checks exist but no Playwright MCP → *"no browser-automation MCP installed; install one (e.g. official Playwright MCP) and re-run, or verify these checks manually"* — list checks — and stop. Don't shell out to `npx playwright`; this skill operates strictly through MCP.

## Procedure

### 1. Resolve the slug

`$ARGUMENTS` parses as `<slug> [<criterion-id>]`. Read CLAUDE.md → resolve `$META.specs_path` (default `.claude/specs/`).

Read:

- `{$META.specs_path}{slug}.md`
- `{$META.specs_path}{slug}.acceptance.md`

Either missing → stop. Tell user spec is not approved; run `/mol:spec <slug>`.

### 2. Build the working set

Two sources, merged:

- **Spec-body checks (current convention)** — bullets under `## UI verification` in `<slug>.md`. Assign synthetic ids `ui-001`, `ui-002`, … in document order; each bullet's text is its `pass_when`. Non-binding — results are reported, never written anywhere.
- **Legacy acceptance criteria** — every `type: ui_runtime` entry in the acceptance frontmatter, keeping its `ac-NNN` id. Binding for that old spec; ledger update applies (§ 5).

`<criterion-id>` given: only that one (refuse if it is neither a `ui-NNN` body check nor a `ui_runtime` acceptance criterion).

Empty working set → see § Detect.

### 3. Start the dev server and resolve the URL from its banner

This skill always boots its own dev server. No "probe a URL the user might already have running" — ambiguous (can't tell whose process answered) and the printed banner is the only source of truth for the actual URL (dev servers fall back to different ports when the configured one is busy).

Read `mol_project.dev` from CLAUDE.md (§ Project configuration below). If `command` + `ready_pattern` + `url_pattern` not all set, stop and tell user to declare them. Don't invent commands — CLAUDE.md is source of truth.

Show user the working set (id + summary + pass_when, one line each) and configured `dev.command`. Then:

1. Run `dev.command` in background; capture combined stdout/stderr to `/tmp/mol-web-<slug>.log`. Record PID for Step 6 cleanup.
2. Tail log every 1 s; consider server ready when `ready_pattern` appears, bounded by `ready_timeout` (default 90 s).
3. Parse actual URL from ready line using `url_pattern` regex.
4. Probe parsed URL with browser-automation MCP `navigate`, 5 s timeout. On success → Step 4. On failure or `ready_timeout` → kill PID, stop, point user at log file.

> **Remote dev server.** This skill is for dev servers it owns end-to-end. For long-running dev servers started outside `mol` (remote box, `tmux`, sidecar container), use the browser MCP directly, or add `mol_project.dev.remote_url` mode in a future iteration.

## Project configuration

Project-agnostic; everything project-specific lives in CLAUDE.md under `mol_project.dev`. Project that wants `/mol:web` to work must declare `command` + `ready_pattern` + `url_pattern` — all three required.

```yaml
mol_project:
  dev:
    # required: shell command that boots the dev server
    command: <project-specific shell command>

    # required: log line substring meaning "server is now listening"
    ready_pattern: <project-specific marker>

    # required: regex with one capture group extracting actual URL from
    # ready line (dev server, not CLAUDE.md, decides URL — may pick a
    # different port than configured)
    url_pattern: <project-specific regex>

    # optional: seconds to wait for ready_pattern before giving up
    ready_timeout: 90
```

### 4. Delegate per criterion

For each criterion in working set, delegate to `playwright-evaluator` agent with criterion verbatim plus target URL. Agent translates `pass_when` into navigate / interact / observe / assert sequence; returns:

- verdict (`✅ pass` / `❌ fail` / `⏭ skip`)
- one-line evidence
- artifact paths (screenshots, console dump) under `.claude/specs/<slug>.artifacts/<criterion-id>/`

Run delegations **sequentially** — Playwright sessions interfere when run concurrently against same target.

### 5. Aggregate, emit, update acceptance ledger

Print verdict in evaluator-protocol shape:

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

Then, **for legacy `ac-NNN` criteria only**, update `acceptance.md` per `plugins/mol/rules/evaluator-protocol.md` § *Ledger write-back* (pass → verified, fail → failed, skip → unchanged; `last_checked` beside any flip; touch nothing else — don't rewrite spec body, reorder, or add/remove ids).

Spec-body `ui-NNN` checks are advisory: report the verdicts, write **nothing** back to spec or acceptance — they never gate close.

End with one-line summary: *"<slug>: 4 UI checks, 3 pass, 1 fail (advisory). See artifacts under .claude/specs/<slug>.artifacts/."* — append *"acceptance.md updated; re-run `/mol:impl <slug>` to advance"* only when legacy criteria were flipped.

### 6. Cleanup

Stop the dev server started in Step 3:

```
kill <PID>
```

Always run cleanup, even on skip/fail, so half-finished evaluation doesn't leave a zombie. Skill is sole owner of this PID — Step 3 always starts its own server.

## Guardrails

- **Read-only on source.** Never edits code. On `fail`, user (or orchestrator) decides whether to feed back into `/mol:fix` or `/mol:spec`.
- **Write-narrow on `acceptance.md`, legacy criteria only.** May only update `status` and `last_checked` on just-evaluated legacy `ui_runtime` criteria, per evaluator-protocol § *Ledger write-back*. Spec-body `ui-NNN` checks write nothing. Never edit spec body or other fields. Never delete acceptance file — that's `/mol:close` at `done`.
- **Artifacts under specs/, not docs/.** Artifacts are scratch — delete when spec is closed (`/mol:impl` Step 7 deletes spec; deleting `.artifacts/` is manual cleanup, since impl doesn't know about runtime artifacts by design).
- **No auto-loop.** On fail, do not re-run after a code change. Loop-back decision belongs to orchestrator.
- **Browser dialog hazard.** Avoid clicking elements that trigger native `alert/confirm/prompt` without first acknowledging the user — they block the session and break the next criterion.

## Why this lives in `mol`

`/mol:web` doesn't bundle Playwright (consumes whatever browser-automation MCP user installed); only asset is this procedure plus `playwright-evaluator` agent — fits inside `mol` as sibling to `/mol:review`, behind self-detect gate. Other runtime evaluators under same shape (`/mol:bench`, future `mol:numeric`, …) follow `plugins/mol/rules/evaluator-protocol.md`.
