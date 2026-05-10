---
description: Inspect a repository's agent harness and report what's installed, what's missing, what's misaligned. Combines a quick presence/health check with the full harness-engineering design audit (layering + two-layer model + orthogonality + knowledge + capability + workflow + output + idempotency). Read-only.
argument-hint: "[<project-root>]"
---

# /mol-agent:check — Harness Inspection

Inspect a repository's agent harness — `docs/`, `.claude/notes/`, `.claude/`,
`CLAUDE.md` — and produce one report covering both:

1. **Health** — is the harness installed and internally consistent?
2. **Design** — does it follow the contract in
   `${CLAUDE_PLUGIN_ROOT}/rules/design-principles.md`?

Apply to any project that uses the mol harness. **Not** for the
`claude-plugin/` marketplace repository itself — that has no
CLAUDE.md / `.claude/notes/` / `.claude/specs/` to inspect; use
`/mol-plugin:check` for the marketplace's own self-audit.

This skill is **read-only**. It reports findings; it never edits. Use
`/mol-agent:bootstrap` (first time) or `/mol-agent:update` (idempotent
re-run) to apply fixes.

## Procedure

### Phase 1 — Health (presence & consistency)

Cheap checks first; fail-fast if the harness isn't there at all:

- **Presence**: do `CLAUDE.md` and at least one of `.claude/notes/`,
  `.claude/specs/` exist? If none, report *"no harness installed —
  run `/mol-agent:bootstrap`"* and stop. No design rules apply yet.
- **`mol_project:` frontmatter** (when the project opted into the
  `mol` contract): is the YAML block at the top of CLAUDE.md
  parseable? Are required fields populated (per
  `${CLAUDE_PLUGIN_ROOT}/rules/claude-md-metadata.md`)? Flag missing
  or malformed fields as 🔴.
- **Spec INDEX consistency**: for every file in `.claude/specs/`,
  is it listed in `INDEX.md`? For every entry in `INDEX.md`, does
  the file still exist? Mismatches are 🟡.
- **Status / checkbox consistency** on each spec:
  - `status: done` + file still present → 🟡 (`/mol:impl` should
    have deleted it)
  - `status: done` + unchecked task boxes → 🔴 contradiction
- **Stable markers**: every `<!-- mol-agent:bootstrap:managed begin -->`
  block must have a matching `end -->`. Orphans are 🔴.

### Phase 2 — Design (full checklist)

Read `${CLAUDE_PLUGIN_ROOT}/rules/design-principles.md` for the full
checklist. Walk each section against the target tree.

#### Layering (L)

Inspect the four zones, keeping the **active vs passive** split
inside `.claude/` in mind:

- `docs/` — does it exist? Does it contain only public-user content
  (tutorials, API reference, user guides)? Flag any agent contract,
  handoff, working memory, rubric, **or spec** living under `docs/`.
  (L1, L2)
- `.claude/notes/` — passive internal context. Look for `notes.md`,
  `architecture.md`, plus any `decisions/`, `contracts/`,
  `handoffs/`, `rubrics/`, `debt/`, `open-questions.md`. Is it free
  of public-user prose? Is it free of active runtime artifacts
  (specs)? (L1)
- `.claude/specs/` — active runtime artifacts. For each spec:
  - Does it have a **Tasks** section with checkboxes? (L4) Flag if
    missing.
  - (Status/checkbox consistency was already checked in Phase 1.)
- `.claude/agents/`, `.claude/skills/`, `.claude/hooks/`,
  `.claude/settings.json` — Claude Code's own runtime config. Flag
  long-lived domain knowledge embedded inside skill or agent bodies
  that belongs in `.claude/notes/` or CLAUDE.md instead. (L2). Also
  flag if project notes have been mixed into `.claude/agents/` (a
  common newcomer mistake — `agents/` is for *agent definitions*
  loaded by Claude Code, not for project notes; project notes go in
  `.claude/notes/`).
- Anything *else* directly under `.claude/` (a `.md` or directory
  not listed above) — flag as zone-mixing: passive content goes in
  `.claude/notes/`, active in `.claude/specs/`, runtime config in
  its conventional subfolders. Loose files at `.claude/` root are
  always a smell. (L1, L2)
- `CLAUDE.md` — line-count it. ≤ ~150 lines is the soft budget. Flag
  if CLAUDE.md embeds large rule sets, full architecture diagrams,
  long examples, or anything else that should be linked rather than
  inlined. (L3)

For projects that opt into the `mol` plugin contract, confirm
CLAUDE.md starts with a `mol_project:` frontmatter block, and that:

- `specs_path` points under `.claude/specs/` (canonically just
  `.claude/specs/`). Flag if set to `docs/`, `.claude/notes/`, or
  bare `.claude/` — that's a zone-mixing error.
- `notes_path` points under `.claude/notes/` (canonically
  `.claude/notes/notes.md`). Flag if set under `.claude/specs/`,
  `.claude/` root (e.g. `.claude/NOTES.md`), `docs/`, or anywhere
  outside `.claude/notes/` — passive content does not belong in
  the active or runtime-config zones. This is the rule whose
  violation `/mol:map` used to silently propagate; do not enable
  it.

#### Layer presence

- Do `skills/*/SKILL.md` and `agents/*.md` both exist (when the
  project chose to ship custom skills/agents)?
- Does every user-invocable verb live in `skills/`, not in `agents/`?
- Is there a CLAUDE.md acting as a router?

#### Orthogonality (O)

- O1 — List each agent's single axis. Flag any overlap.
- O2 — Grep agent bodies for `delegate to .* agent` / `invoke .*-agent`
  patterns. Agents must not call agents.
- O3 — Each skill names its delegates explicitly (no implicit
  routing).
- O4 — Skills contain no expert knowledge (worked examples, reference
  data, tolerances). If found, flag as an agent extraction.

#### Knowledge (K)

- K1 — Every agent's first non-frontmatter line mentions reading
  CLAUDE.md (and the project's notes file).
- K2 — A `/mol:note`-equivalent skill exists and enforces conflict
  detection + stale sweep + promotion.
- K3 — Agent prompts do not duplicate CLAUDE.md content.
- K4 — Skill prompts do not restate domain rules; they reference
  CLAUDE.md.

#### Capability (C)

- C1 — Read-only agents declare only Read/Grep/Glob/Bash (plus
  optionally WebSearch / WebFetch for the scientist). Flag Write/Edit
  on any agent whose role is not write-capable.
- C2 — Every writing skill's `description` frontmatter states what
  it writes.
- C3 — Diagnose-only skills enforce read-only in their procedure
  body, not just in the description.

#### Workflow (W)

- W1 — Plan (spec/litrev) / Build (impl/fix/refactor) / Verify
  (arch/review/test/perf) / Document (docs) / Memory (note) — each
  phase has at least one skill.
- W2 — The implementation skill calls the `tester` agent before any
  implementation.
- W3 — Review-style skills fan out in parallel (one message,
  multiple tool calls).
- W4 — Architecture validation is scheduled at: (a) scope assessment
  in `impl`, (b) post-impl, (c) post-refactor.
- W5 — Debug and fix are separate skills; fix does not subsume debug.

#### Output (F)

- F1 — Review-style agents output `<emoji> file:line — message` where
  emoji is 🚨 / 🔴 / 🟡 / 🟢 (Critical / High / Medium / Low).
- F2 — Skills end with a one-line user-facing summary.

#### Idempotency (I)

- I1 — Bootstrap-style skills detect existing files and offer
  merge / replace / keep instead of overwriting. Look for stable
  markers (`<!-- ... managed begin -->`) on managed sections.
- I2 — The notes skill does conflict + duplicate detection before
  writing.
- I3 — Generators write managed sections via stable markers.

#### Anti-patterns

Spot-check for the patterns listed in
`rules/design-principles.md` § 7:

- template sprawl (large skill/agent set on a tiny repo)
- knowledge in `.claude/` (rules embedded in skill/agent bodies that
  should be in CLAUDE.md or `.claude/notes/`)
- contracts in `docs/`
- CLAUDE.md as manual
- fake precision (architecture rules invented without evidence)
- agent calling agent
- non-idempotent generators

#### Per-project domain coverage

Identify each project-specific axis of risk and confirm each has an
agent. For the plugin itself, the thirteen generic axes
(architecture / tests / science / numerics / performance / docs /
user-experience / product / CI-parity / visual-design / security /
hygiene / review) are the expected coverage. Visual-design and
security are detect-then-run — they only contribute to a project's
review when the diff actually contains frontend code or an attack
surface.

## Output

Emit severity-sorted findings (🚨 Critical, 🔴 High, 🟡 Medium, 🟢
Low):

```
<emoji> <path> — message
  Rule: <rule id, e.g. H (health), L2, O2, K3, I1>
  Fix: <recommendation, often "run /mol-agent:update">
```

End with a summary table:

| Rule family       | 🚨 | 🔴 | 🟡 | 🟢 |
|-------------------|----|----|----|----|
| Health (H)        |    |    |    |    |
| Layering (L)      |    |    |    |    |
| Orthogonality (O) |    |    |    |    |
| Knowledge (K)     |    |    |    |    |
| Capability (C)    |    |    |    |    |
| Workflow (W)      |    |    |    |    |
| Output (F)        |    |    |    |    |
| Idempotency (I)   |    |    |    |    |

Verdict: APPROVE / REQUEST CHANGES / BLOCK.

End with a one-line user-facing summary (F2).
