// The DSH plugin, on DSH's own extension points, feeding the real guard
// scripts. molab itself is a fake that logs every call and answers with a
// chosen verdict.
//
//   node --test tests/dsh

import assert from "node:assert/strict";
import { chmodSync, existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { beforeEach, test } from "node:test";
import { Config, TOOLS, apply, preToolEvent } from "../../dsh/index.js";

let dir;
let verdict;
let log;
let env;

beforeEach(() => {
  dir = mkdtempSync(join(tmpdir(), "molcrafts-harness-dsh-"));
  verdict = join(dir, "verdict.json");
  log = join(dir, "molab.log");
  writeFileSync(verdict, JSON.stringify({ allowed: true }));
  mkdirSync(join(dir, "bin"));
  const fake = join(dir, "bin", "molab");
  writeFileSync(
    fake,
    `#!/usr/bin/env python3\nimport json, sys\nopen(${JSON.stringify(log)}, "a").write(json.dumps(sys.argv[1:]) + "\\n")\nprint(open(${JSON.stringify(verdict)}).read())\n`,
  );
  chmodSync(fake, 0o755);
  env = { PATH: `${join(dir, "bin")}:${process.env.PATH}`, XDG_CACHE_HOME: join(dir, "cache") };
});

function configOf(input) {
  const result = Config["~standard"].validate(input);
  assert.equal(result.issues, undefined, JSON.stringify(result.issues));
  return result.value;
}

/** A DSH context with just what the plugin uses; returns what the plugin registered. */
function load(options = {}) {
  const listeners = {};
  const warnings = [];
  const sections = [];
  const disposers = [];
  const globalTools = new Set(options.tools ?? ["bash", "write", "edit", "read", "pwsh"]);
  const ctx = {
    on: (event, listener) => (listeners[event] = listener),
    effect: (open) => disposers.push(open()),
    inject: (_deps, callback) => callback({ systemPrompt: { section: (section) => sections.push(section) } }),
    logger: { warn: (text) => warnings.push(text) },
    workingDirectory: { ensure: async () => dir },
    tools: { get: (name) => (globalTools.has(name) ? { name } : undefined) },
  };
  apply(ctx, configOf({ env, ...options.config }));
  const unload = () => disposers.reverse().forEach((dispose) => dispose?.());
  return { listeners, warnings, sections, unload };
}

const agent = (steered = []) => {
  const restricted = [];
  return {
    session: { id: "session-1" },
    steer: (message) => steered.push(message),
    restricted,
    ctx: {
      tools: {
        restrict: (filter) => {
          restricted.push(filter);
          return () => restricted.splice(restricted.indexOf(filter), 1);
        },
      },
    },
  };
};
const calls = () => (existsSync(log) ? readFileSync(log, "utf8").trim().split("\n").map((line) => JSON.parse(line)) : []);
const allow = async () => ({ kind: "allow" });
const call = (name, args, me = agent()) => ({ name, agent: me, arguments: args, signal: AbortSignal.timeout(60_000) });

test("edit paths are made absolute against the agent's directory", () => {
  const event = preToolEvent("edit", { file_path: "notes/a.md", old_string: "x", new_string: "y" }, { sessionId: "s", cwd: "/lab" });
  assert.equal(event.tool_name, "Edit");
  assert.equal(event.tool_input.file_path, "/lab/notes/a.md");
  assert.equal(preToolEvent("read", { file_path: "a" }, { sessionId: "s", cwd: "/lab" }), undefined);
});

test("config has defaults, ignores a leftover policy key, and rejects what it cannot use", () => {
  assert.deepEqual(configOf({}), { withhold: [], python: "python3", env: {} });
  assert.deepEqual(configOf({ policy: "/x.toml" }), { withhold: [], python: "python3", env: {} });
  const bad = Config["~standard"].validate({ withhold: "pwsh", extra: true });
  assert.deepEqual(bad.issues.map((issue) => issue.path[0]).sort(), ["extra", "withhold"]);
});

test("an allowed write is allowed; molab saw its path", async () => {
  const { listeners } = load();
  const decision = await listeners["tools/pre-execute"](call("write", { file_path: "notes/a.md", content: "# A\n" }), allow);
  assert.deepEqual(decision, { kind: "allow" });
  assert.ok(calls().some((args) => args[1] === "path" && args[2] === join(dir, "notes/a.md")));
  assert.ok(calls().some((args) => args[1] === "tree" && args.includes("--snapshot")), "the first call snapshots the workspace");
});

test("a refused write is a deny decision carrying molab's reason", async () => {
  writeFileSync(verdict, JSON.stringify({ allowed: false, reason: "index.md frontmatter is molab's", command: "molab index write" }));
  const { listeners } = load();
  const decision = await listeners["tools/pre-execute"](call("edit", { file_path: "index.md", old_string: "a", new_string: "b" }), () => assert.fail("must not allow"));
  assert.equal(decision.kind, "deny");
  assert.equal(decision.info.code, "HARNESS_GUARD_DENIED");
  assert.match(decision.reason, /frontmatter is molab's/);
  assert.match(decision.reason, /molab index write/);
});

test("other tools pass straight through", async () => {
  const { listeners } = load();
  assert.deepEqual(await listeners["tools/pre-execute"](call("read", {}), allow), { kind: "allow" });
  assert.deepEqual(calls(), []);
});

test("new molab errors at the end of a turn steer the agent back once", async () => {
  const { listeners, warnings } = load();
  const steered = [];
  const me = agent(steered);
  await listeners["tools/pre-execute"](call("bash", { command: "ls" }, me), allow);
  writeFileSync(verdict, JSON.stringify({ allowed: false, reason: "1 new error", issues: [{ rule: "layout.stray", path: "x.py", hint: "move it" }] }));
  const stopping = { agent: me, turn: 1, signal: AbortSignal.timeout(60_000) };
  await listeners["agent/turn-stopping"](stopping);
  await listeners["agent/turn-stopping"](stopping);
  assert.equal(steered.length, 1, "blocked once, then the turn may end");
  assert.match(warnings.join("\n"), /errors remain after the stop check/, "the second stop says what is left");
  assert.equal(steered[0].role, "user");
  assert.match(steered[0].content[0].text, /layout.stray/);
});

test("DSH tool names come from hooks/tools.json", () => {
  const inventory = JSON.parse(readFileSync(new URL("../../hooks/tools.json", import.meta.url), "utf8"));
  assert.deepEqual(TOOLS, inventory.hosts.dsh);
});

test("an interpreter and ordinary code stay available", async () => {
  const { listeners, sections } = load();
  assert.deepEqual(sections, []);
  const decision = await listeners["tools/pre-execute"](call("bash", { command: "python3 -c 'print(1)'" }), allow);
  assert.deepEqual(decision, { kind: "allow" });
  const written = await listeners["tools/pre-execute"](
    call("write", { file_path: "scratch/try.py", content: "import rdkit\nprint(1)\n" }),
    allow,
  );
  assert.deepEqual(written, { kind: "allow" });
});

test("withheld tools leave every agent's view, and unloading lifts that", () => {
  const { listeners, unload } = load({ tools: ["bash", "pwsh"], config: { withhold: ["pwsh"] } });
  const me = agent();
  listeners["agent/created"]({ agent: me });
  assert.deepEqual(me.restricted, [{ deny: ["pwsh"] }], "only withheld tools that exist are named");
  unload();
  assert.deepEqual(me.restricted, []);
});
