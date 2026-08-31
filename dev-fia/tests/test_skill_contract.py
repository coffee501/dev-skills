from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


FIA_ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = FIA_ROOT.parent


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_fia(status: str = "ReadyForReview") -> dict:
    return {
        "protocol_version": "DEV-SUITE-7.1",
        "id": "FIA-001",
        "type": "frontend-interface-alignment",
        "change": "CHG-001",
        "version": 1,
        "status": status,
        "owner": "integration-owner",
        "sources": ["API-001@v2", "openapi.yaml@sha256:abc"],
        "applies_to": {"backend": "2.0", "frontend": "consumer-a"},
        "risks": [],
        "evidence": ["openapi.yaml#/paths/~1orders"],
        "updated_at": "2026-08-21T12:00:00+08:00",
        "service": "order-service",
        "consumers": ["consumer-a"],
        "contract_refs": ["API-001@v2"],
        "contract_identity": [{
            "source_type": "OpenAPI",
            "locator": "openapi.yaml",
            "version": "2.0",
            "fingerprint": "sha256:abc",
            "authority": "api-owner",
            "scope": "order operations",
        }],
        "scenarios": [{"id": "SCN-001", "name": "submit order"}],
        "operations": [{"operation_id": "submitOrder", "contract_ref": "API-001@v2"}],
        "semantic_gaps": [],
        "compatibility": {"supported_combinations": ["frontend-current/backend-2.0"]},
        "readiness": {
            "assessment": "Ready",
            "blockers": [],
            "conditions": [],
            "assessed_at": "2026-08-21T12:00:00+08:00",
        },
        "handoff_refs": [],
    }


class FiaSkillContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load("fia_validator", FIA_ROOT / "scripts" / "validate_fia_artifact.py")

    def test_ready_for_review_artifact_is_valid(self) -> None:
        self.assertEqual(self.validator.validate_artifact(valid_fia()), [])

    def test_baselined_requires_confirmation(self) -> None:
        errors = self.validator.validate_artifact(valid_fia("Baselined"))
        self.assertTrue(any("alignment_confirmation.confirmed_by" in error for error in errors))

    def test_reviewable_artifact_requires_scenarios_and_operations(self) -> None:
        artifact = valid_fia()
        artifact["scenarios"] = []
        artifact["operations"] = []
        errors = self.validator.validate_artifact(artifact)
        self.assertTrue(any("at least one scenario" in error for error in errors))
        self.assertTrue(any("at least one operation" in error for error in errors))

    def test_contract_identity_is_versioned(self) -> None:
        artifact = valid_fia()
        del artifact["contract_identity"][0]["fingerprint"]
        errors = self.validator.validate_artifact(artifact)
        self.assertTrue(any("fingerprint" in error for error in errors))

    def test_ready_rejects_open_p0_semantic_gap(self) -> None:
        artifact = valid_fia()
        artifact["semantic_gaps"] = [{"severity": "P0", "status": "Open"}]
        errors = self.validator.validate_artifact(artifact)
        self.assertTrue(any("open P0 semantic gaps" in error for error in errors))

    def test_behavior_cases_cover_high_risk_alignment(self) -> None:
        import json

        cases = json.loads((FIA_ROOT / "tests" / "behavior-cases.json").read_text(encoding="utf-8"))["cases"]
        ids = {case["id"] for case in cases}
        self.assertTrue({
            "openapi-only-is-insufficient", "new-required-request-field",
            "async-accepted-not-completed", "mixed-frontend-backend-versions",
            "no-frontend-code-generation",
        }.issubset(ids))

    def test_skill_preserves_product_boundary_and_references_exist(self) -> None:
        skill = (FIA_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("OpenAPI", skill)
        self.assertIn("不生成任何前端代码", skill)
        self.assertIn("共享协议不可用", skill)
        for name in (
            "source-authority.md", "openapi-baseline.md", "consumer-semantics.md",
            "compatibility-and-versioning.md", "readiness-checklist.md", "output-template.md",
            "output-contract.md",
        ):
            self.assertTrue((FIA_ROOT / "references" / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
