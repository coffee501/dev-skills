#!/usr/bin/env python3
"""Validate the shared DEV-SUITE artifact envelope."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SUPPORTED_PROTOCOLS = {"DEV-SUITE-7.0", "DEV-SUITE-7.1", "DEV-SUITE-8.0"}
COMMON_FIELDS = {
    "protocol_version", "id", "type", "change", "version", "status", "owner",
    "sources", "applies_to", "risks", "evidence", "updated_at",
}


def _timestamp(value: Any) -> bool:
    return isinstance(value, str) and bool(
        re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value)
    )


def validate_envelope(document: Any) -> list[str]:
    if not isinstance(document, dict):
        return ["artifact must be a JSON object"]

    errors: list[str] = []
    missing = sorted(COMMON_FIELDS - document.keys())
    if missing:
        errors.append("missing shared envelope fields: " + ", ".join(missing))
    if document.get("protocol_version") not in SUPPORTED_PROTOCOLS:
        errors.append("unsupported protocol_version")
    if not isinstance(document.get("id"), str) or not re.fullmatch(
        r"[A-Z][A-Z0-9]*-(?:PENDING-)?[A-Za-z0-9][A-Za-z0-9._-]*", document.get("id", "")
    ):
        errors.append("id must be a stable uppercase-prefixed identifier")
    for field in ("type", "change", "status", "owner"):
        if not isinstance(document.get(field), str) or not document[field].strip():
            errors.append(f"{field} must be a non-empty string")
    if not isinstance(document.get("version"), (str, int)) or isinstance(document.get("version"), bool):
        errors.append("version must be a string or integer")
    for field in ("sources", "risks", "evidence"):
        if field in document and not isinstance(document[field], list):
            errors.append(f"{field} must be a list")
    if "applies_to" in document and not isinstance(document["applies_to"], (list, dict)):
        errors.append("applies_to must be a list or object")
    if not _timestamp(document.get("updated_at")):
        errors.append("updated_at must be an ISO-8601 timestamp with timezone")
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
    errors = validate_envelope(document)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"valid shared artifact envelope: {document['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
