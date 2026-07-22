---
name: review
description: "Multi-axis static review with one verdict. Free-form before commit/PR: 看看这 diff/review this — not every casual turn. Optional --axis=. Read-only."
argument-hint: "[<path> ...] [--axis=<name>[,<name>...]]"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:review — Multi-Axis Code Review

Static code review only. Read `CLAUDE.md` and parse `mol_project:` metadata when available.

## 1. Resolve scope

`$ARGUMENTS` may include:

- file path(s)
- directory path(s)
- `--axis=<name>` for one review axis
- `--axis=<a,b,c>` for multiple review axes

If no path is provided, review files from:

```bash
git diff --name-only
````

If no axis is provided, run all applicable axes.

Supported axes:

| Axis       | Agent                                                    |
| ---------- | -------------------------------------------------------- |
| `arch`     | `architect`                                              |
| `perf`     | `optimizer`                                              |
| `docs`     | `documenter` audit mode                                  |
| `ux`       | `undergrad`                                              |
| `api`      | `pm`                                                     |
| `science`  | `scientist`, only when science review is enabled         |
| `numerics` | `compute-scientist`, only when science review is enabled |
| `visual`   | `web-design`, only for frontend/UI files                 |
| `security` | `security-reviewer`                                      |
| `ffi`      | `ffi-guard`, only for files touching a language-binding surface |
| `hygiene`  | `janitor`                                                |

Unknown axis → refuse and list supported axes.

Requested gated axis that is unavailable → refuse and explain.

## 2. Fan out to selected reviewers

Delegate each selected axis to its matching agent.

Each agent should review only its own dimension.

Findings must use this format:

```text
<severity> file:line — message
```

Severity levels:

```text
🚨 Critical
🔴 High
🟡 Medium
🟢 Low
```

Agents may return `N/A` when their axis does not apply to the selected files.

`janitor` also reads `.claude/notes/` and may suggest reusable rule captures.

## 3. Aggregate

Pass all raw reviewer outputs to `reviewer`.

The `reviewer` handles:

* deduplication
* conflict resolution
* severity table
* final verdict
* reusable-rule suggestions from `janitor`

Verdict must be one of:

```text
APPROVE
REQUEST CHANGES
BLOCK
```

`/mol:review` must render exactly what `reviewer` returns.

**No silent debt:** every finding is in-scope for prioritization. Do not drop "pre-existing" issues from the table. Verdict stays honest — known rot that blocks quality is still REQUEST CHANGES / BLOCK when severity warrants.

## 4. Final summary

End with a one-line F2 summary listing:

* reviewed file count
* axes covered
* verdict
* findings by severity
