---
description: Audit and repair CI / pre-commit parity — patches .pre-commit-config.yaml and the CI workflow so every check runs both locally at commit time and remotely, and scaffolds both files for projects that have neither. Write-mode counterpart of the read-only ci-guard agent; writes config files only, never source code.
argument-hint: "[<project-root>]"
---

# /mol:ci-sync — CI / Pre-commit Parity Repair

Read CLAUDE.md → parse `mol_project:` (`$META`). Project root: `$ARGUMENTS`
(default: current directory).

Writes **config files only** (`.pre-commit-config.yaml`,
`.github/workflows/*.yml` or the detected CI equivalent). Never edits source,
tests, or docs. The audit itself belongs to `ci-guard`; this skill applies
what `ci-guard` finds — the same split as `janitor` → `/mol:simplify`.

## Step 1 — Detect project shape

```bash
ls .pre-commit-config.yaml 2>/dev/null
ls .github/workflows/*.yml .gitlab-ci.yml 2>/dev/null
```

Classify:

- **new-project** — neither exists → skip to Step 4.
- **existing-partial** — one exists → audit it, scaffold the other (Step 4),
  then sync.
- **existing-both** — audit and sync (Steps 2–3).

## Step 2 — Audit

Delegate to the `ci-guard` agent on the project root. Collect its findings,
keyed by direction:

- `CI_ONLY` — check runs remotely but not at commit time (lint drift lands
  in CI, not on the dev's machine).
- `PRECOMMIT_ONLY` — hook runs locally but CI never enforces it.
- `VERSION_DRIFT` — same tool, different pinned version on each side.

## Step 3 — Fix gaps

For each `CI_ONLY` gap, add the matching local hook to
`.pre-commit-config.yaml`, using the language-canonical toolchain from
`$META.build` (Python: `ruff` + `ty` + `pytest`; TypeScript: `biome` +
`tsc`; Rust: `cargo fmt` + `clippy` + `cargo check`). Local-tool hooks use
`repo: local` with `language: system` and the exact command from
`$META.build.*` so local and CI run the same invocation. Long-running
checks (full test suite) get `stages: [pre-commit]` with a fast subset, or
are left to `/mol:ship push` — note the choice in the report.

For each `VERSION_DRIFT`, pin the CI install step to the version in the
pre-commit `rev:` (single source of truth: pre-commit pins, CI follows).

For each `PRECOMMIT_ONLY` gap: advisory only. Local-hygiene hooks
(nbstripout, whitespace fixers) are intentionally absent from CI; list them
in the report, change nothing unless the user asks.

## Step 4 — Scaffold (new-project / missing side)

Write the missing file(s) from `$META.build` and `$META.ci`:

- `.pre-commit-config.yaml` — format + lint + type-check hooks from the
  canonical toolchain, `repo: local` for project-pinned tools.
- CI workflow — install → the same checks pre-commit runs → `$META.build.test`,
  on the platform(s) `$META.ci` declares (default: one linux job).

Both sides must invoke identical commands — generate them from one list, do
not hand-write each side.

## Step 5 — Verify

```bash
pre-commit run --all-files
```

Report the exit code. New failures introduced by added hooks are reported as
blockers with a `Suggested agent:` route (`/mol:fix` for code, `/mol:simplify`
for hygiene) — do **not** fix source code here and do not loosen the hook to
make it pass.

## Step 6 — Report

- table of gaps found → action taken (patched / scaffolded / advisory)
- files written
- verify result (PROCEED-shaped or the blocker list)
- suggest pinning the synthesized merge-tier command into `mol_project.ci.local`
  when one was derived

End with the one-line F2 summary: `/mol:ci-sync: <N> gaps — <M> patched, <K> scaffolded; verify <PROCEED | BLOCKED: reason>`.
