---
name: molvis
description: Use molvis to show a molecule, a highlighted group, or a structural change in the live viewer. Applies to seeing a structure, not to job submission or to chemistry the user did not ask to display.
---

# molvis

Use the installed `molvis` command when a person should see a molecule, a
group on it, or a change from one structure to the next.

For more than one step, run `molvis serve`, then `molvis exec`. The code you
send is a notebook cell. `mv.Stage(name=...)` with the same name is the same
viewer, and names you bind stay in that shell for the next `exec`. Do not
start molmcp, and do not call `molvis_open` or `molvis_exec`.

Do not draw the molecule yourself with matplotlib, a bespoke viewer, or an
HTML page.

Before an unfamiliar subcommand, read `molvis --help` and that subcommand's
help. Before an unfamiliar Stage method, read its docstring (`help(...)`
inside `exec`). The installed command and the live Stage are the authority
for syntax. Do not invent flags or method names.

Selection and frontend events are the Stage's `selection`, `on`, and
`wait_for`. Highlight through the selection method the docstring names.
Choose atom indices with molpy in the same cell. Do not count atoms in a
SMILES string by hand.

Build the chemistry with molpy inside the shell. molvis does not know
molecule names. Leave job submission to molq.

If `exec` reports that no browser is connected, give the user the error and
the page address, and wait. Write snapshot bytes to a file and look at the
image before saying what is on screen.

When the user asks for a notebook, call the same `Stage` API there. Do not
wrap it in a second session object.
