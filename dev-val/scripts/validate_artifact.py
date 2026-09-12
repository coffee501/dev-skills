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
SUPPORTED_PROTOCOLS = {"DEV-SUITE-7.0", "DEV-SUITE-7.1", "DEV-SUITE-8.0"}

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
GATE_8_0_REQUIRED = {
    "run_refs", "defect_refs", "target_results", "execution_summary",
    "unverified_scope", "quarantined_or_skipped", "risk_acceptances",
    "revalidation_conditions", "next_responsibility", "handoff_refs",
    "confirmation_record",
}
GATE_RESULTS = {"NotAssessed", "Pass", "Fail", "Blocked", "Expired"}
EXECUTION_SUMMARY_FIELDS = {
    "selected", "executed", "passed", "failed", "blocked", "skipped", "not_run",
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
    if artifact_type == "validation-gate" and document.get("protocol_version") == "DEV-SUITE-8.0":
        missing.extend(sorted(GATE_8_0_REQUIRED - document.keys()))
    if missing:
        errors.append("missing required fields: " + ", ".join(sorted(set(missing))))

    artifact_id = document.get("id")
    if not isinstance(artifact_id, str) or not re.fullmatch(re.escape(rule["prefix"]) + r"(?:PENDING-)?[A-Za-z0-9][A-Za-z0-9._-]*", artifact_id):
        errors.append(f"id must start with {rule['prefix']} and contain a suffix")

    if document.get("protocol_version") not in SUPPORTED_PROTOCOLS:
        errors.append("protocol_version must be one of: DEV-SUITE-7.0, DEV-SUITE-7.1, DEV-SUITE-8.0")

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

    if artifact_type == "validation-gate":
        confirmation = document.get("confirmation")
        if confirmation not in {"Suggested", "Confirmed"}:
            errors.append("confirmation must be Suggested or Confirmed")
        if document.get("protocol_version") == "DEV-SUITE-8.0":
            confirmation_record = document.get("confirmation_record")
            if confirmation == "Suggested":
                if confirmation_record is not None:
                    errors.append("Suggested gate confirmation_record must be null")
            elif confirmation == "Confirmed":
                if not isinstance(confirmation_record, dict):
                    errors.append("Confirmed gate requires a confirmation_record object")
                else:
                    required_confirmation = {"confirmed_by", "confirmed_at", "scope", "basis"}
                    missing_confirmation = sorted(required_confirmation - confirmation_record.keys())
                    if missing_confirmation:
                        errors.append(
                            "confirmation_record missing required fields: " + ", ".join(missing_confirmation)
                        )
                    confirmed_by = confirmation_record.get("confirmed_by")
                    if not isinstance(confirmed_by, str) or not confirmed_by.strip():
                        errors.append("confirmation_record.confirmed_by must be a non-empty string")
                    if not validate_timestamp(confirmation_record.get("confirmed_at")):
                        errors.append("confirmation_record.confirmed_at must be an ISO-8601 timestamp with timezone")
                    scope = confirmation_record.get("scope")
                    if (
                        isinstance(scope, bool)
                        or not isinstance(scope, (str, list, dict))
                        or not scope
                        or (isinstance(scope, str) and not scope.strip())
                    ):
                        errors.append("confirmation_record.scope must be a non-empty string, list, or object")
                    basis = confirmation_record.get("basis")
                    if (
                        not isinstance(basis, list)
                        or not basis
                        or any(not isinstance(item, str) or not item.strip() for item in basis)
                    ):
                        errors.append("confirmation_record.basis must be a non-empty list of non-empty references")

            for field in (
                "validation_targets", "run_refs", "evidence_refs", "defect_refs", "target_results",
                "unverified_scope", "revalidation_conditions", "handoff_refs",
            ):
                if field in document and not isinstance(document[field], list):
                    errors.append(f"{field} must be a list")

            target_results = document.get("target_results")
            if isinstance(target_results, list):
                result_refs: list[str] = []
                for index, result in enumerate(target_results):
                    if not isinstance(result, dict):
                        errors.append(f"target_results[{index}] must be an object")
                        continue
                    required = {"target_ref", "result", "evidence_refs", "unmet_conditions"}
                    missing_result = sorted(required - result.keys())
                    if missing_result:
                        errors.append(
                            f"target_results[{index}] missing required fields: "
                            + ", ".join(missing_result)
                        )
                    target_ref = result.get("target_ref")
                    if not isinstance(target_ref, str) or not target_ref.strip():
                        errors.append(f"target_results[{index}].target_ref must be a non-empty string")
                    else:
                        result_refs.append(target_ref)
                    if result.get("result") not in GATE_RESULTS:
                        errors.append(f"target_results[{index}].result must be a valid gate result")
                    for field in ("evidence_refs", "unmet_conditions"):
                        if field in result and not isinstance(result[field], list):
                            errors.append(f"target_results[{index}].{field} must be a list")
                if len(result_refs) != len(set(result_refs)):
                    errors.append("target_results must not contain duplicate target_ref values")
                validation_targets = document.get("validation_targets")
                if isinstance(validation_targets, list) and set(result_refs) != set(validation_targets):
                    errors.append("target_results must cover validation_targets exactly")

            execution_summary = document.get("execution_summary")
            if not isinstance(execution_summary, dict):
                if "execution_summary" in document:
                    errors.append("execution_summary must be an object")
            else:
                missing_summary = sorted(EXECUTION_SUMMARY_FIELDS - execution_summary.keys())
                if missing_summary:
                    errors.append(
                        "execution_summary missing required fields: " + ", ".join(missing_summary)
                    )
                for field in EXECUTION_SUMMARY_FIELDS & execution_summary.keys():
                    value = execution_summary[field]
                    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                        errors.append(f"execution_summary.{field} must be a non-negative integer")

            next_responsibility = document.get("next_responsibility")
            if not isinstance(next_responsibility, str) or not next_responsibility.strip():
                errors.append("next_responsibility must be a non-empty string")

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
