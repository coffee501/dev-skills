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
        self.assertIn("套件协议不可用", skill)

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

    def test_claude_adapters_reference_canonical_core(self) -> None:
        command = (SUITE_ROOT / ".claude" / "skills" / "dev-orch" / "SKILL.md").read_text(encoding="utf-8")
        agent = (SUITE_ROOT / ".claude" / "agents" / "dev-orch.md").read_text(encoding="utf-8")
        self.assertIn("../../../dev-orch/SKILL.md", command)
        self.assertIn("../../dev-orch/SKILL.md", agent)


if __name__ == "__main__":
    unittest.main()
