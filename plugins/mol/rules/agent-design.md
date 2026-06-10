# Agent design — producer vs reviewer split

This document explains why some `mol` agents are write-capable and
others are read-only. The asymmetry is principled, not accidental.

## Two-layer model

`mol` separates concerns across two layers:

| Layer | Who | Job |
|---|---|---|
| **Skill** (`plugins/mol/skills/<name>/SKILL.md`) | the orchestrator | parses arguments, fans out, gates with build/test, applies patches, reverts on regression, decides routing |
| **Agent** (`plugins/mol/agents/<name>.md`) | the single-axis specialist | reads code, produces findings or content along *one* axis, returns text |

Skills compose agents. Agents do not compose skills, and do not
call other agents — the skill is the only orchestrator
(design-principles rule O2).

## Producer vs reviewer

The agents fall into two kinds, distinguished by **what their
primary output is**:

### Producer agents

Their primary deliverable is **content** — markdown, code, or
artifacts — not findings. They split into two sub-kinds by where
the persistence happens:

#### Producer-write (own write tools)

Persist the artifact themselves. Use when there is no
user-approval gate between drafting and persisting.

| Agent | Produces | Why writing belongs in the agent |
|---|---|---|
| `tester` | test code (RED tests) | the produced test *is* the verification mechanism — running it is the gate. No external orchestration needed for the write itself. |
| `implementer` | production source (one spec task / one fix patch) | the RED test written by `tester` *is* the gate for the write — the same mechanism that justifies `tester`'s write access; the calling skill still runs the full-suite gate and owns revert. |
| `documenter` | docstrings + tutorials | docs don't change runtime behavior — zero behavioral risk. |
| `playwright-evaluator` | screenshots / console / network logs | artifacts are evaluation by-products, not source-of-truth code. |

#### Producer-return (no write tools)

Draft the artifact and return it as text; the orchestrating
skill persists after a gate (user approval, acceptance check).
Use when the artifact must be reviewable before it lands on
disk.

| Agent | Produces | Why the skill writes, not the agent |
|---|---|---|
| `spec-writer` | spec body + acceptance.md | the spec is the binding contract for an entire feature — it must pass user approval (`/mol:spec` Step 6) before being persisted. The agent returns the draft; the skill negotiates and writes. |

### Reviewer agents (read-only)

Their primary deliverable is **findings about content** —
`<emoji> file:line — message` tuples. Applying findings as patches
is workflow-level work that needs build/test gates, regression
revert, and cross-cutting judgment — that's skill-layer concerns.

| Agent | Reviews | Write-mode counterpart skill |
|---|---|---|
| `architect` | module boundaries / layer rules | `/mol:refactor` (with architect pre/post check) |
| `debugger` | failure root cause + fix recommendation | `/mol:fix` (applies the recommendation; debugger never patches) |
| `optimizer` | perf anti-patterns | `/mol:fix` (perf-driven fix) |
| `scientist` | equations / units / refs | `/mol:fix` (corrected math) or `/mol:spec` (refine derivation) |
| `compute-scientist` | numerical stability / HPC | `/mol:fix` (with regression test from `tester`) |
| `pm` | public-API ergonomics / breaking change | `/mol:refactor` (with deprecation path) |
| `undergrad` | new-user friction | `/mol:docs` (Mode B tutorial) or `/mol:fix` (error message) |
| `user` | doc-first learnability + cross-library composition (no glue) | `/mol:docs` (fix/complete docs) or `/mol:spec` (close a composition seam) |
| `web-design` | visual / a11y / state coverage | `/mol:fix` (one fix per finding) |
| `security-reviewer` | attack surface | `/mol:fix` (sanitize / parameterize / authorize) |
| `ffi-guard` | FFI-boundary safety | `/mol:fix` (error-code path, handle conversion) or `/mol:spec` (API-shape change) |
| `janitor` | hygiene / tech debt | **`/mol:simplify`** (the dedicated cleanup applier) |
| `ci-guard` | CI parity | **`/mol:ci-sync`** (config parity repair) / `/mol:fix` / `/mol:impl` per the agent's `Suggested agent:` route |
| `librarian` | spec-time placement + reuse consult (fixed advisory report) | n/a — advice consumed by `/mol:spec`; the blueprint it reads is refreshed by `/mol:map` |
| `reviewer` | aggregator (findings → table + verdict) | n/a — itself a reviewer over reviewers |

## Why not let `optimizer` or `janitor` write?

Three reasons, in priority order:

1. **The patch isn't 1:1 with the finding.** A perf finding "this
   loop should vectorize" maps to many possible patches —
   `np.einsum` vs explicit broadcasting vs migrating to
   `numba` — and the right choice depends on benchmark numbers,
   call-site context, and whether the test suite has a perf
   guard. That's orchestration.

2. **The apply step needs a gate.** Every behavior-affecting
   change must run `$META.build.test` and revert on regression.
   That's a skill-level loop. Letting an agent own the loop
   conflates "expert in axis X" with "expert in our build
   system."

3. **Two layers is easier to test and refactor.** Single-axis
   agents have a stable contract (input: scope; output:
   findings). Skills can be rewritten without touching agents,
   and vice versa. Adding write capability inside agents would
   couple the layers.

## Why is `tester` the exception?

A test is **its own verification**. Writing a test does not
require the orchestrator to ask "did we regress?" — the test
*is* the regression check. So the "needs a build/test gate"
argument doesn't apply to test files specifically.

Same shape for `documenter` (docs don't affect runtime, so no
gate needed) and `playwright-evaluator` (artifacts are
evaluation outputs, not source).

`implementer` extends the same argument to production code:
unlike a reviewer finding, a spec task *is* 1:1 with its patch,
and the gate already exists — the RED test written by `tester`
plus the calling skill's full-suite gate. The skill still owns
tick, commit, and revert; `implementer` never does any of the
three.

## Adding a new agent

When proposing a new agent, decide which kind it is by walking
two questions in order:

1. **What is the primary output?**
   - findings about content → reviewer (no write tools)
   - content itself (markdown / code / artifacts) → producer
2. **(producer only) Is there a user-approval gate before
   persistence?**
   - no gate → **producer-write** (gets `Write/Edit` tools)
   - yes gate → **producer-return** (no write tools; returns
     text, skill persists after the gate)

If you find yourself writing "and then it applies the fix,"
stop. That's a skill, not an agent.

A producer-return agent is the right move when the content is
load-bearing (a spec, a public API contract, a release
changelog) and a draft-then-review loop is unavoidable.
Letting the agent write directly would mean the user reviews
*after* the file lands — wrong polarity.

## Adding a new skill

When proposing a new skill, decide whether it's:

- An **applier** for an existing reviewer agent → mirrors the
  agent's axis (e.g. `/mol:simplify` ↔ `janitor`).
- An **orchestrator** that composes multiple agents → fan-out +
  aggregator pattern (e.g. `/mol:review`).
- A **gate** → read-only check that returns PROCEED / BLOCK
  (e.g. `/mol:ship`).
- A **runtime evaluator** → drives a live system to verify
  acceptance criteria (e.g. `/mol:web`).

The git-workflow skills (`/mol:commit`, `/mol:push`, `/mol:pr`,
`/mol:tag`) are a fifth kind — workflow-state mutators that
chain into gates.

Model-tier assignment per agent kind (opus / sonnet / haiku) lives
in `plugins/mol/rules/model-policy.md`.
