#!/usr/bin/env python3
"""Validate the minimum JSON contract for dev-rel artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


COMMON = {
    "protocol_version", "id", "type", "change", "version", "status", "owner",
    "sources", "applies_to", "risks", "evidence", "updated_at",
}
RULES = {
    "release": {
        "prefix": "REL-",
        "statuses": {"Draft", "Approved", "Deploying", "Observing", "Completed", "RolledBack", "Failed"},
        "required": {"sources", "applies_to", "authorization", "window", "batches", "stop_conditions", "recovery"},
    },
    "deployment-batch": {
        "prefix": "DEP-",
        "statuses": {"Planned", "Ready", "Running", "Succeeded", "Failed", "Blocked", "Aborted", "RolledBack"},
        "required": {"rel_ref", "objective", "target", "candidate", "execution", "postconditions", "observation_refs", "recovery_refs"},
    },
    "migration-run": {
        "prefix": "MIGRUN-",
        "statuses": {"Planned", "Ready", "Running", "Verified", "Failed", "Blocked", "Aborted", "Compensated", "ForwardFixed"},
        "required": {"rel_ref", "mig_ref", "source_target", "checkpoint", "counts", "validation", "recovery"},
    },
    "release-observation": {
        "prefix": "OBS-",
        "statuses": {"Planned", "Active", "Healthy", "Degraded", "Failed", "Closed"},
        "required": {"rel_ref", "batch_refs", "window", "baseline", "signals", "decision", "limitations"},
    },
}


def _timestamp(value: Any) -> bool:
    return isinstance(value, str) and bool(
        re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value)
    )


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
        errors.append("missing required fields: " + ", ".join(missing))

    artifact_id = document.get("id")
    if not isinstance(artifact_id, str) or not re.fullmatch(re.escape(rule["prefix"]) + r"(?:PENDING-)?[A-Za-z0-9][A-Za-z0-9._-]*", artifact_id):
        errors.append(f"id must start with {rule['prefix']} and contain a suffix")
    if document.get("protocol_version") != "DEV-SUITE-7.0":
        errors.append("protocol_version must be DEV-SUITE-7.0")
    if document.get("status") not in rule["statuses"]:
        errors.append("invalid status; expected one of: " + ", ".join(sorted(rule["statuses"])))
    if not _timestamp(document.get("updated_at")):
        errors.append("updated_at must be an ISO-8601 timestamp with timezone")
    if not isinstance(document.get("change"), str) or not document.get("change"):
        errors.append("change must be a non-empty string")
    if not isinstance(document.get("owner"), str) or not document.get("owner"):
        errors.append("owner must be a non-empty string")
    for field in ("sources", "applies_to", "risks", "evidence"):
        if field in document and document[field] is None:
            errors.append(f"{field} must not be null")
    if not isinstance(document.get("version"), (str, int)) or isinstance(document.get("version"), bool):
        errors.append("version must be a string or integer")

    if artifact_type == "release" and document.get("status") != "Draft":
        authorization = document.get("authorization")
        if not isinstance(authorization, dict) or not authorization:
            errors.append("non-Draft release requires a non-empty authorization object")

    if artifact_type == "migration-run" and document.get("status") == "Verified":
        validation = document.get("validation")
        if not isinstance(validation, dict) or validation.get("status") != "passed":
            errors.append("Verified migration-run requires validation.status=passed")

    if artifact_type == "release-observation" and document.get("status") == "Healthy":
        if not document.get("signals"):
            errors.append("Healthy release-observation requires non-empty signals")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path, help="Path to a JSON artifact")
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
    print(f"valid {document['type']} artifact: {document['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
