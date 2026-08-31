#!/usr/bin/env python3
"""Validate DEV-SUITE-7.1 frontend-interface-alignment artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PROTOCOL = "DEV-SUITE-7.1"
COMMON = {
    "protocol_version", "id", "type", "change", "version", "status", "owner",
    "sources", "applies_to", "risks", "evidence", "updated_at",
}
REQUIRED = {
    "service", "consumers", "contract_refs", "contract_identity", "scenarios",
    "operations", "semantic_gaps", "compatibility", "readiness", "handoff_refs",
}
STATUSES = {
    "Draft", "ReadyForReview", "Baselined", "NeedsReview", "Superseded", "Deprecated",
}
READINESS = {"NotAssessed", "Ready", "ConditionallyReady", "Blocked"}
CONTRACT_IDENTITY = {"source_type", "locator", "version", "fingerprint", "authority", "scope"}


def _timestamp(value: Any) -> bool:
    return isinstance(value, str) and bool(
        re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value)
    )


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_artifact(document: Any) -> list[str]:
    if not isinstance(document, dict):
        return ["artifact must be a JSON object"]

    errors: list[str] = []
    missing = sorted((COMMON | REQUIRED) - document.keys())
    if missing:
        errors.append("missing required fields: " + ", ".join(missing))
    if document.get("protocol_version") != PROTOCOL:
        errors.append(f"protocol_version must be {PROTOCOL}")
    if document.get("type") != "frontend-interface-alignment":
        errors.append("type must be frontend-interface-alignment")
    artifact_id = document.get("id")
    if not isinstance(artifact_id, str) or not re.fullmatch(r"FIA-(?:PENDING-)?[A-Za-z0-9][A-Za-z0-9._-]*", artifact_id):
        errors.append("id must be a non-empty FIA- identifier")
    if document.get("status") not in STATUSES:
        errors.append("invalid status; expected one of: " + ", ".join(sorted(STATUSES)))
    if not _timestamp(document.get("updated_at")):
        errors.append("updated_at must be an ISO-8601 timestamp with timezone")
    if not isinstance(document.get("version"), (str, int)) or isinstance(document.get("version"), bool):
        errors.append("version must be a string or integer")
    for field in ("change", "owner", "service"):
        if not _non_empty_string(document.get(field)):
            errors.append(f"{field} must be a non-empty string")
    for field in ("sources", "risks", "evidence", "consumers", "contract_refs", "semantic_gaps", "handoff_refs"):
        if not isinstance(document.get(field), list):
            errors.append(f"{field} must be a list")
    for field in ("applies_to", "compatibility"):
        if not isinstance(document.get(field), dict):
            errors.append(f"{field} must be an object")

    identities = document.get("contract_identity")
    if not isinstance(identities, list) or not identities:
        errors.append("contract_identity must be a non-empty list")
    else:
        for index, identity in enumerate(identities):
            if not isinstance(identity, dict):
                errors.append(f"contract_identity[{index}] must be an object")
                continue
            identity_missing = sorted(CONTRACT_IDENTITY - identity.keys())
            if identity_missing:
                errors.append(
                    f"contract_identity[{index}] missing required fields: " + ", ".join(identity_missing)
                )
            for field in CONTRACT_IDENTITY:
                if field in identity and not _non_empty_string(identity[field]):
                    errors.append(f"contract_identity[{index}].{field} must be a non-empty string")

    scenarios = document.get("scenarios")
    operations = document.get("operations")
    if not isinstance(scenarios, list):
        errors.append("scenarios must be a list")
    if not isinstance(operations, list):
        errors.append("operations must be a list")
    if document.get("status") in {"ReadyForReview", "Baselined"}:
        if not scenarios:
            errors.append("ReadyForReview or Baselined FIA requires at least one scenario")
        if not operations:
            errors.append("ReadyForReview or Baselined FIA requires at least one operation")
        if not document.get("contract_refs"):
            errors.append("ReadyForReview or Baselined FIA requires at least one contract_ref")

    if isinstance(operations, list):
        for index, operation in enumerate(operations):
            if not isinstance(operation, dict):
                errors.append(f"operations[{index}] must be an object")
                continue
            for field in ("operation_id", "contract_ref"):
                if not _non_empty_string(operation.get(field)):
                    errors.append(f"operations[{index}].{field} must be a non-empty string")

    readiness = document.get("readiness")
    if not isinstance(readiness, dict):
        errors.append("readiness must be an object")
    else:
        for field in ("assessment", "blockers", "conditions", "assessed_at"):
            if field not in readiness:
                errors.append(f"readiness.{field} is required")
        if readiness.get("assessment") not in READINESS:
            errors.append("readiness.assessment must be one of: " + ", ".join(sorted(READINESS)))
        if "assessed_at" in readiness and not _timestamp(readiness.get("assessed_at")):
            errors.append("readiness.assessed_at must be an ISO-8601 timestamp with timezone")
        if readiness.get("assessment") == "Ready" and readiness.get("blockers"):
            errors.append("Ready assessment must not have blockers")
        for field in ("blockers", "conditions"):
            if field in readiness and not isinstance(readiness[field], list):
                errors.append(f"readiness.{field} must be a list")
        if readiness.get("assessment") == "Ready" and isinstance(document.get("semantic_gaps"), list):
            open_p0 = any(
                isinstance(gap, dict)
                and gap.get("severity") == "P0"
                and gap.get("status") not in {"Resolved", "Superseded"}
                for gap in document["semantic_gaps"]
            )
            if open_p0:
                errors.append("Ready assessment must not have open P0 semantic gaps")

    if document.get("status") == "Baselined":
        confirmation = document.get("alignment_confirmation")
        if (
            not isinstance(confirmation, dict)
            or not _non_empty_string(confirmation.get("confirmed_by"))
            or not _timestamp(confirmation.get("confirmed_at"))
        ):
            errors.append("Baselined FIA requires alignment_confirmation.confirmed_by and confirmed_at")
        if isinstance(readiness, dict) and readiness.get("assessment") == "Blocked":
            errors.append("Baselined FIA cannot have Blocked readiness")

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
    print(f"valid frontend-interface-alignment artifact: {document['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
