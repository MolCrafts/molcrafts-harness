# MolCrafts Harness contract

Keep this repository to standard Agent Skills, evaluation, and the hooks named
below. Harness never proxies tools. Tools own syntax, schemas, and domain
facts. Keep one short skill per tool; use Vercel skills or the Claude Code
plugin for distribution. No custom installer, registry, version resolver, RAG,
MCP gateway, or agent runtime without a concrete evaluation failure
demonstrating the need.

Hooks are the one exception, and they were added after such a failure. Agents
wrote a molab workspace by hand: files beside experiment records, hand-made
records, finished jobs never recorded. A hook only forwards an event to the
tool's own check command (`molab check`) and passes the tool's verdict back.
It holds no rule. A missing tool means allow. A new rule goes into the tool,
not into `hooks/`.

Every behavior rule should map to an evaluation case. Evaluate decisions and
observable evidence, not exact command strings. Preserve explicit user choices.
Run `python3 -m unittest discover -s tests/skill-quality -v` and
`python3 -m unittest discover -s tests/hooks -v` after changes.
