from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = ROOT.parent


class DevCtxContractTests(unittest.TestCase):
    def test_context_artifact_family_and_eligibility_are_defined(self) -> None:
        package = (ROOT / "references" / "context-package.md").read_text(encoding="utf-8")
        artifacts = (ROOT / "references" / "context-artifacts.md").read_text(encoding="utf-8")
        self.assertIn("Eligible CTX", package)
        for token in (
            "type: implementation-context", "type: implementation-context-fact",
            "type: implementation-context-path", "type: implementation-context-gap",
        ):
            self.assertIn(token, package + artifacts)
        self.assertIn("blocking_for", artifacts)
        self.assertIn("freshness", artifacts)

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
