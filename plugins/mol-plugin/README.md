# mol-plugin

Maintenance toolkit for the molcrafts plugin marketplace itself.

`mol-plugin` is for **developing the plugins**, not for using them in a
project. If you want to *use* mol skills in a repo, install `mol`
instead.

Claude Code remains authoritative. Codex uses the same maintenance skill files
through a native manifest and the small `skills/CODEX.md` runtime adapter.

## Install

### Claude Code (primary)

```
/plugin marketplace add https://github.com/MolCrafts/molcrafts-harness
/plugin install mol-plugin@molcrafts
```

For local development:
`/plugin marketplace add <path-to-molcrafts-harness-checkout>`.

### Codex

```bash
codex plugin marketplace add MolCrafts/molcrafts-harness
codex plugin add mol-plugin@molcrafts
```

For local development:
`codex plugin marketplace add <path-to-molcrafts-harness-checkout>`.
Restart Codex and test updated skills in a new thread.

## Skills

| Skill | Purpose |
|---|---|
| `/mol-plugin:new-skill` | Scaffold one shared Claude/Codex skill in any plugin (`mol`, `mol-plugin`). Authors a complete, runnable SKILL.md (no TODO placeholders), links the common Codex adapter, and appends one README row. Runs `/mol-plugin:check`; does not touch plugin manifests. |
| `/mol-plugin:check` | Unified marketplace self-check: deterministic dual-runtime validator, semantic contracts, skill/agent content janitor (safe rewrites), and Claude/Codex install smoke. Flags: `[<plugin>] [--static-only] [--no-write]`. |
| `/mol-plugin:release` | Unified version bump (patch/minor/major) — advances every Claude and Codex plugin manifest plus the Claude marketplace entries to one shared version, gates through `/mol-plugin:check` + commit chain, and publishes end-to-end. Does not write a CHANGELOG. |

## Deterministic validation

Run the same stdlib-only validator used by `/mol-plugin:check` (structure phase), CI, and the developer hook:

```bash
python3 plugins/mol-plugin/scripts/validate_repository.py
```

Installing `mol-plugin` also loads `hooks/hooks.json`. After `Write` or `Edit`,
the hook runs the validator only when the current repository contains the
MolCrafts marketplace; it is a no-op everywhere else. `mol` itself ships no
hook, so normal project users are unaffected.

## Workflow

```
/mol-plugin:new-skill mol:bench "Microbenchmark hot paths"
# author the skill body
/mol-plugin:check              # structure + content + smoke
/mol-plugin:check --static-only  # faster: no Claude/Codex install
# fix anything red
/mol-plugin:release minor
/mol:tag
```

## License

MIT — see the root [LICENSE](../../LICENSE).
