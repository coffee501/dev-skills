---
name: dev-orch
description: 管理生命周期路线、门禁与交接，并调度跨多个 Dev Skills 的开发任务。
argument-hint: "[change objective, scope, constraints, and available inputs]"
disable-model-invocation: true
context: fork
agent: dev-orch
background: false
---

Coordinate the following change through the Dev Skills lifecycle:

$ARGUMENTS

Before acting, read `${CLAUDE_SKILL_DIR}/../../../dev-orch/AGENT.md` completely and treat it as the canonical cross-platform agent workflow.
Resolve its relative references from `${CLAUDE_SKILL_DIR}/../../../dev-orch`; the Claude command and Agent only map platform tools and invocation behavior.

If the task description is empty, return the exact invocation format and do not create or update lifecycle state:
`/dev-skills:dev-orch <change objective, scope, constraints, and available inputs>`

This forked command does not inherit the caller's conversation history. Use only the supplied arguments and cited repository or state evidence; if an essential prior decision is missing, report that gap before affected work.

Otherwise, pass the objective, scope, constraints, and available inputs to the `dev-orch` Agent. It actively selects and runs the applicable professional Skills, then reports progress, results, blockers, and next responsibility. Keep internal protocol JSON in the state service; specialist conclusions follow their own Skill contracts.
