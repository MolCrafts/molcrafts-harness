# MolCrafts Harness contract

Keep this repository to standard Agent Skills and evaluation. Harness never
executes or proxies tools. Tools own syntax, schemas, and domain facts. Keep one
short skill per tool; use Vercel skills for distribution. No custom installer,
registry, version resolver, adapter, RAG, MCP gateway, or agent runtime without a
concrete evaluation failure demonstrating the need.

Every behavior rule should map to an evaluation case. Evaluate decisions and
observable evidence, not exact command strings. Preserve explicit user choices.
Run `python3 -m unittest discover -s tests/skill-quality -v` after changes.
