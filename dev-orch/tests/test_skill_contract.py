from __future__ import annotations

import re
import json
import unittest
from pathlib import Path


ORCH_ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = ORCH_ROOT.parent


class DevOrchContractTests(unittest.TestCase):
    def test_orchestrator_core_has_thin_launchers(self) -> None:
        self.assertTrue((ORCH_ROOT / "AGENT.md").is_file())
        self.assertTrue((SUITE_ROOT / ".codex" / "agents" / "dev-orch.toml").is_file())
        self.assertFalse((ORCH_ROOT / "SKILL.md").exists())
        self.assertFalse((ORCH_ROOT / "agents" / "openai.yaml").exists())
        launcher = (SUITE_ROOT / ".agents" / "skills" / "dev-orch" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("AGENT.md", launcher)
        self.assertLess(len(launcher.splitlines()), 20)
        plugin = json.loads((SUITE_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertIn("./.claude/skills/dev-orch", plugin["skills"])
        self.assertIn("./.claude/agents/dev-orch.md", plugin["agents"])

    def test_orchestrator_owns_lifecycle_after_lc_removal(self) -> None:
        skill = (ORCH_ROOT / "AGENT.md").read_text(encoding="utf-8")
        self.assertFalse((SUITE_ROOT / "dev-lc").exists())
        self.assertFalse((SUITE_ROOT / ".claude" / "skills" / "dev-lc").exists())
        for token in ("建立 CHG 上下文", "评估阶段适用性", "管理阶段门", "管理变化与失效"):
            self.assertIn(token, skill)
        for name in ("artifact-contract.md", "lifecycle-state-model.md", "handoff-contract.md", "invalidation-rules.md"):
            self.assertTrue((ORCH_ROOT / "references" / name).is_file())

    def test_agent_core_actively_routes_and_preserves_boundaries(self) -> None:
        skill = (ORCH_ROOT / "AGENT.md").read_text(encoding="utf-8")
        self.assertIn("$dev-orch", skill)
        self.assertIn("主动加载并执行对应专业 Skill", skill)
        self.assertIn("capability-routing.md", skill)
        self.assertIn("outline.md", skill)
        self.assertIn("session-coordinate", skill)
        self.assertIn("durable-coordinate", skill)
        self.assertIn("SWI-001", skill)
        self.assertIn("更高优先级限制", skill)
        self.assertIn("lifecycle_route_status: missing", skill)
        self.assertIn("lifecycle_route_ref", skill)
        self.assertIn("route_change_request", skill)
        self.assertIn("coordination_status: Completed", skill)
        self.assertIn("`dev-cr` 默认使用与产生被审查 `IMP` 的 Agent 和上下文隔离的评审者", skill)
        self.assertIn("`CompensatingControls`", skill)
        self.assertIn("同一上下文自查不得冒充独立批准", skill)
        self.assertIn("自动分派对应 `dev-cr` 节点", skill)
        self.assertIn("选择最短充分路线", skill)

    def test_route_and_execution_projection_are_distinct(self) -> None:
        interface = (ORCH_ROOT / "references" / "orchestration-interface.md").read_text(encoding="utf-8")
        for token in ("lifecycle_route_ref", "route_change_request", "coordination_status: Completed", "node_id", "无环图"):
            self.assertIn(token, interface)
        self.assertIn("不得在编译任务图时临时增加、删除或改写阶段", interface)

    def test_codex_manifest_requires_explicit_invocation(self) -> None:
        manifest = (SUITE_ROOT / ".agents" / "skills" / "dev-orch" / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("$dev-orch", manifest)
        self.assertIn("allow_implicit_invocation: false", manifest)

    def test_platform_mapping_covers_codex_native_agents(self) -> None:
        mapping = (ORCH_ROOT / "references" / "platform-mapping.md").read_text(encoding="utf-8")
        for token in (
            "spawn_agent", "followup_task", "send_message", "list_agents",
            "interrupt_agent", "wait_agent", "session-coordinate", "route-only",
            "SWI-001", "高优先级规则",
        ):
            self.assertIn(token, mapping)
        self.assertIn("不要用新任务/线程创建能力代替子代理", mapping)
        self.assertIn("不得使用 `followup_task`、`send_message`", mapping)
        self.assertIn("不得形成 `REV Approved`", mapping)

    def test_claude_adapters_reference_canonical_core(self) -> None:
        command = (SUITE_ROOT / ".claude" / "skills" / "dev-orch" / "SKILL.md").read_text(encoding="utf-8")
        agent = (SUITE_ROOT / ".claude" / "agents" / "dev-orch.md").read_text(encoding="utf-8")
        self.assertIn("../../../dev-orch/AGENT.md", command)
        self.assertIn("../../dev-orch/AGENT.md", agent)
        self.assertIn("开始前完整读取", agent)
        tools = re.search(r"(?m)^tools:\s*(.+)$", agent)
        self.assertIsNotNone(tools)
        allowed = {item.strip() for item in tools.group(1).split(",")}
        self.assertNotIn("mcp__dev_state__*", allowed)
        self.assertIn("mcp__dev_state__change_get", allowed)
        self.assertIn("mcp__dev_state__lifecycle_get", allowed)
        self.assertIn("mcp__dev_state__handoff_list", allowed)
        self.assertIn("mcp__dev_state__work_prepare", allowed)
        self.assertIn("mcp__dev_state__work_list", allowed)
        self.assertIn("mcp__dev_state__agent_run_list", allowed)
        for required in ("change_get_or_create", "change_put", "lifecycle_put", "handoff_prepare", "invalidation_apply", "work_complete"):
            self.assertIn(f"mcp__dev_state__{required}", allowed)
        for forbidden in ("artifact_put", "promotion_prepare", "promotion_confirm"):
            self.assertNotIn(f"mcp__dev_state__{forbidden}", allowed)


if __name__ == "__main__":
    unittest.main()
