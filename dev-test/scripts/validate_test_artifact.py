#!/usr/bin/env python3
"""Validate DEV-SUITE test-case and automation-spec JSON artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SUPPORTED_PROTOCOLS = {"DEV-SUITE-7.0", "DEV-SUITE-7.1", "DEV-SUITE-8.0"}
COMMON = {
    "protocol_version", "id", "type", "change", "version", "status", "owner",
    "sources", "applies_to", "risks", "evidence", "updated_at",
}
TEST_STATUSES = {"Draft", "Ready", "NeedsReview", "Deprecated", "Superseded"}
RULES = {
    "test-scenario": {
        "prefix": "TSC-",
        "required": {
            "name", "traceability", "risk_refs", "preconditions", "triggers", "participants",
            "input_classes", "expected_outcomes", "oracle_refs", "state_and_data_effects",
            "target_layers", "priority", "test_case_refs",
        },
        "ready_required": {"traceability", "expected_outcomes", "oracle_refs", "target_layers"},
    },
    "test-case": {
        "prefix": "TC-",
        "required": {
            "name", "traceability", "priority", "preconditions", "data_refs", "steps",
            "expected_results", "oracle_refs", "cleanup", "execution_method", "automation_refs",
        },
        "ready_required": {"traceability", "steps", "expected_results", "oracle_refs"},
    },
    "test-data-partition": {
        "prefix": "TDP-",
        "required": {
            "name", "traceability", "dimension", "classes", "boundaries", "constraints",
            "sensitivity", "generation", "cleanup", "test_case_refs",
        },
        "ready_required": {"traceability", "dimension", "classes", "test_case_refs"},
    },
    "test-data-set": {
        "prefix": "TD-",
        "required": {
            "name", "partition_refs", "data_definition", "generation", "constraints",
            "sensitivity", "isolation", "cleanup", "test_case_refs",
        },
        "ready_required": {"data_definition", "generation", "cleanup", "test_case_refs"},
    },
    "test-environment": {
        "prefix": "TENV-",
        "required": {
            "name", "topology", "component_versions", "contract_versions", "configuration_refs",
            "dependency_refs", "data_refs", "isolation", "reset", "limitations",
        },
        "ready_required": {"topology", "component_versions", "isolation", "reset"},
    },
    "test-condition": {
        "prefix": "TCOND-",
        "required": {
            "name", "condition_type", "setup", "trigger", "observation", "reset",
            "dependency_refs", "test_case_refs",
        },
        "ready_required": {"condition_type", "setup", "observation", "reset", "test_case_refs"},
    },
    "automation-spec": {
        "prefix": "AUT-",
        "required": {
            "test_case_refs", "target_layer", "data_setup", "dependencies", "assertions",
            "entrypoint", "triggers", "isolation", "stability",
        },
        "ready_required": {"test_case_refs", "target_layer", "data_setup", "assertions", "entrypoint", "stability"},
    },
}


def _timestamp(value: Any) -> bool:
    return isinstance(value, str) and bool(
        re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value)
    )


def _non_empty(value: Any) -> bool:
    return isinstance(value, (str, list, dict)) and bool(value)


def validate_artifact(document: Any) -> list[str]:
    if not isinstance(document, dict):
        return ["artifact must be a JSON object"]

    artifact_type = document.get("type")
    rule = RULES.get(artifact_type)
    if rule is None:
        return [f"unsupported artifact type: {artifact_type!r}"]

    errors: list[str] = []
    missing = sorted((COMMON | rule["required"]) - document.keys())
    if missing:
        errors.append(f"missing fields: {', '.join(missing)}")
    if document.get("protocol_version") not in SUPPORTED_PROTOCOLS:
        errors.append("unsupported protocol_version")
    if not isinstance(document.get("id"), str) or not document["id"].startswith(rule["prefix"]):
        errors.append(f"id must start with {rule['prefix']}")
    if document.get("status") not in TEST_STATUSES:
        errors.append(f"invalid status for {artifact_type}")
    for field in ("change", "owner"):
        if not isinstance(document.get(field), str) or not document[field].strip():
            errors.append(f"{field} must be a non-empty string")
    if not isinstance(document.get("version"), (str, int)) or isinstance(document.get("version"), bool):
        errors.append("version must be a string or integer")
    if not _timestamp(document.get("updated_at")):
        errors.append("updated_at must be an ISO-8601 timestamp with timezone")

    if document.get("status") == "Ready":
        for field in sorted(rule.get("ready_required", set())):
            if not _non_empty(document.get(field)):
                errors.append(f"Ready {artifact_type} requires {field}")

    if artifact_type == "test-case":
        if document.get("priority") not in {"Critical", "High", "Medium", "Low"}:
            errors.append("test-case priority must be Critical/High/Medium/Low")
        if document.get("execution_method") not in {"Manual", "AutomationCandidate", "Automated"}:
            errors.append("test-case execution_method must be Manual/AutomationCandidate/Automated")
        if document.get("execution_method") == "Automated" and not _non_empty(document.get("automation_refs")):
            errors.append("Automated test-case requires automation_refs")

    if artifact_type == "test-scenario" and document.get("priority") not in {"Critical", "High", "Medium", "Low"}:
        errors.append("test-scenario priority must be Critical/High/Medium/Low")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()
    try:
        document = json.loads(args.artifact.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: unable to read artifact: {exc}", file=sys.stderr)
        return 2
    errors = validate_artifact(document)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Test artifact is structurally valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
