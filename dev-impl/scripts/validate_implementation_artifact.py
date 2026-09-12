#!/usr/bin/env python3
"""Validate DEV-SUITE implementation and local-build JSON artifacts."""

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
IMPLEMENTATION_KINDS = {"code", "config", "contract", "migration", "test-automation"}
RULES = {
    "implementation": {
        "prefix": "IMP-",
        "statuses": {
            "Planned", "InProgress", "Implemented", "Reviewed", "Integrated",
            "Blocked", "Aborted", "Superseded",
        },
        "required": {
            "kind", "scope", "preserved_behavior", "changes", "dependencies", "verification",
            "rollback", "deviations", "review_refs",
        },
    },
    "local-check-batch": {
        "prefix": "BUILD-",
        "statuses": {"Planned", "Running", "Passed", "Failed", "Blocked", "Aborted"},
        "required": {
            "implementation", "candidate_version", "workspace", "dependencies", "environment",
            "commands", "artifacts", "limitations",
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
        errors.append(f"missing fields: {', '.join(missing)}")
    if document.get("protocol_version") not in SUPPORTED_PROTOCOLS:
        errors.append("unsupported protocol_version")
    if not isinstance(document.get("id"), str) or not document["id"].startswith(rule["prefix"]):
        errors.append(f"id must start with {rule['prefix']}")
    if document.get("status") not in rule["statuses"]:
        errors.append(f"invalid status for {artifact_type}")
    for field in ("change", "owner"):
        if not isinstance(document.get(field), str) or not document[field].strip():
            errors.append(f"{field} must be a non-empty string")
    if not isinstance(document.get("version"), (str, int)) or isinstance(document.get("version"), bool):
        errors.append("version must be a string or integer")
    if not _timestamp(document.get("updated_at")):
        errors.append("updated_at must be an ISO-8601 timestamp with timezone")

    if artifact_type == "implementation":
        if document.get("kind") not in IMPLEMENTATION_KINDS:
            errors.append("implementation kind must be code/config/contract/migration/test-automation")
        if document.get("status") in {"Reviewed", "Integrated"} and not _non_empty(document.get("review_refs")):
            errors.append("Reviewed or Integrated implementation requires review_refs")
        if document.get("kind") == "test-automation":
            sources = document.get("sources")
            if not isinstance(sources, list) or not any(
                isinstance(item, str) and (item.startswith("TC-") or item.startswith("AUT-"))
                for item in sources
            ):
                errors.append("test-automation implementation requires a versioned TC or AUT source")

    if artifact_type == "local-check-batch":
        if not _non_empty(document.get("implementation")):
            errors.append("local-check-batch requires implementation references")
        if not _non_empty(document.get("candidate_version")):
            errors.append("local-check-batch requires candidate_version")
        commands = document.get("commands")
        if document.get("status") == "Passed":
            if not isinstance(commands, list) or not commands:
                errors.append("Passed local-check-batch requires commands")
            elif any(not isinstance(item, dict) or item.get("exit_code") != 0 for item in commands):
                errors.append("Passed local-check-batch requires every command exit_code to be 0")

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
    print("Implementation artifact is structurally valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
