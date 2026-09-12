#!/usr/bin/env python3
"""Validate DEV-SUITE-7.x and 8.0 lifecycle-control JSON artifacts."""

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
ROUTE_NODE_FIELDS = {
    "node_id", "stage", "skill", "applicability", "dependencies", "entry_conditions",
    "expected_outputs", "stop_conditions",
}
ORCHESTRATION_ONLY_ROUTE_FIELDS = {
    "agent", "parallel_groups", "attempt", "runtime_status", "work_item_id",
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
    if document.get("protocol_version") not in SUPPORTED_PROTOCOLS:
        errors.append("protocol_version must be one of: DEV-SUITE-7.0, DEV-SUITE-7.1, DEV-SUITE-8.0")
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
        if document.get("protocol_version") == "DEV-SUITE-8.0" and document.get("status") == "Acknowledged":
            acknowledgement = document.get("acknowledgement")
            if (
                not isinstance(acknowledgement, dict)
                or not acknowledgement.get("acknowledged_by")
                or not _timestamp(acknowledgement.get("acknowledged_at"))
            ):
                errors.append(
                    "Acknowledged handoff requires acknowledgement.acknowledged_by and acknowledgement.acknowledged_at"
                )
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
        if document.get("protocol_version") == "DEV-SUITE-8.0" and document.get("status") == "Superseded":
            supersession = document.get("supersession")
            if (
                not isinstance(supersession, dict)
                or not supersession.get("reason")
                or not supersession.get("superseded_by")
                or not _timestamp(supersession.get("superseded_at"))
            ):
                errors.append(
                    "Superseded handoff requires supersession.reason, superseded_by and superseded_at"
                )

    if artifact_type == "lifecycle-view":
        if not _non_empty(document.get("chg_ref")):
            errors.append("lifecycle-view requires non-empty chg_ref")
        if document.get("protocol_version") == "DEV-SUITE-8.0" and "route" in document:
            route = document.get("route")
            if not isinstance(route, list):
                errors.append("lifecycle-view route must be a list")
            else:
                route_nodes: dict[str, list[str]] = {}
                route_details: dict[str, dict[str, Any]] = {}
                for index, node in enumerate(route):
                    if not isinstance(node, dict):
                        errors.append(f"route[{index}] must be an object")
                        continue
                    missing_route_fields = sorted(ROUTE_NODE_FIELDS - node.keys())
                    if missing_route_fields:
                        errors.append(f"route[{index}] missing fields: {', '.join(missing_route_fields)}")
                    forbidden_route_fields = sorted(ORCHESTRATION_ONLY_ROUTE_FIELDS & node.keys())
                    if forbidden_route_fields:
                        errors.append(f"route[{index}] contains orchestration-only fields: {', '.join(forbidden_route_fields)}")
                    if node.get("applicability") not in {"Applicable", "NotApplicable"}:
                        errors.append(f"route[{index}].applicability must be Applicable or NotApplicable")
                    if node.get("applicability") == "NotApplicable" and not _non_empty(node.get("applicability_reason")):
                        errors.append(f"route[{index}].applicability_reason is required when NotApplicable")
                    if node.get("skill") == "dev-cr" and node.get("applicability") == "NotApplicable":
                        decision = node.get("applicability_decision")
                        if not isinstance(decision, dict):
                            errors.append(
                                f"route[{index}].applicability_decision is required for NotApplicable dev-cr"
                            )
                        else:
                            if not isinstance(decision.get("owner"), str) or not decision["owner"].strip():
                                errors.append(
                                    f"route[{index}].applicability_decision.owner must be a non-empty string "
                                    "for NotApplicable dev-cr"
                                )
                            for field in ("basis", "residual_risks", "invalidates_when"):
                                value = decision.get(field)
                                if not isinstance(value, list) or not value or any(
                                    not isinstance(item, str) or not item.strip() for item in value
                                ):
                                    errors.append(
                                        f"route[{index}].applicability_decision.{field} must be a non-empty "
                                        "string list for NotApplicable dev-cr"
                                    )
                    node_id = node.get("node_id")
                    if not isinstance(node_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", node_id):
                        errors.append(f"route[{index}].node_id must be a non-empty stable identifier")
                    elif node_id in route_nodes:
                        errors.append(f"lifecycle-view route contains duplicate node_id: {node_id}")
                    elif isinstance(node_id, str) and node_id:
                        route_details[node_id] = node
                    for field in ("dependencies", "entry_conditions", "expected_outputs", "stop_conditions"):
                        if field in node and not isinstance(node[field], list):
                            errors.append(f"route[{index}].{field} must be a list")
                    dependencies = node.get("dependencies")
                    if isinstance(node_id, str) and node_id and isinstance(dependencies, list):
                        invalid_dependencies = [
                            item for item in dependencies
                            if not isinstance(item, str) or not item.strip()
                        ]
                        if invalid_dependencies:
                            errors.append(f"route[{index}].dependencies must contain non-empty node_id references")
                        else:
                            route_nodes[node_id] = dependencies

                known_nodes = set(route_nodes)
                for node_id, dependencies in route_nodes.items():
                    unknown = sorted(set(dependencies) - known_nodes)
                    if unknown:
                        errors.append(f"route node {node_id} references unknown dependencies: {', '.join(unknown)}")
                    if node_id in dependencies:
                        errors.append(f"route node {node_id} must not depend on itself")

                visiting: set[str] = set()
                visited: set[str] = set()

                def has_cycle(node_id: str) -> bool:
                    if node_id in visiting:
                        return True
                    if node_id in visited:
                        return False
                    visiting.add(node_id)
                    for dependency in route_nodes.get(node_id, []):
                        if dependency in route_nodes and has_cycle(dependency):
                            return True
                    visiting.remove(node_id)
                    visited.add(node_id)
                    return False

                if any(has_cycle(node_id) for node_id in route_nodes if node_id not in visited):
                    errors.append("lifecycle-view route dependencies must be acyclic")

                def ancestors(node_id: str) -> set[str]:
                    found: set[str] = set()
                    pending = list(route_nodes.get(node_id, []))
                    while pending:
                        dependency = pending.pop()
                        if dependency in found:
                            continue
                        found.add(dependency)
                        pending.extend(route_nodes.get(dependency, []))
                    return found

                applicable_impls = {
                    node_id for node_id, node in route_details.items()
                    if node.get("skill") == "dev-impl" and node.get("applicability") == "Applicable"
                }
                review_nodes = {
                    node_id for node_id, node in route_details.items()
                    if node.get("skill") == "dev-cr"
                }
                applicable_reviews = {
                    node_id for node_id in review_nodes
                    if route_details[node_id].get("applicability") == "Applicable"
                }

                for node_id in applicable_impls:
                    if route_details[node_id].get("stage") != "G4":
                        errors.append(f"applicable dev-impl route node {node_id} must use stage G4")
                    covering_reviews = [
                        review_id for review_id in review_nodes
                        if node_id in ancestors(review_id)
                    ]
                    if not covering_reviews:
                        errors.append(
                            f"applicable dev-impl route node {node_id} must lead to a dev-cr review node"
                        )

                for node_id in review_nodes:
                    if route_details[node_id].get("stage") != "G4":
                        errors.append(f"dev-cr route node {node_id} must use stage G4")

                for node_id, node in route_details.items():
                    if (
                        node.get("skill") == "dev-val"
                        and node.get("stage") == "G5"
                        and node.get("applicability") == "Applicable"
                    ):
                        missing_reviews = sorted(applicable_reviews - ancestors(node_id))
                        if missing_reviews:
                            errors.append(
                                f"applicable G5 dev-val route node {node_id} must depend on all applicable "
                                f"dev-cr nodes: {', '.join(missing_reviews)}"
                            )

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
