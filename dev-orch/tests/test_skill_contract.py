from __future__ import annotations

import re
import unittest
from pathlib import Path


ORCH_ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = ORCH_ROOT.parent


class DevOrchContractTests(unittest.TestCase):
    def test_root_skill_is_explicit_and_tool_neutral(self) -> None:
        skill = (ORCH_ROOT / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = re.match(r"\A---\n(?P<body>.*?)\n---\n", skill, re.DOTALL)
        self.assertIsNotNone(frontmatter)
        self.assertEqual(
            sorted(re.findall(r"(?m)^([A-Za-z0-9_-]+):", frontmatter.group("body"))),
            ["description", "name"],
        )
        self.assertIn("$dev-orch", skill)
        self.assertIn("session-coordinate", skill)
        self.assertIn("durable-coordinate", skill)
        self.assertIn("SWI-001", skill)
        self.assertIn("更高优先级限制", skill)
        self.assertIn("lifecycle_route_status: missing", skill)
        self.assertIn("lifecycle_route_ref", skill)
        self.assertIn("route_change_request", skill)
        self.assertIn("coordination_status: Completed", skill)
        self.assertIn("不得让 `dev-cr` 续接被审查实现的 `dev-impl` 上下文", skill)
        self.assertIn("自动分派对应 `dev-cr` 节点", skill)
        self.assertNotIn("选择最短充分路线", skill)
        self.assertNotIn("开始前完整读取 [dev-lc]", skill)

    def test_lifecycle_and_orchestration_ownership_is_separated(self) -> None:
        lifecycle = (SUITE_ROOT / "dev-lc" / "SKILL.md").read_text(encoding="utf-8")
        interface = (SUITE_ROOT / "dev-lc" / "references" / "orchestration-interface.md").read_text(encoding="utf-8")
        self.assertIn("生命周期规则和状态权威", lifecycle)
        self.assertIn("不创建 `WIT/SWI`", lifecycle)
        self.assertNotIn("session-coordinate", lifecycle)
        self.assertNotIn("durable-coordinate", lifecycle)
        for token in ("lifecycle_route_ref", "route_change_request", "coordination_status: Completed", "不得增加、删除或改写阶段"):
            self.assertIn(token, interface)

    def test_codex_manifest_requires_explicit_invocation(self) -> None:
        manifest = (ORCH_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
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
        self.assertIn("../../../dev-orch/SKILL.md", command)
        self.assertIn("../../dev-orch/SKILL.md", agent)
        self.assertIn("不要默认加载完整 `dev-lc/SKILL.md`", agent)
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
        for forbidden in (
            "change_get_or_create", "change_put", "lifecycle_put", "artifact_put",
            "handoff_prepare", "handoff_acknowledge", "handoff_accept", "handoff_reject",
            "handoff_supersede", "invalidation_apply", "change_archive", "promotion_confirm",
        ):
            self.assertNotIn(f"mcp__dev_state__{forbidden}", allowed)


if __name__ == "__main__":
    unittest.main()
