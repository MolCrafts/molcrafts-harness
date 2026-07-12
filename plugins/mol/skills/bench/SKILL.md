---
description: "External benchmark evaluator — verifies `type: scientific` and `type: performance` criteria from `<slug>.acceptance.md` by running the project's separate `bm_*` pytest-benchmark suite (e.g. `bm-molrs-molpy/`), which pairs each kernel with an equality check against a user-named reference library (freud, scipy, LAMMPS, …). The bench repo owns the test bodies, reference imports, tolerances, and result storage; this skill selects tests per criterion, runs pytest, reports the verdict, and updates `acceptance.md`. Skips cleanly when no bench repo is configured."
argument-hint: "<spec-slug> [<criterion-id>]"
---

# /mol:bench — External Benchmark Evaluator

Runtime sibling of `/mol:web`. Where `/mol:web` drives a UI through a browser MCP, `/mol:bench` runs the project's **external** bench suite — a separate `bm_*` repo with paired perf + correctness tests against a reference impl — and writes per-criterion verdicts back into `acceptance.md`.

The bench repo owns the comparison logic. This skill does not invent tolerances or compute deltas; it runs pytest in the bench repo, reads pytest's exit code + pytest-benchmark JSON, and reports.

## Detect

- spec has ≥1 `scientific` or `performance` criterion in `<slug>.acceptance.md` (else: *"no scientific or performance criteria for `<slug>` — nothing to do"* and stop)
- `mol_project.bench.repo` declared and the directory exists (else: stop with adoption snippet from § Project configuration)
- `pytest` runs from inside the bench repo (e.g. `cd <repo> && pytest --version` exits 0)

## Procedure

### 1. Resolve slug + criteria

Read CLAUDE.md → `$META`. Resolve `$META.specs_path` (default `.claude/specs/`). Parse `$ARGUMENTS` as `<slug> [<criterion-id>]`. Read `<slug>.md` + `<slug>.acceptance.md`; either missing → stop with `/mol:spec` hint.

Working set: every criterion with `type: scientific` or `type: performance`, unless `<criterion-id>` was given (only that one; refuse if its `type` is neither).

### 2. Build a pytest selector per criterion

Each criterion's `evaluator_hint` carries the bench-repo selector. Accept any of:

- `marker: <name>` → `-m <name>` (e.g. `marker: box`)
- `k: <expr>` → `-k <expr>` (e.g. `k: molrs_wrap`)
- `path: <rel-path>` → positional path under the bench repo
- combinations → all of the above on the same pytest invocation

Then layer on the type:

- `type: scientific` → add `-m correctness` (intersects with the feature marker)
- `type: performance` → add `-m 'not correctness' --benchmark-json=<out>` where `<out>` = `.benchmarks/<machine>/<slug>_<criterion-id>.json` (pytest-benchmark autosave dir; machine name is whatever the bench repo already uses)

Missing `evaluator_hint` → mark criterion ⏭ skip with reason `no pytest selector — add evaluator_hint: marker:<name> | k:<expr> | path:<...> to the criterion`.

### 3. Run pytest in the bench repo

`cd $META.bench.repo` (and optionally into `$META.bench.target` if set), run the selector, capture stdout + exit code + JSON path.

- **Scientific verdict.** Exit 0 → ✅ pass with evidence *"N tests passed under `<selector>`"*. Exit non-zero → ❌ fail with the first `AssertionError` line from the bench helpers (e.g. *"`assert_arrays_close` column 'positions': max|rel|=3.2e-5 (rtol=1e-7)"*) as evidence.
- **Performance verdict.** Pytest exit 0 + parse the JSON. Each criterion's `pass_when` MUST be a parseable ratio constraint over `benchmark.group` names, shape: `median(<target_test>) {≤|≥} <factor>× median(<reference_test>)`. Compute the ratio from JSON medians; compare. Examples: `median(molrs_wrap) ≤ 1.5 × median(molpy_wrap)` → pass if measured ratio ≤ 1.5×. Unparseable `pass_when` → ⏭ skip with reason *"pass_when not a ratio constraint; cannot mechanically verify"*.

Don't impose a determinism gate — the bench repo's own `pytest.ini_options` already pins warmup, rounds, and gc; trust the suite's discipline rather than overriding it.

### 4. Verdict + acceptance update

Emit one block per evaluator-protocol shape (`plugins/mol/rules/evaluator-protocol.md`):

```markdown
## /mol:bench — <slug>

| Criterion | Verdict | Evidence |
|-----------|---------|----------|
| ac-006    | ✅ pass | scientific: 4 tests passed under `-m box -m correctness` |
| ac-007    | ✅ pass | performance: median(molrs_wrap)=23µs ≤ 1.50× median(molpy_wrap)=45µs (target ≤1.5×) — measured 0.51× |
| ac-008    | ❌ fail | scientific: `assert_arrays_close` column 'positions': max|rel|=3.2e-5 (rtol=1e-7) |
| ac-009    | ⏭ skip | no pytest selector — add `evaluator_hint: marker: nblist` |

### Artifacts

- `<bench.repo>/.benchmarks/<machine>/<slug>_ac-007.json`
```

Then update `acceptance.md` for each handled criterion per `plugins/mol/rules/evaluator-protocol.md` § *Ledger write-back* (pass → verified, fail → failed, skip → unchanged; `last_checked` beside any flip; touch nothing else).

End with one-line summary:

```
/mol:bench <slug>: 4 criteria evaluated — 2 pass, 1 fail, 1 skip. Bench data under <bench.repo>/.benchmarks/. Re-run `/mol:impl <slug>` to advance to `done` (fix the failure first).
```

## Project configuration

```yaml
mol_project:
  bench:
    # required: absolute path to the external bench repo
    # (e.g. /Users/.../bm-molrs-molpy)
    repo: <abs path>

    # optional: subpath inside the bench repo to scope collection to
    # (e.g. src/bm_molpy/ when this project is molpy)
    target: <relative path, default: src/>
```

Reference libraries (`freud`, `scipy`, `lammps`, …) are declared in the **bench repo's** `pyproject.toml`, not here — the skill defers to whatever the bench repo's environment provides. Missing reference → the bench repo's test fails its own `import` and the skill surfaces that as the fail evidence.

## Acceptance criterion shape

For this skill to verify a criterion, the spec author (`/mol:spec`) should produce:

- **scientific** — `evaluator_hint` names a pytest selector; the matching `test_<feature>_correctness.py` in the bench repo already encodes the reference comparison + tolerance via `bm_common.correctness.assert_*`. `pass_when` is human prose (the skill does not parse it).
  ```yaml
  - id: ac-006
    type: scientific
    evaluator_hint: "marker: box"
    pass_when: "molrs.Box.wrap matches molpy.Box.wrap to atol 1e-9 on all SIZES"
  ```
- **performance** — `evaluator_hint` names the perf-test selector; `pass_when` is a parseable ratio constraint over `benchmark.group` member test names.
  ```yaml
  - id: ac-007
    type: performance
    evaluator_hint: "marker: box; k: wrap"
    pass_when: "median(molrs_wrap) ≤ 1.5 × median(molpy_wrap)"
  ```

## Guardrails

- **Read-only on source.** Never edits implementation code, bench tests, or the bench repo. A failing comparison is fixed by `/mol:fix` in the target project (real regression) or by hand in the bench repo (wrong tolerance / test bug) — not here.
- **Write-narrow on `acceptance.md`.** Only `status` + `last_checked` on just-evaluated criteria, per evaluator-protocol § *Ledger write-back*. Never edit spec body or other fields.
- **The bench repo is authoritative.** Tolerances, reference imports, fixtures, and machine-name partitioning live in the bench repo. This skill does not override them or shell out to other benchmark frameworks. (A C++ / Rust-native suite would need its own evaluator skill — `/mol:bench` is pytest-benchmark-only by design.)
- **Self-skip, don't crash.** Missing `bench.repo`, missing `pytest`, or missing `evaluator_hint` on a criterion → clean exit / `⏭ skip` with the specific gap named.
- **No auto-loop.** Failed verdict does not trigger a re-run after a code change; loop-back belongs to `/mol:impl` or the user.
