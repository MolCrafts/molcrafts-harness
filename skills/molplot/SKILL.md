---
name: molplot
description: Use molplot to draw data plots (lines, bars, scatter, distributions) from simulation or analysis results, saved as PNG. Applies to charts of numbers, not to pictures of molecules, which belong to molvis.
---

# molplot

Use the installed `molplot` Python package for data plots. Call
`molplot.use(preset)` first, so the figure carries the unified preset and its
palette. Build specs with `molplot.line_spec` / `bar_spec` / `scatter_spec` and
draw them with `molplot.render(spec, ax=...)`. Take colours from
`molplot.palette(preset)`; do not invent a colour list.

Write PNG only. Save with `fig.savefig("name.png", dpi=300)`. Never write SVG
or PDF: no `.svg` or `.pdf` path, no `molplot.to_svg`, no `format="svg"` or
`format="pdf"`, and no vector copy beside the PNG. If a reader asks for a
vector file, ask before writing one.

Before an unfamiliar function, read its docstring (`help(molplot.line_spec)`)
or the installed source. The installed package is the authority for names and
arguments. Do not invent arguments.

When molplot has no spec for what you need (error bars, shaded spans,
annotations), draw that part on the same matplotlib axes after `render` and
keep the preset. Report the missing spec as a molplot gap.

Look at every PNG before describing it. Fix overlapping labels, legends on
data, and clipped text before you hand it over.

Draw molecules and simulation boxes with molvis, not with matplotlib.
