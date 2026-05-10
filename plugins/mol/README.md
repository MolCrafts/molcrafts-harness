# mol

Shared molcrafts project-workflow skills and common-axis agents,
built around **harness engineering**: give the repository a small,
well-shaped harness — principled boundaries, predictable layers, and
just enough scaffolding to make safe defaults the obvious move — so
the *next* agent that walks in succeeds without re-deriving the rules.

`mol` is the day-to-day toolbox: spec, implement, review, fix,
refactor, simplify, ship. The harness *itself* (CLAUDE.md, `.claude/notes/`,
`.claude/specs/`) is installed and maintained by the sibling plugin
[`mol-agent`](../mol-agent/README.md).

Skills adapt to each project by reading a `mol_project:` YAML
frontmatter block at the top of the project's `CLAUDE.md` — so one
plugin serves Atomiverse, molpy, molexp, molrs, molvis, molq, and
molnex without per-project forks.

## Install

```
/plugin marketplace add https://github.com/MolCrafts/claude-plugin
/plugin install mol@molcrafts
/plugin install mol-agent@molcrafts
```

For local development:
`/plugin marketplace add <path-to-claude-plugin-checkout>`.

## Four-zone layering (active vs passive)

Every well-shaped repository the `mol` plugin works on separates four
kinds of content. Top-level layout follows Claude Code's project
convention (`.claude/` is the canonical project folder); the
active/passive split lives inside `.claude/`.

| Zone (path)              | Purpose                                                                                 |
|--------------------------|-----------------------------------------------------------------------------------------|
| `docs/`                  | public-facing documentation (tutorials, API, user guides)                               |
| `.claude/notes/`         | **passive** internal context (project notes, blueprint, decisions, contracts, handoffs, rubrics, debt, open questions) — outlives any feature |
| `.claude/specs/`         | **active** runtime artifacts — alive, ticked off as `/mol:impl` works, deleted on completion |
| `.claude/agents/`, `.claude/skills/`, `.claude/hooks/`, `.claude/settings.json` | Claude Code's own runtime configuration |
| `CLAUDE.md`              | thin entry router — points to where things live; no manual                              |

> Note: `.claude/notes/` (passive *project knowledge*) is a different
> folder from `.claude/agents/` (Claude Code's *agent definitions*). The
> naming is deliberately distinct — "notes" = what the agent reads,
> "agents" = what the agent *is*.

Notes are kept; specs are intentionally ephemeral. Full rules in
[`rules/design-principles.md`](rules/design-principles.md). Run
`/mol-agent:check` to verify compliance.

## Skills

All `mol` skills require a `mol_project:` frontmatter in CLAUDE.md
(see [`rules/claude-md-metadata.md`](rules/claude-md-metadata.md)) and
fail fast with an adoption hint when it is missing. To create
CLAUDE.md and the surrounding harness, run `/mol-agent:bootstrap`
first.

One frontmatter field worth knowing about up front:
`mol_project.stage` — `experimental` (default) / `beta` / `stable` /
`maintenance` — governs how aggressive the writing skills and
reviewers may be when touching existing code. `experimental` lets
`/mol:impl` rewrite legacy on sight; `stable` requires deprecation
shims for public-signature changes; `maintenance` makes
`/mol:refactor` and new-feature `/mol:impl` refuse outright (only
`/mol:fix` proceeds). Full matrix in
[`rules/stage-policy.md`](rules/stage-policy.md).

The 19 skills group by intent. Each row shows what it does, when to
reach for it, and a one-line example.

### 1 — Plan & specify

| Skill | What | When | Example |
|---|---|---|---|
| `/mol:discuss <topic>` | Free-form design / improvement / scientific-insight discussion. Frames the topic, drives toward convergence with an explicit per-turn `Convergence pulse`, and exits one of two ways: **converge** → packages a one-paragraph requirement and tells the user to invoke `/mol:spec` on it; **discard** → leaves no artifacts. Hard 8-turn cap. Read-only. Pairs upstream of `/mol:spec`. | When the requirement isn't yet clear enough for `/mol:spec` and you want to think it through with the agent. | `/mol:discuss should /mol:web own remote dev servers?` |
| `/mol:spec` | Natural-language requirement → structured `<slug>.md` + binding `<slug>.acceptance.md` under `.claude/specs/`. Bulk drafting + self-validation (sections / atomic tasks / RED-before-GREEN / Files↔Tasks cross-reference) is delegated to the `spec-writer` subagent so parent context stays small. Skill orchestrates conflict detection, user approval, and persistence. Detects conflicts with existing specs and updates them in place when superseded. | Before starting any non-trivial implementation. | `/mol:spec add Morse bond potential to molpy` |
| `/mol:litrev` | Literature + reference-implementation review (gated on `mol_project.science.required`). Returns equations, validation targets, open questions. | Before specifying a domain-critical feature. | `/mol:litrev Nose-Hoover thermostat` |

### 2 — Implement (writes code)

| Skill | What | When | Example |
|---|---|---|---|
| `/mol:impl` | Full TDD workflow gated on an approved spec + acceptance contract. Resume-syncs already-done tasks before writing new code. Ticks the spec's checkboxes as it progresses; deletes the spec + acceptance + INDEX entry on completion. | After `/mol:spec` is `status: approved`. | `/mol:impl morse-bond` |
| `/mol:fix` | Minimal-diff bug fix — reproduce, delegate diagnosis to `debugger` subagent (Step 2), patch the smallest surface, verify. Calls `tester` for a regression test when the root cause suggests a missing one. | When a test fails or a bug is reported. | `/mol:fix energy NaN at zero distance` |
| `/mol:refactor` | Restructure code while preserving all architectural invariants. Snapshot → incremental change → re-verify. Calls `architect` pre and post. | When the structure needs to change but behavior must not. | `/mol:refactor split forces module by backend` |
| `/mol:simplify` | Apply `janitor`'s hygiene findings as the write-mode counterpart — dead code, debug residue, magic-literal substitution, captured-rule naming drift. Behavior-preserving by contract; reverts the whole batch if any test regresses. | After `/mol:impl` finishes, before `/mol:commit`, to strip cruft accumulated during exploration. | `/mol:simplify` |

### 3 — Review (read-only)

| Skill | What | When | Example |
|---|---|---|---|
| `/mol:review` | The unified multi-axis static reviewer. Fans out to up to 10 single-axis agents, hands findings to the `reviewer` agent for the table + verdict. Use `--axis=<name>` to scope to one dimension: `arch`, `perf`, `docs`, `ux`, `api`, `science`, `numerics`, `visual`, `security`, `hygiene`. Surfaces runtime evaluator handoffs (`/mol:web`, etc.) when an `acceptance.md` is in scope. | Before commit / push / PR; or when you want one specific axis checked. | `/mol:review` &nbsp;·&nbsp; `/mol:review --axis=security` &nbsp;·&nbsp; `/mol:review morse-bond` |
| `/mol:debug` | Diagnose-only — never writes code. Thin wrapper around the `debugger` subagent: classifies the failure (build / test / runtime), gathers evidence, returns root cause + fix recommendation + preventive-test idea. | When a failure is mysterious and you want a clean diagnosis before patching. | `/mol:debug segfault in dipole kernel` |
| `/mol:test` | Run the suite via `mol_project.build.test`; delegate to `tester` in **analyze-mode** for category coverage and tolerance discipline. (Test *writing* lives in `/mol:impl` and `/mol:fix`.) | When you want to know the state of the suite + what categories are missing. | `/mol:test` &nbsp;·&nbsp; `/mol:test tests/forces/` |
| `/mol:ship <tier>` | Three-tier CI-parity gate (`commit` ⊆ `push` ⊆ `merge`). Reports PROCEED or BLOCK and routes blockers to the right write-mode skill. Read-only — never edits. | The gates underneath `/mol:commit`, `/mol:push`. Run manually before a `merge` to mirror remote CI locally. | `/mol:ship merge` |

### 4 — Runtime evaluator

| Skill | What | When | Example |
|---|---|---|---|
| `/mol:web <slug>` | Frontend runtime evaluator. Reads `<slug>.acceptance.md`, picks `type: ui_runtime` criteria, starts the dev server via `mol_project.dev.command` and parses the URL from its ready banner, drives whatever Playwright MCP / browser-automation plugin you installed, returns per-criterion verdicts + screenshots / console / network artifacts. Self-skips when no Playwright MCP is reachable. | After `/mol:impl` finishes a UI feature with `ui_runtime` criteria. | `/mol:web spec-tree-view` |

### 5 — Documentation & knowledge

| Skill | What | When | Example |
|---|---|---|---|
| `/mol:docs` | Mode A: docstring audit keyed to `mol_project.doc.style` (google / rustdoc / jsdoc-tiered / doxygen). Mode B: narrative tutorial (with mandatory two-part Part 1 derivation + Part 2 code mapping for science topics). | After implementing a public API; when adding a tutorial; when an audit finds drift. | `/mol:docs molpy.forces.morse` &nbsp;·&nbsp; `/mol:docs tutorial: running your first MD` |
| `/mol:note` | Capture an architectural decision into `.claude/notes/notes.md`. Detects conflicts with existing notes / CLAUDE.md, cleans up stale notes, and promotes stable rules into CLAUDE.md (or a `.claude/notes/<topic>.md` page). | When a non-obvious convention is decided in conversation and would otherwise be re-derived later. | `/mol:note use n_atoms (not natoms) in all public signatures` |
| `/mol:map [<scope>]` | Build or refresh `.claude/notes/architecture.md` — the passive project blueprint (modules, public surface, style summary, layer roles) consumed by `librarian` during `/mol:spec` Step 4.5. Delegates inventory to the `architect` agent; diffs against the existing blueprint; writes only after explicit user approval. Idempotent — a re-run with no drift exits without writing. | After significant architectural changes; before a sprint of new specs that need accurate placement / reuse advice. | `/mol:map` &nbsp;·&nbsp; `/mol:map src/forces/` |

### 6 — Git workflow (writes / pushes)

A linear chain. Each step gates with `/mol:ship` underneath. Follows
the standard GitHub fork convention: `origin` = your fork, `upstream`
= canonical repo. None of these need extra config.

| Skill | What | When | Example |
|---|---|---|---|
| `/mol:commit [<msg>]` | Stage + commit gated on `/mol:ship commit` (format + lint + pre-commit). Generates a conventional-commit message from the diff if you don't supply one. Local only — does not push. | Whenever you'd run `git commit`. | `/mol:commit` &nbsp;·&nbsp; `/mol:commit fix: clamp distance in morse kernel` |
| `/mol:push [<branch>]` | Push to **origin** (your fork) gated on `/mol:ship push` (full test suite). Auto-runs `/mol:commit` first if the tree is dirty. Refuses to push the upstream default branch from a fork. | Whenever you'd run `git push`. | `/mol:push` |
| `/mol:pr [<title>]` | Open a pull request from `origin` to `upstream/<default_branch>` via `gh`. Calls `/mol:push` first. Drafts title + body from the commit range; refuses to create a duplicate of an existing open PR. | When the branch is ready for review. | `/mol:pr` |
| `/mol:tag [<tag>]` | Push an existing release tag (created by `/mol-plugin:release`) to **upstream** so a `on: push: tags:` workflow fires. Refuses to push to origin when upstream exists; refuses to overwrite a remote tag. | After `/mol-plugin:release` cuts the local tag. | `/mol:tag v0.2.0` |

## Common workflows

### New feature, end-to-end

```
/mol:litrev <topic>           # only if science.required and you need refs
/mol:spec <feature>           # → <slug>.md + <slug>.acceptance.md
/mol:impl <slug>              # TDD; ticks tasks; deletes spec on done
/mol:web <slug>               # only if ui_runtime criteria exist
/mol:simplify                 # strip cruft from exploration
/mol:review                   # full static review, all axes
/mol:commit && /mol:push && /mol:pr
```

### Bug fix

```
/mol:debug <symptom>          # optional: diagnose-only first
/mol:fix <bug>                # write regression test + minimal patch
/mol:review --axis=arch       # or any single axis you suspect
/mol:commit && /mol:push
```

### Single-axis spot check

```
/mol:review --axis=security   # adversarial-input scan only
/mol:review --axis=perf       # perf anti-patterns only
/mol:review --axis=hygiene    # janitor only (read-only); pair with /mol:simplify to apply
```

### Pre-merge confidence

```
/mol:ship merge               # mirrors remote CI locally; PROCEED or BLOCK
```

## Agents

Agents are invoked only through skills (never directly by the user).
Each owns one expertise axis. They split into two kinds —
**producer** agents (write content to files) and **reviewer** agents
(read-only, emit findings) — explained in
[`rules/agent-design.md`](rules/agent-design.md).

| Agent | Kind | Axis |
|---|---|---|
| `architect` | reviewer | Module boundaries, layer rules, dependency graph |
| `debugger` | reviewer | Failure root cause + fix recommendation + preventive-test idea (used by `/mol:debug` standalone, and by `/mol:fix` Step 2 to diagnose before patching) |
| `tester` | producer-write (write-mode) / reviewer (analyze-mode) — dual-mode | TDD red-before-green (write-mode); coverage gaps + tolerance discipline (analyze-mode) |
| `scientist` | reviewer | Equations, units, conservation, literature (every claim cites a fetched-this-run reference or derives inline) |
| `compute-scientist` | reviewer | Numerical stability, complexity, determinism, HPC / DDP readiness |
| `optimizer` | reviewer | Hot-path performance. Detects per-file which catalog applies (numpy / pytorch / cuda / simd-xsimd / wasm-bridge / subprocess / async-io / web-render). |
| `documenter` | producer-write (Mode B) / reviewer (Mode A) | Docstrings + narrative docs; audience locked to a capable but uninitiated undergraduate |
| `spec-writer` | producer-return | Drafts spec body + acceptance.md given a parsed requirement; self-validates against quality checklist; returns markdown text — `/mol:spec` persists after user approval |
| `undergrad` | reviewer | User's-perspective: API, onboarding, extension ergonomics, error messages |
| `pm` | reviewer | Public-surface discipline, breaking-change analysis, downstream integration contracts |
| `ci-guard` | reviewer | CI-parity: detects CI config, runs tiered local equivalent |
| `web-design` | reviewer | Visual / UX on frontend code — tokens, info density, empty/error/loading states, a11y, responsive. Self-skips non-frontend files. |
| `security-reviewer` | reviewer | Adversarial-input — shell / SQL / path / SSRF / prompt injection, deserialization, secret leakage, missing authorization. Self-skips files outside the attack-surface signal set. |
| `janitor` | reviewer | Continuous tech-debt servicing — applies the project's captured `.claude/notes/` aesthetic rules to every diff. Pays down debt a little every review. |
| `reviewer` | reviewer | Multi-axis aggregator — collects findings from the other reviewers into a severity table, resolves conflicts, renders the verdict. |
| `playwright-evaluator` | producer-write (artifacts) | Verifies one `ui_runtime` acceptance criterion against a running app via whatever browser-automation MCP is installed. |

Review-style agents emit `<emoji> file:line — message` using 🚨 Critical,
🔴 High, 🟡 Medium, 🟢 Low. Verdict: any 🚨 → BLOCK; any 🔴 → REQUEST
CHANGES; otherwise APPROVE.

## Design contract

The plugin follows the harness-engineering layering plus a strict
two-layer model (skill = orchestrator + workflow; agent = single
expertise axis). The producer-vs-reviewer split — why `tester`
writes but `optimizer` doesn't — is documented in
[`rules/agent-design.md`](rules/agent-design.md). Layering,
orthogonality, knowledge-locality, capability, workflow, output, and
idempotency rules are spelled out — and audit-checked — in
[`rules/design-principles.md`](rules/design-principles.md). Run
`/mol-agent:check` against any project's harness to verify
compliance. (The marketplace repo itself has no harness; use
`/mol-plugin:check` for its self-audit.)

## Adopt in a project

1. Run `/mol-agent:bootstrap` from the project root. It inspects the
   repo, asks what to add, and installs only what's justified —
   including the `mol_project:` frontmatter if you opt in.
2. Smoke-test with `/mol-agent:check` (harness presence + design
   compliance) and `/mol:review --axis=arch` (architecture).

Each project's harness is rewritten in place rather than migrated in
phases — this is continuous iteration.

## License

MIT — see the root [LICENSE](../../LICENSE).
