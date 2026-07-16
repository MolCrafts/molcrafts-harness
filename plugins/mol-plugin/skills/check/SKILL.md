---
name: check
description: Self-check the Claude-first marketplace and its Codex compatibility metadata — validates both marketplace formats, both plugin manifests, every SKILL.md, adapter, and agent definition. Use after editing plugin metadata or workflows; read-only.
argument-hint: "[<plugin>]"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol-plugin:check — Marketplace Self-Check

Walk the marketplace tree and verify structural soundness before publishing. Read-only — reports findings; never edits.

Scope: no argument → every plugin in the authoritative `.claude-plugin/marketplace.json`. With plugin name → just that one. Codex metadata must describe the same plugin set but never replaces the Claude registry.

## Procedure

### 1. Marketplace registries

Read `.claude-plugin/marketplace.json` first:

- top-level required fields present (`name`, `owner`, `plugins`)
- every `plugins[]` entry has `name`, `source`, `version`, `description`
- `source` paths resolve to existing directories
- no two plugins share a `name`

Then read `.agents/plugins/marketplace.json`:

- top-level required fields present (`name`, `interface.displayName`, `plugins`)
- `name` matches the Claude marketplace name
- plugin names match the authoritative Claude registry exactly
- every entry has `source.source: local`, a `source.path` resolving to the same plugin directory, `policy.installation`, `policy.authentication`, and `category`
- installation policy is `AVAILABLE | INSTALLED_BY_DEFAULT | NOT_AVAILABLE`
- authentication policy is `ON_INSTALL | ON_USE`
- no Codex entry stores a duplicate plugin `version` or `description`; those belong to `.codex-plugin/plugin.json`

### 2. Per-plugin metadata

For each plugin under `plugins/`:

- treat `.claude-plugin/plugin.json` as authoritative; require parseable `name`, `version`, and `description`
- require `.codex-plugin/plugin.json`; validate `name`, strict-semver `version`, `description`, `author.name`, `skills: ./skills/`, and required `interface` fields
- both manifest names match the directory name
- both manifest versions match each other; the Claude version also matches `.claude-plugin/marketplace.json`
- descriptions may be platform-specific but must describe the same plugin responsibility
- `keywords` is an array when present
- `apps` and `mcpServers` appear in the Codex manifest only when their companion files exist

### 3. Skills

For each `plugins/<plugin>/skills/<skill>/SKILL.md`:

- YAML frontmatter parses
- `name` present, kebab-case, and equal to the skill directory name
- `description` present and non-empty
- `argument-hint` present (even if `""`); shape built from primitives in any combination:
  - `<arg>` — required positional placeholder; `arg` may be short prose hint (`<feature description>`) or `|`-alternation of literals (`<commit | push | merge>`)
  - `[arg]` — optional positional placeholder; same content rules
  - `[<arg>]` and `<arg> [<arg>]` are explicit composites; allowed
  - whitespace separates positional slots; do not embed parenthetical annotations (move into procedure body)
- H1 is `# /<plugin>:<skill> — <title>` and matches directory name
- file ends with the standard one-line summary convention (F2) — at minimum, procedure mentions an end-of-run summary
- internal `/<plugin>:<verb>` references point at existing skills (this plugin or sibling)
- `${CLAUDE_PLUGIN_ROOT}` references resolve to existing paths
- the first body block directs Codex to `../CODEX.md`

For each plugin's `skills/CODEX.md`:

- file exists and is referenced by every shared skill
- adapter states that Claude Code follows the canonical `SKILL.md` directly
- adapter maps Codex skill invocation, tool intent, plugin-relative paths, and any agent dispatch used by that plugin
- adapter does not duplicate individual workflow procedures

### 4. Agents (if plugin ships any)

For each `plugins/<plugin>/agents/<agent>.md`:

- YAML frontmatter parses
- required fields per existing agents in `plugins/mol/agents/` (`name`, `description`, `tools`, `model`)
- `model` is one of `opus | sonnet | haiku | inherit`
- for agents under `plugins/mol/agents/`: `model: inherit` → 🟡 (policy requires an explicit tier — `plugins/mol/rules/model-policy.md`)
- `tools` lists only what the role needs (read-only agents must not declare `Write`/`Edit`)
- body's first non-frontmatter line mentions reading CLAUDE.md (Knowledge rule K1)

### 5. Cross-plugin sanity

- no two skills across plugins share the same `<plugin>:<verb>` qualified name
- skills referencing each other (e.g. `/mol:bootstrap` inside `/mol:spec`) reference only existing skills
- READMEs reference only existing skills
- every plugin in either marketplace has both manifests, and no manifest exists for an unregistered plugin
- `.codex-plugin/plugin.json` points at the same shared `skills/` directory Claude Code loads; a parallel copied skill tree is a 🔴 duplication finding

### 6. Output

Severity-sorted findings:

```
<emoji> <path> — <message>
  Rule: <where it came from, e.g. "marketplace.json: name required",
        "SKILL.md: argument-hint missing">
  Fix: <one-line recommendation>
```

Count summary:

| Plugin       | 🚨 | 🔴 | 🟡 | 🟢 |
|--------------|----|----|----|----|
| mol          |    |    |    |    |
| mol-plugin   |    |    |    |    |

Verdict: PUBLISH-READY / FIX REQUIRED.

End with one-line F2 summary.

## Guardrails

- **Read-only.** Never write, never auto-fix.
- **Do not** flag stylistic preferences (tone, sentence length). Validate structure, not voice.
- **Do not** invent rules not listed here. Class of problem worth catching → surface as 🟡 with rule `"unspecified — consider adding to /mol-plugin:check"`.
