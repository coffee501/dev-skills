from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = ROOT.parent


class DevLldContractTests(unittest.TestCase):
    def test_lld_defines_implementation_inputs_without_claiming_execution(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for token in ("DET", "DDEC", "DATA", "MIG", "API", "EVT", "JOB", "CFG", "DVAL"):
            self.assertIn(token, skill)
        self.assertIn("不得自行宣布验证通过", skill)
        self.assertIn("完整测试用例交接给 `dev-test`", skill)
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
