---
name: dev-orch
description: Start the Dev Skills lifecycle orchestrator for a multi-stage backend or system-integration change.
argument-hint: "[change objective, scope, constraints, and available inputs]"
disable-model-invocation: true
context: fork
agent: dev-orch
background: false
---

Coordinate the following change through the Dev Skills lifecycle:

$ARGUMENTS

Before acting, read `${CLAUDE_SKILL_DIR}/../../../dev-orch/SKILL.md` completely and treat it as the canonical cross-platform orchestration workflow.
Resolve its relative references from `${CLAUDE_SKILL_DIR}/../../../dev-orch`; the Claude command and Agent only map platform tools and invocation behavior.

If the task description is empty, return the exact invocation format and do not create or update lifecycle state:
`/dev-skills:dev-orch <change objective, scope, constraints, and available inputs>`

Otherwise, apply the canonical Skill plus the `dev-orch` Agent's Claude-specific tool and external-state mapping. Return the current route, state, blockers, responsibility boundaries, and next action; do not implement specialist work in the orchestrator.
