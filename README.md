# MolCrafts Harness

Agent Skills + behavioral evaluation. One short skill per tool. **molq** helps
agents find the job tool and avoid reimplementing scheduler workflows.
**molvis** helps agents show a molecule in the live viewer through that
tool's own CLI, and avoid a second viewer or an MCP session. **molab** helps
agents keep a workspace, a workflow, and knowledge through that tool's own
CLI. The skill states the frame; the installed help owns the verbs.

Harness does not execute or proxy MolCrafts tools. Agents call them directly.
Tool help, schemas, and documentation own operational facts. Skills contain
short decision guidance, with one standard `SKILL.md` per tool and only latest.
There is no installer, registry, runtime, gateway, or version resolver here.

## Install

From the project where you want to use the skill, point Vercel
[skills](https://github.com/vercel-labs/skills) at this checkout:

```sh
npx skills add /path/to/molcrafts-harness --skill molq
npx skills add /path/to/molcrafts-harness --skill molvis
npx skills add /path/to/molcrafts-harness --skill molab
```

Choose supported agents interactively, or use its documented `--agent` option.
To inspect discovery without installing:

```sh
npx skills add /path/to/molcrafts-harness --list
```

## Evaluate

`evals/molq/cases.json`, `evals/molvis/cases.json`, and `evals/molab/cases.json`
each contain between 10 and 20 tasks with environment conditions, available skills, expected
tool/discovery behavior, forbidden shortcuts, and success criteria. The
matching `evals/<tool>/README.md` describes paired baseline/skill runs and
evidence scoring. Evaluation is manual and agent-independent; this repository
does not launch an agent or invoke the tools. Record transcripts from the
agent you already use.

```sh
python3 -m unittest discover -s tests/skill-quality -v
```

These checks validate collection quality, not agent performance. Behavioral
improvement requires actual paired runs. Do not claim fixture checks establish
live HPC support or a live viewer. Add infrastructure only after observed
evaluation failures justify it. A new tool gets one skill and one `evals/`
directory of the same shape. It does not get a gateway, registry, or runtime
in this repository.
