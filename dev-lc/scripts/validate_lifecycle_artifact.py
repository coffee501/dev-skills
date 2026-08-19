#!/usr/bin/env python3
"""Validate DEV-SUITE-7.0 lifecycle-control JSON artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PROTOCOL = "DEV-SUITE-7.0"
COMMON = {
    "protocol_version", "id", "type", "change", "version", "status", "owner",
    "sources", "applies_to", "risks", "evidence", "updated_at",
}
RULES = {
    "lifecycle-change": {
        "prefix": "CHG-",
        "statuses": {"Draft", "Active", "Completed", "Cancelled", "Superseded"},
        "required": {
            "objective", "scope", "non_scope", "change_types", "route", "gates",
            "handoff_refs", "open_handoffs", "artifact_refs", "completion",
        },
    },
    "handoff": {
        "prefix": "HOF-",
        "statuses": {"Prepared", "Acknowledged", "Accepted", "Rejected", "Superseded"},
        "required": {
            "from", "to", "reason", "inputs", "preserved_behavior", "decisions", "unresolved",
            "invalidated", "expected_outputs", "entry_conditions",
        },
    },
    "lifecycle-view": {
        "prefix": "LCV-",
        "statuses": {"Current", "Superseded"},
        "required": {
            "chg_ref", "stages", "gates", "artifact_refs", "open_handoffs", "invalidation",
            "blockers", "next_responsibility", "confirmation_scope",
        },
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
        errors.append("missing required fields: " + ", ".join(missing))
    if document.get("protocol_version") != PROTOCOL:
        errors.append(f"protocol_version must be {PROTOCOL}")
    artifact_id = document.get("id")
    if not isinstance(artifact_id, str) or not re.fullmatch(re.escape(rule["prefix"]) + r"(?:PENDING-)?[A-Za-z0-9][A-Za-z0-9._-]*", artifact_id):
        errors.append(f"id must be a non-empty {rule['prefix']} identifier")
    if document.get("status") not in rule["statuses"]:
        errors.append("invalid status; expected one of: " + ", ".join(sorted(rule["statuses"])))
    if not _timestamp(document.get("updated_at")):
        errors.append("updated_at must be an ISO-8601 timestamp with timezone")
    if not isinstance(document.get("version"), (str, int)) or isinstance(document.get("version"), bool):
        errors.append("version must be a string or integer")
    for field in ("change", "owner"):
        if not isinstance(document.get(field), str) or not document[field]:
            errors.append(f"{field} must be a non-empty string")
    for field in ("sources", "applies_to", "risks", "evidence"):
        if field in document and document[field] is None:
            errors.append(f"{field} must not be null")

    if artifact_type == "lifecycle-change":
        if document.get("change") != document.get("id"):
            errors.append("lifecycle-change requires change equal to id")
        if document.get("status") == "Completed":
            completion = document.get("completion")
            if not isinstance(completion, dict) or not completion.get("confirmed_by") or not _timestamp(completion.get("confirmed_at")):
                errors.append("Completed lifecycle-change requires completion.confirmed_by and completion.confirmed_at")
            if document.get("open_handoffs"):
                errors.append("Completed lifecycle-change must not have open_handoffs")

    if artifact_type == "handoff":
        if document.get("from") == document.get("to"):
            errors.append("handoff from and to must differ")
        if document.get("status") == "Accepted":
            acceptance = document.get("acceptance")
            if not isinstance(acceptance, dict) or not acceptance.get("accepted_by") or not _timestamp(acceptance.get("accepted_at")):
                errors.append("Accepted handoff requires acceptance.accepted_by and acceptance.accepted_at")
        if document.get("status") == "Rejected":
            rejection = document.get("rejection")
            if (
                not isinstance(rejection, dict)
                or not rejection.get("reason")
                or not rejection.get("rejected_by")
                or not _timestamp(rejection.get("rejected_at"))
            ):
                errors.append("Rejected handoff requires rejection.reason, rejected_by and rejected_at")

    if artifact_type == "lifecycle-view":
        if not _non_empty(document.get("chg_ref")):
            errors.append("lifecycle-view requires non-empty chg_ref")

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
    print(f"valid {document['type']} artifact: {document['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
