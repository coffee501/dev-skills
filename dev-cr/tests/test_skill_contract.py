from __future__ import annotations

import importlib.util
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT.parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DevCrContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.manifest = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        cls.validator = load_module("dev_cr_validator", ROOT / "scripts" / "validate_review_artifact.py")

    def test_frontmatter_and_policy(self) -> None:
        match = re.match(r"\A---\n(?P<body>.*?)\n---\n", self.skill, re.DOTALL)
        self.assertIsNotNone(match)
        self.assertEqual(sorted(re.findall(r"(?m)^([A-Za-z0-9_-]+):", match.group("body"))), ["description", "name"])
        self.assertIn("name: dev-cr", match.group("body"))
        for value in ("实际实现及变更", "正确、完整地落实", "实现质量与工程风险"):
            self.assertIn(value, match.group("body"))
        self.assertIn("$dev-cr", self.manifest)
        self.assertIn('display_name: "CR 实现审查"', self.manifest)
        self.assertIn("实际实现的正确性、完整性", self.manifest)
        self.assertRegex(self.manifest, r"allow_implicit_invocation:\s*true")

    def test_required_contracts_and_links(self) -> None:
        for name in ("review-model.md", "review-checklist.md", "re-review.md", "output-contracts.md"):
            self.assertTrue((ROOT / "references" / name).is_file())
        for value in ("REV Approved", "共享协议不可用", "不自动调用其他 Skill", "复杂度与拆分治理", "validate_review_artifact.py"):
            self.assertIn(value, self.skill)
        pattern = re.compile(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)")
        for path in ROOT.rglob("*.md"):
            for target in pattern.findall(path.read_text(encoding="utf-8")):
                resolved = (path.parent / target).resolve()
                self.assertTrue(resolved.exists(), f"broken link: {path} -> {target}")
                self.assertTrue(resolved.is_relative_to(ROOT) or resolved.is_relative_to(SUITE / "dev-lc"))

    def test_behavior_cases(self) -> None:
        document = json.loads((ROOT / "tests" / "behavior-cases.json").read_text(encoding="utf-8"))
        self.assertEqual(document["schema_version"], 1)
        self.assertGreaterEqual(len(document["cases"]), 12)
        case_ids = {case["id"] for case in document["cases"]}
        self.assertTrue({
            "planned-implementation-omitted", "implementation-deviates-from-design",
            "speculative-abstraction", "mechanical-implementation-fragmentation",
        }.issubset(case_ids))
        for case in document["cases"]:
            self.assertGreaterEqual(len(case["expected_invariants"]), 2)
            self.assertGreaterEqual(len(case["forbidden_outcomes"]), 1)

    def test_validator_cross_field_rules(self) -> None:
        review = {
            "protocol_version": "DEV-SUITE-7.0", "id": "REV-001", "type": "code-review",
            "change": "CHG-001", "version": 1, "status": "Approved", "owner": "reviewer",
            "sources": ["IMP-001@v1"], "applies_to": {"base": "a", "head": "b"}, "risks": [],
            "evidence": ["diff://a..b"], "updated_at": "2026-08-14T12:00:00+08:00",
            "review_scope": {"repository": "repo"}, "base": "a", "head": "b", "imp_refs": ["IMP-001@v1"],
            "build_refs": ["BUILD-001@v1"], "requirement_refs": ["AC-001@v1"], "design_refs": ["DDEC-001@v1"],
            "test_refs": ["TC-001@v1"], "files_reviewed": ["service.py"], "generated_or_external": [],
            "findings": [], "required_actions": [], "verification_requirements": ["targeted regression"],
            "limitations": [], "handoff_refs": ["HOF-001@v1"],
        }
        self.assertEqual(self.validator.validate_artifact(review), [])
        finding = {"id": "F-1", "severity": "P1", "status": "Open"}
        errors = self.validator.validate_artifact(dict(review, findings=[finding]))
        self.assertTrue(any("open P0/P1" in error for error in errors))
        errors = self.validator.validate_artifact(dict(review, status="ChangesRequested", findings=[]))
        self.assertTrue(any("requires an open P0/P1" in error for error in errors))

    def test_8_0_approved_review_requires_proven_independence(self) -> None:
        review = {
            "protocol_version": "DEV-SUITE-8.0", "id": "REV-800", "type": "code-review",
            "change": "CHG-800", "version": 1, "status": "Approved", "owner": "reviewer-agent",
            "sources": ["IMP-800@v1"], "applies_to": {"base": "a", "head": "b"}, "risks": [],
            "evidence": ["diff://a..b"], "updated_at": "2026-09-12T12:00:00+08:00",
            "review_scope": {"repository": "repo"}, "base": "a", "head": "b", "imp_refs": ["IMP-800@v1"],
            "build_refs": ["BUILD-800@v1"], "requirement_refs": ["AC-800@v1"], "design_refs": ["DDEC-800@v1"],
            "test_refs": ["TC-800@v1"], "files_reviewed": ["service.py"], "generated_or_external": [],
            "findings": [], "required_actions": [], "verification_requirements": ["targeted regression"],
            "limitations": [], "handoff_refs": ["HOF-800@v1"],
            "reviewer": {
                "identity": "reviewer-agent", "role": "implementation-reviewer", "execution_context": "review-run-800",
            },
            "implementation_actors": [{
                "identity": "implementation-agent", "role": "implementation-owner", "execution_context": "implementation-run-800",
            }],
            "independence": {
                "status": "Independent", "basis": ["agent-run://review-run-800"], "compensating_controls": [],
            },
        }
        self.assertEqual(self.validator.validate_artifact(review), [])

        same_reviewer = dict(review, implementation_actors=[{
            "identity": "reviewer-agent", "role": "implementation-owner", "execution_context": "implementation-run-800",
        }])
        self.assertTrue(any("reviewer identity distinct" in error for error in self.validator.validate_artifact(same_reviewer)))

        same_context = dict(review, implementation_actors=[{
            "identity": "implementation-agent", "role": "implementation-owner", "execution_context": "review-run-800",
        }])
        self.assertTrue(any("reviewer execution_context distinct" in error for error in self.validator.validate_artifact(same_context)))

        not_established = dict(review, independence={
            "status": "NotEstablished", "basis": ["review-log://800"], "compensating_controls": [],
        })
        self.assertTrue(any("requires established independence" in error for error in self.validator.validate_artifact(not_established)))

        no_controls = dict(review, independence={
            "status": "CompensatingControls", "basis": ["review-log://800"], "compensating_controls": [],
        })
        self.assertTrue(any("requires non-empty compensating_controls" in error for error in self.validator.validate_artifact(no_controls)))

        with_controls = dict(review, independence={
            "status": "CompensatingControls", "basis": ["review-log://800"],
            "compensating_controls": ["second-pass-from-clean-context", "mandatory-targeted-validation"],
        })
        self.assertEqual(self.validator.validate_artifact(with_controls), [])


if __name__ == "__main__":
    unittest.main()
