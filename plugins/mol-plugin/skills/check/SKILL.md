---
description: Self-check the marketplace — validates `marketplace.json`, every `plugin.json`, every SKILL.md and agent .md for required frontmatter, well-formed argument hints, valid cross-references, and naming consistency. Use after editing any of these files; read-only.
argument-hint: "[<plugin>]"
---

# /mol-plugin:check — Marketplace Self-Check

Walk the marketplace tree and verify structural soundness before publishing. Read-only — reports findings; never edits.

Scope: no argument → every plugin in `.claude-plugin/marketplace.json`. With plugin name → just that one.

## Procedure

### 1. Marketplace registry

Read `.claude-plugin/marketplace.json`:

- top-level required fields present (`name`, `owner`, `plugins`)
- every `plugins[]` entry has `name`, `source`, `version`, `description`
- `source` paths resolve to existing directories
- no two plugins share a `name`

### 2. Per-plugin metadata

For each plugin under `plugins/`:

- `.claude-plugin/plugin.json` exists and parseable
- required: `name`, `version`, `description`
- `name` matches directory name
- `version` matches the entry in marketplace.json
- `keywords` is an array if present

### 3. Skills

For each `plugins/<plugin>/skills/<skill>/SKILL.md`:

- YAML frontmatter parses
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
