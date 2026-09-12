from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = ROOT.parent


class DevReqContractTests(unittest.TestCase):
    def test_negative_activation_boundary_is_semantic_not_phrase_dependent(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = re.match(r"\A---\n(?P<body>.*?)\n---\n", skill, re.DOTALL)
        self.assertIsNotNone(frontmatter)
        description = re.search(r'(?m)^description:\s*"?(.*?)"?\s*$', frontmatter.group("body"))
        self.assertIsNotNone(description)
        for excluded in ("一般代码理解", "调试", "重构", "实现审查", "代码评审", "架构分析"):
            self.assertIn(excluded, description.group(1))

    def test_negative_behavior_case_prevents_requirement_misrouting(self) -> None:
        document = json.loads((ROOT / "tests" / "behavior-cases.json").read_text(encoding="utf-8"))
        cases = {case["id"]: case for case in document["cases"]}
        case = cases["negative-general-code-debugging"]
        self.assertEqual(case["mode"], "negative-trigger")
        self.assertIn("dev-req is not selected solely for debugging", case["expected_invariants"])
        self.assertIn("formal REQ RULE or AC identifiers", case["forbidden_outcomes"])

    def test_markdown_links_resolve_inside_suite(self) -> None:
        for path in ROOT.rglob("*.md"):
            for target in re.findall(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)", path.read_text(encoding="utf-8")):
                if re.match(r"^[a-z][a-z0-9+.-]*:", target):
                    continue
                resolved = (path.parent / target).resolve()
                self.assertTrue(resolved.is_relative_to(SUITE_ROOT.resolve()), f"link escapes suite: {path} -> {target}")
                self.assertTrue(resolved.exists(), f"broken link: {path} -> {target}")


if __name__ == "__main__":
    unittest.main()
