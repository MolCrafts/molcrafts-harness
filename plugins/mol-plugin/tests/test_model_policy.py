"""
Structural-validation suite for the model policy (conversation modes +
agent model tiers) introduced with plugins/mol/rules/model-policy.md.

Guards:
- every shipped mol agent pins an explicit tier (no `model: inherit`)
- tier assignments match the canonical opus/sonnet sets (a new agent
  requires a deliberate update here — that is the point)
- the `implementer` producer-write agent exists with the right contract
- the mode/tier wiring in impl / fix / impl-all / release SKILL.md
- count-drift: hardcoded agent counts live only in the two json
  descriptions, never in READMEs or agent-design.md

Stdlib only: unittest + pathlib + re. Run with:

    python plugins/mol-plugin/tests/test_model_policy.py
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

# tests/ -> mol-plugin/ -> plugins/ -> <repo root>
REPO_ROOT = Path(__file__).resolve().parents[3]

AGENTS_DIR = REPO_ROOT / "plugins" / "mol" / "agents"
SKILLS_DIR = REPO_ROOT / "plugins" / "mol" / "skills"
RULES_DIR = REPO_ROOT / "plugins" / "mol" / "rules"

OPUS_AGENTS = {
    "architect",
    "scientist",
    "compute-scientist",
    "debugger",
    "security-reviewer",
    "optimizer",
    "pm",
    "librarian",
    "undergrad",
    "user",
    "web-design",
    "spec-writer",
    "tester",
    "documenter",
    "implementer",
}

SONNET_AGENTS = {
    "ci-guard",
    "playwright-evaluator",
    "reviewer",
    "janitor",
}


def _split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Return (frontmatter_dict, body). Empty dict if no frontmatter."""
    if not text.startswith("---"):
        return {}, text
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


class ModelPolicyTests(unittest.TestCase):
    """Structural tests for conversation modes and agent model tiers."""

    def test_every_agent_pins_an_explicit_tier(self) -> None:
        agent_files = sorted(AGENTS_DIR.glob("*.md"))
        self.assertTrue(agent_files, f"no agents found under {AGENTS_DIR}")
        for path in agent_files:
            fm, _ = _split_frontmatter(_read(path))
            model = fm.get("model", "")
            self.assertIn(
                model,
                {"opus", "sonnet", "haiku"},
                f"{path.name}: model must be an explicit tier "
                f"(opus | sonnet | haiku), not {model!r} — "
                f"`inherit` is banned under plugins/mol/agents/ "
                f"per rules/model-policy.md.",
            )

    def test_tier_sets_match_canonical_assignment(self) -> None:
        actual_opus: set[str] = set()
        actual_sonnet: set[str] = set()
        for path in AGENTS_DIR.glob("*.md"):
            fm, _ = _split_frontmatter(_read(path))
            tier = fm.get("model", "")
            if tier == "opus":
                actual_opus.add(path.stem)
            elif tier == "sonnet":
                actual_sonnet.add(path.stem)
        self.assertEqual(
            actual_opus,
            OPUS_AGENTS,
            "opus tier drifted from the canonical set in "
            "rules/model-policy.md — a new agent needs a deliberate "
            "entry both there and here.",
        )
        self.assertEqual(
            actual_sonnet,
            SONNET_AGENTS,
            "sonnet tier drifted from the canonical set in "
            "rules/model-policy.md.",
        )

    def test_implementer_agent_contract(self) -> None:
        path = AGENTS_DIR / "implementer.md"
        self.assertTrue(path.exists(), f"{path} must exist.")
        text = _read(path)
        fm, body = _split_frontmatter(text)

        self.assertEqual(
            fm.get("tools", "").replace(" ", ""),
            "Read,Grep,Glob,Bash,Write,Edit",
            "implementer is producer-write: exactly "
            "Read, Grep, Glob, Bash, Write, Edit.",
        )
        self.assertEqual(fm.get("model"), "opus", "implementer runs on opus.")
        self.assertIn(
            "RED",
            body,
            "implementer must state the RED-test precondition.",
        )
        self.assertIn(
            "Never edit test files",
            body,
            "implementer must forbid editing test files (tester owns tests).",
        )
        self.assertIn(
            "no reverts",
            body.lower().replace("no commits, no reverts", "no reverts"),
            "implementer must state it never reverts (caller owns revert).",
        )

    def test_model_policy_rules_file(self) -> None:
        path = RULES_DIR / "model-policy.md"
        self.assertTrue(path.exists(), f"{path} must exist.")
        text = _read(path)
        for token in ("Advisor", "Orchestration", "opus", "sonnet", "haiku"):
            self.assertIn(
                token, text, f"model-policy.md must mention {token!r}."
            )
        self.assertIn(
            "MUST NOT author production",
            text,
            "model-policy.md must pin the main-loop rule "
            "(never authors production source).",
        )

    def test_skill_wiring(self) -> None:
        impl = _read(SKILLS_DIR / "impl" / "SKILL.md")
        self.assertIn(
            "`implementer`",
            impl,
            "impl/SKILL.md § 2b must delegate GREEN to implementer.",
        )

        fix = _read(SKILLS_DIR / "fix" / "SKILL.md")
        self.assertIn(
            "`implementer`",
            fix,
            "fix/SKILL.md Step 3 must delegate the patch to implementer.",
        )
        self.assertIn(
            "do **not** re-delegate",
            fix,
            "fix/SKILL.md Step 2 must consume an existing debugger report "
            "instead of re-running diagnosis.",
        )

        impl_all = _read(SKILLS_DIR / "impl-all" / "SKILL.md")
        self.assertIn(
            "model: haiku",
            impl_all,
            "impl-all/SKILL.md § 2b must dispatch the evaluator with "
            "an explicit `model: haiku`.",
        )
        self.assertNotIn(
            "/mol:commit -m",
            impl_all,
            "impl-all must not invoke /mol:commit — /mol:impl owns the "
            "per-spec checkpoint (double-commit regression guard).",
        )
        self.assertNotIn(
            "then `/mol:commit`",
            impl_all,
            "impl-all must not chain a /mol:commit invocation after specs.",
        )

        release = _read(
            REPO_ROOT
            / "plugins"
            / "mol-plugin"
            / "skills"
            / "release"
            / "SKILL.md"
        )
        self.assertIn(
            '/mol:commit "release: v',
            release,
            "release § 7 must route the commit through /mol:commit.",
        )
        self.assertNotIn(
            'git commit -m "release:',
            release,
            "release must not run an inline git commit — that bypasses "
            "the unified /mol:commit path.",
        )

    def test_no_hardcoded_agent_counts_outside_json(self) -> None:
        # Counts are sanctioned only in plugin.json / marketplace.json
        # descriptions; prose files must not carry them (drift prevention).
        pattern = re.compile(r"\b\d+ (?:single-axis )?agents\b")
        for rel in (
            "README.md",
            "plugins/mol/README.md",
            "plugins/mol/rules/agent-design.md",
        ):
            text = _read(REPO_ROOT / rel)
            match = pattern.search(text)
            self.assertIsNone(
                match,
                f"{rel} hardcodes an agent count ({match.group(0) if match else ''!r}) — "
                f"counts live only in plugin.json / marketplace.json.",
            )


if __name__ == "__main__":
    unittest.main()
