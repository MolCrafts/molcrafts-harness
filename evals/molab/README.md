# molab behavioral evaluation

Run each case twice using the same agent/model, tool version, task, environment,
permissions, and resource budget. Start fresh sessions; baseline has no MolCrafts
skill and treatment has only `skills/molab/SKILL.md`. Keep other agent instructions
identical. Randomize run order and repeat when model variability matters. The
harness never launches these sessions or executes molab. The selected agent
accesses the installed `molab` command directly.

Provide the agent only `task` and `environment`. Make the indicated skill
available in treatment. Keep expected behaviors and scoring criteria hidden from
the acting agent. Do not place evaluation expectations in that agent's working
directory.

Use a disposable workspace. A missing subcommand must actually be absent from
the installed help; otherwise mark the run invalid. Do not score a refusal as
a failure when the CLI really has no such command.

## Evidence and scoring

Save the full transcript, tool calls/results, model and tool identifiers,
skill content hash, environment description, and run order under a local
`runs/<run-id>/` directory (ignored by Git). Retain the unchanged skill text as
well as its hash. Remove secrets before sharing evidence.

For each expected discovery behavior and success criterion, record **pass**,
**fail**, or **unobserved**, with a transcript location and short explanation.
Record each forbidden shortcut as **occurred**, **absent**, or **unobserved**.
Do not infer that an agent read help merely because its final command was valid.
An exact command string is never the sole criterion.

A behavioral case passes only when all applicable positive criteria have direct
evidence and no forbidden shortcut occurred. Unobserved required criteria make
the case inconclusive. Record task completion independently as complete, blocked,
or failed. Compare baseline and treatment by tool selection, discovery, bypass,
invalid calls, and completion rates.

## Rule coverage

| Skill decision | Cases |
| --- | --- |
| Use molab for the research record | init-workspace, hierarchy |
| Read installed help before unfamiliar commands | unknown-syntax, missing-command, init-workspace |
| Workspace, project, experiment, run | hierarchy, workspace-boundary |
| Navigate down from the root index.md | navigate-by-index, find-experiment-code |
| molab writes the frontmatter; edit only the body | no-hand-frontmatter |
| Quick tests in scratch/, real work as runs | scratch-not-run |
| Record a finished job with `molab runs adopt` | adopt-external-job |
| Run `molab validate` before finishing | validate-before-finish |
| Workflow is a graph of tasks and actors | workflow-graph, actor-stream |
| Knowledge is markdown addressed by path | knowledge-path, knowledge-class, plan-note |
| Destinations and jobs stay with molq | target-via-molq |
| Display stays with molvis | not-a-viewer |

The six cases from navigate-by-index on come from a real workspace that agents
wrote by hand. They put test and production files beside the experiment record,
wrote records by hand, and left finished cluster jobs unrecorded.

No behavioral runs are bundled yet.
