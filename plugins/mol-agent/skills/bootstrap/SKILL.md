---
description: Repository-specific agent-harness initializer. Inspects the repo, discovers local conventions, and installs only the minimum guardrails needed for future agents to work safely. Idempotent — safe to re-run. Writes CLAUDE.md and the agent-harness scaffolding (.agent/ and/or .claude/) only; never writes project source.
argument-hint: "[one-sentence purpose, optional]"
---

# /mol-agent:bootstrap — Agent Harness Bootstrap

Use this skill to **initialize or improve** the agent-facing setup of a
repository.

The goal is not to impose a rigid template. The goal is to make the
repository easier for future agents to understand, modify, evaluate, and
continue working on — by separating the four kinds of content
(public docs / internal agent context / runtime / router) and installing
only the minimum guardrails this particular repo actually needs.

> `/mol-agent:bootstrap` is **not a template copier**. It is a repository-
> specific agent-harness initializer that discovers local conventions
> and installs only the minimum guardrails needed for future agents to
> work safely.

This skill does not require an existing `mol_project:` frontmatter — it
is the tool that creates CLAUDE.md and (optionally) populates that
frontmatter. It works on any repository, mol-family or otherwise.

---

## Core principle — four-zone separation, active vs passive

```
docs/         public-facing documentation (tutorials, API, user guides)
.agent/       passive internal context (notes, contracts, handoffs,
              rubrics, decisions, open questions, debt) — outlives
              any single feature
.claude/      Claude Code runtime + active artifacts: skills, agents,
              hooks, settings, AND specs/ (alive, ticked off as
              /mol:impl works, deleted on completion)
CLAUDE.md     thin entry router — points to where things live; does
              not embed all the rules
```

The split between `.agent/` and `.claude/` is **active vs passive**.
Notes are kept; specs are intentionally ephemeral.

Do not pollute public documentation with internal agent workflow
artifacts. Do not put specs in `docs/` or `.agent/` — they live in
`.claude/specs/`. Keep CLAUDE.md short.

If the repo already has a working equivalent for any of these zones,
**respect that**. Adapt to the repo before reshaping it.

---

## Procedure

### 1. Inspect

Discover, in parallel where possible:

- working directory, git status, primary language(s)
  (`git ls-files | awk -F. '{print $NF}' | sort | uniq -c | sort -rn | head`)
- whether each of `docs/`, `.agent/`, `.claude/`, `CLAUDE.md` already
  exists — and if so, what they contain
- existing build / test / format commands (look for `pyproject.toml`,
  `Cargo.toml`, `package.json`, `CMakeLists.txt`, `go.mod`, `Makefile`,
  `.pre-commit-config.yaml`, `.github/workflows/*`)
- existing documentation conventions (where do tutorials live? where do
  API docs go? is there a project-specific style?)
- any existing CLAUDE.md, agent definitions, or skill directories
- repository shape: library / app / docs site / workflow tool / UI /
  scientific code / mixed

State the discovery result to the user in one paragraph. Do not write
anything yet.

### 2. Classify what already exists

For every file you would consider creating, classify it as one of:

- **keep** — exists, fits the harness, leave alone
- **merge** — exists, partially fits; you will add a managed section
  with stable markers
- **replace** — exists but is broken / superseded; you will ask the
  user before overwriting
- **create** — does not exist; safe to create

Also flag any file that is **misplaced** under harness-engineering
layering — e.g. agent contracts living in `docs/`, public tutorials
living in `.claude/`. Recommend a move; do not move automatically.

### 3. Decide the minimal addition

Pick the *smallest* set of changes that gives this repo a useful
harness. Do not impose a fixed structure. Reasonable defaults:

- a thin `CLAUDE.md` (router) — always
- `.agent/README.md` — explains what this directory is for
- `.agent/notes.md` — passive memory, captured by `/mol:note`
- `.claude/specs/` (empty directory) — the destination `/mol:spec`
  will write into. No need to populate it; it just needs to exist
  so the convention is visible
- a project blueprint stub at `.agent/architecture.md` (one line:
  `> 跑 /mol:map 填充本蓝图` / *"run /mol:map to populate this
  blueprint"*) — the canonical home for the structured catalog
  that `librarian` consumes during `/mol:spec` Step 4.5; do NOT
  pre-populate the catalog here, that is `/mol:map`'s job

Add more **only when justified by the repo**:

- `.agent/contracts/` if there are real agent handoff contracts to
  record
- `.agent/rubrics/` if there are real review checklists to encode
- `.agent/decisions/` if the project has substantial architectural
  history worth preserving
- `.agent/debt/` if there is real technical debt the user wants
  tracked
- `.agent/handoffs/` if work is regularly paused mid-flight
- `.claude/skills/` and `.claude/agents/` only if the project will
  benefit from running custom skills/agents — for many small repos a
  thin CLAUDE.md plus the installed plugins are enough

Prefer **adding small things later, on demand**, over front-loading a
large template that mostly sits unused.

If the user wants the full `mol`-plugin contract (`mol_project:`
frontmatter, the canonical set of mol skills/agents), offer it as an
opt-in. Do not assume it.

### 4. Reach approval

Show the user a short plan:

- what you inspected (one paragraph)
- what already exists and how you classified it (keep / merge /
  replace / create / misplaced)
- what you propose to add or change, with a one-line justification
  per item
- what you intentionally leave alone

Wait for approval before writing files. Do not write past this gate
without an explicit go-ahead.

For follow-up runs (idempotent re-runs), the plan can be a one-liner
("everything is in place, no action") and you may skip approval.

### 5. Apply

Write only the approved set. Use stable markers (e.g.
`<!-- mol-agent:bootstrap:managed begin -->` … `end -->`) for any managed
section so future re-runs can update in place without duplicating or
clobbering user content.

For CLAUDE.md, prefer a short router — see the template at the bottom
of this skill. Do not turn CLAUDE.md into a giant prompt or knowledge
dump.

If a target path exists with content you would replace, **ask
per-file**. Never silently overwrite.

### 6. Self-check

Before reporting, verify the result satisfies the layering rules:

- `docs/` (if it exists) contains only public-user content (no
  specs, no agent contracts, no rubrics)
- `.agent/` (if you created or modified it) contains only passive
  internal context, no public-user prose, no specs
- `.claude/` contains only behavior (skills/agents/hooks/settings)
  and active artifacts (`specs/`) — no long-lived knowledge
- CLAUDE.md is a thin router (rough budget: ≤ ~150 lines) and points
  to where things live rather than embedding them
- nothing was overwritten without explicit approval

Run `/mol-agent:check` against the result and surface any 🚨 or 🔴
findings. If there are none, say so plainly.

### 7. Report

Concise summary:

- what you inspected
- what you added or changed (with paths)
- what you intentionally left untouched (and why)
- any open questions you recorded in `.agent/open-questions.md`
- the suggested next improvement

End with a one-line summary in the standard form (F2).

---

## Guardrails

The following are non-negotiable. If you find yourself reaching for
one of these, stop and reconsider.

- **Do not** blindly overwrite existing files. Use stable markers for
  managed sections; ask per-file for the rest.
- **Do not** create boilerplate just because a template exists. Each
  file you add must be justified by something you *observed* in the
  repository.
- **Do not** put agent contracts, handoffs, rubrics, temporary plans,
  or private reasoning into `docs/`. Those belong in `.agent/`.
- **Do not** turn `CLAUDE.md` into a long manual. It is a router.
- **Do not** duplicate information that already exists elsewhere in
  the repository.
- **Do not** invent architecture rules without evidence from the
  codebase. If something is unclear, record it as an open question
  rather than guessing.
- **Do not** create fake precision. If you do not know whether the
  project uses pytest or unittest, do not write "the project uses
  pytest" — go look, or ask.
- **Do not** make implementation changes unrelated to bootstrapping
  the agent setup. This skill never writes project source code.
- **Do not** assume the `mol` plugin's `mol_project:` contract is
  wanted. Offer it; let the user opt in.

---

## Idempotency

Running `/mol-agent:bootstrap` multiple times must be safe:

- existing well-shaped files → keep, do not touch
- managed sections → updated in place via stable markers
- new artifacts → added only after approval
- user-authored notes / decisions / docs → never deleted or rewritten

If a re-run finds the harness already in good shape, the output is a
single line: *"harness in place, nothing to change"*.

---

## CLAUDE.md template (router, not manual)

When you create a fresh CLAUDE.md, prefer something close to this
shape. Adapt to the repo. Do not pad with sections you don't have
content for.

```markdown
# CLAUDE.md

<!-- mol-agent:bootstrap:managed begin -->
<!-- This block is regenerated by /mol-agent:bootstrap. Custom content goes
     OUTSIDE these markers. -->

## What this repo is

<one paragraph: what the project does, who it serves, what language
or stack>

## Where things live

- Source code: `<path>`
- Public documentation: `docs/`
- Passive internal context (notes, decisions, debt): `.agent/`
- Claude Code runtime + active specs: `.claude/` (`.claude/specs/`
  holds in-flight work; specs are deleted on completion)
- Tests: `<path>`

## Default workflow

For non-trivial work, prefer:
1. plan (`/mol:spec` or write to `.agent/`)
2. implement (`/mol:impl` or `/mol:fix`)
3. review (`/mol:review`)
4. capture decisions (`/mol:note`)

## What must never change casually

<list any invariants, public APIs, on-disk formats, or contracts that
require a deliberate decision to break>

<!-- mol-agent:bootstrap:managed end -->

<!-- Free-form additions below this line are preserved across re-runs.
     If you add a section that becomes a stable rule, leave it here.
     If it grows past a screen, promote it to .agent/<topic>.md and
     link from above. -->
```

If the user opts into the `mol` plugin contract, prepend a
`mol_project:` YAML block per `docs/claude-md-metadata.md` and route
references in the body to the project's chosen `notes_path` and
`specs_path`.

---

## .agent/ starter template (only if creating fresh)

```
.agent/
  README.md             # what this directory is for, how to navigate
  notes.md              # evolving decisions, captured by /mol:note
  architecture.md       # project blueprint — structured catalog of
                          modules, public surface, style summary, and
                          layer roles. Stub created here as a single
                          line pointing the user at /mol:map; populated
                          by /mol:map (never by bootstrap directly).
                          Consumed by `librarian` during /mol:spec
                          Step 4.5.
  open-questions.md     # things you weren't sure about during
                          bootstrap; the user fills these in over time
```

Add `.agent/contracts/`, `.agent/rubrics/`, `.agent/decisions/`,
`.agent/debt/`, `.agent/handoffs/` **only when** the repo has real
content for them. Empty directories are not value.

## .claude/ starter (only if creating fresh)

```
.claude/
  specs/                # active runtime artifacts; /mol:spec writes
                          here, /mol:impl ticks + deletes
    INDEX.md            # one-line entry per live spec; updated by
                          /mol:spec, pruned by /mol:impl
```

Skills/agents/hooks/settings under `.claude/` are added later only
when the repo justifies project-specific behavior. Do not pre-create
empty `skills/` or `agents/` directories.

---

## Output format

- During inspection: one short paragraph summarizing what you found.
- During planning: a short bulleted plan with classifications.
- During application: per-file action lines (`created`, `merged`,
  `kept`, `skipped — needs your call`).
- During self-check: any 🚨 / 🔴 findings from the layering audit, or
  *"layering check passed"*.
- Final summary (F2): one line — *what was created, what was
  skipped, what to do next*.

This skill is the only one that may produce more than a one-line
summary in its body, because the work itself is structural.
