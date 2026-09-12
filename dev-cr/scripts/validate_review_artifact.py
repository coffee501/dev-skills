#!/usr/bin/env python3
"""Validate DEV-SUITE-7.x and 8.0 code-review artifacts."""

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
SUPPORTED_PROTOCOLS = {"DEV-SUITE-7.0", "DEV-SUITE-7.1", "DEV-SUITE-8.0"}
REQUIRED = {
    "review_scope", "base", "head", "imp_refs", "build_refs", "requirement_refs", "design_refs",
    "test_refs", "files_reviewed", "generated_or_external", "findings", "required_actions",
    "verification_requirements", "limitations", "handoff_refs",
}
REQUIRED_8_0 = {"reviewer", "implementation_actors", "independence"}
STATUSES = {"Planned", "InReview", "Approved", "ChangesRequested", "Blocked", "Superseded"}
INDEPENDENCE_STATUSES = {"Independent", "CompensatingControls", "NotEstablished"}


def _timestamp(value: Any) -> bool:
    return isinstance(value, str) and bool(
        re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value)
    )


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_actor(value: Any, field: str, errors: list[str]) -> dict[str, str] | None:
    if not isinstance(value, dict):
        errors.append(f"{field} must be an object")
        return None
    for key in ("identity", "role", "execution_context"):
        if not _non_empty_string(value.get(key)):
            errors.append(f"{field}.{key} must be a non-empty string")
    return value


def validate_artifact(document: Any) -> list[str]:
    if not isinstance(document, dict):
        return ["artifact must be a JSON object"]
    errors: list[str] = []
    missing = sorted((COMMON | REQUIRED) - document.keys())
    if document.get("protocol_version") == "DEV-SUITE-8.0":
        missing.extend(sorted(REQUIRED_8_0 - document.keys()))
    if missing:
        errors.append("missing required fields: " + ", ".join(sorted(set(missing))))
    if document.get("protocol_version") not in SUPPORTED_PROTOCOLS:
        errors.append("protocol_version must be one of: DEV-SUITE-7.0, DEV-SUITE-7.1, DEV-SUITE-8.0")
    if document.get("type") != "code-review":
        errors.append("type must be code-review")
    if not isinstance(document.get("id"), str) or not re.fullmatch(r"REV-(?:PENDING-)?[A-Za-z0-9][A-Za-z0-9._-]*", document["id"]):
        errors.append("id must be a non-empty REV identifier")
    if document.get("status") not in STATUSES:
        errors.append("invalid code-review status")
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

    findings = document.get("findings")
    if not isinstance(findings, list):
        errors.append("findings must be a list")
        findings = []
    open_high = [f for f in findings if isinstance(f, dict) and f.get("severity") in {"P0", "P1"} and f.get("status", "Open") == "Open"]
    status = document.get("status")
    reviewer: dict[str, str] | None = None
    implementation_actors: list[dict[str, str]] = []
    independence: dict[str, Any] | None = None
    if document.get("protocol_version") == "DEV-SUITE-8.0":
        reviewer = _validate_actor(document.get("reviewer"), "reviewer", errors)
        raw_actors = document.get("implementation_actors")
        if not isinstance(raw_actors, list):
            errors.append("implementation_actors must be a list")
        else:
            for index, actor in enumerate(raw_actors):
                valid_actor = _validate_actor(actor, f"implementation_actors[{index}]", errors)
                if valid_actor is not None:
                    implementation_actors.append(valid_actor)

        raw_independence = document.get("independence")
        if not isinstance(raw_independence, dict):
            errors.append("independence must be an object")
        else:
            independence = raw_independence
            if independence.get("status") not in INDEPENDENCE_STATUSES:
                errors.append("independence.status must be Independent, CompensatingControls, or NotEstablished")
            basis = independence.get("basis")
            if not isinstance(basis, list) or not basis or not all(_non_empty_string(item) for item in basis):
                errors.append("independence.basis must be a non-empty list of evidence references")
            controls = independence.get("compensating_controls", [])
            if not isinstance(controls, list) or not all(_non_empty_string(item) for item in controls):
                errors.append("independence.compensating_controls must be a list of non-empty strings")

    if status == "Approved":
        if open_high:
            errors.append("Approved review must not contain open P0/P1 findings")
        for field in ("base", "head", "files_reviewed", "evidence"):
            if not document.get(field):
                errors.append(f"Approved review requires non-empty {field}")
        if any(isinstance(item, dict) and item.get("blocking") for item in document.get("limitations", [])):
            errors.append("Approved review must not contain blocking limitations")
        if document.get("protocol_version") == "DEV-SUITE-8.0":
            if not implementation_actors:
                errors.append("Approved review requires at least one implementation actor")
            if independence is not None:
                independence_status = independence.get("status")
                if independence_status == "NotEstablished":
                    errors.append("Approved review requires established independence or compensating controls")
                if independence_status == "Independent" and reviewer is not None:
                    for actor in implementation_actors:
                        if reviewer.get("identity") == actor.get("identity"):
                            errors.append("Independent review requires a reviewer identity distinct from every implementation actor")
                            break
                        if reviewer.get("execution_context") == actor.get("execution_context"):
                            errors.append("Independent review requires a reviewer execution_context distinct from every implementation actor")
                            break
                if independence_status == "CompensatingControls" and not independence.get("compensating_controls"):
                    errors.append("CompensatingControls review requires non-empty compensating_controls")
    if status == "ChangesRequested" and not open_high:
        errors.append("ChangesRequested review requires an open P0/P1 finding")
    if status == "Blocked":
        blocking = document.get("blocking")
        if not isinstance(blocking, dict) or not blocking.get("reason") or not blocking.get("exit_conditions"):
            errors.append("Blocked review requires blocking.reason and exit_conditions")
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
    print(f"valid code-review artifact: {document['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
