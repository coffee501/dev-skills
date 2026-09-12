from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


IMPL_ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    path = IMPL_ROOT / "scripts" / "validate_implementation_artifact.py"
    spec = importlib.util.spec_from_file_location("validate_implementation_artifact", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DevImplContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_skill_links_validator_and_uses_canonical_kinds(self) -> None:
        skill = (IMPL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        model = (IMPL_ROOT / "references" / "implementation-unit.md").read_text(encoding="utf-8")
        self.assertIn("scripts/validate_implementation_artifact.py", skill)
        self.assertIn("code/config/contract/migration/test-automation", model)
        self.assertNotIn("kind=product", skill + model)

    def test_implementation_review_state_requires_review_reference(self) -> None:
        artifact = {
            "protocol_version": "DEV-SUITE-8.0", "id": "IMP-001", "type": "implementation",
            "change": "CHG-001", "version": 1, "kind": "code", "status": "Reviewed",
            "owner": "implementation-owner", "sources": ["DDEC-001@v1"], "applies_to": ["service"],
            "risks": [], "evidence": ["commit:abc"], "updated_at": "2026-09-12T12:00:00+08:00",
            "scope": ["service"], "preserved_behavior": [], "changes": ["implemented feature"],
            "dependencies": [], "verification": ["BUILD-001@v1"], "rollback": ["revert commit"],
            "deviations": [], "review_refs": [],
        }
        errors = self.validator.validate_artifact(artifact)
        self.assertTrue(any("requires review_refs" in error for error in errors))
        artifact["review_refs"] = ["REV-001@v1"]
        self.assertEqual(self.validator.validate_artifact(artifact), [])

    def test_test_automation_requires_spec_source(self) -> None:
        artifact = {
            "protocol_version": "DEV-SUITE-8.0", "id": "IMP-002", "type": "implementation",
            "change": "CHG-001", "version": 1, "kind": "test-automation", "status": "Implemented",
            "owner": "implementation-owner", "sources": ["REQ-001@v1"], "applies_to": ["tests"],
            "risks": [], "evidence": ["commit:def"], "updated_at": "2026-09-12T12:00:00+08:00",
            "scope": ["tests"], "preserved_behavior": [], "changes": ["added test"],
            "dependencies": [], "verification": ["BUILD-002@v1"], "rollback": ["revert commit"],
            "deviations": [], "review_refs": [],
        }
        errors = self.validator.validate_artifact(artifact)
        self.assertTrue(any("requires a versioned TC or AUT source" in error for error in errors))
        artifact["sources"] = ["TC-001@v2", "AUT-001@v1"]
        self.assertEqual(self.validator.validate_artifact(artifact), [])

    def test_passed_build_requires_successful_commands(self) -> None:
        artifact = {
            "protocol_version": "DEV-SUITE-8.0", "id": "BUILD-001", "type": "local-check-batch",
            "change": "CHG-001", "version": 1, "status": "Passed", "owner": "implementation-owner",
            "sources": ["IMP-001@v1"], "applies_to": ["candidate:abc"], "risks": [],
            "evidence": ["log:build-001"], "updated_at": "2026-09-12T12:00:00+08:00",
            "implementation": ["IMP-001@v1"], "candidate_version": "abc", "workspace": {"repository": "repo"},
            "dependencies": {"digest": "sha256:x"}, "environment": {"runtime": "python"},
            "commands": [{"command": "test", "exit_code": 1}], "artifacts": [], "limitations": [],
        }
        errors = self.validator.validate_artifact(artifact)
        self.assertTrue(any("exit_code to be 0" in error for error in errors))
        artifact["commands"][0]["exit_code"] = 0
        self.assertEqual(self.validator.validate_artifact(artifact), [])


if __name__ == "__main__":
    unittest.main()
