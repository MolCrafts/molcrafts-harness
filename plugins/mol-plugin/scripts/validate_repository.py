#!/usr/bin/env python3
"""Validate the dual Claude Code/Codex MolCrafts plugin marketplace."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)(.*)$", re.DOTALL)
SKILL_REF_RE = re.compile(r"/(mol(?:-plugin)?):([a-z0-9][a-z0-9-]*)")
VALID_MODELS = {"opus", "sonnet", "haiku", "inherit"}
VALID_INSTALL_POLICIES = {"AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE"}
VALID_AUTH_POLICIES = {"ON_INSTALL", "ON_USE"}
CODEX_DIRECTIVE = (
    "> **Codex:** Read `../CODEX.md` before executing this shared workflow. "
    "Claude Code follows the workflow directly."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Claude Code and Codex metadata for this marketplace."
    )
    parser.add_argument(
        "--root",
        type=Path,
        help="Repository root. Defaults to the repository containing this script.",
    )
    parser.add_argument(
        "--root-from-cwd",
        action="store_true",
        help="Find a marketplace root from cwd; exit successfully when none exists.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the success summary. Errors and warnings are still printed.",
    )
    return parser.parse_args()


def find_marketplace_root(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".claude-plugin" / "marketplace.json").is_file():
            return candidate
    return None


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    match = FRONTMATTER_RE.match(text)
    if match is None:
        return None
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line or line[0].isspace() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition(":")
        if separator:
            fields[key.strip()] = value.strip()
    return fields, match.group(2)


class Validator:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.skill_names: dict[str, set[str]] = {}

    def rel(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return str(path)

    def error(self, path: Path, message: str) -> None:
        self.errors.append(f"{self.rel(path)} — {message}")

    def warn(self, path: Path, message: str) -> None:
        self.warnings.append(f"{self.rel(path)} — {message}")

    def load_json(self, path: Path) -> dict[str, Any] | None:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            self.error(path, "missing JSON file")
            return None
        except (OSError, json.JSONDecodeError) as exc:
            self.error(path, f"invalid JSON: {exc}")
            return None
        if not isinstance(value, dict):
            self.error(path, "top level must be an object")
            return None
        return value

    def validate(self) -> None:
        legacy_path = self.root / ".claude-plugin" / "marketplace.json"
        codex_path = self.root / ".agents" / "plugins" / "marketplace.json"
        legacy = self.load_json(legacy_path)
        codex = self.load_json(codex_path)
        if legacy is None or codex is None:
            return

        legacy_entries = self.validate_legacy_marketplace(legacy_path, legacy)
        codex_entries = self.validate_codex_marketplace(codex_path, codex)

        legacy_names = [entry.get("name") for entry in legacy_entries]
        codex_names = [entry.get("name") for entry in codex_entries]
        if legacy_names != codex_names:
            self.error(
                codex_path,
                f"plugin order/names {codex_names!r} do not match Claude registry {legacy_names!r}",
            )

        if legacy.get("name") != codex.get("name"):
            self.error(codex_path, "marketplace name does not match Claude registry")

        codex_by_name = {
            entry.get("name"): entry
            for entry in codex_entries
            if isinstance(entry.get("name"), str)
        }
        registered: set[str] = set()
        for entry in legacy_entries:
            name = entry.get("name")
            source = entry.get("source")
            if not isinstance(name, str) or not name:
                self.error(legacy_path, "plugin entry has no non-empty name")
                continue
            if not isinstance(source, str) or not source.startswith("./"):
                self.error(legacy_path, f"{name}: source must be a ./-prefixed string")
                continue
            plugin_root = (self.root / source).resolve()
            if self.root not in plugin_root.parents:
                self.error(legacy_path, f"{name}: source escapes the repository")
                continue
            registered.add(name)
            self.validate_plugin(name, plugin_root, entry, codex_by_name.get(name))

        plugins_root = self.root / "plugins"
        if plugins_root.is_dir():
            discovered = {
                path.name
                for path in plugins_root.iterdir()
                if path.is_dir()
                and (
                    (path / ".claude-plugin" / "plugin.json").is_file()
                    or (path / ".codex-plugin" / "plugin.json").is_file()
                )
            }
            for name in sorted(discovered - registered):
                self.error(plugins_root / name, "plugin is not registered in the Claude marketplace")

        self.validate_references()

    def validate_legacy_marketplace(
        self, path: Path, payload: dict[str, Any]
    ) -> list[dict[str, Any]]:
        for field in ("name", "description", "owner", "plugins"):
            if field not in payload:
                self.error(path, f"missing top-level field {field!r}")
        owner = payload.get("owner")
        if not isinstance(owner, dict) or not isinstance(owner.get("name"), str):
            self.error(path, "owner.name must be a string")
        entries = payload.get("plugins")
        if not isinstance(entries, list):
            self.error(path, "plugins must be an array")
            return []
        typed = [entry for entry in entries if isinstance(entry, dict)]
        if len(typed) != len(entries):
            self.error(path, "every plugin entry must be an object")
        names = [entry.get("name") for entry in typed]
        if len(names) != len(set(names)):
            self.error(path, "plugin names must be unique")
        return typed

    def validate_codex_marketplace(
        self, path: Path, payload: dict[str, Any]
    ) -> list[dict[str, Any]]:
        interface = payload.get("interface")
        if not isinstance(interface, dict) or not isinstance(
            interface.get("displayName"), str
        ):
            self.error(path, "interface.displayName must be a string")
        entries = payload.get("plugins")
        if not isinstance(entries, list):
            self.error(path, "plugins must be an array")
            return []
        typed = [entry for entry in entries if isinstance(entry, dict)]
        if len(typed) != len(entries):
            self.error(path, "every plugin entry must be an object")
        for entry in typed:
            name = entry.get("name", "<unnamed>")
            source = entry.get("source")
            if not isinstance(source, dict):
                self.error(path, f"{name}: source must be an object")
            else:
                if source.get("source") != "local":
                    self.error(path, f"{name}: source.source must be 'local'")
                source_path = source.get("path")
                if not isinstance(source_path, str) or not source_path.startswith("./"):
                    self.error(path, f"{name}: source.path must be ./-prefixed")
            policy = entry.get("policy")
            if not isinstance(policy, dict):
                self.error(path, f"{name}: policy must be an object")
            else:
                if policy.get("installation") not in VALID_INSTALL_POLICIES:
                    self.error(path, f"{name}: invalid installation policy")
                if policy.get("authentication") not in VALID_AUTH_POLICIES:
                    self.error(path, f"{name}: invalid authentication policy")
            if not isinstance(entry.get("category"), str):
                self.error(path, f"{name}: category must be a string")
            for duplicate in ("version", "description"):
                if duplicate in entry:
                    self.error(path, f"{name}: {duplicate} belongs in the plugin manifest")
        return typed

    def validate_plugin(
        self,
        name: str,
        plugin_root: Path,
        legacy_entry: dict[str, Any],
        codex_entry: dict[str, Any] | None,
    ) -> None:
        if not plugin_root.is_dir():
            self.error(plugin_root, f"registered plugin {name!r} directory is missing")
            return
        legacy_path = plugin_root / ".claude-plugin" / "plugin.json"
        codex_path = plugin_root / ".codex-plugin" / "plugin.json"
        legacy = self.load_json(legacy_path)
        codex = self.load_json(codex_path)
        if legacy is None or codex is None:
            return

        if legacy.get("name") != name or codex.get("name") != name:
            self.error(plugin_root, "directory, Claude manifest, and Codex manifest names differ")
        if legacy.get("version") != codex.get("version"):
            self.error(plugin_root, "Claude and Codex manifest versions differ")
        if legacy_entry.get("version") != legacy.get("version"):
            self.error(legacy_path, "version differs from Claude marketplace entry")
        if not isinstance(legacy.get("displayName"), str):
            self.error(legacy_path, "displayName must be present for Claude Code UI")
        if legacy.get("$schema") != "https://json.schemastore.org/claude-code-plugin-manifest.json":
            self.error(legacy_path, "Claude manifest must declare the official JSON schema")

        source_path = None
        if isinstance(codex_entry, dict) and isinstance(codex_entry.get("source"), dict):
            source_path = codex_entry["source"].get("path")
        expected_source = f"./plugins/{name}"
        if source_path != expected_source:
            self.error(codex_path, f"Codex marketplace source must be {expected_source!r}")

        author = codex.get("author")
        interface = codex.get("interface")
        if not isinstance(author, dict) or not isinstance(author.get("name"), str):
            self.error(codex_path, "author.name must be a string")
        if codex.get("skills") != "./skills/":
            self.error(codex_path, "skills must point to the shared ./skills/ directory")
        if (plugin_root / "codex-skills").exists():
            self.error(
                plugin_root / "codex-skills",
                "remove the duplicated Codex skill tree; both runtimes must share ./skills/",
            )
        required_interface = {
            "displayName",
            "shortDescription",
            "longDescription",
            "developerName",
            "category",
            "capabilities",
            "defaultPrompt",
        }
        if not isinstance(interface, dict):
            self.error(codex_path, "interface must be an object")
        else:
            missing = sorted(required_interface - set(interface))
            if missing:
                self.error(codex_path, f"interface is missing {', '.join(missing)}")

        self.validate_skills(name, plugin_root)
        self.validate_agents(plugin_root)
        self.validate_hooks(plugin_root)

    def validate_skills(self, plugin_name: str, plugin_root: Path) -> None:
        skills_root = plugin_root / "skills"
        adapter = skills_root / "CODEX.md"
        if not adapter.is_file():
            self.error(adapter, "missing shared Codex runtime adapter")
        skill_names: set[str] = set()
        if not skills_root.is_dir():
            self.error(skills_root, "missing skills directory")
            return
        for skill_root in sorted(skills_root.iterdir()):
            if not skill_root.is_dir():
                continue
            skill_md = skill_root / "SKILL.md"
            if not skill_md.is_file():
                self.error(skill_md, "skill directory has no SKILL.md")
                continue
            skill_names.add(skill_root.name)
            parsed = parse_frontmatter(skill_md)
            if parsed is None:
                self.error(skill_md, "missing or malformed YAML frontmatter")
                continue
            fields, body = parsed
            if fields.get("name") != skill_root.name:
                self.error(skill_md, "frontmatter name must match the skill directory")
            if not fields.get("description"):
                self.error(skill_md, "description must be non-empty")
            if CODEX_DIRECTIVE not in body:
                self.error(skill_md, "missing the shared Codex adapter directive")
            expected_h1 = f"# /{plugin_name}:{skill_root.name} — "
            if expected_h1 not in body:
                self.error(skill_md, f"H1 must begin with {expected_h1!r}")
        self.skill_names[plugin_name] = skill_names

    def validate_agents(self, plugin_root: Path) -> None:
        agents_root = plugin_root / "agents"
        if not agents_root.is_dir():
            return
        for path in sorted(agents_root.glob("*.md")):
            parsed = parse_frontmatter(path)
            if parsed is None:
                self.error(path, "missing or malformed YAML frontmatter")
                continue
            fields, body = parsed
            for field in ("name", "description", "tools", "model"):
                if not fields.get(field):
                    self.error(path, f"missing non-empty frontmatter field {field!r}")
            if fields.get("name") != path.stem:
                self.error(path, "agent name must match filename")
            if fields.get("model") not in VALID_MODELS:
                self.error(path, f"model must be one of {sorted(VALID_MODELS)!r}")
            if fields.get("model") == "inherit":
                self.warn(path, "mol agents should pin an explicit model tier")
            first_line = next((line for line in body.splitlines() if line.strip()), "")
            if "CLAUDE.md" not in first_line:
                self.error(path, "first body instruction must read CLAUDE.md")
            tools = fields.get("tools", "")
            if "read-only" in fields.get("description", "").lower() and any(
                tool in tools for tool in ("Write", "Edit")
            ):
                self.error(path, "read-only agent declares Write or Edit")

    def validate_hooks(self, plugin_root: Path) -> None:
        hooks_path = plugin_root / "hooks" / "hooks.json"
        if not hooks_path.exists():
            return
        payload = self.load_json(hooks_path)
        if payload is None:
            return
        hooks = payload.get("hooks")
        if not isinstance(hooks, dict) or not hooks:
            self.error(hooks_path, "hooks must be a non-empty object")

    def validate_references(self) -> None:
        for plugin_name, names in sorted(self.skill_names.items()):
            plugin_root = self.root / "plugins" / plugin_name
            candidates = list((plugin_root / "skills").glob("*/SKILL.md"))
            candidates.append(plugin_root / "README.md")
            for path in candidates:
                if not path.is_file():
                    continue
                text = path.read_text(encoding="utf-8")
                for target_plugin, target_skill in SKILL_REF_RE.findall(text):
                    target_names = self.skill_names.get(target_plugin)
                    if target_names is None or target_skill in target_names:
                        continue
                    # new-skill intentionally contains hypothetical examples.
                    if path.name == "SKILL.md" and path.parent.name == "new-skill":
                        continue
                    self.warn(
                        path,
                        f"reference /{target_plugin}:{target_skill} has no matching skill",
                    )

    def report(self, quiet: bool) -> int:
        for item in self.errors:
            print(f"ERROR: {item}", file=sys.stderr)
        for item in self.warnings:
            print(f"WARNING: {item}", file=sys.stderr)
        if self.errors:
            print(
                f"plugin validation failed: {len(self.errors)} error(s), "
                f"{len(self.warnings)} warning(s)",
                file=sys.stderr,
            )
            return 1
        if not quiet:
            print(f"plugin validation passed: {len(self.warnings)} warning(s)")
        return 0


def main() -> int:
    args = parse_args()
    if args.root_from_cwd:
        root = find_marketplace_root(Path.cwd())
        if root is None:
            return 0
    elif args.root is not None:
        root = args.root.resolve()
    else:
        root = Path(__file__).resolve().parents[3]

    validator = Validator(root)
    validator.validate()
    return validator.report(args.quiet)


if __name__ == "__main__":
    raise SystemExit(main())
