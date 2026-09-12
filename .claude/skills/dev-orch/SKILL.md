---
name: dev-orch
description: 依据 dev-lc 确定的生命周期路线，调度并收敛跨多个 Dev Skills 的开发任务。
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

Otherwise, apply the canonical Skill plus the `dev-orch` Agent's Claude-specific tool and external-state mapping. Return the lifecycle route reference, execution projection, coordination state, blockers, responsibility boundaries, and next action. Do not alter lifecycle semantics; do not implement specialist work in the orchestrator.
