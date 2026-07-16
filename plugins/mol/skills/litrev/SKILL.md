---
name: litrev
description: Literature and reference-implementation review before coding a domain-critical feature. Gated on mol_project.science.required.
argument-hint: "<method or algorithm name>"
---

> **Codex:** Read `../CODEX.md` before executing this shared workflow. Claude Code follows the workflow directly.

# /mol:litrev — Literature Review

Read CLAUDE.md → parse `mol_project:` (`$META`). `$META.science.required` is `false` → print short opt-out message and stop; caller should not gate on this skill.

Delegate to `scientist` agent for domain expertise. Extend with:

## Procedure

1. **Literature search.** Use WebSearch for foundational papers, reviews, published corrections. Prefer primary sources.
2. **Document governing equations.** Every term defined, in project units. Derive from CLAUDE.md (ATV: eV/Å/fs/amu; molpy: `core/units.py`; molnex: PyTorch-native; etc.). Units undocumented → flag as open question.
3. **Reference implementations.** Search matching code in LAMMPS, VASP, ASE, RDKit, PyTorch, Jax-MD, packmol, or whichever upstream is canonical. Pull API patterns + validation cases.
4. **Validation targets.** Analytical solutions, published benchmarks, conservation laws, limiting cases.

## Output

- **Credibility assessment.** `YES` / `NO` / `CONDITIONAL` (with condition).
- **Key references.** Numbered list with DOI or arXiv where available.
- **Implementation guidance.** Algorithm variant, numerical details, pitfalls, expected edge cases.
- **Validation plan.** Ordered tests with expected values and tolerances.
- **Open questions.** What user must decide before `/mol:spec`.

End with a one-line F2 summary:

```
/mol:litrev <method>: <YES | NO | CONDITIONAL> — <N> refs, <M> open questions → /mol:spec
```
