---
name: dev-rel
description: Execute authorized backend and integration releases, including preflight, deployment, migration, progressive rollout, observation, stop decisions, rollback, recovery, and production handoff. Use for release readiness, dry runs, deployment, canaries, and release recovery.
disable-model-invocation: true
---

# Claude Code Adapter

Before acting, read `${CLAUDE_SKILL_DIR}/../../../dev-rel/SKILL.md` completely and follow it as the canonical workflow.
Treat `${CLAUDE_SKILL_DIR}/../../../dev-rel` as the Skill root and resolve every relative reference from there.
This adapter changes discovery and invocation policy only; do not add, remove, or reinterpret core workflow rules.
