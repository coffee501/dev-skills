---
name: dev-ctx
description: Build or refresh evidence-backed As-Is context for existing backend services and integrations. Use for project understanding, reusable current-state baselines, execution-flow tracing, impact discovery, and downstream design context.
disable-model-invocation: true
---

# Claude Code Adapter

Before acting, read `${CLAUDE_SKILL_DIR}/../../../dev-ctx/SKILL.md` completely and follow it as the canonical workflow.
Treat `${CLAUDE_SKILL_DIR}/../../../dev-ctx` as the Skill root and resolve every relative reference from there.
This adapter changes discovery and invocation policy only; do not add, remove, or reinterpret core workflow rules.
