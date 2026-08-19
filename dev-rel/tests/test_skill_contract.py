from __future__ import annotations

import importlib.util
import json
import re
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
        cls.lifecycle = (SUITE_ROOT / "dev-lc" / "references" / "lifecycle-state-model.md").read_text(encoding="utf-8")
        cls.validator = load_module("dev_rel_validator", SKILL_ROOT / "scripts" / "validate_release_artifact.py")

    def test_frontmatter_and_activation_policy(self) -> None:
        match = re.match(r"\A---\n(?P<body>.*?)\n---\n", self.skill, re.DOTALL)
        self.assertIsNotNone(match)
        keys = re.findall(r"(?m)^([A-Za-z0-9_-]+):", match.group("body"))
        self.assertEqual(sorted(keys), ["description", "name"])
        self.assertRegex(match.group("body"), r"(?m)^name: dev-rel$")
        self.assertIn("$dev-rel", self.manifest)
        self.assertRegex(self.manifest, r"allow_implicit_invocation:\s*false")

    def test_skill_is_active_independent_and_bounded(self) -> None:
        required = [
            "执行发布流程",
            "共享协议不可用",
            "不自动调用其他 Skill",
            "REL/DEP/MIGRUN/OBS",
            "外部质量门",
            "不自行接受风险",
            "不表示生产长期稳定",
            "scripts/validate_release_artifact.py",
        ]
        for value in required:
            self.assertIn(value, self.skill)
        self.assertNotIn("Initial scaffold", self.skill)
        self.assertNotIn("职责骨架阶段", self.skill)

    def test_required_resources_exist(self) -> None:
        required = [
            "release-safety.md",
            "release-model.md",
            "preflight-authorization.md",
            "deployment-execution.md",
            "migration-execution.md",
            "observation-decision.md",
            "rollback-recovery.md",
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

    def test_lifecycle_model_defines_release_substates(self) -> None:
        required = [
            "部署批次",
            "Succeeded / Failed / Blocked / Aborted / RolledBack",
            "迁移执行",
            "Verified / Failed / Blocked / Aborted / Compensated / ForwardFixed",
            "发布观察",
            "Healthy / Degraded / Failed / Closed",
            "发布就绪、发布执行完成、观察窗口通过",
        ]
        for value in required:
            self.assertIn(value, self.lifecycle)

    def test_behavior_cases_cover_release_hazards(self) -> None:
        document = json.loads((SKILL_ROOT / "tests" / "behavior-cases.json").read_text(encoding="utf-8"))
        self.assertEqual(document["schema_version"], 1)
        cases = {case["id"]: case for case in document["cases"]}
        required = {
            "non-production-approved-release",
            "vague-production-authorization",
            "candidate-digest-mismatch",
            "failed-quality-gate-without-waiver",
            "irreversible-migration-without-forward-fix",
            "canary-stop-threshold-breach",
            "application-rollback-data-incompatible",
            "interrupted-migration-resume",
            "negative-unplanned-production-fix",
        }
        self.assertEqual(set(cases), required)
        for case in cases.values():
            self.assertGreaterEqual(len(case["expected_invariants"]), 2)
            self.assertGreaterEqual(len(case["forbidden_outcomes"]), 1)

    def test_artifact_validator(self) -> None:
        valid_observation = {
            "protocol_version": "DEV-SUITE-7.0",
            "id": "OBS-001",
            "type": "release-observation",
            "change": "CHG-PENDING-001",
            "version": 1,
            "status": "Healthy",
            "owner": "release-owner",
            "sources": ["REL-001@v1", "DEP-001@v1"],
            "applies_to": {"candidate": "sha256:abc", "environment": "production-a"},
            "risks": [],
            "evidence": ["metrics://release-001"],
            "updated_at": "2026-08-14T12:00:00+08:00",
            "rel_ref": "REL-001@v1",
            "batch_refs": ["DEP-001@v1"],
            "window": {"start": "t1", "end": "t2"},
            "baseline": ["error-rate"],
            "signals": [{"name": "error-rate", "status": "within-limit"}],
            "decision": {"action": "continue"},
            "limitations": [],
        }
        self.assertEqual(self.validator.validate_artifact(valid_observation), [])
        invalid_observation = dict(valid_observation, id="DEP-001", signals=[])
        errors = self.validator.validate_artifact(invalid_observation)
        self.assertTrue(any("id must start" in error for error in errors))
        self.assertTrue(any("non-empty signals" in error for error in errors))

        invalid_migration = {
            "protocol_version": "DEV-SUITE-7.0",
            "id": "MIGRUN-001",
            "type": "migration-run",
            "change": "CHG-001",
            "version": 1,
            "status": "Verified",
            "owner": "release-owner",
            "sources": ["REL-001@v1", "MIG-001@v1"],
            "applies_to": {"candidate": "sha256:abc", "environment": "production-a"},
            "risks": [],
            "evidence": ["migration://run-001"],
            "updated_at": "2026-08-14T12:00:00+08:00",
            "rel_ref": "REL-001@v1",
            "mig_ref": "MIG-001@v1",
            "source_target": {},
            "checkpoint": None,
            "counts": {},
            "validation": {"status": "pending"},
            "recovery": {},
        }
        self.assertTrue(any("validation.status=passed" in error for error in self.validator.validate_artifact(invalid_migration)))


if __name__ == "__main__":
    unittest.main()
