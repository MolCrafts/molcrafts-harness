# Model Policy — Conversation Modes and Agent Tiers

Which model runs each layer of the two-layer model
(`rules/design-principles.md` § 2). The main conversation always runs
the session model — the top tier available (Fable class). Agents pin
their tier explicitly in frontmatter so cost/quality routing survives
session-model changes.

## Two conversation modes

| Mode | Deliverable | Who authors the deliverable | Subagents do |
|---|---|---|---|
| **Advisor** (顾问模式) | words — an answer, plan, verdict, or diagnosis | the main conversation (session model, top tier) | gather evidence only |
| **Orchestration** (编排模式) | artifacts — code, docs, specs, commits | opus-class producer agents | author the artifacts |

- Advisor skills: `/mol:discuss`, `/mol:grill`, `/mol:debug`,
  `/mol:review`, `/mol:test`, `/mol:ship`, `/mol:litrev`, `/mol:note`,
  `/mol:map`. The judgment in the deliverable is the top model's own;
  reviewer agents feed it findings.
- Orchestration skills: `/mol:spec`, `/mol:impl`, `/mol:impl-all`,
  `/mol:fix`, `/mol:refactor`, `/mol:docs`, `/mol:simplify`, and the
  git chain. The main loop plans, routes, gates, and verifies.

A skill's mode follows its deliverable, not a flag. A skill that both
answers and writes (e.g. `/mol:spec`) is orchestration: the persisted
artifact is the deliverable.

## The main-loop rule

In orchestration mode the main conversation plans, routes, gates
(build/test), verifies, and reverts — it MUST NOT author production
source code. Artifact writing is delegated to a producer agent:
`implementer` for production code, `tester` for tests, `documenter`
for docs, `spec-writer` for spec drafts.

*Exception:* mechanical, reviewer-flagged deletions/reverts applied
under a test gate (e.g. `/mol:simplify`'s batch) may stay in the main
loop — the cost of delegation exceeds the judgment involved.

Rationale: the session model's context is the orchestration state —
plans, gate results, routing decisions. Mixing authored code into it
degrades both, and the strongest model's time is best spent on the
decisions only it can make.

## Three tiers

| Tier (`model:`) | Agents | Why |
|---|---|---|
| `opus` | architect, scientist, compute-scientist, debugger, security-reviewer, optimizer, pm, librarian, undergrad, user, web-design, spec-writer, tester, documenter, implementer | judgment: design trade-offs, diagnosis, adversarial reasoning, artifact authorship |
| `sonnet` | ci-guard, playwright-evaluator, reviewer, janitor | mechanical: run tools, aggregate findings, pattern-match against fixed catalogs |
| `haiku` | `/mol:impl-all` § 2b completion evaluator (prose-dispatched — no agent file) | binary ledger read against a fixed schema |

`model: inherit` is not used under `plugins/mol/agents/` — every
shipped agent pins its tier. (Project-local agents scaffolded by
`/mol:bootstrap` are outside this policy.)

## Tier-decision procedure (for future agents)

1. Does the agent produce or judge content requiring domain reasoning
   — design trade-offs, root cause, security, science, code authorship?
   → `opus`.
2. Is its output determined by running tools plus a fixed rule catalog
   — lint trio, CI config, verdict aggregation, scripted browser steps?
   → `sonnet`.
3. Is it a schema-shaped read-and-classify with no judgment?
   → `haiku`, and prefer prose dispatch over a new agent file.

When in doubt between two tiers, take the higher one — a wrong verdict
costs more than the tier difference.
