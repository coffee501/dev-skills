from __future__ import annotations

import importlib.util
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

    def test_suite_contract(self) -> None:
        self.assertEqual(self.suite_validator.validate_suite(SUITE_ROOT), [])

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


if __name__ == "__main__":
    unittest.main()
