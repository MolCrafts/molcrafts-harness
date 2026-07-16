---
name: note
description: Capture an architectural decision into the project's notes file. Detects conflicts with existing notes or CLAUDE.md, cleans up stale notes, and promotes stable rules into CLAUDE.md. Writes notes and (when promoting) CLAUDE.md.
argument-hint: "<what to remember>"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:note — Architecture Note

Read CLAUDE.md → parse `mol_project:` (`$META`).

Resolve notes path: `$META.notes_path` if set, else `.claude/notes/notes.md`. Create file + parent dir if missing.

Notes are **passive internal context** under `.claude/notes/`. Never `docs/` (public). Never `.claude/specs/` (active runtime artifacts; see `/mol:spec`). Notes outlive any single feature; specs do not.

## Procedure

### 1. Conflict check (MANDATORY — before any write)

Read notes file + `CLAUDE.md`. For new note:

- **Duplicate.** Existing note or CLAUDE.md says same thing → tell user, don't add.
- **Contradiction.** Existing rule says opposite:
  ```
  CONFLICT: new note "<X>" contradicts existing "<Y>" in {file}:{line}.
  ```
  Ask which is correct. Then:
  - Update or delete the wrong entry.
  - Wrong entry in CLAUDE.md → fix CLAUDE.md.
  - Wrong entry in notes → delete or rewrite.
- **Supersede.** New note refines/replaces older → update old in-place; do not keep both.

### 2. Scan for stale notes

Every invocation also scans existing entries:

- **Outdated.** Grep to verify note still references live code. Delete notes pointing at dead code.
- **Already promoted.** Rule fully covered by CLAUDE.md → delete the note.
- **Contradicts current code.** Flag for user.

Report any cleanup performed.

### 3. Decide placement

- Stable, proven, verified in code → write directly to CLAUDE.md. Keep CLAUDE.md as thin router (L3): large rule → write `.claude/notes/<topic>.md` + link, don't inline.
- New or evolving → write to notes file.
- Already covered → tell user, do nothing.

### 4. Write the entry

```markdown
---

## [YYYY-MM-DD] Short title

Description of the decision or correction.

**Rule**: the concrete rule to follow.
```

### 5. Promotion check

After writing, scan all notes entries. Promote any that are:

- Verified in current code (grep to confirm).
- Unchanged in recent conversation history.

Promoting = copy rule to appropriate CLAUDE.md section (or `.claude/notes/<topic>.md` page if large enough that inlining bloats CLAUDE.md past router budget), then delete from notes file.

End with one-line summary: captured, cleaned, promoted, notes file path used.
