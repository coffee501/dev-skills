#!/usr/bin/env python3
"""Validate the minimum JSON contract for dev-ops artifacts."""

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
RULES = {
    "operations-runbook": {
        "prefix": "RUNBOOK-",
        "statuses": {"Draft", "Reviewed", "Ready", "NeedsReview", "Deprecated", "Superseded"},
        "required": {
            "objective", "triggers", "scope", "non_applicable", "preconditions", "target_resolution",
            "permissions", "steps", "stop_conditions", "recovery", "verification", "evidence",
            "escalation", "freshness",
        },
    },
    "incident": {
        "prefix": "INC-",
        "statuses": {"Detected", "Triaged", "Mitigating", "Recovered", "RCA", "Closed"},
        "required": {
            "detected_at", "severity", "impact", "scope", "current_state", "timeline", "actions",
            "communications", "evidence", "recovery_criteria", "observation", "residual_risks",
            "release_refs", "runbook_refs", "rca_refs", "capa_refs",
        },
    },
    "root-cause-analysis": {
        "prefix": "RCA-",
        "statuses": {"Draft", "Investigating", "Reviewed", "Accepted", "Superseded"},
        "required": {
            "incident_refs", "impact_summary", "timeline_refs", "facts", "hypotheses", "causal_chain",
            "contributing_factors", "control_failures", "detection_response_gaps", "excluded_paths",
            "open_questions", "evidence", "limitations", "capa_refs", "review",
        },
    },
    "corrective-preventive-action": {
        "prefix": "CAPA-",
        "statuses": {"Proposed", "Approved", "InProgress", "Verified", "Closed", "Cancelled", "Superseded"},
        "required": {
            "incident_refs", "rca_refs", "action_type", "objective", "owner_role", "due_at", "route_to",
            "implementation_refs", "verification", "residual_risk",
        },
    },
}


def _timestamp(value: Any) -> bool:
    return isinstance(value, str) and bool(
        re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value)
    )


def _non_empty(value: Any) -> bool:
    if isinstance(value, (str, list, dict)):
        return bool(value)
    return value is not None


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
    if document.get("protocol_version") not in SUPPORTED_PROTOCOLS:
        errors.append("protocol_version must be one of: DEV-SUITE-7.0, DEV-SUITE-7.1")
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

    if artifact_type == "operations-runbook" and document.get("status") == "Ready":
        for field in ("steps", "stop_conditions", "recovery", "verification", "evidence"):
            if not _non_empty(document.get(field)):
                errors.append(f"Ready operations-runbook requires non-empty {field}")
        freshness = document.get("freshness")
        if not isinstance(freshness, dict) or not freshness.get("reviewed_at") or not freshness.get("review_due_at"):
            errors.append("Ready operations-runbook requires freshness.reviewed_at and freshness.review_due_at")

    if artifact_type == "incident":
        if not _timestamp(document.get("detected_at")):
            errors.append("detected_at must be an ISO-8601 timestamp with timezone")
        if document.get("status") in {"Recovered", "RCA", "Closed"}:
            observation = document.get("observation")
            if not isinstance(observation, dict):
                errors.append("Recovered incident requires an observation object")
            else:
                if not _non_empty(observation.get("business_signals")):
                    errors.append("Recovered incident requires non-empty observation.business_signals")
                if not _non_empty(observation.get("technical_signals")):
                    errors.append("Recovered incident requires non-empty observation.technical_signals")
                if not _non_empty(observation.get("window")):
                    errors.append("Recovered incident requires observation.window")
        if document.get("status") == "Closed":
            if not _non_empty(document.get("rca_refs")):
                errors.append("Closed incident requires non-empty rca_refs")
            closure = document.get("closure")
            if not isinstance(closure, dict) or not closure.get("authorized_by"):
                errors.append("Closed incident requires closure.authorized_by")

    if artifact_type == "root-cause-analysis":
        if document.get("status") in {"Reviewed", "Accepted"}:
            if not _non_empty(document.get("facts")) or not _non_empty(document.get("causal_chain")):
                errors.append("Reviewed RCA requires non-empty facts and causal_chain")
        if document.get("status") == "Accepted":
            review = document.get("review")
            if not isinstance(review, dict) or not review.get("accepted_by"):
                errors.append("Accepted RCA requires review.accepted_by")

    if artifact_type == "corrective-preventive-action":
        if document.get("action_type") not in {"corrective", "preventive", "corrective-preventive"}:
            errors.append("action_type must be corrective, preventive, or corrective-preventive")
        if not _timestamp(document.get("due_at")):
            errors.append("due_at must be an ISO-8601 timestamp with timezone")
        if document.get("status") in {"Verified", "Closed"}:
            verification = document.get("verification")
            if not isinstance(verification, dict) or verification.get("status") != "passed" or not verification.get("evidence_refs"):
                errors.append("Verified CAPA requires verification.status=passed and non-empty evidence_refs")
        if document.get("status") == "Closed":
            closure = document.get("closure")
            if not isinstance(closure, dict) or not closure.get("authorized_by"):
                errors.append("Closed CAPA requires closure.authorized_by")

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
