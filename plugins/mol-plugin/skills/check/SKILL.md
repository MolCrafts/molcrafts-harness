---
name: check
description: Unified marketplace self-check — deterministic dual-manifest validator, semantic contracts, skill/agent content janitor (safe rewrites in place), and Claude/Codex install smoke. Use after plugin, skill, agent, hook, or marketplace edits.
argument-hint: "[<plugin>] [--static-only] [--no-write]"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol-plugin:check — Marketplace Self-Check

One skill owns the full marketplace audit (structure + content + install smoke). Do not reintroduce separate smoke or content-janitor skills.

| Phase | What | Mutates source? |
|-------|------|-----------------|
| **Structure** | `validate_repository.py` + semantic contracts | no |
| **Content** | Skill/agent prose janitor | safe rewrites only (unless `--no-write`) |
| **Smoke** | Claude native validate + isolated Codex install | no (temp home only) |

## Arguments

```
[<plugin>] [--static-only] [--no-write]
```

- no plugin → every plugin in `.claude-plugin/marketplace.json` for structure semantic + content; smoke always whole marketplace
- `<plugin>` → semantic + content scoped to that plugin; deterministic gate + smoke still whole-repo
- `--static-only` → structure + content only; skip Claude CLI validate and Codex install
- `--no-write` → content phase reports only; do not patch skill/agent files

Unknown plugin name → print available names and stop. Unknown flags → print usage and stop.

## Procedure

### 1. Locate the marketplace root

Walk upward from cwd until `.claude-plugin/marketplace.json` exists. No match → BLOCK: run from this repository.

### 2. Structure — deterministic gate

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate_repository.py" --root <root>
```

When `${CLAUDE_PLUGIN_ROOT}` is unavailable (source checkout):

```bash
python3 <root>/plugins/mol-plugin/scripts/validate_repository.py --root <root>
```

Script owns: both marketplace schemas and plugin order; Claude/Codex manifest names, versions, fields, source paths; skill frontmatter/names/H1s/adapter directives; agent frontmatter, model tiers, read-only boundaries; hook JSON; no duplicated Codex skill trees.

Any script error → record as structure failure. Preserve exact path + message. Do not re-implement the script in prose. Continue only if you can still report later phases without invalid trees; otherwise stop after structure report.

### 3. Structure — semantic contracts

For each in-scope plugin, read README, manifests, `skills/*/SKILL.md`, `skills/CODEX.md`, agents, and rules those skills need. Judge only what syntax cannot establish:

- **Responsibility** — descriptions match behavior; one user-facing workflow per skill
- **Boundaries** — read-only vs write explicit; no two skills claim the same mutation/verdict
- **Delegation** — one axis per agent; producer/reviewer split matches `plugins/mol/rules/agent-design.md`
- **Safety** — approval, clean-tree, destructive, push, tag, release gates explicit and ordered
- **Progressive disclosure** — large rules live in shared rule files; skills link them
- **Cross-runtime fidelity** — `skills/CODEX.md` translates runtime only; does not change Claude-first workflow
- **Documentation truth** — READMEs list real capabilities only

Do not flag tone unless it hides an execution rule.

### 4. Content — skill & agent janitor

Inventory:

- `plugins/<plugin>/skills/<skill>/SKILL.md`
- `plugins/<plugin>/agents/<agent>.md`

Scope to `<plugin>` when given. Skip unparseable frontmatter (structure owns that).

Per file, enforce:

- **Single responsibility** — `description` is one job; multi-verb ("validate AND fix") → flag for split
- **Correct placement** — skills = user verbs; agents = orchestrator roles
- **Actionable language** — imperative "do X when Y"; flag motivational / vague prose; flag pure enumerable paragraphs that should be bullets (not causal prose)
- **Length discipline** — flag only when over ~500 words **and** full of non-actionable prose; genuine dual-skill weld → AMBIGUITY
- **No duplicate responsibility** — pairwise job overlap → flag
- **Shared rules in docs** — rule repeated in 3+ files → should live under `plugins/mol/rules/` (or plugin docs) and be referenced
- **Local rules stay local** — one-skill rule stays in that skill

**Safe rewrites** (unless `--no-write`): language normalization, delete repeated principles, remove motivational tone, replace vague phrasing with imperatives. Tighten language inside `description` / H1; **never** rename the skill or change `argument-hint` / contract meaning.

**AMBIGUITY only (never auto-apply):** split file, skill↔agent move, promote shared content, merge two files, change contract surface.

After writes: re-run the deterministic validator once. New error caused by this phase → `git checkout -- <path>` on the offender and re-flag as AMBIGUITY.

### 5. Smoke — cross-runtime install

Skip entire phase if `--static-only`.

#### 5a. Claude Code native validators

Require `claude` CLI:

```bash
claude plugin validate <root>
claude plugin validate <root>/plugins/mol
claude plugin validate <root>/plugins/mol-plugin
```

Error → smoke BLOCK. Warnings → WARN (do not alone block PUBLISH-READY unless severity is error).

#### 5b. Isolated Codex install

Require `codex` CLI. Create a **new** temp dir + `codex-home/` child. Set `CODEX_HOME` only for these commands — never the user's real Codex home, never export into the parent shell.

```bash
CODEX_HOME=<temp>/codex-home codex plugin marketplace add <root> --json
CODEX_HOME=<temp>/codex-home codex plugin list
CODEX_HOME=<temp>/codex-home codex plugin add mol@molcrafts --json
CODEX_HOME=<temp>/codex-home codex plugin add mol-plugin@molcrafts --json
CODEX_HOME=<temp>/codex-home codex plugin list
```

Final list must show both plugins installed and enabled at manifest versions.

Inspect installed `mol` cache: `skills/CODEX.md`, every source `skills/*/SKILL.md`, `agents/`, `rules/`.

Inspect installed `mol-plugin` cache: `skills/CODEX.md`, `scripts/validate_repository.py`, `hooks/hooks.json` when present in source.

Delete only this run's temp dir. Failed cleanup → WARN, not BLOCK.

Missing `claude` / `codex` CLI when not `--static-only` → smoke BLOCK with install hint (or skip that sub-gate with WARN only if the CLI is optional on this machine **and** document it; prefer BLOCK for release paths).

### 6. Report

Severity-sorted findings:

```text
<emoji> <path> — <message>
  Phase: structure | content | smoke
  Rule: <…>
  Action: none | applied | ambiguity   # content phase
  Fix: <one concrete recommendation>
```

Severity:

- 🚨 invalid metadata, unsafe destructive behavior, missing required gate, install hard-fail
- 🔴 broken workflow contract, duplicated responsibility, runtime incompatibility
- 🟡 drift / ambiguity / smoke warnings
- 🟢 optional cleanup

Smoke table (omit rows when `--static-only`):

| Gate | Result | Evidence |
|---|---|---|
| repository validator | PASS / BLOCK | error/warning counts |
| semantic | PASS / FIX REQUIRED | finding counts |
| content | PASS / FIX REQUIRED | applied / ambiguity counts |
| Claude marketplace / mol / mol-plugin | PASS / WARN / BLOCK / SKIP | native summary |
| Codex marketplace / mol / mol-plugin install | PASS / WARN / BLOCK / SKIP | version + cache |

**Verdict**

- `PUBLISH-READY` — deterministic PASS, no 🚨/🔴 structure or content, smoke not BLOCK (PASS or WARN or SKIP via `--static-only`)
- `FIX REQUIRED` — otherwise

Content AMBIGUITY alone does not force FIX REQUIRED unless it is 🚨/🔴; list outstanding AMBIGUITY counts in the summary.

End with:

```
/mol-plugin:check: <PUBLISH-READY | FIX REQUIRED> — structure <…>, content <applied/ambiguity>, smoke <PASS|WARN|BLOCK|SKIP>
```

## Guardrails

- **Structure & smoke:** never edit plugin source, manifests, marketplaces, or user Claude/Codex config for those phases.
- **Content writes only** under `plugins/*/skills/**` and `plugins/*/agents/**`, and only safe language rewrites (or nothing with `--no-write`).
- **Never** invent architecture (merge/rename/move skills) — AMBIGUITY only.
- **Never** change contract surfaces (`description` meaning, H1 identity, `argument-hint` shape).
- **Never** install into the user's real Claude or Codex home; smoke uses a temp `CODEX_HOME` only.
- **Never** use network for marketplace sources; both are local paths.
- Keep deterministic rules in `scripts/validate_repository.py` only.
- Claude marketplace metadata remains authoritative over Codex.

## Idempotency

Clean tree + `--no-write` → same findings. Full run with writes on already-clean content → zero applied patches.
