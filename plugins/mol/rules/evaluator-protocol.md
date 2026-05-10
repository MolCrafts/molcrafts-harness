# Evaluator Protocol

Specifies the artifact and verdict shapes that connect the planner
(`/mol:spec`), the generator (`/mol:impl`), and the runtime
evaluators (`/mol:web`, future `/mol:bench` / `/mol:numeric` / …).
The protocol exists so the **driving flow** stays domain-neutral
while runtime evaluators can be added per-domain without re-shaping
the rest of the harness.

This is a **protocol document**, not an enforcement mechanism.
There is no central registry; `/mol:review` does not auto-discover
evaluators. The protocol is a *convention* that orchestrators
(manual user, a future `/mol:loop` skill, or a third-party system
like the user's Symphony orchestrator) can rely on.

## Three artifacts

```
.claude/specs/<slug>.md              ← the spec       (planner output)
.claude/specs/<slug>.acceptance.md   ← the contract   (planner output, sibling)
.claude/specs/<slug>.artifacts/      ← evaluator artifacts (screenshots, logs)
```

- **spec.md** — design, files, tasks, testing strategy. Produced
  by `/mol:spec`. Its `status:` field gates `/mol:impl`.
- **acceptance.md** — the binding "done" contract, also produced
  by `/mol:spec` (validation + acceptance negotiation are folded
  into the same skill). Structured frontmatter so external
  orchestrators can parse it without LLM intervention.
- **artifacts/** — scratch directory for runtime-evaluator output
  (screenshots, console logs, network dumps). Per-criterion
  subdirectories. Cleaned up manually when the spec is closed.

## acceptance.md format

```markdown
---
spec: <slug>                       # must match spec filename without .md
created: YYYY-MM-DD
criteria:
  - id: ac-001
    summary: "<short title, ≤80 chars>"
    type: code | runtime | ui_runtime | scientific | performance | docs
    evaluator_hint: <optional, e.g. "mol:web">
    pass_when: "<single observable condition in plain prose>"
    status: pending | verified | failed     # default pending; updated by impl + evaluators
    last_checked: YYYY-MM-DD                # optional; written when status flips
out_of_scope:
  - "<bullet>"
---

# Acceptance — <slug>

<one paragraph: what "done" means for this spec, in human prose>

## AC-001 — <title>

<expanded reasoning, fixtures, edge cases, links to test files>

(repeat per criterion)
```

### Field semantics

- **`id`** — kebab-case, prefixed `ac-`. Stable identifier within
  a spec lifetime; ids do not renumber on minor refinement. A
  supersede / refine flow that rewrites the spec body restarts
  numbering at `ac-001` because the spec itself is a new design.
- **`type`** — partitions criteria by which evaluator can verify
  them:
  - `code` — static analysis suffices. `/mol:review`'s static
    reviewers (architect, optimizer, documenter, undergrad, pm,
    janitor) handle these.
  - `runtime` — requires executing code (test suite, CLI
    invocation, backend smoke).
  - `ui_runtime` — requires driving a running frontend (Playwright
    via `/mol:web`).
  - `scientific` — requires numerical comparison against reference
    data or analytical solution.
  - `performance` — requires a benchmark with a quantified
    threshold.
  - `docs` — requires inspecting generated documentation
    (cross-references, examples that compile, link integrity).
- **`evaluator_hint`** — soft preference, not a hard binding. The
  user (or an orchestrator) MAY pick a different evaluator if
  available. `mol` does not enforce.
- **`pass_when`** — must be observable: a query you can answer
  yes/no by inspecting the impl, the running system, or an
  artifact. *"Code is well-designed"* is **not** observable;
  *"Reading `Workspace` from a JSON dir produced by v0.4 succeeds
  without errors"* **is**.
- **`status`** — the verification ledger for this criterion. Three
  values:
  - `pending` — never verified, or verified once and the impl has
    since changed in a way that invalidated the verdict (the
    invalidator is responsible for resetting `pending`).
  - `verified` — most-recent verification passed. The criterion
    is "done"; nothing else has to happen for this criterion.
  - `failed` — most-recent verification ran and did not pass.
    The user (or `/mol:fix`) acts on this.

  Defaults to `pending` at spec creation. **Who writes it:**
  - `/mol:spec` writes initial `pending` for every criterion when
    it generates `acceptance.md` (and at supersede / refine).
  - `/mol:impl` writes `verified` / `failed` for `code` and
    `runtime` criteria during Step 7 close-out, based on whether
    the traced test path is green.
  - Runtime evaluator skills (`/mol:web`, future `/mol:bench` /
    `/mol:numeric` / …) write `verified` / `failed` for the
    criterion `type` they handle, after each verification run.

  This is the one **explicit exception** to the "evaluator MUST
  NOT mutate `acceptance.md`" rule below: a runtime evaluator
  MAY update only the `status` and `last_checked` fields on the
  criteria it just verified. Every other field — `id`,
  `summary`, `type`, `evaluator_hint`, `pass_when` — stays
  immutable; only `/mol:spec` rewrites those.

- **`last_checked`** — optional ISO date. Written alongside
  `status` whenever the value flips, so a stale `verified` (e.g.
  the impl changed three weeks ago and nothing re-ran the
  evaluator) is visible at a glance.

### Acceptance lifecycle

`<slug>.acceptance.md` is written by `/mol:spec` at the same time
as `<slug>.md`. The two files always exist together. `/mol:impl`
gates on **both** the spec status (`approved`) **and** the
existence of the acceptance file.

If a supersede / refine flow rewrites the spec body, `/mol:spec`
also regenerates `acceptance.md` from scratch — criteria
negotiated against the old design are not portable.

The spec moves through these statuses:

| spec `status:`  | What it means                                                                    |
|-----------------|----------------------------------------------------------------------------------|
| `draft`         | written but the user deferred approval; `acceptance.md` not yet on disk          |
| `approved`      | user signed off both files; ready for `/mol:impl`                                |
| `in-progress`   | `/mol:impl` is mid-run; tasks ticking off                                        |
| `code-complete` | every `code` / `runtime` criterion is `status: verified`; runtime-evaluator types (`ui_runtime` / `scientific` / `performance` / `docs`) still `pending` — code work is done, runtime verification owed |
| `done`          | every criterion is `status: verified`. **Only this status triggers deletion** of `<slug>.md`, `<slug>.acceptance.md`, and the INDEX entry |

A spec with no runtime-evaluator-typed criteria skips
`code-complete` — `/mol:impl` advances it directly from
`in-progress` to `done` and deletes the artifacts immediately. A
spec that *does* have such criteria parks at `code-complete`;
running `/mol:web` (etc.) flips the relevant criteria to
`verified`; the next `/mol:impl <slug>` (or a future
`/mol:close <slug>` skill) re-checks and advances to `done` only
when all criteria are verified. This is the lifecycle hook that
keeps `acceptance.md` alive long enough for runtime evaluators
to consume it.

The `artifacts/` directory is left for the user to clean (since
impl does not own it).

## Evaluator skill contract

A skill that provides a runtime evaluator MUST:

### Accept

A single argument shaped as `<spec-slug> [criterion-id]`:

- without `criterion-id`: evaluate every criterion the skill can
  handle (matched by `type`).
- with `criterion-id`: evaluate only the named criterion.

The skill reads:

- `.claude/specs/<slug>.md`
- `.claude/specs/<slug>.acceptance.md`
- the implementation under the project root

### Self-skip when prerequisites are absent

If the skill's prerequisites are missing (e.g. no
browser-automation MCP for `/mol:web`, no benchmark harness
configured for a future `/mol:bench`), the skill MUST exit cleanly
with a message naming what is missing — not crash and not pretend
to verify. Detection happens up front, before any acceptance file
is read.

### Return

A markdown block with this shape:

```markdown
## /<plugin>:<skill> — <slug>

| Criterion | Verdict | Evidence |
|-----------|---------|----------|
| ac-001    | ✅ pass | <one line + path to artifact> |
| ac-003    | ❌ fail | <one line + path to artifact> |
| ac-005    | ⏭ skip | <reason — wrong type for this skill> |

### Artifacts

- `<path>` — <what it is>
```

Verdicts MUST be exactly one of `✅ pass`, `❌ fail`, `⏭ skip`. The
evaluator MUST NOT mutate `spec.md`, and MUST NOT mutate any
field of `acceptance.md` **except** the `status` and
`last_checked` fields of the criteria it just verified (per the
`status` field semantics above) — this is the one carved-out
exception so the verification ledger stays current. `id`,
`summary`, `type`, `evaluator_hint`, `pass_when`, and the spec
body are owned by `/mol:spec`.

### Naming convention

The skill SHOULD be `mol:<axis>` so orchestrators can find it by
convention: `/mol:web` for `ui_runtime`, future `/mol:bench` for
`performance`, future `/mol:numeric` for `scientific`. Each
self-skips when its target type is not present in `acceptance.md`.

## Known evaluator skills

| Skill      | Handles `type`     | Prerequisite                                              |
|------------|--------------------|-----------------------------------------------------------|
| `mol:web`  | `ui_runtime`       | A browser-automation MCP (Playwright MCP, claude-in-chrome, …) installed by the user |

Add to this table when a new evaluator skill lands inside `mol`.

## What this protocol is *not*

- **Not an auto-dispatcher.** `/mol:review` does not invoke
  evaluators. It does the static-review job (always available)
  and *suggests* which runtime evaluator to invoke next based on
  `type` fields in `acceptance.md`. A human or external
  orchestrator decides whether to run them.
- **Not a model contract.** Evaluator skills are free to use any
  model, MCP server, or external tool. The contract is over the
  *artifact shape* on input and the *markdown shape* on output.
- **Not a CI integration.** This protocol describes interactive
  evaluation during development. CI hookup is the orchestrator's
  problem.
- **Not a plugin contract.** Runtime evaluators live as `/mol:*`
  skills inside the `mol` plugin (not as separate plugins).
  Plugins are reserved for capability boundaries that justify
  independent versioning and dependency scope (e.g. `mol-agent`
  owns harness lifecycle; `mol-plugin` owns marketplace
  maintenance). Evaluators are just procedures that consume a
  shared artifact and emit a shared verdict shape — they do not
  warrant their own plugin scope.
