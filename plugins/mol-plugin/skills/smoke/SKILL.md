---
name: smoke
description: Verify that the MolCrafts marketplace and both plugins validate and install correctly in Claude Code and Codex without changing user configuration. Use after metadata, skill, hook, or release changes; supports a static-only mode for fast local checks.
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol-plugin:smoke — Cross-Runtime Plugin Smoke Test

Validate source structure, run each platform's native manifest checks, and install both Codex plugins in an isolated temporary home. This complements `/mol-plugin:check`: `check` audits repository contracts, while `smoke` proves the packaged marketplace can be discovered and installed.

## Procedure

### 1. Locate the marketplace root

Start at the current directory and walk upward until `.claude-plugin/marketplace.json` exists. Treat that directory as `<root>`. No match → BLOCK with an instruction to run from this repository.

Parse `$ARGUMENTS`:

- no argument → full smoke test
- `--static-only` → run Steps 2–3 and skip isolated installation
- anything else → print usage and stop

### 2. Run deterministic repository validation

From `<root>`, run:

```bash
python3 plugins/mol-plugin/scripts/validate_repository.py --root <root>
```

Non-zero → BLOCK and relay every finding. Do not continue with partially valid metadata.

### 3. Run Claude Code's native validators

Require the `claude` CLI. Run:

```bash
claude plugin validate <root>
claude plugin validate <root>/plugins/mol
claude plugin validate <root>/plugins/mol-plugin
```

Any error → BLOCK. Warnings remain visible and make the result WARN rather than PASS.

With `--static-only`, report now.

### 4. Install through an isolated Codex home

Require the `codex` CLI. Create a new temporary directory and a `codex-home/` child. Set `CODEX_HOME` only for commands in this step; never export it into the parent shell or use the user's real Codex home.

Run in order:

```bash
CODEX_HOME=<temp>/codex-home codex plugin marketplace add <root> --json
CODEX_HOME=<temp>/codex-home codex plugin list
CODEX_HOME=<temp>/codex-home codex plugin add mol@molcrafts --json
CODEX_HOME=<temp>/codex-home codex plugin add mol-plugin@molcrafts --json
CODEX_HOME=<temp>/codex-home codex plugin list
```

Require the final list to show both plugins as installed and enabled at the versions declared by their manifests.

Inspect the installed `mol` cache and require:

- `skills/CODEX.md`
- every source `skills/*/SKILL.md`
- `agents/`
- `rules/`

Inspect the installed `mol-plugin` cache and require `skills/CODEX.md`, `scripts/validate_repository.py`, and `hooks/hooks.json` when that hook exists in source.

Delete only the temporary directory created by this run. A failed cleanup is WARN, not BLOCK.

### 5. Report

Render one row per gate:

| Gate | Result | Evidence |
|---|---|---|
| repository validator | PASS / BLOCK | error and warning counts |
| Claude marketplace | PASS / WARN / BLOCK | native validator summary |
| Claude `mol` | PASS / WARN / BLOCK | native validator summary |
| Claude `mol-plugin` | PASS / WARN / BLOCK | native validator summary |
| Codex marketplace | PASS / SKIP / BLOCK | resolved marketplace path |
| Codex `mol` install | PASS / SKIP / BLOCK | version + cache path |
| Codex `mol-plugin` install | PASS / SKIP / BLOCK | version + cache path |

Verdict is BLOCK if any required gate blocks, WARN if only warnings remain, otherwise PASS.

End with: `/mol-plugin:smoke: <PASS | WARN | BLOCK> — Claude <state>, Codex <state>`.

## Guardrails

- Never edit plugin source, manifests, marketplaces, or user configuration.
- Never install into the user's real Claude or Codex home.
- Never add, remove, upgrade, publish, commit, tag, or push a real marketplace.
- Never use network access; both marketplace sources are local.
- Keep static validation in `scripts/validate_repository.py`; do not duplicate its checks here.
