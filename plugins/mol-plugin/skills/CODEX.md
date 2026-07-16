# Codex runtime adapter

Apply this file only when Codex loads a skill from this plugin. Claude Code follows the canonical `SKILL.md` directly.

- Treat the current `SKILL.md` as the canonical workflow. This file only translates runtime and path concepts.
- Preserve `/mol-plugin:<name>` in user-facing output. In Codex, it means the sibling skill at `../<name>/SKILL.md`.
- Treat invocation text supplied with the selected skill as `$ARGUMENTS`.
- Map Claude tool names to the available Codex tools by intent instead of requiring literal names.
- Resolve `plugins/mol-plugin/...` from this plugin root and `plugins/mol/...` from the installed `mol` plugin. If a required cross-plugin skill or file is unavailable, stop and name the missing `mol` dependency.
- When a workflow invokes another skill, read that skill and its Codex adapter before executing it.
- Keep `.claude-plugin/` as the authoritative Claude Code metadata. Treat `.agents/plugins/marketplace.json` and `.codex-plugin/plugin.json` as Codex metadata and validate both without deriving one format from the other.
- Preserve all approval, clean-tree, commit, tag, and push gates from the canonical workflow.
