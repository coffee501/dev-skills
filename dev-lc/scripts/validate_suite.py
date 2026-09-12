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
    "dev-fia", "dev-test", "dev-val", "dev-lc", "dev-orch",
}
CONTROL_SKILLS = {"dev-lc", "dev-orch"}
SPECIALISTS = EXPECTED_SKILLS - CONTROL_SKILLS
EXECUTION_SKILLS = {"dev-impl", "dev-val"}
EXPLICIT_ONLY_SKILLS = EXECUTION_SKILLS | {"dev-ctx", "dev-orch"}
COMMON_FIELDS = {
    "protocol_version", "id", "type", "change", "version", "status", "owner",
    "sources", "applies_to", "risks", "evidence", "updated_at",
}
EXPECTED_CASES = {
    "brownfield-feature-change", "low-risk-defect-fix", "high-risk-data-migration",
    "test-automation-loop", "validation-failure-feedback-loop",
    "handoff-rejection-and-rework", "standalone-skill-use", "frontend-interface-alignment",
}
EXPECTED_ORCHESTRATION_CASES = {
    "single-stage-direct-route", "brownfield-end-to-end", "migration-development-readiness",
    "handoff-rejection-replan", "input-version-invalidation", "depth-limit-fallback",
    "external-state-unavailable", "promotion-boundary", "frontend-consumer-alignment",
    "codex-session-coordinate", "codex-native-unavailable", "missing-lifecycle-route",
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
    version_path = root / "VERSION"
    try:
        suite_version = version_path.read_text(encoding="utf-8").strip()
        if not re.fullmatch(r"\d+\.\d+\.\d+", suite_version):
            errors.append("VERSION must contain a semantic version")
    except OSError as exc:
        suite_version = ""
        errors.append(f"unable to read VERSION: {exc}")
    found = {path.name for path in root.glob("dev-*") if (path / "SKILL.md").is_file()}
    if found != EXPECTED_SKILLS:
        errors.append(f"skill set mismatch: expected {sorted(EXPECTED_SKILLS)}, found {sorted(found)}")

    required_contract_surfaces = {
        ".github/workflows/validate.yml",
        "VERSION",
        "scripts/validate_all.py",
        "dev-lc/scripts/validate_artifact_envelope.py",
        "dev-ctx/tests/test_skill_contract.py",
        "dev-req/tests/test_skill_contract.py",
        "dev-hld/tests/test_skill_contract.py",
        "dev-lld/tests/test_skill_contract.py",
        "dev-impl/scripts/validate_implementation_artifact.py",
        "dev-impl/tests/test_skill_contract.py",
        "dev-test/references/output-contracts.md",
        "dev-test/scripts/validate_test_artifact.py",
        "dev-test/tests/test_skill_contract.py",
    }
    for relative in sorted(required_contract_surfaces):
        if not (root / relative).is_file():
            errors.append(f"missing contract validation surface: {relative}")

    runner_path = root / "scripts" / "validate_all.py"
    if runner_path.is_file():
        runner_text = runner_path.read_text(encoding="utf-8")
        for token in (
            "dev-req/scripts/validate.ps1", "dev-state/tests/state-store.test.mjs",
            "dev-state/tests/mcp-server.test.mjs", "Node.js 22.5",
        ):
            if token not in runner_text:
                errors.append(f"complete validation runner missing {token}")

    workflow_path = root / ".github" / "workflows" / "validate.yml"
    if workflow_path.is_file():
        workflow_text = workflow_path.read_text(encoding="utf-8")
        for token in ("ubuntu-latest", "windows-latest", "python scripts/validate_all.py"):
            if token not in workflow_text:
                errors.append(f"validation workflow missing {token}")

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
        if plugin.get("version") != suite_version:
            errors.append("Claude plugin version must match VERSION")
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
        elif entries[0].get("source") != "./" or entries[0].get("version") != suite_version:
            errors.append("Claude marketplace dev-skills entry must use source ./ and match VERSION")
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
            "CHG", "HOF", "LCV", "WIT", "Prepared", "Accepted", "dev-fia",
            "mcp__dev_state__workspace_resolve", "workspace_resolve", "external-state-contract.md",
            "orchestration-interface.md", "不要默认加载完整 `dev-lc/SKILL.md`",
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
            expected_agent_tools = {
                "Read", "Glob", "Grep", "Skill", "Agent", "SendMessage", "TaskStop",
                "mcp__dev_state__state_info", "mcp__dev_state__workspace_resolve",
                "mcp__dev_state__change_get", "mcp__dev_state__lifecycle_get",
                "mcp__dev_state__handoff_get", "mcp__dev_state__handoff_list",
                "mcp__dev_state__artifact_list",
                "mcp__dev_state__work_prepare", "mcp__dev_state__work_get",
                "mcp__dev_state__work_list", "mcp__dev_state__work_claim",
                "mcp__dev_state__work_complete", "mcp__dev_state__agent_run_bind",
                "mcp__dev_state__agent_run_list", "mcp__dev_state__audit_list",
            }
            if allowed != expected_agent_tools:
                errors.append("Claude Code dev-orch agent tool allowlist is invalid")
            if "mcp__dev_state__*" in allowed or any(
                name in allowed for name in {
                    "mcp__dev_state__change_get_or_create", "mcp__dev_state__change_put",
                    "mcp__dev_state__lifecycle_put", "mcp__dev_state__artifact_put",
                    "mcp__dev_state__handoff_prepare", "mcp__dev_state__handoff_acknowledge",
                    "mcp__dev_state__handoff_accept", "mcp__dev_state__handoff_reject",
                    "mcp__dev_state__handoff_supersede", "mcp__dev_state__invalidation_apply",
                    "mcp__dev_state__change_archive", "mcp__dev_state__promotion_prepare",
                    "mcp__dev_state__promotion_confirm",
                }
            ):
                errors.append("Claude Code dev-orch agent must not receive lifecycle mutation tools")
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
            "/dev-skills:dev-orch", "Do not alter lifecycle semantics",
            "do not implement specialist work", "../../../dev-orch/SKILL.md",
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
        for token in (
            "从 REQ/RULE/AC 建立 TSC/TC 草案", "IMP(kind=test-automation)", "人工路径",
            "人类可读实现交付摘要", "只读投影",
            suite_version, "scripts/validate_all.py", "dev-cr/tests", "dev-impl/tests", "dev-test/tests", "dev-val/tests",
            "场景JSON只是前向评估用例目录",
        ):
            if token not in readme_text:
                errors.append(f"README.md missing test lifecycle rule: {token}")
        for target in link_pattern.findall(readme_text):
            if re.match(r"^[a-z][a-z0-9+.-]*:", target):
                continue
            resolved = (root / target).resolve()
            if not resolved.exists():
                errors.append(f"broken link: README.md -> {target}")
            elif not resolved.is_relative_to(root.resolve()):
                errors.append(f"link escapes suite: README.md -> {target}")

    artifact_contract = (LC_ROOT / "references" / "artifact-contract.md").read_text(encoding="utf-8")
    for token in (
        "DEV-SUITE-8.0", "dev-cr", "REV", "dev-fia", "FIA", "dev-orch", "WIT",
        "TSC/TC Draft", "IMP(kind=test-automation)", "闭环验证结论 `GATE`", "只读投影视图",
        "人类可读实现交付摘要", "不能替代实际差异、`REV` 或 `GATE`",
    ):
        if token not in artifact_contract:
            errors.append(f"artifact contract missing {token}")

    lifecycle_contract = (LC_ROOT / "references" / "lifecycle-state-model.md").read_text(encoding="utf-8")
    for token in (
        "G1基于 `REQ/RULE/AC`", "IMP(kind=code/config/contract/migration)",
        "AUT Ready → IMP(kind=test-automation) → BUILD Passed → REV Approved",
        "`GATE` 是G5的版本化验证结论记录", "只读投影视图", "可验证的审查独立性",
        "Prepared → Acknowledged / Accepted / Rejected / Superseded",
    ):
        if token not in lifecycle_contract:
            errors.append(f"lifecycle contract missing test lifecycle rule: {token}")

    orchestration_interface = LC_ROOT / "references" / "orchestration-interface.md"
    if not orchestration_interface.is_file():
        errors.append("lifecycle-orchestration interface is missing")
    else:
        interface_text = orchestration_interface.read_text(encoding="utf-8")
        for token in (
            "lifecycle_route_ref", "route_change_request", "coordination_status: Completed",
            "不得增加、删除或改写阶段", "node_id", "无环图", "自动分派", "全部适用 `dev-cr`",
            "capability_isolation: prompt-only",
        ):
            if token not in interface_text:
                errors.append(f"lifecycle-orchestration interface missing {token}")

    lifecycle_skill = (root / "dev-lc" / "SKILL.md").read_text(encoding="utf-8")
    for token in ("生命周期规则和状态权威", "不创建 `WIT/SWI`", "orchestration-interface.md"):
        if token not in lifecycle_skill:
            errors.append(f"dev-lc missing governance boundary: {token}")
    for forbidden in ("session-coordinate", "durable-coordinate"):
        if forbidden in lifecycle_skill:
            errors.append(f"dev-lc must not own runtime mode: {forbidden}")

    orchestrator_skill = (root / "dev-orch" / "SKILL.md").read_text(encoding="utf-8")
    for token in ("lifecycle_route_ref", "route_change_request", "coordination_status: Completed", "orchestration-interface.md"):
        if token not in orchestrator_skill:
            errors.append(f"dev-orch missing execution boundary: {token}")
    for forbidden in ("选择最短充分路线", "开始前完整读取 [dev-lc]"):
        if forbidden in orchestrator_skill:
            errors.append(f"dev-orch duplicates lifecycle authority: {forbidden}")

    test_skill = (root / "dev-test" / "SKILL.md").read_text(encoding="utf-8")
    for token in ("测试设计从G1开始", "IMP(kind=test-automation)", "自动化实现就绪"):
        if token not in test_skill:
            errors.append(f"dev-test missing lifecycle rule: {token}")

    implementation_skill = (root / "dev-impl" / "SKILL.md").read_text(encoding="utf-8")
    implementation_template = (root / "dev-impl" / "references" / "delivery-template.md").read_text(encoding="utf-8")
    for token in (
        "人类可读实现交付摘要", "无独立状态的只读投影视图",
        "当前 `IMP/BUILD` 来源", "不得产生新的批准、完成或验证结论",
    ):
        if token not in implementation_skill:
            errors.append(f"dev-impl missing implementation summary rule: {token}")
    for token in (
        "实现交付摘要（人类可读只读投影）", "来源变化后", "需求与设计落实",
        "实际修改与行为", "契约与工程影响", "偏差、限制与剩余风险",
        "不建立新的正式产物类型、编号、状态、owner或批准结论",
    ):
        if token not in implementation_template:
            errors.append(f"dev-impl delivery template missing implementation summary rule: {token}")
    for forbidden in ("type: implementation-summary", "id: IDOC-"):
        if forbidden in implementation_template:
            errors.append(f"implementation summary must remain a read-only view: {forbidden}")

    validation_skill = (root / "dev-val" / "SKILL.md").read_text(encoding="utf-8")
    for token in (
        "版本化验证结论记录", "完整验证和正式G5评估必须形成 `GATE`",
        "无独立状态的只读视图", "不建立新的正式产物类型",
        "confirmation_record: null", "带时区时间、非空范围和依据",
    ):
        if token not in validation_skill:
            errors.append(f"dev-val missing validation closure rule: {token}")

    complexity_contract = LC_ROOT / "references" / "complexity-governance.md"
    if not complexity_contract.is_file():
        errors.append("complexity and decomposition governance contract is missing")
    else:
        complexity_text = complexity_contract.read_text(encoding="utf-8")
        for token in ("必要复杂度", "过度设计", "有效拆分", "过度拆分", "最低充分决策", "不得仅凭"):
            if token not in complexity_text:
                errors.append(f"complexity governance contract missing {token}")
        complexity_consumers = {"dev-lc", "dev-hld", "dev-lld", "dev-impl", "dev-cr", "dev-test", "dev-orch"}
        for skill_name in sorted(complexity_consumers):
            skill_text = (root / skill_name / "SKILL.md").read_text(encoding="utf-8")
            if "complexity-governance.md" not in skill_text:
                errors.append(f"{skill_name}: complexity governance link is missing")

    external_contract = LC_ROOT / "references" / "external-state-contract.md"
    if not external_contract.is_file():
        errors.append("external state contract is missing")
    else:
        external_text = external_contract.read_text(encoding="utf-8")
        for token in (
            "DEV_SKILLS_STATE_HOME", "CLAUDE_PLUGIN_DATA", "WIT", "语义所有权", "expected_version",
            "promotion_prepare", "不得回退到项目目录", "session-coordinate", "state_persistence: none",
            "lifecycle_id", "LCV-*", "不是接受或拒绝的前置条件",
        ):
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
            "lifecycle_route_status: missing",
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
    state_store_path = root / "dev-state" / "server" / "state-store.mjs"
    if state_store_path.is_file():
        state_store = state_store_path.read_text(encoding="utf-8")
        for token in (
            'CHANGE_STATUSES = new Set(["Draft", "Active", "Completed", "Cancelled", "Superseded"])',
            'LIFECYCLE_STATUSES = new Set(["Current", "Superseded"])',
            "changePut", "CHANGE_TRANSITIONS", "handoffAcknowledge", "accepted_by", "rejected_by", "handoffSupersede",
            "cannot archive change in", "lifecycle_id must start with LCV-",
            "multiple Current lifecycle views exist", "supersedes_lifecycle_id",
            "changeGet", "handoffGet", "handoffList", "workGet", "workList", "agentRunList",
            "agent run input fingerprint does not match current work item",
        ):
            if token not in state_store:
                errors.append(f"external state lifecycle enforcement missing {token}")

    gate_contract = root / "dev-val" / "references" / "output-contracts.md"
    if gate_contract.is_file():
        gate_text = gate_contract.read_text(encoding="utf-8")
        for token in ("confirmation_record: null", "confirmed_by", "confirmed_at", "scope", "basis"):
            if token not in gate_text:
                errors.append(f"GATE confirmation contract missing {token}")

    review_contract = root / "dev-cr" / "references" / "output-contracts.md"
    review_validator = root / "dev-cr" / "scripts" / "validate_review_artifact.py"
    if review_contract.is_file() and review_validator.is_file():
        review_text = review_contract.read_text(encoding="utf-8")
        review_validator_text = review_validator.read_text(encoding="utf-8")
        for token in ("reviewer", "implementation_actors", "independence", "CompensatingControls", "NotEstablished"):
            if token not in review_text or token not in review_validator_text:
                errors.append(f"REV independence contract missing {token}")
    for forbidden in (root / ".dev-state", root / ".dev-lifecycle", root / "dev-state.db"):
        if forbidden.exists():
            errors.append(f"project-local intermediate state is forbidden: {forbidden.relative_to(root)}")

    validator_specs = [
        ("envelope", root / "dev-lc" / "scripts" / "validate_artifact_envelope.py", "COMMON_FIELDS"),
        ("dev_val", root / "dev-val" / "scripts" / "validate_artifact.py", "COMMON_FIELDS"),
        ("dev_cr", root / "dev-cr" / "scripts" / "validate_review_artifact.py", "COMMON"),
        ("dev_fia", root / "dev-fia" / "scripts" / "validate_fia_artifact.py", "COMMON"),
        ("dev_impl", root / "dev-impl" / "scripts" / "validate_implementation_artifact.py", "COMMON"),
        ("dev_lc", root / "dev-lc" / "scripts" / "validate_lifecycle_artifact.py", "COMMON"),
        ("dev_test", root / "dev-test" / "scripts" / "validate_test_artifact.py", "COMMON"),
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
            if getattr(module, "PROTOCOL", None) != "DEV-SUITE-8.0":
                errors.append("dev_fia: new FIA artifacts must use DEV-SUITE-8.0")
            supported = set(getattr(module, "SUPPORTED_PROTOCOLS", set()))
            if not {"DEV-SUITE-7.1", "DEV-SUITE-8.0"}.issubset(supported):
                errors.append("dev_fia: validator must preserve DEV-SUITE-7.1 and accept DEV-SUITE-8.0")
        else:
            supported = set(getattr(module, "SUPPORTED_PROTOCOLS", set()))
            if not {"DEV-SUITE-7.0", "DEV-SUITE-7.1", "DEV-SUITE-8.0"}.issubset(supported):
                errors.append(f"{name}: validator must preserve DEV-SUITE-7.x and accept DEV-SUITE-8.0")

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
            if route & CONTROL_SKILLS:
                errors.append(f"{case.get('id')}: execution route must not dispatch control skills")
            if case.get("id") == "missing-lifecycle-route":
                if case.get("lifecycle_route_ref") is not None or case.get("lifecycle_route_status") != "missing" or case.get("route"):
                    errors.append("missing lifecycle route must stop without an execution task graph")
            elif not isinstance(case.get("lifecycle_route_ref"), str) or not case.get("lifecycle_route_ref"):
                errors.append(f"{case.get('id')}: lifecycle_route_ref is required")
            if not isinstance(case.get("route_change_requested"), bool):
                errors.append(f"{case.get('id')}: route_change_requested must be boolean")
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
        migration_route = indexed.get("migration-development-readiness", {}).get("route", [])
        if not migration_route or migration_route[-1] != "dev-val":
            errors.append("migration development route must stop at dev-val")
        if indexed.get("depth-limit-fallback", {}).get("mode") != "route-only":
            errors.append("dev-orch must fall back to route-only mode at the spawn limit")
        if indexed.get("external-state-unavailable", {}).get("mode") != "route-only":
            errors.append("dev-orch must use route-only when durable state is required but unavailable")
        if indexed.get("codex-session-coordinate", {}).get("mode") != "session-coordinate":
            errors.append("Codex native agents must support non-durable session coordination")
        if indexed.get("codex-native-unavailable", {}).get("mode") != "route-only":
            errors.append("Codex must use route-only mode when native agents are unavailable")
        if indexed.get("missing-lifecycle-route", {}).get("mode") != "route-only":
            errors.append("missing lifecycle route must use route-only mode")
        if not indexed.get("promotion-boundary", {}).get("requires_explicit_authorization"):
            errors.append("promotion must preserve explicit project-write authorization")
        if not indexed.get("handoff-rejection-replan", {}).get("route_change_requested"):
            errors.append("handoff rejection must request LC route recalculation")
        if not indexed.get("input-version-invalidation", {}).get("route_change_requested"):
            errors.append("input invalidation must request LC route recalculation")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"unable to read orchestration cases: {exc}")
    return errors


def main() -> int:
    errors = validate_suite()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Dev Skill suite validation passed: {len(EXPECTED_SKILLS)} skills, protocol DEV-SUITE-8.0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
