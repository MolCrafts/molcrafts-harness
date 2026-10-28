---
name: molab
description: Use molab to create and operate a research workspace, the workflow that runs in it, and the knowledge written beside it. Applies to organizing and recording research, not to drawing molecules or owning a scheduler.
---

# molab

Use the installed `molab` command for the research record. Do not build that
record as hand-written directories, JSON, or frontmatter, and do not
reimplement it in another tool. Read `molab --help` and the subcommand's help
before an unfamiliar call; the installed command owns verbs and flags.

## Workspace

Workspace, then Project, then Experiment, then Run. Start at the workspace
root `AGENTS.md` and `index.md`. Each level's `index.md` frontmatter is that
level's record, and its `index:` key lists the children; follow those paths
down instead of searching the tree. molab writes the frontmatter. You may edit
only the body. Create from the top. Register a compute destination in molq
first, then name it from molab.

An experiment is the parameter definition. A run is one execution of it.
Quick tests go in the experiment's `scratch/`, which is disposable. A long job,
a trajectory, or anything you will cite becomes a run: run it through molab,
or record a job that already finished with `molab runs adopt`. Before you
finish, run `molab validate` and fix what your work added.

## Workflow

A workflow is a graph. A task runs once and returns a value. An actor yields
a stream. Tasks with no unfinished dependency run together. Compile the graph,
then execute it. Persisted execution state does not replace the source.
Scheduler submission stays with molq.

## Knowledge

Knowledge is markdown under `knowledges/`. The path is the identity. The
class is YAML frontmatter: Note, Literature, Report, Finding, Plan,
Observation. Report, Finding, Plan, and Observation cite a source. Point at
PDFs; do not copy them in. Read and write through `molab knowledge`.

Leave molecule display to molvis and the job queue to molq.
