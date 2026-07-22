# Codex runtime adapter

Apply this file only when Codex loads a skill from this plugin. Claude Code follows the canonical `SKILL.md` directly.

- Treat the current `SKILL.md` as the canonical workflow. This file only translates runtime and path concepts.
- Preserve `/molexp:<name>` in user-facing output. In Codex, it means the sibling skill at `../<name>/SKILL.md`.
- Treat invocation text supplied with the selected skill as `$ARGUMENTS`.
- Map Claude tool names to the available Codex tools by intent instead of requiring literal names.
- Resolve `plugins/molexp/...` from this plugin root. Cross-plugin calls into `mol` (e.g. `/mol:bootstrap`) require the `mol` plugin installed.
- When a workflow invokes another skill, read that skill and its Codex adapter before executing it.
- Preserve all approval, typed-path, and destructive-action gates from the canonical workflow.
