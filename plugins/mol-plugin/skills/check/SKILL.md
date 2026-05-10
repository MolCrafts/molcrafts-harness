---
description: Self-check the marketplace itself. Validates marketplace.json, each plugin.json, every SKILL.md and agent .md for required frontmatter, well-formed argument-hints, valid cross-references, and naming consistency. This is the marketplace's own audit (claude-plugin/ has no .claude/ harness, so /mol-agent:check does not apply here). Read-only.
argument-hint: "[<plugin>]"
---

# /mol-plugin:check — Marketplace Self-Check

Walk the marketplace tree and verify everything is structurally sound
before publishing. Read-only — reports findings; never edits.

Scope: when called with no argument, validates every plugin listed
in `.claude-plugin/marketplace.json`. With a plugin name, validates
just that one.

## Procedure

### 1. Marketplace registry

Read `.claude-plugin/marketplace.json`:

- top-level required fields present (`name`, `owner`, `plugins`)
- every entry under `plugins[]` has `name`, `source`, `version`,
  `description`
- `source` paths resolve to existing directories
- no two plugins share a `name`

### 2. Per-plugin metadata

For each plugin under `plugins/`:

- `.claude-plugin/plugin.json` exists and is parseable
- required fields: `name`, `version`, `description`
- `name` matches the directory name
- `version` matches the entry in marketplace.json
- `keywords` is an array if present

### 3. Skills

For each `plugins/<plugin>/skills/<skill>/SKILL.md`:

- YAML frontmatter parses
- `description` is present and non-empty
- `argument-hint` is present (even if `""`); the shape is built
  from these primitives, in any combination:
  - `<arg>` — a required positional placeholder; `arg` may be a
    short prose hint (`<feature description>`) or a `|`-alternation
    of literal values (`<commit | push | merge>`)
  - `[arg]` — an optional positional placeholder; same content
    rules as above
  - `[<arg>]` and `<arg> [<arg>]` are explicit composites of the
    above and are allowed
  - whitespace separates positional slots; do not embed
    parenthetical annotations inside the hint (move explanation
    into the procedure body instead)
- the H1 heading is `# /<plugin>:<skill> — <title>` and matches the
  directory name
- the file ends with the standard one-line summary convention
  (F2) — at minimum, the procedure mentions an end-of-run summary
- internal `/<plugin>:<verb>` references point at skills that
  actually exist (in this plugin or a sibling)
- `${CLAUDE_PLUGIN_ROOT}` references resolve to existing paths

### 4. Agents (if the plugin ships any)

For each `plugins/<plugin>/agents/<agent>.md`:

- YAML frontmatter parses
- required fields per the existing agents in `plugins/mol/agents/`
  (`name`, `description`, `tools` — match the shape used today)
- `tools` only lists tools the agent's role needs (read-only agents
  must not declare `Write`/`Edit`)
- the body's first non-frontmatter line mentions reading CLAUDE.md
  (Knowledge rule K1)

### 5. Cross-plugin sanity

- no two skills across different plugins share the same `<plugin>:<verb>`
  qualified name (collisions impossible by construction, but verify)
- skills that reference each other (e.g. `/mol-agent:check`
  appearing inside a `/mol-agent:bootstrap` body) only reference
  skills that exist
- README files in each plugin reference only skills that exist

### 6. Output

Severity-sorted findings:

```
<emoji> <path> — <message>
  Rule: <where it came from, e.g. "marketplace.json: name required",
        "SKILL.md: argument-hint missing">
  Fix: <one-line recommendation>
```

End with a count summary:

| Plugin       | 🚨 | 🔴 | 🟡 | 🟢 |
|--------------|----|----|----|----|
| mol          |    |    |    |    |
| mol-agent    |    |    |    |    |
| mol-plugin   |    |    |    |    |

Verdict: PUBLISH-READY / FIX REQUIRED.

End with a one-line summary (F2).

## Guardrails

- **Read-only.** Never write, never auto-fix. Report and stop.
- **Do not** flag stylistic preferences (tone, sentence length).
  Validate structure, not voice.
- **Do not** invent rules not listed in this procedure. If you find
  a class of problem worth catching, surface it as a 🟡 with rule
  `"unspecified — consider adding to /mol-plugin:check"` and let the
  user codify it later.
