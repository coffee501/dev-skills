from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


LC_ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = LC_ROOT.parent


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SuiteContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.suite_validator = load("suite_validator", LC_ROOT / "scripts" / "validate_suite.py")
        cls.lifecycle_validator = load("lifecycle_validator", LC_ROOT / "scripts" / "validate_lifecycle_artifact.py")
        cls.envelope_validator = load("envelope_validator", LC_ROOT / "scripts" / "validate_artifact_envelope.py")

    def test_suite_contract(self) -> None:
        self.assertEqual(self.suite_validator.validate_suite(SUITE_ROOT), [])

    def test_shared_envelope_covers_artifacts_without_specialized_validators(self) -> None:
        artifact = {
            "protocol_version": "DEV-SUITE-8.0", "id": "DEC-001", "type": "architecture-decision",
            "change": "CHG-001", "version": 1, "status": "Accepted", "owner": "architecture-owner",
            "sources": ["REQ-001@v1"], "applies_to": {"candidate": "abc"}, "risks": [],
            "evidence": ["design-review://001"], "updated_at": "2026-09-12T12:00:00+08:00",
        }
        self.assertEqual(self.envelope_validator.validate_envelope(artifact), [])
        artifact["owner"] = ""
        self.assertIn("owner must be a non-empty string", self.envelope_validator.validate_envelope(artifact))
        artifact["owner"] = "architecture-owner"
        artifact["sources"] = "REQ-001@v1"
        self.assertIn("sources must be a list", self.envelope_validator.validate_envelope(artifact))

    def test_implementation_and_test_design_have_deterministic_contract_surfaces(self) -> None:
        for relative in (
            "dev-impl/scripts/validate_implementation_artifact.py",
            "dev-impl/tests/test_skill_contract.py",
            "dev-test/references/output-contracts.md",
            "dev-test/scripts/validate_test_artifact.py",
            "dev-test/tests/test_skill_contract.py",
        ):
            self.assertTrue((SUITE_ROOT / relative).is_file(), relative)

    def test_handoff_acceptance_requires_evidence(self) -> None:
        handoff = {
            "protocol_version": "DEV-SUITE-7.0", "id": "HOF-001", "type": "handoff",
            "change": "CHG-001", "version": 1, "status": "Accepted", "owner": "implementation-owner",
            "sources": ["IMP-001@v1"], "applies_to": {"candidate": "abc"}, "risks": [], "evidence": [],
            "updated_at": "2026-08-14T12:00:00+08:00", "from": "dev-impl", "to": "dev-cr",
            "reason": "review", "inputs": ["IMP-001@v1"], "preserved_behavior": [], "decisions": [],
            "unresolved": [], "invalidated": [], "expected_outputs": ["REV"], "entry_conditions": [],
        }
        errors = self.lifecycle_validator.validate_artifact(handoff)
        self.assertTrue(any("acceptance.accepted_by" in error for error in errors))

    def test_completed_change_requires_confirmation(self) -> None:
        change = {
            "protocol_version": "DEV-SUITE-7.0", "id": "CHG-001", "type": "lifecycle-change",
            "change": "CHG-001", "version": 1, "status": "Completed", "owner": "change-owner",
            "sources": [], "applies_to": {"repository": "repo"}, "risks": [], "evidence": [],
            "updated_at": "2026-08-14T12:00:00+08:00", "objective": "deliver change", "scope": {},
            "non_scope": [], "change_types": ["feature"], "route": [], "gates": {}, "handoff_refs": [],
            "open_handoffs": [], "artifact_refs": [], "completion": {},
        }
        errors = self.lifecycle_validator.validate_artifact(change)
        self.assertTrue(any("completion.confirmed_by" in error for error in errors))

    def test_control_artifacts_reject_empty_identity(self) -> None:
        handoff = {
            "protocol_version": "DEV-SUITE-7.0", "id": "HOF-002", "type": "handoff",
            "change": "", "version": 1, "status": "Prepared", "owner": "",
            "sources": [], "applies_to": {}, "risks": [], "evidence": [],
            "updated_at": "2026-08-14T12:00:00+08:00", "from": "dev-impl", "to": "dev-cr",
            "reason": "review", "inputs": [], "preserved_behavior": [], "decisions": [],
            "unresolved": [], "invalidated": [], "expected_outputs": ["REV"], "entry_conditions": [],
        }
        errors = self.lifecycle_validator.validate_artifact(handoff)
        self.assertIn("change must be a non-empty string", errors)
        self.assertIn("owner must be a non-empty string", errors)

    def test_8_0_lifecycle_route_excludes_runtime_scheduling_fields(self) -> None:
        lifecycle_view = {
            "protocol_version": "DEV-SUITE-8.0", "id": "LCV-001", "type": "lifecycle-view",
            "change": "CHG-001", "version": 1, "status": "Current", "owner": "lifecycle-owner",
            "sources": [], "applies_to": {"candidate": "abc"}, "risks": [], "evidence": [],
            "updated_at": "2026-09-12T12:00:00+08:00", "chg_ref": "CHG-001@v1",
            "stages": [], "gates": {}, "artifact_refs": [], "open_handoffs": [],
            "invalidation": [], "blockers": [], "next_responsibility": "dev-req",
            "confirmation_scope": "Suggested",
            "route": [{
                "node_id": "G1-requirements", "stage": "G1", "skill": "dev-req", "applicability": "Applicable",
                "dependencies": [], "entry_conditions": [], "expected_outputs": ["REQ", "RULE", "AC"],
                "stop_conditions": [],
            }],
        }
        self.assertEqual(self.lifecycle_validator.validate_artifact(lifecycle_view), [])
        lifecycle_view["route"][0]["agent"] = "worker-1"
        errors = self.lifecycle_validator.validate_artifact(lifecycle_view)
        self.assertTrue(any("orchestration-only fields: agent" in error for error in errors))

    def test_8_0_lifecycle_route_rejects_unknown_and_cyclic_dependencies(self) -> None:
        def node(node_id: str, dependencies: list[str]) -> dict:
            return {
                "node_id": node_id, "stage": "G1", "skill": "dev-req", "applicability": "Applicable",
                "dependencies": dependencies, "entry_conditions": [], "expected_outputs": [], "stop_conditions": [],
            }

        lifecycle_view = {
            "protocol_version": "DEV-SUITE-8.0", "id": "LCV-CYCLE", "type": "lifecycle-view",
            "change": "CHG-001", "version": 1, "status": "Current", "owner": "lifecycle-owner",
            "sources": [], "applies_to": {}, "risks": [], "evidence": [],
            "updated_at": "2026-09-12T12:00:00+08:00", "chg_ref": "CHG-001@v1",
            "stages": [], "gates": {}, "artifact_refs": [], "open_handoffs": [], "invalidation": [],
            "blockers": [], "next_responsibility": "dev-req", "confirmation_scope": "Suggested",
            "route": [node("requirements", ["design"]), node("design", ["requirements", "missing-node"])],
        }
        errors = self.lifecycle_validator.validate_artifact(lifecycle_view)
        self.assertTrue(any("unknown dependencies: missing-node" in error for error in errors))
        self.assertTrue(any("must be acyclic" in error for error in errors))

    def test_lifecycle_view_without_orchestration_does_not_require_route(self) -> None:
        lifecycle_view = {
            "protocol_version": "DEV-SUITE-8.0", "id": "LCV-NO-ORCH", "type": "lifecycle-view",
            "change": "CHG-001", "version": 1, "status": "Current", "owner": "lifecycle-owner",
            "sources": [], "applies_to": {"candidate": "abc"}, "risks": [], "evidence": [],
            "updated_at": "2026-09-12T12:00:00+08:00", "chg_ref": "CHG-001@v1",
            "stages": [], "gates": {}, "artifact_refs": [], "open_handoffs": [],
            "invalidation": [], "blockers": [], "next_responsibility": "dev-req",
            "confirmation_scope": "Suggested",
        }
        self.assertEqual(self.lifecycle_validator.validate_artifact(lifecycle_view), [])

    def test_8_0_route_requires_implementation_review_before_formal_g5(self) -> None:
        def node(node_id: str, stage: str, skill: str, dependencies: list[str], **extra: object) -> dict:
            result = {
                "node_id": node_id, "stage": stage, "skill": skill, "applicability": "Applicable",
                "dependencies": dependencies, "entry_conditions": [], "expected_outputs": [],
                "stop_conditions": [],
            }
            result.update(extra)
            return result

        lifecycle_view = {
            "protocol_version": "DEV-SUITE-8.0", "id": "LCV-G4-G5", "type": "lifecycle-view",
            "change": "CHG-001", "version": 1, "status": "Current", "owner": "lifecycle-owner",
            "sources": [], "applies_to": {"candidate": "abc"}, "risks": [], "evidence": [],
            "updated_at": "2026-09-12T12:00:00+08:00", "chg_ref": "CHG-001@v1",
            "stages": [], "gates": {}, "artifact_refs": [], "open_handoffs": [],
            "invalidation": [], "blockers": [], "next_responsibility": "dev-impl",
            "confirmation_scope": "Suggested",
            "route": [node("product-impl", "G4", "dev-impl", [])],
        }
        errors = self.lifecycle_validator.validate_artifact(lifecycle_view)
        self.assertTrue(any("must lead to a dev-cr review node" in error for error in errors))

        lifecycle_view["route"] = [
            node("product-impl", "G4", "dev-impl", []),
            node("product-review", "G4", "dev-cr", ["product-impl"]),
            node("formal-validation", "G5", "dev-val", ["product-impl"]),
        ]
        errors = self.lifecycle_validator.validate_artifact(lifecycle_view)
        self.assertTrue(any("must depend on all applicable dev-cr nodes" in error for error in errors))

        lifecycle_view["route"][2]["dependencies"] = ["product-review"]
        self.assertEqual(self.lifecycle_validator.validate_artifact(lifecycle_view), [])

        lifecycle_view["route"] = [
            node("product-impl", "G4", "dev-impl", []),
            node("automation-impl", "G4", "dev-impl", []),
            node("product-review", "G4", "dev-cr", ["product-impl"]),
            node("automation-review", "G4", "dev-cr", ["automation-impl"]),
            node("formal-validation", "G5", "dev-val", ["product-review"]),
        ]
        errors = self.lifecycle_validator.validate_artifact(lifecycle_view)
        self.assertTrue(any("automation-review" in error for error in errors))
        lifecycle_view["route"][4]["dependencies"] = ["product-review", "automation-review"]
        self.assertEqual(self.lifecycle_validator.validate_artifact(lifecycle_view), [])

        lifecycle_view["route"] = [
            node("product-impl", "G4", "dev-impl", []),
            node(
                "review-policy", "G4", "dev-cr", ["product-impl"],
                applicability="NotApplicable",
                applicability_reason="project low-risk review policy with owner and residual-risk record",
            ),
            node("formal-validation", "G5", "dev-val", ["product-impl"]),
        ]
        errors = self.lifecycle_validator.validate_artifact(lifecycle_view)
        self.assertTrue(any("applicability_decision is required" in error for error in errors))
        lifecycle_view["route"][1]["applicability_decision"] = {
            "basis": "POLICY-REVIEW-001@v1", "owner": "quality-owner",
            "residual_risks": [], "invalidates_when": [],
        }
        errors = self.lifecycle_validator.validate_artifact(lifecycle_view)
        self.assertTrue(any("basis must be a non-empty string list" in error for error in errors))
        self.assertTrue(any("residual_risks must be a non-empty string list" in error for error in errors))
        lifecycle_view["route"][1]["applicability_decision"] = {
            "basis": ["POLICY-REVIEW-001@v1"],
            "owner": "quality-owner",
            "residual_risks": ["test automation review deferred for low-risk fixture-only change"],
            "invalidates_when": ["assertion or production-code scope changes"],
        }
        self.assertEqual(self.lifecycle_validator.validate_artifact(lifecycle_view), [])

    def test_orchestrator_preserves_execution_boundaries(self) -> None:
        document = json.loads((LC_ROOT / "tests" / "orchestration-cases.json").read_text(encoding="utf-8"))
        cases = {case["id"]: case for case in document["cases"]}
        self.assertEqual(cases["single-stage-direct-route"]["mode"], "direct")
        self.assertEqual(cases["depth-limit-fallback"]["mode"], "route-only")
        self.assertEqual(cases["external-state-unavailable"]["mode"], "route-only")
        self.assertEqual(cases["migration-development-readiness"]["route"][-1], "dev-val")
        self.assertNotIn("dev-rel", cases["migration-development-readiness"]["route"])
        self.assertNotIn("dev-ops", cases["migration-development-readiness"]["route"])
        self.assertTrue(cases["promotion-boundary"]["requires_explicit_authorization"])
        self.assertIn("dev-fia", cases["frontend-consumer-alignment"]["route"])
        self.assertIn(["dev-fia", "dev-test"], cases["frontend-consumer-alignment"]["parallel_groups"])
        self.assertEqual(cases["codex-session-coordinate"]["mode"], "session-coordinate")
        self.assertEqual(cases["codex-native-unavailable"]["mode"], "route-only")
        self.assertIn("dev-cr", cases["codex-session-coordinate"]["route"])
        brownfield_route = cases["brownfield-end-to-end"]["route"]
        self.assertLess(brownfield_route.index("dev-req"), brownfield_route.index("dev-test"))
        self.assertLess(brownfield_route.index("dev-test"), brownfield_route.index("dev-hld"))
        for case_id, case in cases.items():
            if case_id == "missing-lifecycle-route":
                self.assertIsNone(case["lifecycle_route_ref"])
                self.assertEqual(case["lifecycle_route_status"], "missing")
                self.assertEqual(case["route"], [])
            else:
                self.assertTrue(case["lifecycle_route_ref"])
            self.assertIsInstance(case["route_change_requested"], bool)
            self.assertNotIn("dev-lc", case["route"])
            self.assertNotIn("dev-orch", case["route"])
        self.assertTrue(cases["handoff-rejection-replan"]["route_change_requested"])
        self.assertTrue(cases["input-version-invalidation"]["route_change_requested"])

    def test_lifecycle_rules_and_runtime_orchestration_are_separated(self) -> None:
        lifecycle = (LC_ROOT / "SKILL.md").read_text(encoding="utf-8")
        orchestrator = (SUITE_ROOT / "dev-orch" / "SKILL.md").read_text(encoding="utf-8")
        interface = (LC_ROOT / "references" / "orchestration-interface.md").read_text(encoding="utf-8")
        self.assertIn("生命周期规则和状态权威", lifecycle)
        self.assertIn("不创建 `WIT/SWI`", lifecycle)
        self.assertNotIn("session-coordinate", lifecycle)
        self.assertIn("把 `dev-lc` 提供的生命周期路线编译为执行任务图", orchestrator)
        self.assertIn("route_change_request", orchestrator)
        self.assertNotIn("选择最短充分路线", orchestrator)
        self.assertIn("不得增加、删除或改写阶段及硬依赖", interface)
        self.assertIn("coordination_status: Completed", interface)

    def test_development_boundary_excludes_release_and_operations(self) -> None:
        plugin = json.loads((SUITE_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertFalse(any("dev-rel" in item or "dev-ops" in item for item in plugin["skills"]))
        self.assertFalse((SUITE_ROOT / "dev-rel").exists())
        self.assertFalse((SUITE_ROOT / "dev-ops").exists())
        self.assertFalse((SUITE_ROOT / ".claude" / "skills" / "dev-rel").exists())
        self.assertFalse((SUITE_ROOT / ".claude" / "skills" / "dev-ops").exists())
        lifecycle = (LC_ROOT / "references" / "lifecycle-state-model.md").read_text(encoding="utf-8")
        self.assertNotIn("| G6 |", lifecycle)
        self.assertNotIn("| G7 |", lifecycle)
        self.assertIn("G0至G5", (LC_ROOT / "SKILL.md").read_text(encoding="utf-8"))

    def test_test_design_and_automation_have_explicit_lifecycle_gates(self) -> None:
        readme = (SUITE_ROOT / "README.md").read_text(encoding="utf-8")
        lifecycle = (LC_ROOT / "references" / "lifecycle-state-model.md").read_text(encoding="utf-8")
        artifact = (LC_ROOT / "references" / "artifact-contract.md").read_text(encoding="utf-8")
        test_skill = (SUITE_ROOT / "dev-test" / "SKILL.md").read_text(encoding="utf-8")
        impl_skill = (SUITE_ROOT / "dev-impl" / "SKILL.md").read_text(encoding="utf-8")
        review_skill = (SUITE_ROOT / "dev-cr" / "SKILL.md").read_text(encoding="utf-8")
        validation_skill = (SUITE_ROOT / "dev-val" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("从 REQ/RULE/AC 建立 TSC/TC 草案", readme)
        self.assertIn("G1基于 `REQ/RULE/AC` 建立 `TSC/TC Draft`", lifecycle)
        self.assertIn("TSC/TC Draft", artifact)
        self.assertIn("测试设计从G1开始", test_skill)
        self.assertIn("IMP(kind=test-automation)", impl_skill)
        self.assertIn("测试自动化实现评审", review_skill)
        self.assertIn("AUT Ready → IMP(kind=test-automation) → BUILD Passed → REV Approved", validation_skill)

    def test_validation_closure_uses_gate_without_parallel_report_artifact(self) -> None:
        readme = (SUITE_ROOT / "README.md").read_text(encoding="utf-8")
        lifecycle = (LC_ROOT / "references" / "lifecycle-state-model.md").read_text(encoding="utf-8")
        artifact = (LC_ROOT / "references" / "artifact-contract.md").read_text(encoding="utf-8")
        validation_skill = (SUITE_ROOT / "dev-val" / "SKILL.md").read_text(encoding="utf-8")
        output_contract = (SUITE_ROOT / "dev-val" / "references" / "output-contracts.md").read_text(encoding="utf-8")

        self.assertIn("闭环 `GATE`", readme)
        self.assertIn("`GATE` 是G5的版本化验证结论记录", lifecycle)
        self.assertIn("闭环验证结论 `GATE`", artifact)
        self.assertIn("无独立状态的只读视图", validation_skill)
        self.assertIn("验证摘要是无独立状态的只读投影视图", output_contract)
        self.assertNotIn("type: validation-report", output_contract)

    def test_implementation_delivery_summary_is_a_read_only_projection(self) -> None:
        readme = (SUITE_ROOT / "README.md").read_text(encoding="utf-8")
        artifact = (LC_ROOT / "references" / "artifact-contract.md").read_text(encoding="utf-8")
        lifecycle = (LC_ROOT / "references" / "lifecycle-state-model.md").read_text(encoding="utf-8")
        impl_skill = (SUITE_ROOT / "dev-impl" / "SKILL.md").read_text(encoding="utf-8")
        template = (SUITE_ROOT / "dev-impl" / "references" / "delivery-template.md").read_text(encoding="utf-8")
        review_skill = (SUITE_ROOT / "dev-cr" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("人类可读实现交付摘要", readme)
        self.assertIn("实现交付摘要同样只是指定版本 `IMP/BUILD`", artifact)
        self.assertIn("没有独立状态，不新增阶段门", lifecycle)
        self.assertIn("无独立状态的只读投影视图", impl_skill)
        self.assertIn("## 实现交付摘要（人类可读只读投影）", template)
        self.assertIn("不能替代实际差异", review_skill)
        self.assertNotIn("type: implementation-summary", template)
        self.assertNotIn("id: IDOC-", template)

    def test_handoff_rejects_unqualified_acceptance_timestamp(self) -> None:
        handoff = {
            "protocol_version": "DEV-SUITE-7.0", "id": "HOF-003", "type": "handoff",
            "change": "CHG-001", "version": 1, "status": "Accepted", "owner": "review-owner",
            "sources": [], "applies_to": {}, "risks": [], "evidence": [],
            "updated_at": "2026-08-14T12:00:00+08:00", "from": "dev-impl", "to": "dev-cr",
            "reason": "review", "inputs": [], "preserved_behavior": [], "decisions": [],
            "unresolved": [], "invalidated": [], "expected_outputs": ["REV"], "entry_conditions": [],
            "acceptance": {"accepted_by": "review-owner", "accepted_at": "today"},
        }
        errors = self.lifecycle_validator.validate_artifact(handoff)
        self.assertTrue(any("acceptance.accepted_by" in error for error in errors))

    def test_8_0_acknowledged_and_superseded_statuses_require_their_records(self) -> None:
        handoff = {
            "protocol_version": "DEV-SUITE-8.0", "id": "HOF-004", "type": "handoff",
            "change": "CHG-001", "version": 1, "status": "Acknowledged", "owner": "implementation-owner",
            "sources": [], "applies_to": {}, "risks": [], "evidence": [],
            "updated_at": "2026-09-12T12:00:00+08:00", "from": "dev-lld", "to": "dev-impl",
            "reason": "implementation", "inputs": [], "preserved_behavior": [], "decisions": [],
            "unresolved": [], "invalidated": [], "expected_outputs": ["IMP"], "entry_conditions": [],
        }
        errors = self.lifecycle_validator.validate_artifact(handoff)
        self.assertTrue(any("acknowledgement.acknowledged_by" in error for error in errors))

        handoff["acknowledgement"] = {
            "acknowledged_by": "implementation-owner", "acknowledged_at": "2026-09-12T12:01:00+08:00",
        }
        self.assertEqual(self.lifecycle_validator.validate_artifact(handoff), [])

        handoff["status"] = "Superseded"
        errors = self.lifecycle_validator.validate_artifact(handoff)
        self.assertTrue(any("supersession.reason" in error for error in errors))

        handoff["supersession"] = {
            "reason": "replaced by HOF-005", "superseded_by": "lifecycle-owner",
            "superseded_at": "2026-09-12T12:02:00+08:00",
        }
        self.assertEqual(self.lifecycle_validator.validate_artifact(handoff), [])


if __name__ == "__main__":
    unittest.main()
