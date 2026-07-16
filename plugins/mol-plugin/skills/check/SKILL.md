---
name: check
description: Audit the Claude-first marketplace and its Codex compatibility metadata. Runs the deterministic dual-manifest validator, then reviews semantic boundaries that a script cannot judge. Use after plugin, skill, agent, hook, or marketplace edits; read-only.
argument-hint: "[<plugin>]"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol-plugin:check — Marketplace Self-Check

Validate repository contracts without editing. The script owns syntax, paths, names, versions, and cross-format consistency; this skill owns semantic accuracy, responsibility boundaries, and actionable reporting.

Scope: no argument → both registered plugins. `<plugin>` → restrict semantic review to that plugin after the repository-wide deterministic gate.

## Procedure

### 1. Locate the marketplace root

Walk upward from the current directory until `.claude-plugin/marketplace.json` exists. No match → BLOCK with an instruction to run from this repository.

Validate `<plugin>` against the authoritative Claude marketplace. Unknown name → print available names and stop.

### 2. Run the deterministic gate

Run the validator bundled with this plugin:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate_repository.py" --root <root>
```

When working directly from source and `${CLAUDE_PLUGIN_ROOT}` is unavailable, use `<root>/plugins/mol-plugin/scripts/validate_repository.py`.

The script owns:

- both marketplace schemas and matching plugin order
- Claude and Codex manifest names, versions, required fields, and source paths
- shared skill frontmatter, names, H1s, adapter directives, and references
- agent frontmatter, model tiers, read-only tool boundaries, and knowledge bootstrap
- default hook JSON shape
- absence of duplicated Codex skill trees

Any script error → `FIX REQUIRED`. Preserve its exact path and message in the report. Do not re-implement or second-guess deterministic checks in prose.

### 3. Review semantic contracts

For each in-scope plugin, read its README, manifests, `skills/*/SKILL.md`, `skills/CODEX.md`, agents, and rules needed by those skills. Judge only what syntax cannot establish:

- **Responsibility:** plugin and skill descriptions match actual behavior; each skill owns one user-facing workflow.
- **Boundaries:** read-only/write behavior is explicit; neighboring skills do not claim the same mutation or verdict.
- **Delegation:** each agent has one expertise axis; producer/reviewer ownership matches `rules/agent-design.md`; workflows do not bypass required independence.
- **Safety:** approval, clean-tree, destructive-action, push, tag, and release gates remain explicit and ordered.
- **Progressive disclosure:** large rules live in shared rule/reference files; SKILL.md links them instead of copying them.
- **Cross-runtime fidelity:** `skills/CODEX.md` translates runtime concepts without changing the Claude-first workflow contract.
- **Documentation truth:** READMEs list existing capabilities and do not promise unimplemented plugins, skills, hooks, or MCP servers.

Do not flag tone or formatting preferences unless they obscure an execution rule.

### 4. Report

Sort findings by severity:

```text
<emoji> <path> — <message>
  Rule: <deterministic validator | responsibility | boundaries |
         delegation | safety | progressive-disclosure |
         cross-runtime-fidelity | documentation-truth>
  Fix: <one concrete recommendation>
```

Severity:

- 🚨 invalid metadata, unsafe destructive behavior, or a missing required gate
- 🔴 broken workflow contract, duplicated responsibility, or runtime incompatibility
- 🟡 drift or ambiguity that should be corrected before release
- 🟢 optional cleanup with no behavior impact

Render counts per plugin plus one `repository validator` row. Verdict is `PUBLISH-READY` only when the deterministic gate passes and no 🚨/🔴 semantic finding remains; otherwise `FIX REQUIRED`.

End with: `/mol-plugin:check: <PUBLISH-READY | FIX REQUIRED> — <N> errors, <M> warnings`.

## Guardrails

- Read-only: never patch, format, stage, commit, tag, install, or publish.
- Keep deterministic rules in `scripts/validate_repository.py`, not duplicated in this skill.
- Do not treat the Codex marketplace as authoritative; Claude metadata remains the source contract.
- Do not invent new rules during an audit. A recurring new class belongs in the validator or this skill through a separate reviewed change.
