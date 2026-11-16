// The harness for DeepSeek Harness (DSH). Skills reach DSH the way they reach
// every other agent: Vercel skills installs them into `.agents/skills`, which
// DSH's skill provider scans. This plugin adds the molab workspace check, on
// DSH's own extension points:
//
// - `tools/pre-execute`: `bash`, `write` and `edit` are asked of
//   hooks/molab_guard.py, the same script the Claude Code and Codex hooks run;
//   a refusal is a `deny` decision carrying molab's reason.
// - `agent/turn-stopping`: the stop check; a block steers the agent back once.
//
// Layout rules live in molab. This file only translates. It does not choose
// which programs or imports an agent may use. Claude Code and Codex workers
// run the same molab guard as their own hooks.
// No runtime package is imported, so the plugin loads from any profile.

import { spawn } from "node:child_process";
import { randomUUID } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, isAbsolute, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export const name = "molcrafts-harness";
export const inject = ["tools", "workingDirectory"];

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const HOOKS = join(ROOT, "hooks");
/** Every guard, in the order they are asked. */
export const GUARDS = [join(HOOKS, "molab_guard.py")];
/** The guard's own budget is 100 s; give the process a little more. */
const GUARD_TIMEOUT_MS = 120_000;
/** DSH tool name → the Claude-shaped tool the guards read. One inventory: hooks/tools.json. */
export const TOOLS = JSON.parse(readFileSync(join(HOOKS, "tools.json"), "utf8")).hosts.dsh;
const DENIED = { name: "HarnessGuardDenied", code: "HARNESS_GUARD_DENIED" };

// ── Config (a Standard Schema, so the plugin needs no schema library) ──────

const CONFIG_JSON_SCHEMA = {
  type: "object",
  additionalProperties: false,
  properties: {
    withhold: {
      type: "array",
      items: { type: "string" },
      default: [],
      description: "Optional tool names removed from every agent. Empty by default: other tools stay available.",
    },
    python: { type: "string", default: "python3", description: "Interpreter for the guard scripts." },
    env: { type: "object", additionalProperties: { type: "string" }, default: {}, description: "Extra variables for the guard processes." },
    policy: { description: "Ignored. The allowlist was removed; this key does not restrict tools." },
  },
};

function validateConfig(input) {
  const issues = [];
  const issue = (key, message) => issues.push({ message: `${key}: ${message}`, path: [key] });
  if (input != null && (typeof input !== "object" || Array.isArray(input))) return { issues: [{ message: "config must be an object" }] };
  const value = { ...(input ?? {}) };
  // The allowlist policy is gone. A profile that still names it loads, and the key does nothing.
  delete value.policy;
  for (const key of Object.keys(value)) if (!(key in CONFIG_JSON_SCHEMA.properties)) issue(key, "unknown option");
  const { withhold = [], python = "python3", env = {} } = value;
  if (!Array.isArray(withhold) || withhold.some((item) => typeof item !== "string")) issue("withhold", "must be a list of tool names");
  if (typeof python !== "string" || python === "") issue("python", "must be a command");
  if (typeof env !== "object" || env === null || Object.values(env).some((item) => typeof item !== "string")) issue("env", "must map names to strings");
  if (issues.length > 0) return { issues };
  return { value: { withhold, python, env } };
}

export const Config = {
  "~standard": {
    version: 1,
    vendor: "molcrafts-harness",
    validate: validateConfig,
    jsonSchema: { input: () => CONFIG_JSON_SCHEMA, output: () => CONFIG_JSON_SCHEMA },
  },
};

// ── guard processes ─────────────────────────────────────────────────────────

/** Run `guard` in `mode` with `event` on stdin; resolve its JSON answer (or null). */
export function runGuard(mode, event, { python = "python3", guard, env = {}, cwd, signal } = {}) {
  return new Promise((done, fail) => {
    const child = spawn(python, [guard, mode], {
      cwd,
      env: { ...process.env, ...env },
      stdio: ["pipe", "pipe", "pipe"],
      signal,
      timeout: GUARD_TIMEOUT_MS,
    });
    let out = "";
    let err = "";
    child.stdout.on("data", (chunk) => (out += chunk));
    child.stderr.on("data", (chunk) => (err += chunk));
    child.on("error", fail);
    child.on("close", (code) => {
      if (code !== 0) return fail(new Error(`${guard} exited ${code}: ${err.trim()}`));
      try {
        done(out.trim() ? JSON.parse(out) : null);
      } catch {
        fail(new Error(`${guard} answered with something other than JSON: ${out.slice(0, 200)}`));
      }
    });
    child.stdin.end(JSON.stringify(event));
  });
}

/** The PreToolUse event for one DSH tool call, or undefined when the guard does not look at that tool. */
export function preToolEvent(toolName, args, { sessionId, cwd }) {
  const tool = TOOLS[toolName];
  if (tool === undefined || args === null || typeof args !== "object") return undefined;
  const input = { ...args };
  if (tool === "Bash") {
    if (typeof input.workdir === "string") input.cwd = isAbsolute(input.workdir) ? input.workdir : resolve(cwd, input.workdir);
  } else if (typeof input.file_path === "string") {
    input.file_path = isAbsolute(input.file_path) ? input.file_path : resolve(cwd, input.file_path);
  }
  return { hook_event_name: "PreToolUse", session_id: sessionId, cwd, tool_name: tool, tool_input: input };
}

/** A frozen user message, shaped like DSH's createUserMessage output. */
function harnessMessage(text, summary) {
  return Object.freeze({
    id: randomUUID(),
    role: "user",
    content: Object.freeze([Object.freeze({ type: "text", text })]),
    source: Object.freeze({ kind: "molcrafts-harness", form: "notice", summary }),
  });
}

// ── the plugin ──────────────────────────────────────────────────────────────

export function apply(ctx, config) {
  const { withhold, python, env } = config;

  // Withheld tools leave each agent's view; the disposers are kept here too, so
  // unloading the plugin lifts them even while the agent lives on.
  const restrictions = new Map();
  ctx.effect(() => () => {
    for (const dispose of restrictions.values()) dispose();
    restrictions.clear();
  });
  ctx.on("agent/created", ({ agent }) => {
    const present = withhold.filter((tool) => ctx.tools.get(tool) !== undefined);
    if (present.length === 0) return;
    const dispose = agent.ctx.tools.restrict({ deny: present });
    restrictions.set(agent, dispose);
  });
  ctx.on("agent/disposed", ({ agent }) => restrictions.delete(agent));

  const started = new Set();
  const stopBlocked = new Set();
  const sessionOf = (agent) => String(agent.session.id);

  /** Ask every guard; collect their answers (a failed guard is warned about and skipped). */
  async function ask(mode, event, cwd, signal) {
    const answers = [];
    for (const guard of GUARDS) {
      try {
        const answer = await runGuard(mode, event, { python, guard, env, cwd, signal });
        if (answer?.systemMessage) ctx.logger.warn(`molcrafts-harness: ${answer.systemMessage}`);
        if (answer) answers.push(answer);
        if (answer?.hookSpecificOutput?.permissionDecision === "deny") break;
      } catch (error) {
        ctx.logger.warn(`molcrafts-harness: ${guard} gave no answer (${mode}): ${error.message}`);
      }
    }
    return answers;
  }

  async function ensureStarted(agent, cwd, signal) {
    const sessionId = sessionOf(agent);
    if (started.has(sessionId)) return;
    started.add(sessionId);
    await ask("start", { hook_event_name: "SessionStart", session_id: sessionId, cwd }, cwd, signal);
  }

  ctx.on("tools/pre-execute", async (exec, next) => {
    if (exec.agent === undefined || !(exec.name in TOOLS)) return next();
    const cwd = await ctx.workingDirectory.ensure(exec.agent, exec.signal);
    await ensureStarted(exec.agent, cwd, exec.signal);
    const event = preToolEvent(exec.name, exec.arguments, { sessionId: sessionOf(exec.agent), cwd });
    if (event === undefined) return next();
    const answers = await ask("pre", event, cwd, exec.signal);
    const denied = answers.find((answer) => answer.hookSpecificOutput?.permissionDecision === "deny");
    if (denied === undefined) return next();
    const reason = denied.hookSpecificOutput.permissionDecisionReason ?? "no reason given";
    return { kind: "deny", reason: `The harness refused this call:\n${reason}`, info: DENIED };
  });

  ctx.on("agent/turn-stopping", async ({ agent, turn, signal }) => {
    const sessionId = sessionOf(agent);
    if (!started.has(sessionId)) return;
    const cwd = await ctx.workingDirectory.ensure(agent, signal);
    const key = `${sessionId}:${turn}`;
    const event = { hook_event_name: "Stop", session_id: sessionId, cwd, stop_hook_active: stopBlocked.has(key) };
    const blocks = (await ask("stop", event, cwd, signal)).filter((answer) => answer.decision === "block");
    if (blocks.length > 0 && !stopBlocked.has(key)) {
      stopBlocked.add(key);
      const reasons = blocks.map((answer) => answer.reason ?? "").join("\n\n");
      agent.steer(harnessMessage(`The harness found problems before this turn could end. Fix them, then finish:\n${reasons}`, "harness stop check"));
    }
  });
}
