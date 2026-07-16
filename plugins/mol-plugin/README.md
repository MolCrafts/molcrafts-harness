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
/plugin marketplace add https://github.com/MolCrafts/claude-plugin
/plugin install mol-plugin@molcrafts
```

For local development:
`/plugin marketplace add <path-to-claude-plugin-checkout>`.

### Codex

```bash
codex plugin marketplace add MolCrafts/claude-plugin
codex plugin add mol-plugin@molcrafts
```

For local development:
`codex plugin marketplace add <path-to-claude-plugin-checkout>`.
Restart Codex and test updated skills in a new thread.

## Skills

| Skill | Purpose |
|---|---|
| `/mol-plugin:new-skill` | Scaffold one shared Claude/Codex skill in any plugin (`mol`, `mol-plugin`). Authors a complete, runnable SKILL.md (no TODO placeholders), links the common Codex adapter, and appends one README row. Runs `/mol-plugin:check`; does not touch plugin manifests. |
| `/mol-plugin:check` | The marketplace's self-audit. Runs the deterministic dual-runtime validator, then reviews semantic boundaries that scripts cannot judge. Parallel to `/mol:bootstrap`, but for plugin source; read-only. |
| `/mol-plugin:smoke` | Validate with Claude Code's native CLI and install both plugins through an isolated temporary Codex home. Never changes user plugin configuration; `--static-only` skips installation. |
| `/mol-plugin:release` | Unified version bump (patch/minor/major) — advances every Claude and Codex plugin manifest plus the Claude marketplace entries to one shared version, gates through `/mol:ship commit`, and produces one local commit + one local `v<X.Y.Z>` tag. Does not push or write a CHANGELOG. |
| `/mol-plugin:janitor` | Content-side counterpart to `/mol-plugin:check`: walks every `SKILL.md` and agent `.md` in the marketplace, normalizes prose to plain imperative rules, enforces one responsibility per file, and removes duplicate responsibilities. Applies safe rewrites in place; surfaces splits, moves, merges, and contract-surface changes as AMBIGUITY without editing. Writes inside `plugins/<plugin>/skills/` and `plugins/<plugin>/agents/` only. |

## Deterministic validation

Run the same stdlib-only validator used by `/mol-plugin:check`, CI, and the
developer hook:

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
/mol-plugin:check
/mol-plugin:smoke --static-only
# fix anything red
/mol-plugin:release minor   # bumps every plugin to one shared version
/mol:tag                    # push the v<X.Y.Z> tag to upstream
```

## License

MIT — see the root [LICENSE](../../LICENSE).
