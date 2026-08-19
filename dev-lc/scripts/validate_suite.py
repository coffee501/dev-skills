#!/usr/bin/env python3
"""Validate the structure and cross-skill contracts of the Dev Skill suite."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path


SUITE_ROOT = Path(__file__).resolve().parents[2]
LC_ROOT = SUITE_ROOT / "dev-lc"
EXPECTED_SKILLS = {
    "dev-ctx", "dev-req", "dev-hld", "dev-lld", "dev-impl", "dev-cr",
    "dev-test", "dev-val", "dev-rel", "dev-ops", "dev-lc",
}
SPECIALISTS = EXPECTED_SKILLS - {"dev-lc"}
EXECUTION_SKILLS = {"dev-impl", "dev-val", "dev-rel", "dev-ops"}
COMMON_FIELDS = {
    "protocol_version", "id", "type", "change", "version", "status", "owner",
    "sources", "applies_to", "risks", "evidence", "updated_at",
}
EXPECTED_CASES = {
    "brownfield-feature-change", "low-risk-defect-fix", "high-risk-data-migration",
    "test-automation-loop", "healthy-release-to-operations", "incident-feedback-loop",
    "handoff-rejection-and-rework", "standalone-skill-use",
}


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_suite(root: Path = SUITE_ROOT) -> list[str]:
    errors: list[str] = []
    found = {path.name for path in root.glob("dev-*") if (path / "SKILL.md").is_file()}
    if found != EXPECTED_SKILLS:
        errors.append(f"skill set mismatch: expected {sorted(EXPECTED_SKILLS)}, found {sorted(found)}")

    link_pattern = re.compile(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)")
    for skill_name in sorted(EXPECTED_SKILLS & found):
        skill_root = root / skill_name
        skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        if len(skill.splitlines()) > 500:
            errors.append(f"{skill_name}: SKILL.md exceeds 500 lines")
        match = re.match(r"\A---\n(?P<body>.*?)\n---\n", skill, re.DOTALL)
        if match is None:
            errors.append(f"{skill_name}: invalid frontmatter")
        else:
            keys = sorted(re.findall(r"(?m)^([A-Za-z0-9_-]+):", match.group("body")))
            if keys != ["description", "name"]:
                errors.append(f"{skill_name}: frontmatter must contain only name and description")
            if not re.search(rf"(?m)^name:\s*{re.escape(skill_name)}\s*$", match.group("body")):
                errors.append(f"{skill_name}: frontmatter name mismatch")
        manifest_path = skill_root / "agents" / "openai.yaml"
        if not manifest_path.is_file():
            errors.append(f"{skill_name}: missing agents/openai.yaml")
        else:
            manifest = manifest_path.read_text(encoding="utf-8")
            if not re.search(r'(?m)^\s*display_name:\s*"[^\"]+"\s*$', manifest):
                errors.append(f"{skill_name}: display_name is missing")
            short = re.search(r'(?m)^\s*short_description:\s*"([^\"]+)"\s*$', manifest)
            if short is None or not 25 <= len(short.group(1)) <= 64:
                errors.append(f"{skill_name}: short_description must contain 25-64 characters")
            if f"${skill_name}" not in manifest:
                errors.append(f"{skill_name}: default_prompt must mention ${skill_name}")
            policy = re.search(r"allow_implicit_invocation:\s*(true|false)", manifest)
            if policy is None:
                errors.append(f"{skill_name}: implicit invocation policy must be explicit")
            elif skill_name in EXECUTION_SKILLS and policy.group(1) != "false":
                errors.append(f"{skill_name}: execution skill must disable implicit invocation")
        if skill_name in SPECIALISTS and "共享协议不可用" not in skill and "套件协议不可用" not in skill:
            errors.append(f"{skill_name}: standalone fallback is missing")

        for path in skill_root.rglob("*.md"):
            for target in link_pattern.findall(path.read_text(encoding="utf-8")):
                if re.match(r"^[a-z][a-z0-9+.-]*:", target):
                    continue
                resolved = (path.parent / target).resolve()
                if not resolved.exists():
                    errors.append(f"broken link: {path.relative_to(root)} -> {target}")
                elif not resolved.is_relative_to(root.resolve()):
                    errors.append(f"link escapes suite: {path.relative_to(root)} -> {target}")

    readme = root / "README.md"
    if not readme.is_file():
        errors.append("suite README.md is missing")
    else:
        readme_text = readme.read_text(encoding="utf-8")
        for skill_name in sorted(EXPECTED_SKILLS):
            if f"`{skill_name}`" not in readme_text:
                errors.append(f"README.md missing module {skill_name}")
        for target in link_pattern.findall(readme_text):
            if re.match(r"^[a-z][a-z0-9+.-]*:", target):
                continue
            resolved = (root / target).resolve()
            if not resolved.exists():
                errors.append(f"broken link: README.md -> {target}")
            elif not resolved.is_relative_to(root.resolve()):
                errors.append(f"link escapes suite: README.md -> {target}")

    artifact_contract = (LC_ROOT / "references" / "artifact-contract.md").read_text(encoding="utf-8")
    for token in ("DEV-SUITE-7.0", "dev-cr", "REV", "MIGRUN", "RUNBOOK"):
        if token not in artifact_contract:
            errors.append(f"artifact contract missing {token}")

    validator_specs = [
        ("dev_val", root / "dev-val" / "scripts" / "validate_artifact.py", "COMMON_FIELDS"),
        ("dev_rel", root / "dev-rel" / "scripts" / "validate_release_artifact.py", "COMMON"),
        ("dev_ops", root / "dev-ops" / "scripts" / "validate_ops_artifact.py", "COMMON"),
        ("dev_cr", root / "dev-cr" / "scripts" / "validate_review_artifact.py", "COMMON"),
        ("dev_lc", root / "dev-lc" / "scripts" / "validate_lifecycle_artifact.py", "COMMON"),
    ]
    for name, path, field_name in validator_specs:
        if not path.is_file():
            errors.append(f"missing validator: {path.relative_to(root)}")
            continue
        module = _load(name, path)
        actual = set(getattr(module, field_name, set()))
        missing = sorted(COMMON_FIELDS - actual)
        if missing:
            errors.append(f"{name}: validator missing shared fields: {', '.join(missing)}")

    cases_path = LC_ROOT / "tests" / "end-to-end-cases.json"
    try:
        document = json.loads(cases_path.read_text(encoding="utf-8"))
        if document.get("schema_version") != 1 or len(document.get("cases", [])) < 8:
            errors.append("end-to-end behavior cases are incomplete")
        case_ids = {case.get("id") for case in document.get("cases", [])}
        missing_cases = sorted(EXPECTED_CASES - case_ids)
        if missing_cases:
            errors.append("end-to-end behavior cases missing: " + ", ".join(missing_cases))
        for case in document.get("cases", []):
            unknown = set(case.get("route", [])) - EXPECTED_SKILLS
            if unknown:
                errors.append(f"{case.get('id')}: unknown route skills: {sorted(unknown)}")
            if len(case.get("invariants", [])) < 2:
                errors.append(f"{case.get('id')}: needs at least two invariants")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"unable to read end-to-end cases: {exc}")
    return errors


def main() -> int:
    errors = validate_suite()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Dev Skill suite validation passed: {len(EXPECTED_SKILLS)} skills, protocol DEV-SUITE-7.0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
