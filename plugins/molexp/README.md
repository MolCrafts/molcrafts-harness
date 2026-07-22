# molexp plugin

Data-workspace tooling for **[molexp](https://github.com/MolCrafts)** — not the agent harness (`mol`) and not marketplace maintenance (`mol-plugin`).

Install when you work with experimental data directories and need them under molexp's four-tier layout:

```
Workspace → Project → Experiment → Run
```

## Skills

| Skill | What |
|---|---|
| `/molexp:adopt-workspace <source> [<target>]` | Inspect a legacy data folder, propose a project/experiment/run mapping, materialize via molexp's Python API, then copy (default) or move each file with per-file SHA-256 verification. Resumable ledger; optional typed-path delete of source after successful copy. |

## Install

```
/plugin install molexp@molcrafts
```

Requires `molexp` importable in the environment (`pip install molexp`).

## Relation to other plugins

| Plugin | Domain |
|---|---|
| `mol` | Code project harness (spec / impl / review / git) |
| `molexp` | **Experiment data** workspace adoption |
| `mol-plugin` | This marketplace's scaffolding and release |
