# Codex runtime adapter

Apply this file only when Codex loads a skill from this plugin. Claude Code follows the canonical `SKILL.md` directly.

## Canonical contract

- Treat the current `SKILL.md`, `../../agents/`, and `../../rules/` as the source of truth. This adapter translates runtime concepts; it does not replace workflow rules.
- Keep `CLAUDE.md` and its `mol_project:` frontmatter as the canonical project harness. Also honor every applicable `AGENTS.md` because Codex loads those instructions independently.
- Preserve `/mol:<name>` in user-facing output. In Codex, it means the sibling skill at `../<name>/SKILL.md`, selected through the skill picker or loaded explicitly by another workflow.
- Treat invocation text supplied with the selected skill as `$ARGUMENTS`.

## Invokers (user vs model)

Claude and Codex use different knobs for the same split (see
`../../rules/design-principles.md` § 2.5):

| Intent | Claude (`SKILL.md` frontmatter) | Codex (`skills/<name>/agents/openai.yaml`) |
|---|---|---|
| User-invoked only | `disable-model-invocation: true` | `policy.allow_implicit_invocation: false` |
| Model- or skill-reachable | omit the flag | omit, or `allow_implicit_invocation: true` |

When a workflow auto-invokes a sibling, that sibling **must** be
model-invoked. Read the target skill's `SKILL.md` and any
`agents/openai.yaml` before executing it in-thread. Never route an
auto-invoke through a user-only entry (e.g. call `/mol:grilling`, not
`/mol:grill`).

## Paths

Resolve plugin-owned paths from the active skill directory, not from the user's repository:

- `plugins/mol/skills/<name>/SKILL.md` → `../<name>/SKILL.md`
- `plugins/mol/agents/<name>.md` → `../../agents/<name>.md`
- `plugins/mol/rules/<name>.md` → `../../rules/<name>.md`

Read referenced plugin files completely before applying them. Project paths such as `CLAUDE.md`, `.claude/notes/`, and `.claude/specs/` remain relative to the user's project root.

## Tool translation

- Map Claude tool names such as `Read`, `Grep`, `Glob`, `Bash`, `Write`, `Edit`, `WebSearch`, and `WebFetch` to the available Codex tools with the same intent. Do not require a literal tool name.
- Treat `AskUserQuestion` as a normal blocking user question. Continue with safe assumptions when the question is non-blocking, but preserve every explicit approval or destructive-action gate in the canonical workflow.
- When the workflow says to invoke another skill through the Skill tool, read that sibling skill and its adapter, then execute it in the current thread unless independence is part of the contract.
- Claude-specific built-ins such as `/goal` are unavailable. Follow the fallback loop already described by the canonical skill.

## Agent translation

When the canonical workflow delegates to a named agent:

1. Read `../../agents/<name>.md` completely.
2. Treat its `tools` field as a capability boundary and its body as the role prompt. Do not interpret Claude tool names as literal Codex configuration.
3. Use a Codex subagent when collaboration is available and active instructions allow it. Pass the task inputs plus the role prompt's constraints; do not copy unrelated parent context.
4. If subagents are unavailable, execute the role sequentially in the main thread only when the workflow does not require an independent verdict. If independence is required, stop and report the missing capability rather than claiming an independent check.
5. Preserve producer/reviewer ownership: a reviewer remains read-only; `tester` owns tests; `implementer` owns production code; the orchestrating skill owns gates and ledgers.

Claude model tiers describe workload, not required model IDs:

- `opus` → strongest available reasoning for judgment or production work.
- `sonnet` → balanced general-purpose execution.
- `haiku` → fast, low-cost verification when selectable.

If Codex cannot select a tier, use the session model and preserve the role and independence constraints.
