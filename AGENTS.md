# MolCrafts Harness contract

Keep this repository to standard Agent Skills, evaluation, and the hooks named
below. Harness never proxies tools. Tools own syntax, schemas, and domain
facts. Keep one short skill per tool; use Vercel skills or the Claude Code
plugin for distribution. No custom installer, registry, version resolver, RAG,
MCP gateway, or agent runtime without a concrete evaluation failure
demonstrating the need.

Hooks are the one exception, and they were added after such a failure. Agents
wrote a molab workspace by hand: files beside experiment records, hand-made
records, finished jobs never recorded. `hooks/molab_guard.py` only forwards an
event to `molab check` and passes molab's verdict back. It holds no rule.
A shell command is forwarded whole to `molab check command`, with its working
directory. A command the grammar cannot read is allowed; the stop check
covers every workspace the session touched. A write whose path cannot be read
is denied. A missing tool means
allow when the path can be read. A new rule goes into molab, not into `hooks/`.

Skills name the MolCrafts tool that owns a job and ask the agent to do that
job with that tool. Reading, searching, editing, git, interpreters, package
managers, and tests stay available. Do not add an allowlist, a `policy.toml`,
or a guard that refuses imports and commands outside MolCrafts. A missing
MolCrafts API is reported; the rest of the session continues with the tools
that can finish it.

Every behavior rule should map to an evaluation case. Evaluate decisions and
observable evidence, not exact command strings. Preserve explicit user choices.
Skills reach every agent through Vercel skills. Claude Code and Codex call
the molab guard as hooks (`hooks/hooks.json`, `hooks/codex.json`); DeepSeek
Harness calls it from the DSH plugin in `dsh/`, which follows DSH's plugin
conventions (`tools/pre-execute`, `agent/turn-stopping`, a Standard Schema
`Config`, locale and icon) and only translates DSH tool calls into the same
events. Keep agent-specific code to that translation.

Run `python3 -m unittest discover -s tests/skill-quality -v`,
`python3 -m unittest discover -s tests/hooks -v` and `node --test tests/dsh`
after changes.
