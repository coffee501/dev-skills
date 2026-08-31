#!/usr/bin/env python3
"""Validate DEV-SUITE-7.0 and 7.1 code-review artifacts."""

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
SUPPORTED_PROTOCOLS = {"DEV-SUITE-7.0", "DEV-SUITE-7.1"}
REQUIRED = {
    "review_scope", "base", "head", "imp_refs", "build_refs", "requirement_refs", "design_refs",
    "test_refs", "files_reviewed", "generated_or_external", "findings", "required_actions",
    "verification_requirements", "limitations", "handoff_refs",
}
STATUSES = {"Planned", "InReview", "Approved", "ChangesRequested", "Blocked", "Superseded"}


def _timestamp(value: Any) -> bool:
    return isinstance(value, str) and bool(
        re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value)
    )


def validate_artifact(document: Any) -> list[str]:
    if not isinstance(document, dict):
        return ["artifact must be a JSON object"]
    errors: list[str] = []
    missing = sorted((COMMON | REQUIRED) - document.keys())
    if missing:
        errors.append("missing required fields: " + ", ".join(missing))
    if document.get("protocol_version") not in SUPPORTED_PROTOCOLS:
        errors.append("protocol_version must be one of: DEV-SUITE-7.0, DEV-SUITE-7.1")
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
    if status == "Approved":
        if open_high:
            errors.append("Approved review must not contain open P0/P1 findings")
        for field in ("base", "head", "files_reviewed", "evidence"):
            if not document.get(field):
                errors.append(f"Approved review requires non-empty {field}")
        if any(isinstance(item, dict) and item.get("blocking") for item in document.get("limitations", [])):
            errors.append("Approved review must not contain blocking limitations")
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
