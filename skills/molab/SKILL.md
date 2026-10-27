---
name: molab
description: Use molab to create and operate a research workspace, the workflow that runs in it, and the knowledge written beside it. Applies to organizing and recording research, not to drawing molecules or owning a scheduler.
---

# molab

Use the installed `molab` command for the research record. Do not build that
record as hand-written directories and JSON, and do not reimplement it in
another tool.

Before an unfamiliar subcommand, read `molab --help` and that subcommand's
help. The installed command is the authority for verbs and flags. Do not
invent them.

## Workspace

Workspace, then Project, then Experiment, then Run. A workspace does not know
workflows or knowledge; those layers write into it. An experiment is the
parameter definition. A run is one execution of that definition. Parents find
children by scanning the filesystem, not by a list stored in the parent.
Create from the top. A compute destination is registered in molq first, then
named from molab.

## Workflow

A workflow is a graph. A task runs once and returns a value. An actor yields
a stream. Tasks with no unfinished dependency run together. Compile the graph,
then execute it. Persisted execution state does not replace the source.
Scheduler submission stays with molq.

## Knowledge

Knowledge is markdown under `knowledges/`. The path is the identity. There is
no second database. The class is YAML frontmatter: Note, Literature, Report,
Finding, Plan, Observation. Report, Finding, Plan, and Observation cite a
source. Note and Literature do not. Point at PDFs; do not copy them in.
Read and write through `molab knowledge`.

Leave molecule display to molvis and the job queue to molq.
