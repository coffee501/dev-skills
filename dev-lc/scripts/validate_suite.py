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
    "dev-fia", "dev-test", "dev-val", "dev-rel", "dev-ops", "dev-lc", "dev-orch",
}
CONTROL_SKILLS = {"dev-lc", "dev-orch"}
SPECIALISTS = EXPECTED_SKILLS - CONTROL_SKILLS
EXECUTION_SKILLS = {"dev-impl", "dev-val", "dev-rel", "dev-ops"}
EXPLICIT_ONLY_SKILLS = EXECUTION_SKILLS | {"dev-ctx", "dev-orch"}
COMMON_FIELDS = {
    "protocol_version", "id", "type", "change", "version", "status", "owner",
    "sources", "applies_to", "risks", "evidence", "updated_at",
}
EXPECTED_CASES = {
    "brownfield-feature-change", "low-risk-defect-fix", "high-risk-data-migration",
    "test-automation-loop", "healthy-release-to-operations", "incident-feedback-loop",
    "handoff-rejection-and-rework", "standalone-skill-use", "frontend-interface-alignment",
}
EXPECTED_ORCHESTRATION_CASES = {
    "single-stage-direct-route", "brownfield-end-to-end", "migration-through-release",
    "handoff-rejection-replan", "input-version-invalidation", "depth-limit-fallback",
    "external-state-unavailable", "promotion-boundary", "frontend-consumer-alignment",
    "codex-session-coordinate", "codex-native-unavailable",
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
            else:
                expected_policy = "false" if skill_name in EXPLICIT_ONLY_SKILLS else "true"
                if policy.group(1) != expected_policy:
                    errors.append(f"{skill_name}: Codex invocation policy must be {expected_policy}")
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

    plugin_path = root / ".claude-plugin" / "plugin.json"
    try:
        plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
        expected_skill_entries = {f"./.claude/skills/{name}" for name in EXPECTED_SKILLS}
        actual_skill_entries = set(plugin.get("skills", []))
        if actual_skill_entries != expected_skill_entries:
            errors.append("Claude plugin skill registry does not match the suite")
        if set(plugin.get("agents", [])) != {"./.claude/agents/dev-orch.md"}:
            errors.append("Claude plugin must register .claude/agents/dev-orch.md")
        if plugin.get("version") != "7.4.1":
            errors.append("Claude plugin version must be 7.4.1 for cross-platform orchestration")
        mcp = plugin.get("mcpServers", {}).get("dev_state", {})
        if mcp.get("command") != "node":
            errors.append("Claude plugin dev_state MCP must use the bundled Node server")
        if "${CLAUDE_PLUGIN_ROOT}/dev-state/server/dev-state-server.mjs" not in mcp.get("args", []):
            errors.append("Claude plugin dev_state MCP server path is invalid")
        if mcp.get("cwd") != "${CLAUDE_PLUGIN_ROOT}":
            errors.append("Claude plugin dev_state MCP must run from CLAUDE_PLUGIN_ROOT")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"unable to read Claude plugin manifest: {exc}")

    marketplace_path = root / ".claude-plugin" / "marketplace.json"
    try:
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
        entries = [item for item in marketplace.get("plugins", []) if item.get("name") == "dev-skills"]
        if len(entries) != 1:
            errors.append("Claude marketplace must register exactly one dev-skills plugin")
        elif entries[0].get("source") != "./" or entries[0].get("version") != "7.4.1":
            errors.append("Claude marketplace dev-skills entry must use source ./ and version 7.4.1")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"unable to read Claude marketplace manifest: {exc}")

    for skill_name in sorted(EXPECTED_SKILLS):
        adapter_path = root / ".claude" / "skills" / skill_name / "SKILL.md"
        if not adapter_path.is_file():
            errors.append(f"{skill_name}: missing Claude Code skill adapter")
            continue
        adapter = adapter_path.read_text(encoding="utf-8")
        if not re.search(rf"(?m)^name:\s*{re.escape(skill_name)}\s*$", adapter):
            errors.append(f"{skill_name}: Claude adapter name mismatch")
        expected_disabled = "true" if skill_name in EXPLICIT_ONLY_SKILLS else "false"
        if not re.search(rf"(?m)^disable-model-invocation:\s*{expected_disabled}\s*$", adapter):
            errors.append(f"{skill_name}: Claude invocation policy mismatch")
        expected_core = f"../../../{skill_name}/SKILL.md"
        if expected_core not in adapter:
            errors.append(f"{skill_name}: Claude adapter does not reference its core Skill")

    agent_path = root / ".claude" / "agents" / "dev-orch.md"
    if not agent_path.is_file():
        errors.append("Claude Code dev-orch agent is missing")
    else:
        agent = agent_path.read_text(encoding="utf-8")
        required_agent_tokens = {
            "name: dev-orch", "model: inherit", "effort: high", "Skill", "Agent", "dev-lc",
            "CHG", "HOF", "LCV", "WIT", "Prepared", "Accepted", "dev-fia", "dev-rel", "dev-ops",
            "mcp__dev_state__*", "workspace_resolve", "external-state-contract.md",
            "../../dev-orch/SKILL.md", "${CLAUDE_PLUGIN_ROOT}/dev-orch/SKILL.md",
        }
        for token in sorted(required_agent_tokens):
            if token not in agent:
                errors.append(f"Claude Code dev-orch agent missing {token}")
        tools = re.search(r"(?m)^tools:\s*(.+)$", agent)
        if tools is None:
            errors.append("Claude Code dev-orch agent must declare a tool allowlist")
        else:
            allowed = {item.strip() for item in tools.group(1).split(",")}
            if allowed != {"Read", "Glob", "Grep", "Skill", "Agent", "SendMessage", "TaskStop", "mcp__dev_state__*"}:
                errors.append("Claude Code dev-orch agent tool allowlist is invalid")
        if not re.search(r"(?m)^disallowedTools:\s*.*\bWrite\b.*\bEdit\b.*\bBash\b", agent):
            errors.append("Claude Code dev-orch agent must deny direct mutation tools")

    command_path = root / ".claude" / "skills" / "dev-orch" / "SKILL.md"
    if not command_path.is_file():
        errors.append("Claude Code dev-orch slash command is missing")
    else:
        command = command_path.read_text(encoding="utf-8")
        required_command_tokens = {
            "name: dev-orch", "disable-model-invocation: true", "context: fork",
            "agent: dev-orch", "background: false", "$ARGUMENTS",
            "/dev-skills:dev-orch", "do not implement specialist work", "../../../dev-orch/SKILL.md",
        }
        for token in sorted(required_command_tokens):
            if token not in command:
                errors.append(f"Claude Code dev-orch command missing {token}")

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
    for token in ("DEV-SUITE-7.1", "dev-cr", "REV", "dev-fia", "FIA", "dev-orch", "MIGRUN", "RUNBOOK"):
        if token not in artifact_contract:
            errors.append(f"artifact contract missing {token}")

    external_contract = LC_ROOT / "references" / "external-state-contract.md"
    if not external_contract.is_file():
        errors.append("external state contract is missing")
    else:
        external_text = external_contract.read_text(encoding="utf-8")
        for token in ("DEV_SKILLS_STATE_HOME", "CLAUDE_PLUGIN_DATA", "WIT", "expected_version", "promotion_prepare", "不得回退到项目目录", "session-coordinate", "state_persistence: none"):
            if token not in external_text:
                errors.append(f"external state contract missing {token}")

    platform_mapping = root / "dev-orch" / "references" / "platform-mapping.md"
    if not platform_mapping.is_file():
        errors.append("dev-orch platform mapping is missing")
    else:
        mapping_text = platform_mapping.read_text(encoding="utf-8")
        for token in (
            "$dev-orch", "spawn_agent", "followup_task", "send_message", "list_agents",
            "interrupt_agent", "wait_agent", "session-coordinate", "durable-coordinate",
            "/dev-skills:dev-orch", "Agent", "SendMessage", "TaskStop",
        ):
            if token not in mapping_text:
                errors.append(f"dev-orch platform mapping missing {token}")

    state_files = [
        root / "dev-state" / "server" / "state-store.mjs",
        root / "dev-state" / "server" / "dev-state-server.mjs",
        root / "dev-state" / "tests" / "state-store.test.mjs",
        root / "dev-state" / "tests" / "mcp-server.test.mjs",
    ]
    for path in state_files:
        if not path.is_file():
            errors.append(f"external state component missing: {path.relative_to(root)}")
    for forbidden in (root / ".dev-state", root / ".dev-lifecycle", root / "dev-state.db"):
        if forbidden.exists():
            errors.append(f"project-local intermediate state is forbidden: {forbidden.relative_to(root)}")

    validator_specs = [
        ("dev_val", root / "dev-val" / "scripts" / "validate_artifact.py", "COMMON_FIELDS"),
        ("dev_rel", root / "dev-rel" / "scripts" / "validate_release_artifact.py", "COMMON"),
        ("dev_ops", root / "dev-ops" / "scripts" / "validate_ops_artifact.py", "COMMON"),
        ("dev_cr", root / "dev-cr" / "scripts" / "validate_review_artifact.py", "COMMON"),
        ("dev_fia", root / "dev-fia" / "scripts" / "validate_fia_artifact.py", "COMMON"),
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
        if name == "dev_fia":
            if getattr(module, "PROTOCOL", None) != "DEV-SUITE-7.1":
                errors.append("dev_fia: new FIA artifacts must use DEV-SUITE-7.1")
        else:
            supported = set(getattr(module, "SUPPORTED_PROTOCOLS", set()))
            if not {"DEV-SUITE-7.0", "DEV-SUITE-7.1"}.issubset(supported):
                errors.append(f"{name}: validator must preserve DEV-SUITE-7.0 and accept DEV-SUITE-7.1")

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

    orchestration_path = LC_ROOT / "tests" / "orchestration-cases.json"
    try:
        document = json.loads(orchestration_path.read_text(encoding="utf-8"))
        cases = document.get("cases", [])
        if document.get("schema_version") != 1 or len(cases) < 8:
            errors.append("orchestration behavior cases are incomplete")
        case_ids = {case.get("id") for case in cases}
        missing_cases = sorted(EXPECTED_ORCHESTRATION_CASES - case_ids)
        if missing_cases:
            errors.append("orchestration behavior cases missing: " + ", ".join(missing_cases))
        for case in cases:
            if case.get("mode") not in {"direct", "route-only", "session-coordinate", "durable-coordinate"}:
                errors.append(f"{case.get('id')}: invalid orchestration mode")
            route = set(case.get("route", []))
            unknown = route - EXPECTED_SKILLS
            if unknown:
                errors.append(f"{case.get('id')}: unknown orchestration skills: {sorted(unknown)}")
            for group in case.get("parallel_groups", []):
                if len(group) < 2 or not set(group).issubset(route):
                    errors.append(f"{case.get('id')}: invalid parallel group {group}")
            if not isinstance(case.get("requires_explicit_authorization"), bool):
                errors.append(f"{case.get('id')}: authorization flag must be boolean")
            if len(case.get("invariants", [])) < 2:
                errors.append(f"{case.get('id')}: needs at least two orchestration invariants")
        indexed = {case.get("id"): case for case in cases}
        if indexed.get("single-stage-direct-route", {}).get("mode") != "direct":
            errors.append("single-stage requests must bypass orchestration")
        if not indexed.get("migration-through-release", {}).get("requires_explicit_authorization"):
            errors.append("release migration orchestration must preserve explicit authorization")
        if indexed.get("depth-limit-fallback", {}).get("mode") != "route-only":
            errors.append("dev-orch must fall back to route-only mode at the spawn limit")
        if indexed.get("external-state-unavailable", {}).get("mode") != "route-only":
            errors.append("dev-orch must use route-only when durable state is required but unavailable")
        if indexed.get("codex-session-coordinate", {}).get("mode") != "session-coordinate":
            errors.append("Codex native agents must support non-durable session coordination")
        if indexed.get("codex-native-unavailable", {}).get("mode") != "route-only":
            errors.append("Codex must use route-only mode when native agents are unavailable")
        if not indexed.get("promotion-boundary", {}).get("requires_explicit_authorization"):
            errors.append("promotion must preserve explicit project-write authorization")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"unable to read orchestration cases: {exc}")
    return errors


def main() -> int:
    errors = validate_suite()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Dev Skill suite validation passed: {len(EXPECTED_SKILLS)} skills, protocol DEV-SUITE-7.1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
