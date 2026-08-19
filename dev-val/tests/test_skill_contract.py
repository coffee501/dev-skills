from __future__ import annotations

import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = SKILL_ROOT.parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.manifest = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        cls.validator = load_module("dev_val_validator", SKILL_ROOT / "scripts" / "validate_artifact.py")
        cls.normalizer = load_module("dev_val_normalizer", SKILL_ROOT / "scripts" / "normalize_test_report.py")

    def test_frontmatter_and_activation_policy(self) -> None:
        match = re.match(r"\A---\n(?P<body>.*?)\n---\n", self.skill, re.DOTALL)
        self.assertIsNotNone(match)
        keys = re.findall(r"(?m)^([A-Za-z0-9_-]+):", match.group("body"))
        self.assertEqual(sorted(keys), ["description", "name"])
        self.assertRegex(match.group("body"), r"(?m)^name: dev-val$")
        self.assertIn("$dev-val", self.manifest)
        self.assertRegex(self.manifest, r"allow_implicit_invocation:\s*false")

    def test_skill_is_active_and_bounded(self) -> None:
        required = [
            "执行验证流程",
            "共享协议不可用",
            "不自动调用其他 Skill",
            "RUN/EVD/DEFECT/GATE",
            "不等于风险接受、发布批准或生产稳定",
            "ProductFailure/TestDefect/EnvironmentFailure",
            "scripts/validate_artifact.py",
            "scripts/normalize_test_report.py",
        ]
        for value in required:
            self.assertIn(value, self.skill)
        self.assertNotIn("Initial scaffold", self.skill)
        self.assertNotIn("当前骨架状态", self.skill)

    def test_required_resources_exist(self) -> None:
        required = [
            "execution-safety.md",
            "execution-model.md",
            "evidence-model.md",
            "failure-governance.md",
            "gate-evaluation.md",
            "non-functional-execution.md",
            "output-contracts.md",
            "review-checklist.md",
        ]
        for name in required:
            self.assertTrue((SKILL_ROOT / "references" / name).is_file(), name)

    def test_markdown_links_resolve(self) -> None:
        pattern = re.compile(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)")
        for path in SKILL_ROOT.rglob("*.md"):
            for target in pattern.findall(path.read_text(encoding="utf-8")):
                if re.match(r"^[a-z][a-z0-9+.-]*:", target):
                    continue
                resolved = (path.parent / target).resolve()
                self.assertTrue(resolved.exists(), f"broken link: {path} -> {target}")
                self.assertTrue(
                    resolved.is_relative_to(SKILL_ROOT.resolve())
                    or resolved.is_relative_to((SUITE_ROOT / "dev-lc").resolve()),
                    f"unexpected package dependency: {path} -> {target}",
                )

    def test_behavior_cases_cover_safety_and_gate_edges(self) -> None:
        document = json.loads((SKILL_ROOT / "tests" / "behavior-cases.json").read_text(encoding="utf-8"))
        self.assertEqual(document["schema_version"], 1)
        cases = {case["id"]: case for case in document["cases"]}
        required = {
            "targeted-local-validation",
            "missing-expected-source",
            "shared-environment-unknown-side-effects",
            "production-experiment-routing",
            "flaky-retry-preserves-first-failure",
            "external-ci-evidence-import",
            "gate-with-expired-evidence",
            "negative-code-fix-request",
        }
        self.assertEqual(set(cases), required)
        for case in cases.values():
            self.assertGreaterEqual(len(case["expected_invariants"]), 2)
            self.assertGreaterEqual(len(case["forbidden_outcomes"]), 1)

    def test_artifact_validator(self) -> None:
        valid = {
            "protocol_version": "DEV-SUITE-7.0",
            "id": "EVD-001",
            "type": "validation-evidence",
            "change": "CHG-PENDING-001",
            "version": 1,
            "status": "Valid",
            "owner": "validator",
            "sources": ["RUN-001@v1", "AC-001@v1"],
            "risks": [],
            "evidence": ["report.xml"],
            "updated_at": "2026-08-14T12:00:00+08:00",
            "run_ref": "RUN-001@v1",
            "test_refs": ["TC-001@v1"],
            "expected_sources": ["AC-001@v1"],
            "observations": ["passed"],
            "raw_locators": ["report.xml"],
            "applies_to": {"target": "abc123", "environment": "local"},
            "validity": {"invalidation_conditions": []},
        }
        self.assertEqual(self.validator.validate_artifact(valid), [])
        invalid = dict(valid, id="RUN-001", raw_locators=[])
        errors = self.validator.validate_artifact(invalid)
        self.assertTrue(any("id must start" in error for error in errors))
        self.assertTrue(any("raw_locators" in error for error in errors))

    def test_junit_normalizer_preserves_failure_and_skip(self) -> None:
        junit = """<testsuite name="sample" tests="3" failures="1" skipped="1">
          <testcase classname="A" name="passes" time="0.1" />
          <testcase classname="A" name="fails" time="0.2"><failure message="boom">trace</failure></testcase>
          <testcase classname="A" name="skips" time="0"><skipped message="not applicable" /></testcase>
        </testsuite>"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.xml"
            path.write_text(junit, encoding="utf-8")
            result = self.normalizer.normalize_junit(path, "RUN-001")
        self.assertEqual(result["totals"]["tests"], 3)
        self.assertEqual(result["totals"]["passed"], 1)
        self.assertEqual(result["totals"]["failed"], 1)
        self.assertEqual(result["totals"]["skipped"], 1)
        self.assertIn("boom", next(case for case in result["cases"] if case["name"] == "fails")["detail"])


if __name__ == "__main__":
    unittest.main()
