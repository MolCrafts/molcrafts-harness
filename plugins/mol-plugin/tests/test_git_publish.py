"""
Structural guards for PR-first git publish (plugins/mol/rules/git-publish.md).

Locks:
- shared rule file exists with remotes + iron laws
- /mol:push is origin-only and refuses upstream branch push
- /mol:pr is fork → upstream and requires /mol:push first
- /mol:release and /mol-plugin:release wait for green checks, no red merge
- neither release skill instructs a bare git push upstream for branches

Stdlib only. Run with:

    python plugins/mol-plugin/tests/test_git_publish.py
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MOL_SKILLS = REPO_ROOT / "plugins" / "mol" / "skills"
MOL_PLUGIN_SKILLS = REPO_ROOT / "plugins" / "mol-plugin" / "skills"
RULES = REPO_ROOT / "plugins" / "mol" / "rules"

_FORBID_MARKERS = (
    "never",
    "forbid",
    "do not",
    "don't",
    "must not",
    "not ",
    "refuse",
    "no direct",
    "instead",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _lines_with(text: str, needle: str) -> list[str]:
    return [ln for ln in text.splitlines() if needle in ln]


def _instructs_cmd(text: str, cmd: str) -> list[str]:
    """Lines that contain cmd without a forbid/negative marker on the same line."""
    bad: list[str] = []
    for ln in _lines_with(text, cmd):
        lower = ln.lower()
        if any(m in lower for m in _FORBID_MARKERS):
            continue
        # fenced example that is only the forbidden form without "never" nearby
        # is still a positive instruction if it looks like a shell recipe.
        bad.append(ln.strip())
    return bad


class GitPublishContractTests(unittest.TestCase):
    def test_git_publish_rule_exists(self) -> None:
        path = RULES / "git-publish.md"
        self.assertTrue(path.is_file(), "plugins/mol/rules/git-publish.md missing")
        text = _read(path)
        for needle in (
            "origin",
            "upstream",
            "pre-commit ≡ CI",
            "PR-first",
            "/mol:push",
            "/mol:pr",
            "green",
        ):
            self.assertIn(needle, text, f"git-publish.md must mention {needle!r}")

    def test_mol_push_origin_only(self) -> None:
        text = _read(MOL_SKILLS / "push" / "SKILL.md")
        self.assertIn("git-publish.md", text)
        self.assertIn("origin", text)
        self.assertIn("git push -u origin", text)
        self.assertEqual(
            _instructs_cmd(text, "git push upstream"),
            [],
            "push must not instruct bare git push upstream",
        )
        self.assertRegex(
            text,
            r"[Nn]ever.*upstream|upstream.*[Nn]ever",
            "push must forbid branch pushes to upstream",
        )

    def test_mol_pr_fork_to_upstream(self) -> None:
        text = _read(MOL_SKILLS / "pr" / "SKILL.md")
        self.assertIn("git-publish.md", text)
        self.assertIn("/mol:push", text)
        self.assertIn("upstream", text)
        self.assertIn("origin", text)
        self.assertTrue(
            any("never" in ln.lower() and "git push upstream" in ln for ln in text.splitlines()),
            "pr must forbid substituting push upstream for a PR",
        )

    def test_mol_release_pr_first_green_merge(self) -> None:
        text = _read(MOL_SKILLS / "release" / "SKILL.md")
        self.assertIn("git-publish.md", text)
        self.assertIn("/mol:push", text)
        self.assertIn("/mol:pr", text)
        self.assertIn("gh pr checks", text)
        self.assertIn("/mol:tag", text)
        self.assertIn("green", text.lower())
        self.assertEqual(
            _instructs_cmd(text, "git push upstream"),
            [],
            "mol:release must not instruct branch push to upstream",
        )
        # Unconditional --admin on the merge recipe is forbidden
        for ln in text.splitlines():
            if "gh pr merge" not in ln:
                continue
            if "--admin" in ln and "green" not in ln.lower() and "unless" not in ln.lower():
                self.fail(f"unconditional --admin merge: {ln!r}")

    def test_mol_plugin_release_mirrors_chain(self) -> None:
        text = _read(MOL_PLUGIN_SKILLS / "release" / "SKILL.md")
        self.assertIn("git-publish.md", text)
        for needle in (
            "/mol:push",
            "/mol:pr",
            "gh pr checks",
            "/mol:tag",
            "origin",
            "upstream",
            "pre-commit",
            "PR-first",
            "green",
            '/mol:commit "release: v',
        ):
            self.assertIn(needle, text, f"mol-plugin:release must mention {needle!r}")
        self.assertNotIn(
            'git commit -m "release:',
            text,
            "must not inline git commit",
        )
        self.assertEqual(
            _instructs_cmd(text, "git push upstream"),
            [],
            "mol-plugin:release must not instruct branch push to upstream",
        )

    def test_check_audits_git_publish(self) -> None:
        text = _read(MOL_PLUGIN_SKILLS / "check" / "SKILL.md")
        self.assertIn("git-publish.md", text)
        self.assertIn("Git publish", text)
        self.assertIn("origin", text)
        self.assertIn("upstream", text)

    def test_codex_adapter_preserves_pr_first(self) -> None:
        text = _read(MOL_PLUGIN_SKILLS / "CODEX.md")
        self.assertIn("git-publish.md", text)
        self.assertIn("origin", text)
        self.assertIn("upstream", text)

    def test_readme_documents_pr_first(self) -> None:
        text = _read(REPO_ROOT / "plugins" / "mol-plugin" / "README.md")
        self.assertIn("git-publish.md", text)
        self.assertIn("origin", text)
        self.assertIn("upstream", text)
        self.assertRegex(text, r"push.*origin|origin.*fork", re.I)


if __name__ == "__main__":
    unittest.main()
