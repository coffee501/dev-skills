#!/usr/bin/env python3
"""Run every deterministic validation shipped with the Dev Skill suite."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEST_SKILLS = (
    "dev-lc", "dev-cr", "dev-ctx", "dev-fia", "dev-hld", "dev-impl",
    "dev-lld", "dev-orch", "dev-req", "dev-test", "dev-val",
)


def run(command: list[str]) -> None:
    print("RUN", subprocess.list2cmdline(command), flush=True)
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run(command, cwd=ROOT, env=environment, check=True)


def require_node_version(node: str) -> None:
    completed = subprocess.run([node, "--version"], cwd=ROOT, check=True, capture_output=True, text=True)
    match = completed.stdout.strip().lstrip("v").split(".")
    try:
        version = tuple(int(part) for part in match[:2])
    except ValueError as exc:
        raise RuntimeError(f"unable to parse Node.js version: {completed.stdout.strip()}") from exc
    if version < (22, 5):
        raise RuntimeError(f"Node.js 22.5 or newer is required; found {completed.stdout.strip()}")


def main() -> int:
    python = sys.executable
    run([python, "dev-lc/scripts/validate_suite.py"])
    for skill in TEST_SKILLS:
        tests = ROOT / skill / "tests"
        if tests.is_dir():
            run([python, "-m", "unittest", "discover", "-s", f"{skill}/tests", "-p", "test_*.py", "-v"])

    powershell = shutil.which("pwsh") or shutil.which("powershell")
    if powershell is None:
        raise RuntimeError("PowerShell is required to validate dev-req")
    run([powershell, "-NoProfile", "-File", "dev-req/scripts/validate.ps1"])

    node = shutil.which("node")
    if node is None:
        raise RuntimeError("Node.js 22.5 or newer is required to validate dev-state")
    require_node_version(node)
    run([
        node, "--disable-warning=ExperimentalWarning", "--test",
        "dev-state/tests/state-store.test.mjs", "dev-state/tests/mcp-server.test.mjs",
    ])
    print("All deterministic Dev Skill suite validations passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
