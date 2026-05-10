# `mol_project` CLAUDE.md Metadata Contract

The `mol` plugin's skills and agents are project-agnostic. They learn
the project facts — language, build/test commands, architecture
layout, doc style, hot-path focus, and where internal agent context
lives — by reading a `mol_project:` YAML frontmatter block at the top
of the project's `CLAUDE.md`.

Adopting this contract is **optional**. `/mol-agent:bootstrap` will
create a CLAUDE.md without it (the basic harness-engineering layering — see
`design-principles.md` § 1 — does not require the contract). Add the
block when you want the `mol` plugin's skills (`/mol:impl`,
`/mol:review`, …) to adapt to your project automatically.

## Placement

The block is the very first thing in CLAUDE.md, delimited by `---`:

```markdown
---
mol_project:
  name: molpy
  language: python
  build:
    install: "pip install -e '.[dev]'"
    check: "ruff check src tests && ruff format --check src tests && ty check src"
    test: "pytest tests/ -v -m 'not external'"
    test_single: "pytest {path} -v"
    coverage: "pytest --cov=src/molpy tests/"
  arch:
    style: layered
    rules_section: "## Architecture"
  doc:
    style: google
  science:
    required: true
  notes_path: .claude/notes/notes.md
  specs_path: .claude/specs/
---

# CLAUDE.md

(rest of the file unchanged — kept thin per the L3 router rule)
```

Skills extract this block with a small shell snippet:

```bash
awk '/^---$/{c++; next} c==1' CLAUDE.md | yq .mol_project
```

or a one-line Python fallback when `yq` is absent:

```python
import pathlib, yaml
text = pathlib.Path("CLAUDE.md").read_text()
front = text.split("---\n", 2)[1]
cfg = yaml.safe_load(front)["mol_project"]
```

## Fields

### `name` (required, string)

Project identifier. Used in skill output and for disambiguation. Example:
`atomiverse`, `molpy`, `molrs`.

### `language` (required, enum)

Primary language. Drives language-aware heuristics in agents.

| Value        | Projects              |
|--------------|-----------------------|
| `python`     | molpy, molexp (backend), molq, molnex |
| `rust`       | molrs                 |
| `cpp`        | Atomiverse            |
| `typescript` | molvis (frontend), molexp (ui) |
| `mixed`      | polyglot repos — caller must disambiguate at skill time |

### `build` (required, object)

Exact shell commands the skills run. Skills invoke these verbatim.
Missing keys cause the skill to fall back to a project-type default
(e.g. `pytest tests/` for Python if `test` is absent) with a warning.

| Key            | Purpose                                              |
|----------------|------------------------------------------------------|
| `install`      | Install deps for a fresh checkout                    |
| `check`        | Format + lint + type-check (CI-gating, non-mutating). Should run the **language-canonical toolchain trio**; `janitor` will surface a rule-capture suggestion if any of the three is absent |
| `test`         | Run the full test suite                              |
| `test_single`  | Template with `{path}` placeholder for one test      |
| `coverage`     | Full suite with coverage report                      |

**Recommended `check` value per language** (see
`plugins/mol/agents/janitor.md` § *Language-canonical toolchains*
for the authoritative table):

| `language`    | Suggested `check`                                                                     |
|---------------|---------------------------------------------------------------------------------------|
| `python`      | `ruff check . && ruff format --check . && ty check .` (or `mypy` while migrating)     |
| `typescript`  | `biome check . && tsc --noEmit`                                                       |
| `rust`        | `cargo fmt --check && cargo clippy -- -D warnings && cargo check`                     |
| `cpp`         | `clang-format --dry-run --Werror $(git ls-files '*.cpp' '*.h') && clang-tidy …`       |
| `mixed`       | concatenate the per-language commands with `&&`, scoped by directory                  |

### `arch` (required, object)

| Key              | Type   | Notes                                                             |
|------------------|--------|-------------------------------------------------------------------|
| `style`          | enum   | `layered` / `crate-graph` / `backend-pillars` / `package-tree` / `monorepo` — picks the dependency-rule template the architect agent applies |
| `rules_section`  | string | Exact heading in CLAUDE.md (or in a `.claude/notes/architecture.md` page linked from CLAUDE.md) that holds the architecture rules. The architect agent reads everything under this heading |

### `doc` (required, object)

| Key     | Type | Notes                                                           |
|---------|------|-----------------------------------------------------------------|
| `style` | enum | `google` / `rustdoc` / `jsdoc-tiered` / `doxygen` — the documenter agent adopts this format. `jsdoc-tiered` means a Full/Brief/Inline three-tier system per symbol kind |

### `science` (required, object)

| Key        | Type | Notes                                                             |
|------------|------|-------------------------------------------------------------------|
| `required` | bool | `true` gates `/mol:litrev` and the `scientist` agent onto the `/mol:impl` path. `false` skips both (useful for infrastructure projects like molq) |

### `stage` (optional, enum)

The project's lifecycle stage. Governs how aggressive the writing
skills (`/mol:impl`, `/mol:fix`, `/mol:refactor`, `/mol:simplify`)
and reviewers (`pm`, `janitor`) are allowed to be when touching
existing code. See `plugins/mol/rules/stage-policy.md` for the full
behavioral matrix.

| Value          | Intent                                | Effect summary                                                       |
|----------------|---------------------------------------|----------------------------------------------------------------------|
| `experimental` | pre-1.0, churn allowed (the default)  | breaking changes are normal, legacy code deleted on sight, no shims  |
| `beta`         | pre-1.0 with known users              | breaking changes allowed at minor bumps with migration note          |
| `stable`       | `≥ 1.0`, semver applies               | additive changes preferred; deprecate-then-remove across one major   |
| `maintenance`  | bug fixes / security only             | `/mol:impl` and `/mol:refactor` refuse; only `/mol:fix` proceeds     |

If absent, skills default to `experimental` and emit a warning on
first read. This is intentional graceful degradation — adopting the
harness on a new project should not require thinking about lifecycle
on day one — but the warning surfaces the field so a `1.x` library
maintainer is reminded to set `stage: stable`.

Example:

```yaml
stage: experimental
```

### `ci` (optional, object)

Used by `/mol:ship` and the `ci-guard` agent. If absent, `ci-guard`
auto-detects the workflow file. Declaring it explicitly makes the
merge-gate reproducible and removes guesswork.

| Key      | Type   | Notes                                                                                            |
|----------|--------|--------------------------------------------------------------------------------------------------|
| `config` | string | Path to the primary CI workflow, e.g. `.github/workflows/ci.yml`. `ci-guard` parses its matrix.  |
| `local`  | string | Shell command that reproduces the full CI pipeline locally (e.g. `nox -s ci`, `act push`, `make ci`). Used by the `merge` tier of `/mol:ship`. |

Example:

```yaml
ci:
  config: .github/workflows/ci.yml
  local: "act push"
```

### `style` (optional, mapping) — janitor knobs

Tunes the `janitor` agent's continuous tech-debt scan. Every key is
optional; defaults apply if the section is absent.

| Key                  | Default | Notes                                                                                                        |
|----------------------|---------|--------------------------------------------------------------------------------------------------------------|
| `max_function_lines` | `80`    | Functions longer than this are flagged 🟡 by `janitor` as sprawling.                                          |

Example:

```yaml
style:
  max_function_lines: 60
```

### `debt` (optional, mapping) — debt-marker windowing

Configures when stale `TODO` / `FIXME` / `XXX` markers become hygiene
findings. Defaults apply if absent.

| Key                | Default | Notes                                                                                                  |
|--------------------|---------|--------------------------------------------------------------------------------------------------------|
| `todo_window_days` | `60`    | Markers older than this are 🟡; older than `2×` this without an owner annotation are 🔴.                |

Example:

```yaml
debt:
  todo_window_days: 30
```

### `notes_path` (optional, string)

Where `/mol:note` writes evolving decisions and where every agent
reads recent notes from. This is **internal agent context** (zone
`.claude/notes/` per `design-principles.md` § 1) — never `docs/`.

Resolution order (the skill does this; you only set it once):

1. The value of `mol_project.notes_path` if present.
2. `.claude/notes/notes.md` if `.claude/notes/` exists in the repo.
3. Legacy fallback: `.claude/NOTES.md`.

The harness-engineering preferred default is `.claude/notes/notes.md`. Legacy
projects that already keep their notes in `.claude/NOTES.md` may
continue to do so by declaring it explicitly.

### `specs_path` (optional, string)

Where `/mol:spec` persists specifications.

Resolution order:

1. The value of `mol_project.specs_path` if present.
2. Default: `.claude/specs/`.

Specs are **active runtime artifacts** — `/mol:impl` ticks their
Tasks checkboxes off as it works and **deletes** the file (and its
INDEX entry) on completion. They live under `.claude/`, not under
`.claude/notes/` (passive context) or `docs/` (public documentation).

## Layering note

Following the four-zone layering in `design-principles.md` § 1, the
two configurable paths land in different zones because they hold
different *kinds* of content:

- `notes_path` → `.claude/notes/notes.md` (passive context — decisions,
  reasoning, captured invariants).
- `specs_path` → `.claude/specs/` (active runtime artifacts — alive,
  ticked off as work progresses, deleted on completion).

The full zone breakdown:

- `docs/` — public-facing documentation (no `mol_project` field;
  conventional).
- `.claude/notes/` — internal agent context (`notes_path`, contracts,
  handoffs, rubrics, decisions, debt).
- `.claude/` — Claude Code runtime: skills, agents, hooks, settings,
  and **active** working artifacts like `specs/`.
- `CLAUDE.md` — thin router that holds the `mol_project:`
  frontmatter and points to the other zones.

The distinction between `.claude/notes/` and `.claude/specs/` is the active /
passive split: notes outlive any single feature; specs are intentionally
ephemeral.

## Graceful degradation

Missing `mol_project` block entirely → most skills print:

```
[mol] No mol_project frontmatter found in CLAUDE.md.
Run /mol-agent:bootstrap to set up the harness for this project.
```

`/mol-agent:bootstrap` itself does not require the block — it is the
tool used to create CLAUDE.md (and optionally populate the block).

Missing individual keys → the skill logs a `[mol] falling back …` line
and uses language-based defaults. Partial adoption is supported.
