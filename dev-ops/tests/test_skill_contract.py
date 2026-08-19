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
        cls.validator = load_module("dev_ops_validator", SKILL_ROOT / "scripts" / "validate_ops_artifact.py")

    def test_frontmatter_and_activation_policy(self) -> None:
        match = re.match(r"\A---\n(?P<body>.*?)\n---\n", self.skill, re.DOTALL)
        self.assertIsNotNone(match)
        keys = re.findall(r"(?m)^([A-Za-z0-9_-]+):", match.group("body"))
        self.assertEqual(sorted(keys), ["description", "name"])
        self.assertRegex(match.group("body"), r"(?m)^name: dev-ops$")
        self.assertIn("$dev-ops", self.manifest)
        self.assertRegex(self.manifest, r"allow_implicit_invocation:\s*false")

    def test_skill_is_active_independent_and_bounded(self) -> None:
        required = [
            "执行运行与事故流程",
            "共享协议不可用",
            "不自动调用其他 Skill",
            "RUNBOOK/INC/RCA/CAPA",
            "L4 高风险恢复",
            "本 Skill 不自行接受风险",
            "恢复、事故关闭、RCA接受和CAPA关闭",
            "scripts/validate_ops_artifact.py",
        ]
        for value in required:
            self.assertIn(value, self.skill)
        self.assertNotIn("Initial scaffold", self.skill)
        self.assertNotIn("职责骨架阶段", self.skill)

    def test_required_resources_exist(self) -> None:
        required = [
            "operations-safety.md",
            "operations-model.md",
            "runbook-model.md",
            "incident-response.md",
            "production-recovery.md",
            "evidence-timeline.md",
            "rca-capa.md",
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

    def test_lifecycle_model_defines_ops_substates(self) -> None:
        required = [
            "运行手册",
            "Draft → Reviewed → Ready → NeedsReview",
            "根因分析",
            "Draft → Investigating → Reviewed → Accepted",
            "纠正与预防措施",
            "Proposed → Approved → InProgress → Verified",
            "运行准备就绪、事故影响恢复、RCA被接受、CAPA完成关闭",
            "服务恢复不说明事故已经关闭",
        ]
        for value in required:
            self.assertIn(value, self.lifecycle)

    def test_behavior_cases_cover_operational_hazards(self) -> None:
        document = json.loads((SKILL_ROOT / "tests" / "behavior-cases.json").read_text(encoding="utf-8"))
        self.assertEqual(document["schema_version"], 1)
        cases = {case["id"]: case for case in document["cases"]}
        required = {
            "runbook-review-without-execution",
            "unknown-production-target",
            "read-only-incident-triage",
            "approved-reversible-containment",
            "negative-unapproved-data-repair",
            "conflicting-recovery-signals",
            "recovered-is-not-closed",
            "shallow-human-error-rca",
            "unverifiable-capa",
            "external-incident-import",
        }
        self.assertEqual(set(cases), required)
        for case in cases.values():
            self.assertGreaterEqual(len(case["expected_invariants"]), 2)
            self.assertGreaterEqual(len(case["forbidden_outcomes"]), 1)

    def test_artifact_validator_accepts_recovered_incident(self) -> None:
        incident = {
            "protocol_version": "DEV-SUITE-7.0",
            "id": "INC-001",
            "type": "incident",
            "change": "CHG-PENDING-001",
            "version": 1,
            "status": "Recovered",
            "owner": "incident-commander",
            "sources": ["alert://sync-errors"],
            "applies_to": {"environment": "production", "region": "cn-east"},
            "risks": [],
            "updated_at": "2026-08-14T13:00:00+08:00",
            "detected_at": "2026-08-14T11:00:00+08:00",
            "severity": "unassigned",
            "impact": {"summary": "delayed synchronization"},
            "scope": {"environment": "production", "region": "cn-east"},
            "current_state": "stable observation",
            "timeline": [{"kind": "fact"}],
            "actions": [{"kind": "containment"}],
            "communications": [],
            "evidence": ["metrics://incident-001"],
            "recovery_criteria": ["sync success restored"],
            "observation": {
                "business_signals": [{"name": "sync-success", "status": "healthy"}],
                "technical_signals": [{"name": "error-rate", "status": "healthy"}],
                "window": {"start": "t1", "end": "t2"},
            },
            "residual_risks": [],
            "release_refs": [],
            "runbook_refs": ["RUNBOOK-001@v2"],
            "rca_refs": [],
            "capa_refs": [],
        }
        self.assertEqual(self.validator.validate_artifact(incident), [])
        invalid = dict(incident, id="RCA-001", observation={"technical_signals": ["healthy"]})
        errors = self.validator.validate_artifact(invalid)
        self.assertTrue(any("id must start" in error for error in errors))
        self.assertTrue(any("business_signals" in error for error in errors))
        self.assertTrue(any("observation.window" in error for error in errors))

    def test_artifact_validator_enforces_ready_and_closure_evidence(self) -> None:
        runbook = {
            "protocol_version": "DEV-SUITE-7.0", "id": "RUNBOOK-001", "type": "operations-runbook",
            "change": "CHG-001", "version": 1, "status": "Ready", "owner": "ops-owner",
            "sources": ["DDEC-001@v1"], "applies_to": {"service": "sync"}, "risks": [],
            "updated_at": "2026-08-14T13:00:00+08:00", "objective": "isolate shard", "triggers": ["alert"],
            "scope": {"service": "sync"}, "non_applicable": [], "preconditions": ["authorized"],
            "target_resolution": {"method": "asset inventory"}, "permissions": ["operator"], "steps": [],
            "stop_conditions": [], "recovery": {}, "verification": [], "evidence": [], "escalation": ["owner"],
            "freshness": {"reviewed_at": "2026-08-14", "review_due_at": "2026-11-14"},
        }
        errors = self.validator.validate_artifact(runbook)
        self.assertTrue(any("non-empty steps" in error for error in errors))
        self.assertTrue(any("non-empty recovery" in error for error in errors))

        capa = {
            "protocol_version": "DEV-SUITE-7.0", "id": "CAPA-001", "type": "corrective-preventive-action",
            "change": "CHG-001", "version": 1, "status": "Closed", "owner": "quality-owner",
            "sources": ["RCA-001@v1"], "applies_to": {"service": "sync"}, "risks": [], "evidence": [],
            "updated_at": "2026-08-14T13:00:00+08:00", "incident_refs": ["INC-001@v2"],
            "rca_refs": ["RCA-001@v1"], "action_type": "preventive", "objective": "detect invariant breach",
            "owner_role": "service-owner", "due_at": "2026-09-01T00:00:00+08:00", "route_to": "dev-impl",
            "implementation_refs": ["IMP-001@v1"], "verification": {"status": "passed", "evidence_refs": []},
            "residual_risk": [],
        }
        errors = self.validator.validate_artifact(capa)
        self.assertTrue(any("evidence_refs" in error for error in errors))
        self.assertTrue(any("closure.authorized_by" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
