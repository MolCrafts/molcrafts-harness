---
name: molab
description: Use molab to create and operate a research workspace, the workflow that runs in it, and the knowledge written beside it. Applies to organizing and recording research, not to drawing molecules or owning a scheduler.
---

# molab

Use the installed `molab` command for the research record. Do not build that
record as hand-written directories, JSON, or frontmatter. Read `molab --help`
and the subcommand's help before an unfamiliar call.

## Workspace

Workspace, then Project, then Experiment, then Run. Start at the root
`AGENTS.md` and `index.md`. Each level's `index.md` frontmatter is its record,
and its `index:` key lists the children; follow those paths down instead of
searching. molab writes the frontmatter; edit only the body. Register a compute
destination in molq first, then name it from molab.

An experiment is the parameter definition; a run is one execution of it. Quick
tests go in the experiment's disposable `scratch/`. A long job or anything you
will cite becomes a run: run it through molab, or record a finished job with
`molab runs adopt`. Before you finish, run `molab validate` and fix what you added.

## Recording

Inside a run, use `from molab import print` so output lands in that execution's
stdout. Record training data with `ctx.metrics.scalar`, `histogram`, `text`,
`json` or `image`, and key files with `ctx.emit_artifact`. A plain script calls
`molab.track()`; outside molab it writes a directory for `molab runs adopt --from`.

## Workflow

A workflow is a graph. A task runs once and returns a value. An actor yields a
stream. Independent tasks run together. Compile the graph, then execute it.
Scheduler submission stays with molq.

## Knowledge

Knowledge is markdown under `knowledges/`; the path is the identity. The class
is YAML frontmatter: Note, Literature, Report, Finding, Plan, Observation.
Report, Finding, Plan, and Observation cite a source. Point at PDFs; do not copy
them. Read and write through `molab knowledge`.

Leave molecule display to molvis and the job queue to molq.
