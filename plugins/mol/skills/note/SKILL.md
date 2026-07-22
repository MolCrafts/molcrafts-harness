---
name: note
description: "Sync a decided rule into the harness (CLAUDE.md + `.claude/notes/**`) — supersede/delete fossils, never append-only. Free-form: 记下来/约定变了/we decided/supersede. Writes harness knowledge only."
argument-hint: "<the decision or correction to capture>"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:note — Harness Knowledge Sync

Read CLAUDE.md → parse `mol_project:` (`$META`).

**Not a diary.** One live rule per topic; git is the archive. Every run: reconcile → clean → place → rewrite.

## Write surface

| Edit | Never |
|---|---|
| `CLAUDE.md` (preserve `mol_project:` unless decision renames a path field) | Project source, tests, public `docs/` |
| `$META.notes_path` (default `.claude/notes/notes.md`) | `.claude/specs/**` |
| `.claude/notes/<topic>.md` (create/rewrite/delete) | Plugin agent/skill definitions |
| `architecture.md` — only strike a false one-line claim; full rebuild → `/mol:map` | Binaries / generated assets |

## Procedure

### 1. Parse

From `$ARGUMENTS` + conversation:

- **Rule** — one imperative for the next agent
- **Topic key** — slug (`naming-n-atoms`, `arch-forces-layout`, …)
- **Kind** — `additive` | `supersede` | `retract` | `correct`
- **Evidence** — paths/symbols if any

Overturn language ("改成…", "不再…", "supersede") → force `supersede`. State parse briefly before writing.

### 2. Inventory

Read before write: full `CLAUDE.md`, notes file, `.claude/notes/**` overlapping the topic (list paths first). Optional grep for symbol liveness.

Tag each hit: `same` | `conflict` | `stale` | `predecessor` | `unrelated`.

### 3. Reconcile — new decision wins

| relation | action |
|---|---|
| same | No new entry; still run stale sweep |
| conflict / predecessor | Delete or rewrite in place — never a second contradictory bullet |
| stale | Delete entry (or empty topic page) |
| open-question answered | Remove those bullets |
| unrelated | Leave |

Do **not** ask which is correct when the user just decided. Ask only if two *new* alternatives are still open.

### 4. Stale sweep (every run)

- Dead path/symbol refs → delete/rewrite
- Fully restated in CLAUDE.md → delete notes staging
- Duplicate cluster → one canonical home (Step 5)
- Orphan superseded topic pages → delete file + links

### 5. Single canonical home

| Stability | Home |
|---|---|
| Stable, short, every agent must see | `CLAUDE.md` (thin router) |
| Stable, long | `.claude/notes/<topic>.md` + one link from CLAUDE.md |
| Evolving | `notes.md` — **rewrite** same topic key; don't date-stack clones |
| Module map | Prefer `/mol:map`; one-line claim fix only |

Never leave the same rule in both notes.md and CLAUDE.md.

### 6. Write

1. Remove superseded/stale/dupes.
2. Edit in place when `<!-- mol:note:topic:<key> -->` or same heading exists; append only if topic is new.
3. Promote → write canonical home, delete staging copy.
4. Over-budget CLAUDE.md → move bulk to topic page + link.
5. Touch bootstrap managed markers only if the decision is about that managed content.

```markdown
<!-- mol:note:topic:<topic-key> -->
## [YYYY-MM-DD] Short title

Why (if non-obvious).

**Rule**: <imperative>

**Supersedes**: <old rule or path, if any>
```

CLAUDE.md entries: undated bullets, no diary stack.

### 7. Map handoff

Layout/layer/public-surface change → patch false `architecture.md` claim **or** recommend/invoke `/mol:map`. No architecture essays in notes.md.

### 8. Self-check then report

No contradictions; no notes+CLAUDE dupes; no dead refs; CLAUDE still thin; specs untouched.

```
/mol:note [<topic-key>]: <added|rewrote|promoted|retracted|no-op>
  canonical: <path> | cleaned: N | superseded: N | map: unchanged|patched|→/mol:map
```

## Guardrails

- Sync ≠ append. New decision wins; git keeps history.
- Harness only. Idempotent re-run → no-op or tiny sweep, not a clone.
- Ask only for ambiguous *new* choices.
