# mol-plugin

Maintenance toolkit for the molcrafts plugin marketplace itself.

`mol-plugin` is for **developing the plugins**, not for using them in a
project. If you want to *use* mol skills in a repo, install `mol`
and/or `mol-agent` instead.

## Install

```
/plugin marketplace add https://github.com/MolCrafts/claude-plugin
/plugin install mol-plugin@molcrafts
```

For local development:
`/plugin marketplace add <path-to-claude-plugin-checkout>`.

## Skills

| Skill | Purpose |
|---|---|
| `/mol-plugin:new-skill` | Scaffold a new skill in any plugin (`mol`, `mol-agent`, `mol-plugin`). Authors a complete, runnable SKILL.md (no TODO placeholders) and appends one row to that plugin's `README.md` skills table. Runs `/mol-plugin:check` at the end so the new skill is verified before exit. Does not touch `plugin.json`. |
| `/mol-plugin:check` | The marketplace's self-audit. Structural check across the whole marketplace: `marketplace.json`, every `plugin.json`, every `SKILL.md`, every agent. Parallel to `/mol-agent:check`, but for the plugin source rather than a project's harness. Read-only. |
| `/mol-plugin:release` | Unified version bump (patch/minor/major) — advances *every* plugin's `plugin.json` and the matching `marketplace.json` entries to one shared version, gates the commit through `/mol:ship commit`, and produces one local commit + one local `v<X.Y.Z>` tag. Does not push (pair with `/mol:tag`). Does not write a CHANGELOG — release notes live on the GitHub release and in `git log`. |
| `/mol-plugin:janitor` | Content-side counterpart to `/mol-plugin:check`: walks every `SKILL.md` and agent `.md` in the marketplace, normalizes prose to plain imperative rules, enforces one responsibility per file, and removes duplicate responsibilities. Applies safe rewrites in place; surfaces splits, moves, merges, and contract-surface changes as AMBIGUITY without editing. Writes inside `plugins/<plugin>/skills/` and `plugins/<plugin>/agents/` only. |

## Workflow

```
/mol-plugin:new-skill mol:bench "Microbenchmark hot paths"
# author the skill body
/mol-plugin:check
# fix anything red
/mol-plugin:release minor   # bumps every plugin to one shared version
/mol:tag                    # push the v<X.Y.Z> tag to upstream
```

## License

MIT — see the root [LICENSE](../../LICENSE).
