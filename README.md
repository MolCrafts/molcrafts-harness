# MolCrafts Harness

Agent Skills + behavioral evaluation. One short skill per tool. **molq** helps
agents find the job tool and avoid reimplementing scheduler workflows.
**molvis** helps agents show a molecule in the live viewer through that
tool's own CLI, and avoid a second viewer or an MCP session. **molab** helps
agents keep a workspace, a workflow, and knowledge through that tool's own
CLI. **molplot** helps agents draw data plots with the unified preset and
deliver them as PNG only, never SVG or PDF. The skill states the frame; the
installed help owns the verbs.

Harness does not proxy MolCrafts tools. Agents call them directly.
Tool help, schemas, and documentation own operational facts. Skills contain
short decision guidance, with one standard `SKILL.md` per tool and only latest.
There is no installer, registry, runtime, gateway, or version resolver here.
The one addition is the molab guard, wired into Claude Code, Codex and
DeepSeek Harness (below). It forwards workspace layout to molab. Skills name
the MolCrafts tool that owns a scientific step; the agent's other tools stay
available.

## Install

From the project where you want to use the skill, point Vercel
[skills](https://github.com/vercel-labs/skills) at this checkout:

```sh
npx skills add /path/to/molcrafts-harness --skill molq
npx skills add /path/to/molcrafts-harness --skill molvis
npx skills add /path/to/molcrafts-harness --skill molab
npx skills add /path/to/molcrafts-harness --skill molplot
```

Choose supported agents interactively, or use its documented `--agent` option.
DeepSeek Harness reads `.agents/skills` (project) and `~/.agents/skills`
(user), where Vercel skills installs for agents that share that directory.

To inspect discovery without installing:

```sh
npx skills add /path/to/molcrafts-harness --list
```

### Claude Code plugin

The repository is also a Claude Code plugin with the same skills plus
hooks for molab workspaces. Inside Claude Code:

```text
/plugin marketplace add MolCrafts/molcrafts-harness
/plugin install molcrafts@molcrafts
```

For a local checkout, start `claude --plugin-dir /path/to/molcrafts-harness`.

- **Before Write / Edit / Bash:** `hooks/molab_guard.py` sends the path, and
  for a file edit the content the file would have, to `molab check path`.
  A shell command goes to `molab check command` with its working directory.
  If molab refuses, the call is denied with molab's reason and the command to
  use instead. A write whose path cannot be read is denied. A command the
  grammar cannot read is left to the stop check.
- **On SessionStart / Stop / SubagentStop:** molab snapshots the workspace
  when the session starts, and the first time a command touches another
  workspace (`molab check tree --snapshot`). At stop, errors added since then
  (`--since`) are checked for every workspace the session touched, not only
  the session directory. New errors block the stop once. Older problems are
  not counted.

The hook script holds no rule; molab decides. Without `molab` on `PATH`, or
outside a molab workspace, both hooks allow everything.

### Which tools

Skills name the MolCrafts tool that owns a job: molab for the workspace and
for the workflow molab runs, molq for jobs, molvis for the viewer, molplot
for data plots (PNG only).
Do that job with that tool, and do not reimplement it.

Reading, searching, editing, git, interpreters, package managers, and tests
stay available. A file molab does not execute is ordinary code. The harness
checks workspace layout through molab and leaves every other tool in place.
There is no `policy.toml`.

### Codex

The repository is also a Codex plugin (`.codex-plugin/plugin.json`) with the
same skills and the molab guard (`hooks/codex.json`): before `Bash` and
`apply_patch` (every file a patch adds, updates, deletes or moves is checked;
an added file with its full content), and at `SessionStart` / `Stop` /
`SubagentStop`.

```sh
codex plugin marketplace add /path/to/molcrafts-harness
codex plugin add molcrafts@molcrafts
python3 /path/to/molcrafts-harness/hooks/codex_trust.py --yes   # from inside a workspace
```

Codex runs a hook only after a person has trusted its exact definition, and
an unattended Codex (a subagent, `codex exec`, an app-server client) never
asks, so an untrusted guard is skipped without a word. `codex_trust.py` lists
the guard hooks with their trust and, with `--yes`, trusts them through
Codex's own app-server.

Codex runs the plugin from its own copy (`~/.codex/plugins/cache/`). After
updating the harness, refresh that copy with `codex plugin add
molcrafts@molcrafts` and trust again: Codex marks every hook of a changed
plugin `modified` and skips it until a person trusts it again.

### DeepSeek Harness (Tack)

The repository root is also a DSH bundle (`dsh.bundle.patch` →
`dsh/cordis.patch.yml`, plugin `dsh/index.js`, display metadata in
`locale/`, `icon.svg`):

```sh
tack plugin add /path/to/molcrafts-harness --profile research-run
```

It works on DSH's own extension points:

- `tools/pre-execute`: `bash`, `write` and `edit` go to the molab guard; a
  refusal is a `deny` decision with molab's reason, and the tool does not
  run. The first call of a session snapshots its workspace.
- `agent/turn-stopping`: the stop check; a block sends the agent back once.
- Claude Code and Codex workers run their own harness hooks. The Codex hooks
  must be trusted (above).

Options go on the `molcrafts-harness` row of the profile's
`cordis.patch.yml`. A leftover `policy` key is ignored.

| Option | Default | Meaning |
|---|---|---|
| `withhold` | `[]` | optional tool names removed from every agent |
| `python` | `python3` | interpreter for the molab guard |
| `env` | `{}` | extra variables for the guard (e.g. `MOLAB_GUARD_TRACE=<file>`, which appends every raw event it receives) |

## Evaluate

`evals/molq/cases.json`, `evals/molvis/cases.json`, `evals/molab/cases.json`,
and `evals/molplot/cases.json`
each contain between 10 and 21 tasks with environment conditions, available skills, expected
tool/discovery behavior, forbidden shortcuts, and success criteria. The
matching `evals/<tool>/README.md` describes paired baseline/skill runs and
evidence scoring. Evaluation is manual and agent-independent; this repository
does not launch an agent or invoke the tools. Record transcripts from the
agent you already use.

```sh
python3 -m unittest discover -s tests/skill-quality -v
python3 -m unittest discover -s tests/hooks -v
```

These checks validate collection quality, not agent performance. Behavioral
improvement requires actual paired runs. Do not claim fixture checks establish
live HPC support or a live viewer. Add infrastructure only after observed
evaluation failures justify it. A new tool gets one skill and one `evals/`
directory of the same shape. It does not get a gateway, registry, or runtime
in this repository.
