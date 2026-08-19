#!/usr/bin/env python3
"""Normalize JUnit XML into a neutral dev-val JSON result summary."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def _text(node: ET.Element | None, limit: int) -> str | None:
    if node is None:
        return None
    value = (node.get("message") or "") + ("\n" + (node.text or "") if node.text else "")
    value = value.strip()
    return value[:limit] if value else None


def _case_result(case: ET.Element, limit: int) -> dict[str, Any]:
    failure = case.find("failure")
    error = case.find("error")
    skipped = case.find("skipped")
    if failure is not None or error is not None:
        status = "Failed"
        detail = _text(failure if failure is not None else error, limit)
    elif skipped is not None:
        status = "Skipped"
        detail = _text(skipped, limit)
    else:
        status = "Passed"
        detail = None
    return {
        "id": case.get("id"),
        "classname": case.get("classname"),
        "name": case.get("name") or "unnamed-test",
        "duration_seconds": float(case.get("time", "0") or 0),
        "status": status,
        "detail": detail,
    }


def normalize_junit(path: Path, run_id: str, detail_limit: int = 4000) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    if not suites:
        suites = list(root.findall(".//testsuite"))

    cases: list[dict[str, Any]] = []
    suite_names: list[str] = []
    for suite in suites:
        suite_names.append(suite.get("name") or "unnamed-suite")
        cases.extend(_case_result(case, detail_limit) for case in suite.findall("testcase"))

    totals = {
        "tests": len(cases),
        "passed": sum(case["status"] == "Passed" for case in cases),
        "failed": sum(case["status"] == "Failed" for case in cases),
        "skipped": sum(case["status"] == "Skipped" for case in cases),
        "duration_seconds": round(sum(case["duration_seconds"] for case in cases), 6),
    }
    return {
        "schema_version": 1,
        "format": "dev-val-normalized-test-report",
        "source_format": "junit-xml",
        "run_ref": run_id,
        "source": str(path),
        "suites": suite_names,
        "totals": totals,
        "cases": cases,
        "limitations": [
            "This normalized report is derived evidence and does not replace the source report.",
            "Version, environment, expected-source and authorization context must be recorded in RUN/EVD.",
            "Review output for secrets or sensitive data before retention or sharing.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="JUnit XML report")
    parser.add_argument("--run-id", required=True, help="Source RUN identifier")
    parser.add_argument("--output", type=Path, help="Write JSON to this path; otherwise stdout")
    parser.add_argument("--detail-limit", type=int, default=4000)
    args = parser.parse_args()
    if args.detail_limit < 0:
        parser.error("--detail-limit must be non-negative")
    try:
        document = normalize_junit(args.report, args.run_id, args.detail_limit)
    except (OSError, ET.ParseError, ValueError) as exc:
        print(f"ERROR: unable to normalize report: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
