# Skill / Agent Design Principles

The `mol` plugin is built around **harness engineering**: agents work
better when the repository gives them a small, well-shaped harness —
principled boundaries, predictable layers, and just enough scaffolding to
make safe defaults the obvious move. The aim is not to script every
agent action but to make the *next* agent that walks in succeed without
having to re-derive the rules.

These principles are enforced by `/mol-agent:check`. Run it against
any project that has been bootstrapped with the mol harness to check
compliance. (The `claude-plugin/` marketplace repo itself has no
harness — use `/mol-plugin:check` for its self-audit.)

## 0. Harness Engineering

The harness should *constrain*, not *prescribe*.

- Give the agent **principles** (what's safe, what's risky, why).
- Give the agent **layers** (what kind of artifact lives where).
- Give the agent **judgment criteria** (when to write tests first, when
  to delegate, when to stop and ask).
- Do **not** force a fixed matrix of files, agents, or steps onto every
  project. The shape of the harness should follow the shape of the
  repository it lives in.

A skill or agent that prescribes ten exact steps is brittle. A skill
that names three principles and trusts the agent to apply them is
durable. Prefer the second.

## 1. Four-Zone Layering

Every well-shaped repository separates four kinds of content. Mixing them
poisons future agents because they cannot tell what they are reading.

```
┌──────────────┐  public-facing documentation: tutorials, API docs,
│   docs/      │  user guides, onboarding. Written for human readers
│              │  who do not work on the agent harness.
└──────────────┘
┌──────────────┐  internal agent context (passive): notes, decisions,
│  .agent/     │  contracts, handoffs, rubrics, debt, open questions,
│              │  project map. Outlives any single feature.
└──────────────┘
┌──────────────┐  Claude Code runtime + active artifacts: skills,
│  .claude/    │  agents, hooks, settings, AND specs/ (alive, ticked
│              │  off as /mol:impl progresses, deleted on completion).
└──────────────┘
┌──────────────┐  thin entry router: what is this repo, where do things
│  CLAUDE.md   │  live, what must never be changed casually. Routes;
│              │  never embeds.
└──────────────┘
```

The split between `.agent/` and `.claude/` is **active vs passive**:
notes outlive any single feature and stay; specs are intentionally
ephemeral and disappear when their work is done.

### Layering rules (L)

- **L1.** Public user docs live under `docs/`. Passive internal
  context (notes, decisions, contracts, handoffs, rubrics, debt log,
  open questions) lives under `.agent/`. Runtime configuration AND
  active runtime artifacts (skills, agents, hooks, settings, and
  specs/) live under `.claude/`. Each zone reads, writes, and
  references its own kind only.

- **L2.** Do not pollute `docs/` with agent contracts, handoffs,
  rubrics, specs, working memory, temporary plans, or private
  reasoning. Do not put public-user prose in `.agent/` or
  `.claude/`. Do not put long-lived knowledge in `.claude/` — that
  zone is for *behavior* and *active artifacts*, not for archival
  state.

- **L3.** `CLAUDE.md` is a short router (≤ ~150 lines is a good
  budget). It answers: *what is this repo?*, *where do things live?*,
  *what must never change casually?*, *what is the default workflow?*
  It links to files; it does not embed them. A CLAUDE.md that grows
  past two screens is a smell — promote sections to `.agent/` and
  link.

- **L4.** Specs are alive. `/mol:spec` writes them under
  `.claude/specs/` with a checkbox-tracked Tasks section. `/mol:impl`
  ticks each box as work completes and deletes the spec file (plus
  its INDEX entry) on completion. A spec is never archived to
  `docs/` or `.agent/`; once `done`, it is removed because the
  information that mattered is now in code, tests, and (when
  non-obvious) `.agent/notes.md`.

## 2. Two-Layer Model

```
user ──▶ /skill  (workflow + orchestration, user-invocable)
              │
              ▼
          agent  (single expertise axis, never user-invocable directly)
              │
              ▼
       tools (Read, Grep, Glob, Bash, sometimes Write/Edit)
```

- **Skill** = a *verb* the user types (`/mol:impl`, `/mol:fix`). Owns
  the *procedure*: scope assessment, ordering, parallel fan-out, when
  to delegate, how to aggregate. A skill is short — it reads
  CLAUDE.md, classifies the request, calls one or more agents,
  summarizes.
- **Agent** = a *role* with one expertise. Owns *checks, knowledge,
  and edits inside its domain*. Stateless across invocations. Reached
  only through a skill.

The two layers must not collapse. A skill must not contain expert
knowledge that belongs in an agent. An agent must not contain workflow
choreography that belongs in a skill.

## 3. Why This Split

1. **Reusability.** Multiple skills delegate to the same agent (the
   `architect` agent is used by `/mol:impl`, `/mol:refactor`, and
   `/mol:review` — directly or via `--axis=arch`). One source of
   architecture rules, read by many skills.
2. **Parallelism.** Review-style skills fan out to multiple agents in
   one message; agents have isolated context windows so the
   orchestrator stays small.
3. **Safety.** Read-only agents (`architect`, `optimizer`, `scientist`,
   `compute-scientist`, `undergrad`, `pm`, `ci-guard`, `reviewer`)
   cannot accidentally edit code; write-capable agents (`tester`,
   `documenter`) have edit rights only inside their declared scope.

## 4. Knowledge Hierarchy

```
.agent/notes.md   evolving decisions, captured by /mol:note
        │
        ▼ promotion when stable
   CLAUDE.md  ◀──────── thin router — read by every agent
        │
        ▼
   skills/agents read from it; never duplicate it

.claude/specs/    active, checkbox-tracked plans; written by /mol:spec,
                  ticked + deleted by /mol:impl. Not knowledge —
                  ephemeral work-in-flight.
```

Every agent's first line is *"Read CLAUDE.md and the project's notes
file before running any checks."* Project-specific facts live in
CLAUDE.md (with the `mol_project:` frontmatter for machine-readable
keys) or in the notes file. Agent prompts hold only **unique
knowledge** the agent needs that does not belong in CLAUDE.md
(tolerances, anti-pattern catalogs, grep heuristics, floating-point
conventions).

## 5. Design Rules

### Layering (L)

See Section 1.

### Orthogonality (O)

- **O1.** Each agent owns exactly one expertise axis. If two agents
  would both answer the same question, merge or split until each has a
  unique axis.

  *Worked example — `architect` vs `librarian` boundary.* Both
  agents read the same shared artifact (`.agent/architecture.md`,
  the project blueprint maintained by `/mol:map`), but they answer
  different questions and are wired into different scheduling
  points:

  - `architect` answers *"is the code currently in **compliance**
    with the layering rules?"* — this is the review/refactor-time
    validator. Output: emoji-prefixed findings.
  - `librarian` answers *"given a planned new capability, where
    does it go (**placement**) and is it already there (reuse)?"* —
    this is the spec-time consultant. Output: a fixed
    four-section advisory report.

  Sharing the artifact does not violate O1 because the verbs are
  disjoint (validate vs. consult); the unique-axis rule is about
  *the question answered*, not *the data read*.
- **O2.** Agents do not call other agents. The skill is the only
  orchestrator. *Exception:* a write-capable agent may produce code
  that a read-only agent later validates — but the validation call is
  made by the parent skill, not by the writer.
- **O3.** A skill names its delegates explicitly. There is no implicit
  routing.
- **O4.** A skill does not contain expert knowledge. If a check is
  non-trivial enough to need worked examples or reference data, it
  belongs in an agent.

### Knowledge locality (K)

- **K1.** CLAUDE.md is the single thin source of truth for stable
  rules. Every agent reads it first.
- **K2.** The project's notes file holds evolving decisions; `/mol:note`
  enforces conflict detection and promotes stable entries into
  CLAUDE.md (then deletes from the notes file).
- **K3.** Agent prompts contain only *unique knowledge* not in CLAUDE.md
  (heuristics, grep patterns, tolerances, anti-patterns). They never
  duplicate architecture rules.
- **K4.** Skill prompts contain only *workflow* (steps, when to
  delegate, output format). They never restate domain rules.

### Capability hygiene (C)

- **C1.** Read-only agents declare only Read/Grep/Glob/Bash. Granting
  Write/Edit must be justified by the agent's role (e.g. `tester`
  writes tests; `documenter` writes docs).
- **C2.** A skill that writes (specs, code, docs, tests, notes) must
  say so in its `description` frontmatter so the user knows what will
  change.
- **C3.** Diagnose-only skills (`/mol:debug`) state explicitly that
  they never edit. Enforced in the skill's procedure, not just in the
  description.

### Workflow shape (W)

- **W1.** Plan → Build → Verify → Document → Memory is the canonical
  loop. The `mol` plugin covers each phase.
- **W2.** RED before GREEN: `/mol:impl` must call the `tester` agent
  to write failing tests before any implementation is attempted.
- **W3.** Reviews fan out in parallel. `/mol:review` issues all
  delegate calls in one message.
- **W4.** Architecture validation happens at four points: scope
  assessment (planning), **spec-time librarian consult**
  (`/mol:spec` Step 4.5 — placement and reuse advice against the
  project blueprint at `.agent/architecture.md`), after
  implementation, and after refactor. The spec-time consult is the
  fourth scheduling point and was added to plug the planning-phase
  visibility gap that produced duplicate modules and wrong-layer
  placement in large projects.
- **W5.** Bug fixing is a separate, minimal loop (`/mol:debug` →
  `/mol:fix`) not a degenerate case of `/mol:impl`.

### Output format (F)

- **F1.** Review-style agents output severity-sorted lines prefixed
  with an emoji: 🚨 Critical, 🔴 High, 🟡 Medium, 🟢 Low.
  ```
  🚨 file:line — message
    Fix: ...
  ```
  Skills aggregating multiple agents render a 🚨 / 🔴 / 🟡 / 🟢 table
  and a verdict (APPROVE / REQUEST CHANGES / BLOCK).
- **F2.** Skills end with a one-line user-facing summary suitable for
  scanning: files changed, tests passing, remaining TODOs.

### Idempotency (I)

- **I1.** Bootstrapping skills must be safe to re-run. They detect
  existing files and offer merge / replace / keep per entry instead of
  duplicating or silently overwriting.
- **I2.** Memory skills (notes promotion) must detect duplicates and
  contradictions before writing.
- **I3.** Generators that write managed sections must use stable
  markers so re-runs update in place rather than appending.

## 6. Re-Examination Checklist

`/mol-agent:check <path>` walks this checklist against any `.claude/`
tree. Output one finding per row: `<emoji> file:line — message` (🚨 /
🔴 / 🟡 / 🟢).

### Layering (L)

- [ ] Are public docs under `docs/`? Is `docs/` free of agent
      contracts, handoffs, working memory, rubrics, or specs? (L1, L2)
- [ ] Are passive internal artifacts (notes, decisions, debt log,
      handoffs, rubrics, contracts) under `.agent/`? (L1)
- [ ] Are specs under `.claude/specs/` with a checkbox-tracked Tasks
      section? Are completed specs deleted (not archived)? (L4)
- [ ] Is `.claude/` free of long-lived knowledge? (only skills,
      agents, hooks, settings, and active specs) (L2)
- [ ] Is CLAUDE.md a thin router, not a manual? Does it route to
      `docs/`, `.agent/`, and `.claude/` rather than embedding their
      content? (L3)

### Layer presence

- [ ] Are skills (`.claude/skills/*/SKILL.md`) and agents
      (`.claude/agents/*.md`) both present, or is the project
      conflating the two?
- [ ] Does every user-visible verb live in a skill, not an agent?
- [ ] Is there a CLAUDE.md serving as the entry router?
- [ ] Does CLAUDE.md start with a `mol_project:` frontmatter block (if
      the project opts into the mol plugin contract)?

### Orthogonality

- [ ] List each agent and the question it answers. Are any two
      answering the same question? (O1)
- [ ] Do agents invoke other agents? (O2)
- [ ] Do skills name delegates explicitly? (O3)
- [ ] Does any skill embed expert knowledge that belongs in an agent?
      (O4)

### Knowledge

- [ ] Do agents read CLAUDE.md first? (K1)
- [ ] Is there a `/mol:note`-equivalent skill enforcing conflict
      detection and promotion? (K2)
- [ ] Do agent prompts duplicate CLAUDE.md content? (K3)
- [ ] Do skill prompts restate domain rules instead of pointing to
      CLAUDE.md? (K4)

### Capability

- [ ] Are read-only agents declared with read-only tools? Any
      unjustified Write/Edit? (C1)
- [ ] Does each writing skill announce what it writes? (C2)
- [ ] Are diagnose-only skills enforced in their procedure? (C3)

### Workflow

- [ ] Plan / Build / Verify / Document / Memory — is each phase
      covered? (W1)
- [ ] Does the implementation skill enforce RED before GREEN? (W2)
- [ ] Do review skills fan out in parallel? (W3)
- [ ] Are architecture checks scheduled at the three required points?
      (W4)
- [ ] Are debug and fix kept as separate minimal loops? (W5)

### Output

- [ ] Do review agents emit `<emoji> file:line` lines using 🚨 / 🔴 /
      🟡 / 🟢? (F1)
- [ ] Do skills end with a one-line user-facing summary? (F2)

### Idempotency

- [ ] Is the bootstrap skill safe to re-run? (I1)
- [ ] Does the notes skill detect duplicates and contradictions before
      writing? (I2)

### Per-project domain coverage

For a domain-heavy project, verify there is one agent per *axis of
risk* the project actually has. Every axis where the project can fail
silently must have its own agent, and every agent must map to a real
risk. No filler agents.

## 7. Anti-Patterns

These show up in repositories that were bootstrapped without harness
discipline. The audit flags each as 🟡 or higher.

- **Template sprawl.** A bootstrap dropped twelve skills and ten
  agents into a one-week-old repo, most of which never get invoked.
  Cure: start small, grow on demand.
- **Knowledge in `.claude/`.** Architecture rules, decisions, or
  domain notes embedded in a skill/agent body, or written into
  `.claude/` outside of `.claude/specs/`. Cure: promote to CLAUDE.md
  or `.agent/` and leave a reference.
- **Specs in `.agent/` or `docs/`.** Specs are alive — they belong in
  `.claude/specs/`. Putting them next to passive notes is a category
  error. Cure: move under `.claude/specs/` and add a Tasks checklist.
- **Specs without checkboxes.** A spec with no Tasks section can't be
  ticked, can't be tracked, and can't be auto-deleted. Cure: re-run
  `/mol:spec` to add a concrete checklist.
- **Done specs left around.** A spec marked `done` but still on disk
  is clutter. Cure: `/mol:impl` should have deleted it; if it
  didn't, delete manually and capture any non-obvious context with
  `/mol:note`.
- **Contracts in `docs/`.** Agent handoff contracts or review rubrics
  living next to user tutorials. Cure: move under `.agent/`.
- **CLAUDE.md as manual.** A 600-line CLAUDE.md that nobody reads.
  Cure: split into `.agent/architecture.md`, `.agent/conventions.md`,
  etc. and link.
- **Fake precision.** A bootstrap that invented architecture rules
  with no evidence in the codebase. Cure: record as an open question
  in `.agent/open-questions.md` instead.
- **Agent calling agent.** Implicit routing through agent bodies.
  Cure: hoist orchestration into a skill.
- **One-shot skills with no idempotency.** Re-running them duplicates
  files or clobbers user content. Cure: detect and merge.
