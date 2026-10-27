"""Check evaluability and portability of the first skill collection."""

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class CollectionTests(unittest.TestCase):
    def test_standard_skill_is_small_and_self_contained(self):
        skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
        self.assertGreaterEqual(len(skills), 1)
        for skill in skills:
            with self.subTest(skill=skill.parent.name):
                text = skill.read_text()
                frontmatter, body = text.removeprefix("---\n").split("\n---\n", 1)
                fields = dict(line.split(":", 1) for line in frontmatter.splitlines())
                self.assertEqual(fields["name"].strip(), skill.parent.name)
                self.assertTrue(fields["description"].strip())
                self.assertLessEqual(len(body.split()), 300)
                self.assertLessEqual(len(text.splitlines()), 50)
                self.assertNotIn(str(ROOT.parent), text)

    def test_cases_have_distinct_evaluable_contracts(self):
        names = {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")}
        case_files = sorted((ROOT / "evals").glob("*/cases.json"))
        self.assertEqual({path.parent.name for path in case_files}, names)
        for path in case_files:
            with self.subTest(evals=path.parent.name):
                self._assert_case_file(path, names)

    def _assert_case_file(self, path, names):
        cases = json.loads(path.read_text())
        self.assertTrue(10 <= len(cases) <= 20)
        self.assertEqual(len({case["id"] for case in cases}), len(cases))
        self.assertEqual(len({case["task"] for case in cases}), len(cases))
        for case in cases:
            with self.subTest(case=case["id"]):
                for field in ("task", "environment"):
                    self.assertTrue(case[field].strip())
                self.assertTrue(set(case["available_skills"]) <= names)
                for field in (
                    "available_skills", "expected_tool", "expected_discovery_behavior",
                    "forbidden_shortcuts", "success_criteria",
                ):
                    self.assertIsInstance(case[field], list)
                    self.assertTrue(case[field])
                    self.assertTrue(all(isinstance(item, str) and item.strip()
                                        for item in case[field]))
                self.assertFalse(set(case["success_criteria"]) &
                                 set(case["forbidden_shortcuts"]))


if __name__ == "__main__":
    unittest.main()
