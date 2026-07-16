---
name: docs
description: Documentation audit and writing — docstrings in the project's documented style plus narrative tutorials. Writes docs and code comments.
argument-hint: "[path, spec slug, or feature name]"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:docs — Documentation

Read CLAUDE.md → parse `mol_project:` (`$META`). Pick one mode — do not mix.

## Mode A — Docstring / API audit

Delegate to `documenter` agent in audit mode. Loads style rules for `$META.doc.style`:

- `google` — Google-style Python: short summary, blank line, Args/Returns/Raises sections, types in signatures not prose.
- `rustdoc` — `# Examples`, `# Errors`, `# Panics`; `///` items, `//!` modules; math via `\\[...\\]`.
- `jsdoc-tiered` — three tiers per symbol kind:
  - **Full** — class + top-level function declarations.
  - **Brief** — one-line for internal helpers.
  - **Inline** — beside non-obvious expressions only.
- `doxygen` — `@brief`, `@param` with units, `@return`, `@file` headers.

Audit checks every public symbol for:
1. Required tier present.
2. Unit annotations on every physical quantity (if `$META.science.required`).
3. Matches current implementation (no stale references).
4. No dangling cross-references.

Output: `<emoji> file:line — message` with `Fix:` lines (🚨 / 🔴 / 🟡 / 🟢 = Critical / High / Medium / Low).

## Mode B — Narrative tutorial

Delegate to `documenter` agent in tutorial mode. Before delegating, collect:

1. Relevant spec in `$META.specs_path` (if exists).
2. Implementation files defining current behavior.
3. Existing user-facing docs on the same topic.
4. Real example program the tutorial will reference.

Missing file/target/plot/API → do not mention as if it exists. Correct the tutorial or create the artifact first.

Tutorial rules:
- Lead with problem + intuition; introduce notation after reader knows why it matters.
- Prose over lists. Bullets only for genuine enumeration.
- Every symbol defined before use.
- Reference a concrete, runnable example.
- Math: standard Markdown LaTeX (`$...$` inline, `$$...$$` display). No Doxygen `\f` markers.

**Science content (if `$META.science.required` or topic is scientific):** agent must produce two equal-weight parts — *Part 1* self-contained textbook derivation that an undergrad-level newcomer can verify *without reading the code*; *Part 2* the project / code mapping. Part 1 is a verification artifact — must be **completely equivalent** to the implementation (equations, signs, units, conventions). Discrepancies = findings (fix the wrong side), not stylistic notes. See `agents/documenter.md` § "Science content: mandatory two-part structure" + § "Equivalence rule".

End with one-line summary: files written, example referenced, TODOs. Science tutorials also report the equivalence-rule check (which equations vs. which code locations).
