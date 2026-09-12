from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = ROOT.parent


class DevHldContractTests(unittest.TestCase):
    def test_hld_owns_architecture_without_absorbing_detail_or_execution(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for token in ("DEC", "MOD", "FLOW", "VAL", "系统边界", "模块职责", "dev-lld", "dev-test"):
            self.assertIn(token, skill)
        for boundary in ("字段级", "类级", "完整测试步骤", "自动化脚本"):
            self.assertIn(boundary, skill)
        self.assertIn("复杂度与拆分治理", skill)

    def test_markdown_links_resolve_inside_suite(self) -> None:
        for path in ROOT.rglob("*.md"):
            for target in re.findall(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)", path.read_text(encoding="utf-8")):
                if re.match(r"^[a-z][a-z0-9+.-]*:", target):
                    continue
                resolved = (path.parent / target).resolve()
                self.assertTrue(resolved.is_relative_to(SUITE_ROOT.resolve()), f"link escapes suite: {path} -> {target}")
                self.assertTrue(resolved.exists(), f"broken link: {path} -> {target}")


if __name__ == "__main__":
    unittest.main()
