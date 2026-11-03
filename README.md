# MolCrafts Harness

Agent Skills + behavioral evaluation. One short skill per tool. **molq** helps
agents find the job tool and avoid reimplementing scheduler workflows.
**molvis** helps agents show a molecule in the live viewer through that
tool's own CLI, and avoid a second viewer or an MCP session. **molab** helps
agents keep a workspace, a workflow, and knowledge through that tool's own
CLI. **molplot** is a Python library rather than a CLI: it helps agents
write every matplotlib figure with `import molplot as mpl` (the matplotlib
API with scienceplots journal style and column-width sizing), and hand it
to the user in the `molplot serve` workbench. The skill states the frame;
the installed help owns the verbs.

Harness does not proxy MolCrafts tools. Agents call them directly.
Tool help, schemas, and documentation own operational facts. Skills contain
short decision guidance, with one standard `SKILL.md` per tool and only latest.
There is no installer, registry, runtime, gateway, or version resolver here.
The one addition is a set of Claude Code hooks for molab workspaces (below).

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
  A shell command's destination paths (`mv`, `cp`, `mkdir`, redirects, and
  the same after `cd`) are checked the same way. If molab refuses, the call
  is denied with molab's reason and the command to use instead. A write whose
  path cannot be read is denied. A command whose paths cannot be parsed is
  left to the stop check.
- **On SessionStart / Stop / SubagentStop:** molab snapshots the workspace
  when the session starts, and the first time a command touches another
  workspace (`molab check tree --snapshot`). At stop, errors added since then
  (`--since`) are checked for every workspace the session touched, not only
  the session directory. New errors block the stop once. Older problems are
  not counted.

The hook script holds no rule; molab decides. Without `molab` on `PATH`, or
outside a molab workspace, both hooks allow everything. Other agents get the
same rules from the workspace's `AGENTS.md`, which molab writes.

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
