# mol

Shared molcrafts project-workflow skills and common-axis agents,
built around **harness engineering**: give the repository a small,
well-shaped harness — principled boundaries, predictable layers, and
just enough scaffolding to make safe defaults the obvious move — so
the *next* agent that walks in succeeds without re-deriving the rules.

`mol` is the day-to-day toolbox: spec, implement, review, fix,
refactor, simplify, ship. The harness *itself* (CLAUDE.md, `.claude/notes/`,
`.claude/specs/`) is installed and maintained by `/mol:bootstrap`.

Claude Code is the canonical runtime. Codex loads the same skills through the
plugin's native `.codex-plugin/plugin.json`; `skills/CODEX.md` translates tool,
subagent, and plugin-path concepts without duplicating workflow bodies.

Skills adapt to each project by reading a `mol_project:` YAML
frontmatter block at the top of the project's `CLAUDE.md` — so one
plugin serves Atomiverse, molpy, molexp, molrs, molvis, molq, and
molnex without per-project forks.

## Install

### Claude Code (primary)

```
/plugin marketplace add https://github.com/MolCrafts/molcrafts-harness
/plugin install mol@molcrafts
```

For local development:
`/plugin marketplace add <path-to-molcrafts-harness-checkout>`.

### Codex

```bash
codex plugin marketplace add MolCrafts/molcrafts-harness
codex plugin add mol@molcrafts
```

For local development:
`codex plugin marketplace add <path-to-molcrafts-harness-checkout>`.
Restart Codex and test updated skills in a new thread.

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
`/mol:bootstrap` to verify compliance.

## Conversation modes

Every skill runs in one of two modes, defined in
[`rules/model-policy.md`](rules/model-policy.md):

- **Advisor (顾问模式)** — the deliverable is words: an answer, plan,
  verdict, or diagnosis. The main conversation (session model, top
  tier) authors it; agents only gather evidence. (`/mol:discuss`,
  `/mol:grill` / `/mol:grilling`, `/mol:debug`, `/mol:review`,
  `/mol:test`, `/mol:ship`, …)
- **Orchestration (编排模式)** — the deliverable is artifacts: code,
  docs, specs, commits. The main loop plans, routes, gates, and
  verifies; opus-class producer agents author the artifacts — the
  main loop never authors production source (`implementer` writes
  code, `tester` tests, `documenter` docs). (`/mol:impl`, `/mol:fix`,
  `/mol:spec`, the git chain, `/mol:release`, …)

Orthogonal to mode: **user- vs model-invoked** skills (who may fire
them). User-only entries set `disable-model-invocation: true` (Claude)
and `allow_implicit_invocation: false` (Codex). Anything auto-invoked
by another skill must stay model-invoked. Full rule in
[`rules/design-principles.md`](rules/design-principles.md) § 2.5.
Example: thin `/mol:grill` (user) → body `/mol:grilling` (model;
called by discuss + spec).

Agents pin their model tier in frontmatter — `opus` for judgment,
`sonnet` for mechanical work, `haiku` for `/mol:impl-all`'s completion
evaluator — so the strongest model stays on planning and verdicts
while execution runs on the tier each task needs.

## Skills

All `mol` skills require a `mol_project:` frontmatter in CLAUDE.md
(see [`rules/claude-md-metadata.md`](rules/claude-md-metadata.md)) and
fail fast with an adoption hint when it is missing. To create
CLAUDE.md and the surrounding harness, run `/mol:bootstrap`
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

Skills group by intent. Each row shows what it does, when to
reach for it, and a one-line example.

### 0 — Harness lifecycle

| Skill | What | When | Example |
|---|---|---|---|
| `/mol:bootstrap` | Initialize or maintain the agent harness (CLAUDE.md + `.claude/notes/` + `.claude/specs/`). Three paths: no harness → create fresh; harness exists → audit + repair; healthy harness → single-line no-op. Never writes project source. | First time in a project; after upgrading mol; when harness has drifted. | `/mol:bootstrap` |
| `/mol:adopt-workspace` | Adopt an arbitrary existing data directory as a molexp-compatible workspace (`Workspace → Project → Experiment → Run` folder family). Inspects the source, proposes a mapping for operator review, materializes via molexp's Python API, then copy-verifies (default) or move-verifies each file with SHA-256. Resumable via an on-disk ledger; copy-mode optionally deletes the source after a typed-path gate. | Lifting legacy experimental data into a fresh molexp workspace; consolidating ad-hoc result folders. | `/mol:adopt-workspace ./old-results ./new-workspace` |

### 1 — Plan & specify

| Skill | What | When | Example |
|---|---|---|---|
| `/mol:discuss <topic>` | Free-form design / improvement / scientific-insight discussion. Frames the topic, drives toward convergence with an explicit per-turn `Convergence pulse`, and exits one of two ways: **converge** → packages a one-paragraph requirement and **auto-invokes `/mol:grilling` (plan mode)**; **discard** → leaves no artifacts. Hard 8-turn cap. Read-only. Never auto-invokes `/mol:spec`. | When the requirement isn't yet clear enough for `/mol:spec` and you want to think it through with the agent. | `/mol:discuss should /mol:web own remote dev servers?` |
| `/mol:grill <plan>` | **User-only entry** (`disable-model-invocation: true`). Thin wrapper that runs `/mol:grilling` in plan mode. Other skills must call `/mol:grilling` directly. | When you deliberately want to type a grill session on a plan you already have. | `/mol:grill cache force results per-frame keyed on neighbor-list hash` |
| `/mol:grilling [mode] <plan\|slug>` | **Model-invoked** body. Relentless one-question-at-a-time interview; recommended answers; self-answers from the codebase; per-turn `Grill pulse`. Modes: **plan** (default) — sharpen a free-form plan → hand off to user for `/mol:spec`; **spec-audit** — stress-test a written spec → `audit_result: clean \| supersede_needed` (caller writes). Auto-invoked by `/mol:discuss` (plan) and `/mol:spec` (spec-audit). Read-only on source and specs. | Auto from discuss/spec, free-form “grill me”, or via `/mol:grill`. | `/mol:grilling mode:spec-audit morse-bond` |
| `/mol:spec` | Natural-language requirement → structured `<slug>.md` + binding `<slug>.acceptance.md` under `.claude/specs/`. Gated on a mandatory `librarian` codebase scan: every reuse candidate (tagged `reuse` / `generalize`) must be resolved in the spec's Design § Reuse decision — reimplementing an existing capability instead of reusing or generalizing it is invalid. Bulk drafting + self-validation is delegated to `spec-writer`. Skill persists both files immediately, then **auto-invokes `/mol:grilling` (spec-audit)** — material holes supersede in place; clean audits point to `/mol:impl`. | Before starting any non-trivial implementation. | `/mol:spec add Morse bond potential to molpy` |
| `/mol:litrev` | Literature + reference-implementation review (gated on `mol_project.science.required`). Returns equations, validation targets, open questions. | Before specifying a domain-critical feature. | `/mol:litrev Nose-Hoover thermostat` |

### 2 — Implement (writes code)

| Skill | What | When | Example |
|---|---|---|---|
| `/mol:impl` | Full TDD workflow gated on an approved spec + acceptance contract — pure orchestration: `tester` writes the RED tests and the spec's `regressions/` end-to-end example, `implementer` writes the production code, the main loop gates, ticks, and verifies (the regression example must reproduce its reference values before finalize). Resume-syncs already-done tasks before writing new code. Ticks the spec's checkboxes as it progresses; flips each `code` / `runtime` acceptance criterion to `status: verified` at close-out. Ends every run by auto-invoking `/mol:simplify` and `/mol:close` — no prompts. Parks at `status: code-complete` only if runtime-evaluator-typed criteria (`scientific` / `performance` / `docs`, legacy `ui_runtime`) are still `pending` after auto-close. | After `/mol:spec` has written the spec (`status: approved`). | `/mol:impl morse-bond` |
| `/mol:impl-all <prefix>` | Batch-implement a spec chain (`<prefix>-01-*`, `<prefix>-02-*`, …) end-to-end. Discovers matching specs, sorts by numeric suffix, then drives the chain in its own agentic loop — each spec runs `/mol:impl` + `/mol:commit` + auto `/mol:close`, with an independent cheap-model evaluator confirming the terminal state between specs. Never stops to ask questions. Stops on stall. | When a feature is split into a spec chain and you want hands-off execution. | `/mol:impl-all morse-bond` |
| `/mol:close <slug> [--manual]` | The closing counterpart to `/mol:impl`. Advances a `code-complete` spec to `done` by re-checking the acceptance ledger and deleting the spec + acceptance + INDEX entry. Auto-invoked (default mode) by `/mol:impl` and `/mol:impl-all` after every finished spec; also runnable standalone. Default mode assumes a runtime evaluator (`/mol:bench`, `/mol:web`) already flipped the remaining criteria. `--manual` (operator-only, never automatic) asserts observably-met criteria without an evaluator; flips `pending` → `verified` with a `verified_by: human` audit note. | Standalone: after an owed evaluator has run, or with `--manual` when no evaluator is available. | `/mol:close morse-bond` &nbsp;·&nbsp; `/mol:close morse-bond --manual` |
| `/mol:fix` | Minimal-diff bug fix — reproduce, consume an existing `/mol:debug` report or delegate diagnosis to `debugger` (Step 2), patch the smallest surface via `implementer` (Step 3), verify. Calls `tester` for a regression test when the root cause suggests a missing one. | When a test fails or a bug is reported. | `/mol:fix energy NaN at zero distance` |
| `/mol:refactor` | Restructure code while preserving all architectural invariants. Snapshot → incremental change → re-verify. Calls `architect` pre and post. | When the structure needs to change but behavior must not. | `/mol:refactor split forces module by backend` |
| `/mol:ci-sync [<root>]` | Audit and repair CI / pre-commit parity — write-mode counterpart of the `ci-guard` agent. Delegates the audit to `ci-guard`, then patches `.pre-commit-config.yaml` and the CI workflow so both sides run identical commands from `mol_project.build`; scaffolds both files for projects that have neither. Writes config files only, never source. | When CI catches things pre-commit missed (or vice versa); when adopting a project with no CI at all. | `/mol:ci-sync` |
| `/mol:simplify` | Apply `janitor`'s hygiene findings as the write-mode counterpart — dead code, debug residue, magic-literal substitution, captured-rule naming drift — **and** enforce the language-canonical toolchain trio on the verify gate (Python: `ruff` + `ty`; TypeScript: `biome` + `tsc`; Rust: `cargo fmt` + `clippy` + `cargo check`); a regression in any of them reverts the entire batch. Behavior-preserving by contract. Mandatorily invoked by `/mol:impl` Step 6.5 as the single backward-compat gatekeeper (delete legacy at `experimental`, deprecation-shim at `stable`, migration-note flag at `beta`, leave alone at `maintenance`). | After `/mol:impl` finishes, before `/mol:commit`, to strip cruft accumulated during exploration; or anywhere `/mol:review`'s hygiene axis flagged drift. | `/mol:simplify` |

### 3 — Review (read-only)

| Skill | What | When | Example |
|---|---|---|---|
| `/mol:review` | The unified multi-axis static reviewer. Fans out to one single-axis agent per axis, hands findings to the `reviewer` agent for the table + verdict. Use `--axis=<name>` to scope to one dimension: `arch`, `perf`, `docs`, `ux`, `api`, `science`, `numerics`, `visual`, `security`, `ffi`, `hygiene`. Surfaces runtime evaluator handoffs (`/mol:web`, etc.) when an `acceptance.md` is in scope. | Before commit / push / PR; or when you want one specific axis checked. | `/mol:review` &nbsp;·&nbsp; `/mol:review --axis=security` &nbsp;·&nbsp; `/mol:review morse-bond` |
| `/mol:debug` | Diagnose-only — never writes code. Thin wrapper around the `debugger` subagent: classifies the failure (build / test / runtime), gathers evidence, returns root cause + fix recommendation + preventive-test idea. | When a failure is mysterious and you want a clean diagnosis before patching. | `/mol:debug segfault in dipole kernel` |
| `/mol:test` | Run the suite via `mol_project.build.test`; delegate to `tester` in **analyze-mode** for category coverage and tolerance discipline. (Test *writing* lives in `/mol:impl` and `/mol:fix`.) | When you want to know the state of the suite + what categories are missing. | `/mol:test` &nbsp;·&nbsp; `/mol:test tests/forces/` |
| `/mol:ship <tier>` | Three-tier CI-parity gate (`commit` ⊆ `push` ⊆ `merge`). Reports PROCEED or BLOCK and routes blockers to the right write-mode skill. Read-only — never edits. | The gates underneath `/mol:commit`, `/mol:push`. Run manually before a `merge` to mirror remote CI locally. | `/mol:ship merge` |

### 4 — Runtime evaluator

| Skill | What | When | Example |
|---|---|---|---|
| `/mol:web <slug>` | Frontend runtime evaluator. Reads the spec body's non-binding `## UI verification` checks (plus legacy `type: ui_runtime` acceptance criteria from older specs), starts the dev server via `mol_project.dev.command` and parses the URL from its ready banner, drives whatever Playwright MCP / browser-automation plugin you installed, and returns per-check verdicts + screenshots / console / network artifacts. Advisory — UI checks never gate spec close; only legacy criteria get their `status` written back. Self-skips when no Playwright MCP is reachable. | Ad hoc, whenever you want the frontend exercised against the spec's UI checks. | `/mol:web spec-tree-view` |
| `/mol:bench <slug>` | External benchmark evaluator. Reads `<slug>.acceptance.md`, picks `type: scientific` + `type: performance` criteria, runs the project's separate `bm_*` pytest-benchmark repo (configured via `mol_project.bench.repo`) — which pairs each kernel with an equality check against a user-named reference (freud, scipy, …) — and flips each handled criterion's `status` back into `acceptance.md`. Self-skips when no bench repo is configured or no usable `evaluator_hint` selector is on the criterion. | After `/mol:impl` parks a spec at `status: code-complete` with `scientific` or `performance` criteria still `pending`. | `/mol:bench morse-bond` |

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
| `/mol:release <patch\|minor\|major>` | **Ecosystem library** release end-to-end (not the harness). Hard-gates first-party path/editable deps + registry versions, docs currency, and harness currency; bumps package version; chains `/mol:commit` → push → pr → merge → `/mol:tag`. Distinct from `/mol-plugin:release`. | When shipping molrs / molpack / molpy / … to crates.io · PyPI · npm. | `/mol:release patch` |
| `/mol:tag [<tag>]` | Push an existing release tag (created by `/mol:release` or `/mol-plugin:release`) to **upstream** so a `on: push: tags:` workflow fires. Refuses to push to origin when upstream exists; refuses to overwrite a remote tag. | After a release skill cuts the local tag. | `/mol:tag v0.2.0` |

## Common workflows

### New feature, end-to-end

```
/mol:litrev <topic>           # only if science.required and you need refs
/mol:discuss <topic>          # interactive; converges → auto /mol:grilling (plan)
/mol:grill <plan>             # interactive entry → /mol:grilling (plan)
/mol:spec <feature>           # interactive grill after write; then auto /mol:impl-all
/mol:impl-all <slug|prefix>   # default implement path — end-to-end, auto close
/mol:review                   # full static review, all axes
/mol:release patch            # ecosystem libs: gates + commit/push/pr/tag
/mol-plugin:release patch     # harness marketplace only
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

| Agent | Kind | Model | Axis |
|---|---|---|---|
| `architect` | reviewer | opus | Module boundaries, layer rules, dependency graph |
| `debugger` | reviewer | opus | Failure root cause + fix recommendation + preventive-test idea (used by `/mol:debug` standalone; `/mol:fix` Step 2 consumes an existing report or delegates fresh) |
| `tester` | producer-write (write-mode) / reviewer (analyze-mode) — dual-mode | opus | TDD red-before-green + `regressions/` end-to-end examples (public-API-only, literature-anchored) (write-mode); coverage gaps + tolerance discipline + regression-example presence (analyze-mode) |
| `implementer` | producer-write | opus | Executes one spec Task / one fix patch — minimal production code turning a RED test GREEN; never writes tests, never ticks/commits/reverts |
| `scientist` | reviewer | opus | Equations, units, conservation, literature (every claim cites a fetched-this-run reference or derives inline) |
| `compute-scientist` | reviewer | opus | Numerical stability, complexity, determinism, HPC / DDP readiness |
| `optimizer` | reviewer | opus | Hot-path performance. Detects per-file which catalog applies (numpy / pytorch / cuda / simd-xsimd / wasm-bridge / subprocess / async-io / web-render). |
| `documenter` | producer-write (Mode B) / reviewer (Mode A) | opus | Docstrings + narrative docs; audience locked to a capable but uninitiated undergraduate |
| `spec-writer` | producer-return | opus | Drafts spec body + acceptance.md given a parsed requirement; self-validates against quality checklist; returns markdown text — `/mol:spec` persists immediately, no approval round-trip |
| `librarian` | reviewer (spec-time consultant) | opus | Placement + reuse advice against `.claude/notes/architecture.md` plus a mandatory targeted source scan during `/mol:spec`; returns the fixed four-section advisory report (Reuse candidates tagged `reuse` / `generalize` / `pattern` / Recommended placement / Closest pattern / Confidence) |
| `undergrad` | reviewer | opus | User's-perspective: API, onboarding, extension ergonomics, error messages |
| `user` | reviewer | opus | Comp-chem-undergrad axis: doc-first learnability, doc correctness, and cross-library composition **without glue** across the molcrafts ecosystem (molpy / molpack / molrs / molq / molexp / molnex) |
| `pm` | reviewer | opus | Public-surface discipline, breaking-change analysis, downstream integration contracts |
| `ci-guard` | reviewer | sonnet | CI-parity: detects CI config, runs tiered local equivalent |
| `web-design` | reviewer | opus | Visual / UX on frontend code — tokens, info density, empty/error/loading states, a11y, responsive. Self-skips non-frontend files. |
| `security-reviewer` | reviewer | opus | Adversarial-input — shell / SQL / path / SSRF / prompt injection, deserialization, secret leakage, missing authorization. Self-skips files outside the attack-surface signal set. |
| `ffi-guard` | reviewer | opus | FFI-boundary safety — panics/exceptions across the seam, raw pointers in signatures, stale handles, ownership leaks, string-copy discipline, GIL/Sync hazards. Auto-detects the binding surface (C ABI / CXX / PyO3 / wasm-bindgen / ctypes / N-API); self-skips files with none. |
| `janitor` | reviewer | sonnet | Continuous tech-debt servicing — applies the project's captured `.claude/notes/` aesthetic rules to every diff, plus a language-canonical toolchain pass (formatter + linter + type checker — `ruff` / `ty` for Python, `biome` / `tsc` for TypeScript, `cargo fmt` / `clippy` / `cargo check` for Rust). Pays down debt a little every review. |
| `reviewer` | reviewer | sonnet | Multi-axis aggregator — collects findings from the other reviewers into a severity table, resolves conflicts, renders the verdict. |
| `playwright-evaluator` | producer-write (artifacts) | sonnet | Verifies one UI check (spec-body `## UI verification` item or legacy `ui_runtime` criterion) against a running app via whatever browser-automation MCP is installed. |

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
`/mol:bootstrap` against any project's harness to verify
compliance. (The marketplace repo itself has no harness; use
`/mol-plugin:check` for its self-audit.)

## Adopt in a project

1. Run `/mol:bootstrap` from the project root. It inspects the
   repo, asks what to add, and installs only what's justified —
   including the `mol_project:` frontmatter if you opt in.
2. Smoke-test with `/mol:bootstrap` (re-run to verify harness health)
   and `/mol:review --axis=arch` (architecture).

Each project's harness is rewritten in place rather than migrated in
phases — this is continuous iteration.

## License

MIT — see the root [LICENSE](../../LICENSE).
