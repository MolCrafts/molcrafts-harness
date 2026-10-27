# molvis behavioral evaluation

Run each case twice using the same agent/model, tool version, task, environment,
permissions, and resource budget. Start fresh sessions; baseline has no MolCrafts
skill and treatment has only `skills/molvis/SKILL.md`. Keep other agent instructions
identical. Randomize run order and repeat when model variability matters. The
harness never launches these sessions or executes molvis. The selected agent
accesses the installed `molvis` command directly.

Provide the agent only `task` and `environment`. Make the indicated skill
available in treatment. Keep expected behaviors and scoring criteria hidden from
the acting agent. Do not place evaluation expectations in that agent's working
directory.

A viewer case needs a real `molvis serve` kernel and, when the task says so, a
browser attached to the page URL. If that browser cannot be opened, mark the
run invalid rather than scoring the agent's refusal as a failure. Drawing is
not evidence of a highlight until a snapshot shows the selection.

## Evidence and scoring

Save the full transcript, tool calls/results, model and tool identifiers,
skill content hash, environment description, and run order under a local
`runs/<run-id>/` directory (ignored by Git). Retain the unchanged skill text as
well as its hash. Remove secrets before sharing evidence.

For each expected discovery behavior and success criterion, record **pass**,
**fail**, or **unobserved**, with a transcript location and short explanation.
Record each forbidden shortcut as **occurred**, **absent**, or **unobserved**.
Do not infer that an agent read help merely because its final cell was valid.
A missing kernel can still show correct selection of `molvis serve`; task
completion and decision quality must be scored separately.

A behavioral case passes only when all applicable positive criteria have direct
evidence and no forbidden shortcut occurred. Unobserved required criteria make
the case inconclusive. Record task completion independently as complete, blocked,
or failed. Compare baseline and treatment by tool selection, discovery, bypass,
invalid calls, and completion rates. An exact command string or an exact SMILES
string is never the sole criterion.

Suggested record (one per case/condition/repetition):

```json
{
  "case_id": "dopamine-joke",
  "condition": "skill",
  "repetition": 1,
  "agent": "record actual agent/model",
  "tool_version": "record installed molvis and molpy versions",
  "skill_sha256": "record actual content hash; null for baseline",
  "transcript": "transcript.txt",
  "environment_valid": true,
  "positive_criteria": [],
  "forbidden_shortcuts": [],
  "behavior_result": "inconclusive",
  "task_result": "blocked"
}
```

Each criterion entry should include the case field/index, score, evidence
location, and explanation. Do not commit fabricated results.

## Rule coverage

| Skill decision | Cases |
| --- | --- |
| Use molvis to show a structure | draw-molecule, dopamine-joke, open-pdb |
| serve, then exec, one kernel | serve-then-exec, no-kernel, namespace-persists, no-mcp |
| Same `mv.Stage(name=...)` is the same viewer | namespace-persists, no-mcp, explicit-notebook |
| Highlight via the Stage selection method and molpy indices | highlight-group, dopamine-joke |
| Follow the `draw_frame` docstring when replacing | replace-frame |
| Events are `selection` / `wait_for` | selection-events |
| Do not claim a picture before the browser and the snapshot | not-connected, snapshot-before-claim |
| Discover help and docstrings | discover-help, highlight-group |
| Report a bad SMILES, do not invent a stand-in | bad-smiles |
| One-shot files use `molvis open` | open-pdb |
| Jobs stay with molq | draw-then-submit |
| A requested notebook uses `Stage` directly | explicit-notebook |
| Do not go through molmcp | draw-molecule, serve-then-exec, no-mcp |
