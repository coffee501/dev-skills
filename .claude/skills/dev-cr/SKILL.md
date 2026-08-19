---
name: dev-cr
description: Independently review backend and integration implementations, pull requests, commits, patches, contracts, configuration, migrations, events, jobs, and test automation. Use for findings, verdicts, pre-merge risk assessment, and remediation re-review.
disable-model-invocation: false
---

# Claude Code Adapter

Before acting, read `${CLAUDE_SKILL_DIR}/../../../dev-cr/SKILL.md` completely and follow it as the canonical workflow.
Treat `${CLAUDE_SKILL_DIR}/../../../dev-cr` as the Skill root and resolve every relative reference from there.
This adapter changes discovery and invocation policy only; do not add, remove, or reinterpret core workflow rules.
