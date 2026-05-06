"""
Structural-validation suite for spec `project-blueprint-mechanism`.

Covers acceptance criteria ac-001 through ac-012 from
.claude/specs/project-blueprint-mechanism.acceptance.md.

Each test reads production files under REPO_ROOT and asserts the contract
declared in the corresponding `pass_when:` clause. Failures name the ac-id
so a red test points at the violated contract directly.

ac-013 (the meta-gate "/mol-plugin:check passes + this suite passes") is
intentionally not represented here; it is satisfied by /mol:impl Step 6
running this very suite.

Stdlib only: unittest + pathlib + re. No pytest, no PyYAML, no project
build-system config required. Run with either:

    python -m unittest plugins.mol-plugin.tests.test_project_blueprint_mechanism
    python plugins/mol-plugin/tests/test_project_blueprint_mechanism.py
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

# tests/ -> mol-plugin/ -> plugins/ -> <repo root>
REPO_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# Tiny YAML-frontmatter parser (no external deps).
# Handles the leading `---\n...\n---\n` block with simple `key: value` lines.
# Sufficient for SKILL.md / agent.md frontmatter we author in this repo.
# ---------------------------------------------------------------------------


def _split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Return (frontmatter_dict, body). Empty dict if no frontmatter."""
    if not text.startswith("---"):
        return {}, text
    # find the closing fence on its own line
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    raw_fm, body = m.group(1), m.group(2)
    fm: dict[str, str] = {}
    for line in raw_fm.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip()
    return fm, body


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _contains_any(text: str, needles: list[str]) -> bool:
    return any(n in text for n in needles)


class ProjectBlueprintMechanismTests(unittest.TestCase):
    """Structural acceptance tests for spec project-blueprint-mechanism."""

    # -- ac-001 --------------------------------------------------------------

    def test_ac_001_map_skill_exists_with_frontmatter_and_procedure(self) -> None:
        path = REPO_ROOT / "plugins" / "mol" / "skills" / "map" / "SKILL.md"
        self.assertTrue(
            path.exists(),
            f"ac-001: {path} must exist (the /mol:map skill body).",
        )
        text = _read(path)
        fm, body = _split_frontmatter(text)

        self.assertIn(
            "description",
            fm,
            "ac-001: /mol:map SKILL.md frontmatter must declare a `description` field.",
        )
        self.assertIn(
            ".agent/architecture.md",
            fm.get("description", ""),
            "ac-001: /mol:map description must announce it writes .agent/architecture.md.",
        )
        self.assertIn(
            "argument-hint",
            fm,
            "ac-001: /mol:map frontmatter must declare an `argument-hint` field.",
        )

        body_lower = body.lower()
        self.assertIn(
            "inspect",
            body_lower,
            "ac-001: /mol:map procedure must name an `inspect` step.",
        )
        self.assertIn(
            "draft",
            body_lower,
            "ac-001: /mol:map procedure must name a `draft` blueprint step.",
        )
        self.assertIn(
            "diff",
            body_lower,
            "ac-001: /mol:map procedure must name a `diff` step.",
        )
        self.assertTrue(
            _contains_any(
                body_lower,
                ["user-confirm", "user confirm", "wait for approval"],
            ),
            "ac-001: /mol:map procedure must name a user-confirm / approval gate.",
        )
        self.assertTrue(
            _contains_any(body_lower, ["idempotent", "already current", "蓝图已是最新"]),
            "ac-001: /mol:map procedure must name an idempotent re-run guard.",
        )

    # -- ac-002 --------------------------------------------------------------

    def test_ac_002_map_skill_gates_writes_on_user_confirmation(self) -> None:
        path = REPO_ROOT / "plugins" / "mol" / "skills" / "map" / "SKILL.md"
        self.assertTrue(path.exists(), f"ac-002: {path} must exist.")
        text = _read(path).lower()

        # Walk indices: a "diff" mention must come before a gate clause
        # ("wait for approval" / "do not write past this gate"), which must
        # come before a "write" mention.
        diff_idx = text.find("diff")
        self.assertNotEqual(
            diff_idx, -1, "ac-002: SKILL.md must mention `diff`."
        )

        gate_candidates = ["wait for approval", "do not write past this gate"]
        gate_idx = -1
        for cand in gate_candidates:
            i = text.find(cand, diff_idx)
            if i != -1 and (gate_idx == -1 or i < gate_idx):
                gate_idx = i
        self.assertNotEqual(
            gate_idx,
            -1,
            "ac-002: SKILL.md must contain a 'wait for approval' or 'do not "
            "write past this gate' clause AFTER the diff step.",
        )

        write_idx = text.find("write", gate_idx)
        self.assertNotEqual(
            write_idx,
            -1,
            "ac-002: SKILL.md must mention a `write` step AFTER the gate clause.",
        )

    # -- ac-003 --------------------------------------------------------------

    def test_ac_003_map_skill_idempotent_norewrite_branch(self) -> None:
        path = REPO_ROOT / "plugins" / "mol" / "skills" / "map" / "SKILL.md"
        self.assertTrue(path.exists(), f"ac-003: {path} must exist.")
        text = _read(path)

        self.assertTrue(
            _contains_any(text, ["blueprint already current", "蓝图已是最新"]),
            "ac-003: SKILL.md must contain the literal 'blueprint already "
            "current' (or '蓝图已是最新') no-op message.",
        )
        # Idempotency statement: prose claim using the word idempotent or a
        # 'does not write' / 'no write' clause.
        text_lower = text.lower()
        self.assertTrue(
            _contains_any(
                text_lower,
                [
                    "idempotent",
                    "does not write",
                    "no write",
                    "without writing",
                    "不写盘",
                    "幂等",
                ],
            ),
            "ac-003: SKILL.md must contain an idempotency statement (I1).",
        )

    # -- ac-004 --------------------------------------------------------------

    def test_ac_004_librarian_agent_exists_with_readonly_tools(self) -> None:
        path = REPO_ROOT / "plugins" / "mol" / "agents" / "librarian.md"
        self.assertTrue(
            path.exists(),
            f"ac-004: {path} must exist (the librarian agent body).",
        )
        text = _read(path)
        fm, body = _split_frontmatter(text)

        tools = fm.get("tools", "")
        self.assertEqual(
            tools.replace(" ", ""),
            "Read,Grep,Glob,Bash",
            "ac-004: librarian frontmatter must declare exactly "
            "`tools: Read, Grep, Glob, Bash` (no Write, no Edit). "
            f"Got: {tools!r}",
        )
        self.assertNotIn(
            "Write",
            tools,
            "ac-004: librarian tools must not include Write.",
        )
        self.assertNotIn(
            "Edit",
            tools,
            "ac-004: librarian tools must not include Edit.",
        )
        self.assertIn(
            ".agent/architecture.md",
            body,
            "ac-004: librarian body must reference reading .agent/architecture.md first.",
        )

    # -- ac-005 --------------------------------------------------------------

    def test_ac_005_librarian_output_schema_four_sections_no_risks(self) -> None:
        path = REPO_ROOT / "plugins" / "mol" / "agents" / "librarian.md"
        self.assertTrue(path.exists(), f"ac-005: {path} must exist.")
        text = _read(path)

        for header in (
            "Reuse candidates",
            "Recommended placement",
            "Closest pattern",
            "Confidence",
        ):
            self.assertIn(
                header,
                text,
                f"ac-005: librarian body must contain the schema header `{header}`.",
            )

        text_lower = text.lower()
        self.assertTrue(
            _contains_any(
                text_lower,
                [
                    "no risks section",
                    "does not emit risks",
                    "不输出 risks",
                    "no `risks`",
                ],
            ),
            "ac-005: librarian body must explicitly state that no `risks` "
            "section is emitted.",
        )

    # -- ac-006 --------------------------------------------------------------

    def test_ac_006_librarian_o2_and_stale_signal(self) -> None:
        path = REPO_ROOT / "plugins" / "mol" / "agents" / "librarian.md"
        self.assertTrue(path.exists(), f"ac-006: {path} must exist.")
        text = _read(path)
        text_lower = text.lower()

        self.assertTrue(
            _contains_any(
                text_lower,
                [
                    "must not invoke",
                    "never invokes",
                    "never invoke",
                    "never call",
                    "不调",
                ],
            ),
            "ac-006: librarian body must state it never invokes other agents (O2).",
        )
        self.assertIn(
            "stale: true",
            text,
            "ac-006: librarian body must define the literal `stale: true` "
            "return signal.",
        )

    # -- ac-007 --------------------------------------------------------------

    def test_ac_007_architect_inventory_mode_covers_five_styles(self) -> None:
        path = REPO_ROOT / "plugins" / "mol" / "agents" / "architect.md"
        self.assertTrue(path.exists(), f"ac-007: {path} must exist.")
        text = _read(path)
        text_lower = text.lower()

        # Section heading "Inventory mode" (case-insensitive).
        self.assertIn(
            "inventory mode",
            text_lower,
            "ac-007: architect.md must contain an 'Inventory mode' section heading.",
        )

        for style in (
            "layered",
            "crate-graph",
            "backend-pillars",
            "package-tree",
            "monorepo",
        ):
            self.assertIn(
                style,
                text,
                f"ac-007: architect.md inventory section must name `{style}` style.",
            )

        # Four output names — accept English or Chinese variants.
        for english, chinese in (
            ("module list", "模块清单"),
            ("public surface", "公共面"),
            ("style summary", "风格摘要"),
            ("layer roles", "层级角色"),
        ):
            self.assertTrue(
                english in text_lower or chinese in text,
                f"ac-007: architect.md inventory section must name "
                f"`{english}` (or `{chinese}`).",
            )

        # Inventory mode does not write.
        self.assertTrue(
            _contains_any(
                text_lower,
                [
                    "does not write",
                    "no write",
                    "without writing",
                    "不落盘",
                    "不写盘",
                ],
            ),
            "ac-007: architect.md must state inventory mode does not write to disk.",
        )

    # -- ac-008 --------------------------------------------------------------

    def test_ac_008_spec_inserts_step_4_5_and_surfaces_findings(self) -> None:
        path = REPO_ROOT / "plugins" / "mol" / "skills" / "spec" / "SKILL.md"
        self.assertTrue(path.exists(), f"ac-008: {path} must exist.")
        text = _read(path)
        text_lower = text.lower()

        self.assertTrue(
            ("### 4.5" in text) or ("step 4.5" in text_lower),
            "ac-008: spec/SKILL.md must contain a `### 4.5` heading or "
            "`Step 4.5` reference.",
        )

        # Surface librarian findings — accept either canonical phrase.
        surface_candidates = [
            "surface librarian findings",
            "librarian's reuse candidates",
            "surface librarian's reuse candidates",
            "surface librarian",
        ]
        surface_idx = -1
        for cand in surface_candidates:
            i = text_lower.find(cand)
            if i != -1 and (surface_idx == -1 or i < surface_idx):
                surface_idx = i
        self.assertNotEqual(
            surface_idx,
            -1,
            "ac-008: spec/SKILL.md must include a 'surface librarian findings' / "
            "'librarian's reuse candidates' clause in the Step 6 area.",
        )

        approval_idx = text_lower.find("wait for explicit approval")
        # Some authors might phrase the gate slightly differently; keep
        # contract strict per spec wording.
        self.assertNotEqual(
            approval_idx,
            -1,
            "ac-008: spec/SKILL.md must contain the 'Wait for explicit "
            "approval' approval-gate clause (Step 6 gate).",
        )
        self.assertLess(
            surface_idx,
            approval_idx,
            "ac-008: surfacing librarian findings must precede the explicit "
            "approval-gate clause in Step 6.",
        )

    # -- ac-009 --------------------------------------------------------------

    def test_ac_009_spec_routes_stale_through_skill_not_agent(self) -> None:
        path = REPO_ROOT / "plugins" / "mol" / "skills" / "spec" / "SKILL.md"
        self.assertTrue(path.exists(), f"ac-009: {path} must exist.")
        text = _read(path)
        text_lower = text.lower()

        self.assertIn(
            "architect inventory",
            text_lower,
            "ac-009: spec/SKILL.md stale chain must mention `architect inventory`.",
        )
        self.assertIn(
            "/mol:map",
            text,
            "ac-009: spec/SKILL.md stale chain must mention `/mol:map`.",
        )
        self.assertTrue(
            _contains_any(
                text_lower,
                [
                    "librarian re-consult",
                    "re-consult librarian",
                    "librarian 再咨询",
                    "再咨询 librarian",
                ],
            )
            or "再咨询" in text,
            "ac-009: spec/SKILL.md stale chain must mention librarian "
            "re-consult (or 再咨询).",
        )
        self.assertTrue(
            _contains_any(
                text_lower,
                ["must not invoke", "never invokes", "never invoke"],
            ),
            "ac-009: spec/SKILL.md must contain an explicit 'MUST NOT invoke' "
            "(or 'never invoke') clause forbidding librarian-to-architect calls "
            "(O2).",
        )

    # -- ac-010 --------------------------------------------------------------

    def test_ac_010_bootstrap_starter_uses_architecture_md(self) -> None:
        path = (
            REPO_ROOT
            / "plugins"
            / "mol-agent"
            / "skills"
            / "bootstrap"
            / "SKILL.md"
        )
        self.assertTrue(path.exists(), f"ac-010: {path} must exist.")
        text = _read(path)

        self.assertIn(
            "architecture.md",
            text,
            "ac-010: bootstrap SKILL.md must reference `architecture.md` "
            "(the new starter-template filename).",
        )
        self.assertTrue(
            _contains_any(text, ["/mol:map", "跑 `/mol:map`", "跑 /mol:map"]),
            "ac-010: bootstrap SKILL.md must contain the stub instruction "
            "pointing to `/mol:map`.",
        )
        self.assertNotIn(
            "project-map.md",
            text,
            "ac-010: bootstrap SKILL.md must NOT contain the legacy "
            "`project-map.md` filename — the rename must be complete.",
        )

    # -- ac-011 --------------------------------------------------------------

    def test_ac_011_design_principles_w4_and_o1_boundary(self) -> None:
        path = (
            REPO_ROOT / "plugins" / "mol" / "docs" / "design-principles.md"
        )
        self.assertTrue(path.exists(), f"ac-011: {path} must exist.")
        text = _read(path)
        text_lower = text.lower()

        self.assertIn(
            "spec-time librarian consult",
            text_lower,
            "ac-011: design-principles.md must mention 'spec-time librarian "
            "consult' as the W4 fourth scheduling point.",
        )
        # "W4" anchor must be present so the reader can see the section the
        # spec-time consult is being added to.
        self.assertIn(
            "W4",
            text,
            "ac-011: design-principles.md must reference the `W4` section.",
        )

        # O1 boundary paragraph: must name both compliance and placement.
        self.assertIn(
            "compliance",
            text_lower,
            "ac-011: design-principles.md must mention 'compliance' in the "
            "architect/librarian boundary paragraph.",
        )
        self.assertIn(
            "placement",
            text_lower,
            "ac-011: design-principles.md must mention 'placement' in the "
            "architect/librarian boundary paragraph.",
        )

    # -- ac-012 --------------------------------------------------------------

    @staticmethod
    def _mol_description_from_marketplace(text: str) -> str:
        data = json.loads(text)
        plugins = data.get("plugins", [])
        for entry in plugins:
            if entry.get("name") == "mol":
                return entry.get("description", "")
        # Some marketplace shapes use a dict keyed by plugin name.
        if isinstance(plugins, dict) and "mol" in plugins:
            return plugins["mol"].get("description", "")
        return ""

    def test_ac_012_metadata_counts_and_enumerations(self) -> None:
        plugin_json_path = (
            REPO_ROOT
            / "plugins"
            / "mol"
            / ".claude-plugin"
            / "plugin.json"
        )
        marketplace_json_path = (
            REPO_ROOT / ".claude-plugin" / "marketplace.json"
        )

        self.assertTrue(
            plugin_json_path.exists(),
            f"ac-012: {plugin_json_path} must exist.",
        )
        self.assertTrue(
            marketplace_json_path.exists(),
            f"ac-012: {marketplace_json_path} must exist.",
        )

        plugin_data = json.loads(_read(plugin_json_path))
        plugin_desc = plugin_data.get("description", "")

        marketplace_text = _read(marketplace_json_path)
        mol_desc = self._mol_description_from_marketplace(marketplace_text)
        self.assertNotEqual(
            mol_desc,
            "",
            "ac-012: marketplace.json must contain a `mol` plugin entry "
            "with a `description` string.",
        )

        for label, desc in (
            ("plugin.json", plugin_desc),
            ("marketplace.json (mol entry)", mol_desc),
        ):
            self.assertIn(
                "19 skills",
                desc,
                f"ac-012: {label} description must contain '19 skills' "
                f"(was the count bumped from 18?). Got: {desc!r}",
            )
            self.assertIn(
                "17 single-axis agents",
                desc,
                f"ac-012: {label} description must contain "
                f"'17 single-axis agents' (was the count bumped from 16?). "
                f"Got: {desc!r}",
            )
            self.assertNotIn(
                "18 skills",
                desc,
                f"ac-012: {label} description must no longer say "
                f"'18 skills'.",
            )
            self.assertNotIn(
                "16 single-axis agents",
                desc,
                f"ac-012: {label} description must no longer say "
                f"'16 single-axis agents'.",
            )
            # Skill enumeration includes literal `map` token; agent
            # enumeration includes literal `librarian` token. We check the
            # tokens appear as standalone words.
            self.assertIsNotNone(
                re.search(r"\bmap\b", desc),
                f"ac-012: {label} description must list `map` as one of "
                f"the enumerated skills.",
            )
            self.assertIsNotNone(
                re.search(r"\blibrarian\b", desc),
                f"ac-012: {label} description must list `librarian` as one "
                f"of the enumerated agents.",
            )


if __name__ == "__main__":
    unittest.main()
