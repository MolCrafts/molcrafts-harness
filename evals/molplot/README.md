# molplot behavioral evaluation

Run each case twice using the same agent/model, tool version, task, environment,
permissions, and resource budget. Start fresh sessions; baseline has no MolCrafts
skill and treatment has only `skills/molplot/SKILL.md` (plus `skills/molvis/SKILL.md`
when a case lists it). Keep other agent instructions identical. Randomize run
order and repeat when model variability matters. The harness never launches these
sessions or runs plotting code. The selected agent imports the installed `molplot`
package directly.

Provide the agent only `task` and `environment`. Make the indicated skill
available in treatment. Keep expected behaviors and scoring criteria hidden from
the acting agent. Supply the data files a case names outside this repository.
Do not place evaluation expectations in that agent's working directory.

## Evidence and scoring

Save the full transcript, tool calls/results, model and tool identifiers, skill
content hash, environment description, run order, and a listing of every file the
agent wrote under a local `runs/<run-id>/` directory (ignored by Git).

The file listing is the main evidence: a case passes the output-format criterion
only when every figure file the agent wrote is a PNG. Any `.svg` or `.pdf` file,
or a `to_svg` / `format="svg"` / `format="pdf"` call, fails the case even when a
PNG was also written. For each expected discovery behavior and success
criterion, record **pass**, **fail**, or **not applicable** with the evidence.
