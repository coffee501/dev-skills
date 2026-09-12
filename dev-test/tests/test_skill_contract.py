from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


TEST_ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    path = TEST_ROOT / "scripts" / "validate_test_artifact.py"
    spec = importlib.util.spec_from_file_location("validate_test_artifact", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DevTestContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validator = load_validator()

    def test_skill_links_output_contract_and_validator(self) -> None:
        skill = (TEST_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/output-contracts.md", skill)
        self.assertIn("scripts/validate_test_artifact.py", skill)

    def test_all_owned_test_artifact_types_are_validated(self) -> None:
        expected = {
            "test-scenario", "test-case", "test-data-partition", "test-data-set",
            "test-environment", "test-condition", "automation-spec",
        }
        self.assertEqual(set(self.validator.RULES), expected)
        prefixes = {rule["prefix"] for rule in self.validator.RULES.values()}
        self.assertEqual(prefixes, {"TSC-", "TC-", "TDP-", "TD-", "TENV-", "TCOND-", "AUT-"})

    def test_ready_supporting_artifacts_require_executable_content(self) -> None:
        samples = {
            "test-scenario": ("TSC-001", {
                "name": "reject invalid state", "traceability": [], "risk_refs": [], "preconditions": [],
                "triggers": [], "participants": [], "input_classes": [], "expected_outcomes": [],
                "oracle_refs": [], "state_and_data_effects": [], "target_layers": [], "priority": "High",
                "test_case_refs": [],
            }, "traceability"),
            "test-data-partition": ("TDP-001", {
                "name": "amount boundaries", "traceability": [], "dimension": "", "classes": [],
                "boundaries": [], "constraints": [], "sensitivity": [], "generation": [], "cleanup": [],
                "test_case_refs": [],
            }, "classes"),
            "test-data-set": ("TD-001", {
                "name": "minimum fixture", "partition_refs": [], "data_definition": [], "generation": [],
                "constraints": [], "sensitivity": [], "isolation": [], "cleanup": [], "test_case_refs": [],
            }, "data_definition"),
            "test-environment": ("TENV-001", {
                "name": "integration", "topology": [], "component_versions": [], "contract_versions": [],
                "configuration_refs": [], "dependency_refs": [], "data_refs": [], "isolation": [],
                "reset": [], "limitations": [],
            }, "topology"),
            "test-condition": ("TCOND-001", {
                "name": "dependency timeout", "condition_type": "", "setup": [], "trigger": [],
                "observation": [], "reset": [], "dependency_refs": [], "test_case_refs": [],
            }, "condition_type"),
        }
        for artifact_type, (artifact_id, fields, missing_field) in samples.items():
            with self.subTest(artifact_type=artifact_type):
                artifact = {
                    "protocol_version": "DEV-SUITE-8.0", "id": artifact_id, "type": artifact_type,
                    "change": "CHG-001", "version": 1, "status": "Ready", "owner": "test-owner",
                    "sources": ["AC-001@v1"], "applies_to": ["candidate-family"], "risks": [],
                    "evidence": [], "updated_at": "2026-09-12T12:00:00+08:00", **fields,
                }
                errors = self.validator.validate_artifact(artifact)
                self.assertTrue(any(missing_field in error for error in errors), errors)

    def test_ready_test_case_requires_execution_oracle(self) -> None:
        artifact = {
            "protocol_version": "DEV-SUITE-8.0", "id": "TC-001", "type": "test-case",
            "change": "CHG-001", "version": 1, "status": "Ready", "owner": "test-owner",
            "sources": ["AC-001@v1"], "applies_to": ["candidate-family"], "risks": [],
            "evidence": [], "updated_at": "2026-09-12T12:00:00+08:00", "name": "reject invalid input",
            "traceability": ["TSC-001@v1", "AC-001@v1"], "priority": "High", "preconditions": [],
            "data_refs": ["TD-001@v1"], "steps": ["submit invalid input"],
            "expected_results": ["stable rejection"], "oracle_refs": [], "cleanup": [],
            "execution_method": "Manual", "automation_refs": [],
        }
        errors = self.validator.validate_artifact(artifact)
        self.assertTrue(any("requires oracle_refs" in error for error in errors))
        artifact["oracle_refs"] = ["AC-001@v1"]
        self.assertEqual(self.validator.validate_artifact(artifact), [])

    def test_automated_case_requires_automation_reference(self) -> None:
        artifact = {
            "protocol_version": "DEV-SUITE-8.0", "id": "TC-002", "type": "test-case",
            "change": "CHG-001", "version": 1, "status": "Draft", "owner": "test-owner",
            "sources": ["AC-001@v1"], "applies_to": ["candidate-family"], "risks": [],
            "evidence": [], "updated_at": "2026-09-12T12:00:00+08:00", "name": "automated behavior",
            "traceability": ["TSC-001@v1"], "priority": "Medium", "preconditions": [],
            "data_refs": [], "steps": [], "expected_results": [], "oracle_refs": [], "cleanup": [],
            "execution_method": "Automated", "automation_refs": [],
        }
        errors = self.validator.validate_artifact(artifact)
        self.assertTrue(any("requires automation_refs" in error for error in errors))
        artifact["automation_refs"] = ["AUT-001@v1"]
        self.assertEqual(self.validator.validate_artifact(artifact), [])

    def test_ready_automation_spec_requires_implementation_inputs(self) -> None:
        artifact = {
            "protocol_version": "DEV-SUITE-8.0", "id": "AUT-001", "type": "automation-spec",
            "change": "CHG-001", "version": 1, "status": "Ready", "owner": "test-owner",
            "sources": ["TC-001@v1"], "applies_to": ["candidate-family"], "risks": [],
            "evidence": [], "updated_at": "2026-09-12T12:00:00+08:00",
            "test_case_refs": ["TC-001@v1"], "target_layer": "component", "data_setup": ["fixture"],
            "dependencies": [], "assertions": ["observable result"], "entrypoint": "tests/component",
            "triggers": ["pull request"], "isolation": ["transaction rollback"], "stability": {},
        }
        errors = self.validator.validate_artifact(artifact)
        self.assertTrue(any("requires stability" in error for error in errors))
        artifact["stability"] = {"retry": "none", "time_control": "fake clock"}
        self.assertEqual(self.validator.validate_artifact(artifact), [])


if __name__ == "__main__":
    unittest.main()
