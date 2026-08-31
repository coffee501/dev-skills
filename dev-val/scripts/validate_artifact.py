#!/usr/bin/env python3
"""Validate the minimum JSON contract for dev-val artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


COMMON_FIELDS = {
    "protocol_version", "id", "type", "change", "version",
    "status", "owner", "sources", "applies_to", "risks", "evidence", "updated_at",
}
SUPPORTED_PROTOCOLS = {"DEV-SUITE-7.0", "DEV-SUITE-7.1"}

TYPE_RULES = {
    "validation-run": {
        "prefix": "RUN-",
        "statuses": {"Planned", "Ready", "Running", "Passed", "Failed", "Blocked", "Aborted"},
        "required": {"objective", "test_refs", "applies_to", "commands", "attempts", "cleanup"},
    },
    "validation-evidence": {
        "prefix": "EVD-",
        "statuses": {"Valid", "Expired", "Revoked"},
        "required": {
            "run_ref", "test_refs", "expected_sources", "observations",
            "raw_locators", "applies_to", "validity",
        },
    },
    "validation-defect": {
        "prefix": "DEFECT-",
        "statuses": {"Open", "Triaged", "Resolved", "Closed", "Superseded"},
        "required": {
            "run_ref", "evidence_refs", "test_refs", "classification",
            "observed_result", "route_to", "revalidation_conditions",
        },
    },
    "validation-gate": {
        "prefix": "GATE-",
        "statuses": {"NotAssessed", "Pass", "Fail", "Blocked", "Expired"},
        "required": {
            "confirmation", "applies_to", "rule_version", "validation_targets",
            "evidence_refs", "missing_or_expired", "failures", "reason",
            "invalidation_conditions",
        },
    },
}

FAILURE_CLASSES = {
    "ProductFailure", "TestDefect", "EnvironmentFailure", "DataSetupFailure",
    "DependencyFailure", "FlakySuspected", "PolicyBlocked", "Unknown",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_timestamp(value: Any) -> bool:
    return isinstance(value, str) and bool(
        re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value)
    )


def validate_artifact(document: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(document, dict):
        return ["artifact must be a JSON object"]

    artifact_type = document.get("type")
    rule = TYPE_RULES.get(artifact_type)
    if rule is None:
        return [f"unsupported artifact type: {artifact_type!r}"]

    missing = sorted((COMMON_FIELDS | rule["required"]) - document.keys())
    if missing:
        errors.append("missing required fields: " + ", ".join(missing))

    artifact_id = document.get("id")
    if not isinstance(artifact_id, str) or not re.fullmatch(re.escape(rule["prefix"]) + r"(?:PENDING-)?[A-Za-z0-9][A-Za-z0-9._-]*", artifact_id):
        errors.append(f"id must start with {rule['prefix']} and contain a suffix")

    if document.get("protocol_version") not in SUPPORTED_PROTOCOLS:
        errors.append("protocol_version must be one of: DEV-SUITE-7.0, DEV-SUITE-7.1")

    if document.get("status") not in rule["statuses"]:
        allowed = ", ".join(sorted(rule["statuses"]))
        errors.append(f"invalid status for {artifact_type}; expected one of: {allowed}")

    if not validate_timestamp(document.get("updated_at")):
        errors.append("updated_at must be an ISO-8601 timestamp with timezone")

    if not isinstance(document.get("change"), str) or not document["change"]:
        errors.append("change must be a non-empty string")

    if not isinstance(document.get("owner"), str) or not document["owner"]:
        errors.append("owner must be a non-empty string")
    for field in ("sources", "applies_to", "risks", "evidence"):
        if field in document and document[field] is None:
            errors.append(f"{field} must not be null")

    version = document.get("version")
    if not isinstance(version, (str, int)) or isinstance(version, bool):
        errors.append("version must be a string or integer")

    if artifact_type == "validation-defect" and document.get("classification") not in FAILURE_CLASSES:
        errors.append("invalid validation failure classification")

    if artifact_type == "validation-gate" and document.get("confirmation") not in {"Suggested", "Confirmed"}:
        errors.append("confirmation must be Suggested or Confirmed")

    if artifact_type == "validation-evidence" and document.get("status") == "Valid":
        for field in ("test_refs", "expected_sources", "observations", "raw_locators"):
            if not isinstance(document.get(field), list) or not document[field]:
                errors.append(f"Valid evidence requires a non-empty {field} list")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path, help="Path to a JSON artifact")
    args = parser.parse_args()
    try:
        document = load_json(args.artifact)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: unable to read artifact: {exc}", file=sys.stderr)
        return 2

    errors = validate_artifact(document)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"valid {document['type']} artifact: {document['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
