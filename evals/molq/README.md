# molq behavioral evaluation

Run each case twice using the same agent/model, tool version, task, environment,
permissions, and resource budget. Start fresh sessions; baseline has no MolCrafts
skill and treatment has only `skills/molq/SKILL.md`. Keep other agent instructions
identical and record any preexisting molq knowledge. Randomize run order and
repeat when model variability matters. The harness never launches these sessions
or executes job tools. The selected agent accesses tools directly.

Provide the agent only `task` and `environment`. Make the indicated skill
available in treatment. Keep expected behaviors and scoring criteria hidden from
the acting agent. Supply prepared inputs, references, credentials, and isolated
compute destinations outside this repository when the task requires them. Do not
place evaluation expectations in that agent's working directory.

Use a controlled fixture environment for unsupported operations, permission
errors, and uncertain submissions. A declared condition must actually be present;
otherwise mark the run invalid rather than treating agent refusal as a failure.
Use disposable jobs for live tests. Fixtures can establish decision behavior but
cannot prove actual HPC resource scheduling. Never execute invented commands
against production just to evaluate them.

## Evidence and scoring

Save the full transcript, tool calls/results, model and tool identifiers,
skill content hash, environment description, and run order under a local
`runs/<run-id>/` directory (ignored by Git). Retain the unchanged skill text as
well as its hash. Remove secrets before sharing evidence.

For each expected discovery behavior and success criterion, record **pass**,
**fail**, or **unobserved**, with a transcript location and short explanation.
Record each forbidden shortcut as **occurred**, **absent**, or **unobserved**.
Do not infer that an agent read help merely because its final command was valid.
A blocked environment can still show correct selection and discovery; task
completion and decision quality must be scored separately.

A behavioral case passes only when all applicable positive criteria have direct
evidence and no forbidden shortcut occurred. Unobserved required criteria make
the case inconclusive. Record task completion independently as complete, blocked,
or failed. Compare baseline and treatment by tool selection, discovery, bypass,
invalid calls, and completion rates. Report inconclusive/invalid counts and run
counts alongside rates. An exact command string is never the sole criterion.

Suggested record (one per case/condition/repetition):

```json
{
  "case_id": "slurm-submit",
  "condition": "skill",
  "repetition": 1,
  "agent": "record actual agent/model",
  "tool_version": "record installed tool version",
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

## Rule coverage and ablation

| Skill decision | Cases |
| --- | --- |
| Prefer molq for job management | slurm-submit, local-submit, inspect-jobs, cancel-job |
| Discover installed syntax instead of inventing it | unknown-syntax, slurm-submit |
| Use public interfaces | cluster-info, public-client |
| Avoid capability probing and silent resource emulation | cluster-info, gpu-sharing |
| Verify unsupported behavior before fallback | unsupported-operation |
| Preserve native debugging and explicit user choice | debug-molq, explicit-native |
| Availability/permission failures do not imply missing functionality | missing-tool, permission-error |
| Reconcile uncertain submission without automatic resend | uncertain-submit |
| Leave scientific work to owning tools | mixed-task, non-job-task |

After the first paired runs, remove or alter one rule in a temporary skill copy
and rerun its mapped cases. Compare evidence and skill word count. Keep extra
wording only when it improves observed decisions; collection checks alone do not
justify expansion. No behavioral runs or improvement claims are bundled yet.
