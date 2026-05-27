---
description: "Frontend runtime evaluator — starts the project's dev server and verifies `type: ui_runtime` criteria from `<slug>.acceptance.md` by driving the running app through whatever Playwright MCP is installed. Use after `/mol:impl` parks a spec at `code-complete` with pending UI criteria; skips cleanly when no Playwright tools are available."
argument-hint: "<spec-slug> [<criterion-id>]"
---

# /mol:web — Frontend Runtime Evaluator

Verify `ui_runtime` acceptance criteria against a running app. Runtime half of the harness (`/mol:review` covers static).

## Detect (run only when applicable)

Both must hold:

- spec has ≥1 `ui_runtime` criterion in `<slug>.acceptance.md`
- a Playwright-capable MCP server is reachable. Tool prefixes: `mcp__plugin_playwright_*`, `mcp__claude-in-chrome__*`, or any other browser-automation MCP. **`mol` does not bundle one.**

No `ui_runtime` criteria → *"no `ui_runtime` criteria for `<slug>` — nothing to do"* and stop.

`ui_runtime` criteria exist but no Playwright MCP → *"no browser-automation MCP installed; install one (e.g. official Playwright MCP) and re-run, or verify these criteria manually"* — list criteria — and stop. Don't shell out to `npx playwright`; this skill operates strictly through MCP.

## Procedure

### 1. Resolve the slug

`$ARGUMENTS` parses as `<slug> [<criterion-id>]`. Read CLAUDE.md → resolve `$META.specs_path` (default `.claude/specs/`).

Read:

- `{$META.specs_path}{slug}.md`
- `{$META.specs_path}{slug}.acceptance.md`

Either missing → stop. Tell user spec is not approved; run `/mol:spec <slug>`.

### 2. Filter criteria

Parse `criteria:` from acceptance frontmatter. Working set:

- `<criterion-id>` given: only that one (refuse if `type` not `ui_runtime`)
- otherwise: every `type: ui_runtime`

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

Then **update `acceptance.md`** for each criterion verified (carved-out exception in `plugins/mol/rules/evaluator-protocol.md` § *Field semantics*):

- `✅ pass` → `status: verified`
- `❌ fail` → `status: failed`
- `⏭ skip` → leave `status` unchanged

Set `last_checked: <today's ISO date>` alongside any flipped status. **Touch only `status` and `last_checked`** on criteria handled in this run — every other field (`id`, `summary`, `type`, `evaluator_hint`, `pass_when`) and unhandled criteria are immutable. Don't rewrite spec body, reorder, or add/remove ids.

End with one-line summary: *"<slug>: 4 ui_runtime criteria, 3 pass, 1 fail. acceptance.md updated. Re-run `/mol:impl <slug>` to advance to `done` (or fix the failure first). See artifacts under .claude/specs/<slug>.artifacts/."*

### 6. Cleanup

Stop the dev server started in Step 3:

```
kill <PID>
```

Always run cleanup, even on skip/fail, so half-finished evaluation doesn't leave a zombie. Skill is sole owner of this PID — Step 3 always starts its own server.

## Guardrails

- **Read-only on source.** Never edits code. On `fail`, user (or orchestrator) decides whether to feed back into `/mol:fix` or `/mol:spec`.
- **Write-narrow on `acceptance.md`.** May only update `status` and `last_checked` on just-evaluated criteria, per evaluator-protocol exception. Never edit spec body or other fields. Never delete acceptance file — that's `/mol:impl` at `done`.
- **Artifacts under specs/, not docs/.** Artifacts are scratch — delete when spec is closed (`/mol:impl` Step 7 deletes spec; deleting `.artifacts/` is manual cleanup, since impl doesn't know about runtime artifacts by design).
- **No auto-loop.** On fail, do not re-run after a code change. Loop-back decision belongs to orchestrator.
- **Browser dialog hazard.** Avoid clicking elements that trigger native `alert/confirm/prompt` without first acknowledging the user — they block the session and break the next criterion.

## Why this lives in `mol`

`/mol:web` doesn't bundle Playwright (consumes whatever browser-automation MCP user installed); only asset is this procedure plus `playwright-evaluator` agent — fits inside `mol` as sibling to `/mol:review`, behind self-detect gate. Other runtime evaluators under same shape (`/mol:bench`, future `mol:numeric`, …) follow `plugins/mol/rules/evaluator-protocol.md`.
