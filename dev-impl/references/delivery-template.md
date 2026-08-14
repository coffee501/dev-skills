# 实现交付模板

只保留适用字段；未知内容明确标记待确认，不虚构编号、版本、责任人或证据。

## IMP

```yaml
protocol_version: DEV-SUITE-5.0
id: IMP-001
type: implementation
change: CHG-001
version: 1
kind: code | config | contract | migration | test-automation
status: Planned | InProgress | Blocked | Implemented | Reviewed | Integrated | Aborted | Superseded
applies_to: []
supersedes: []
sources: []
scope: []
preserved_behavior: []
changes: []
dependencies: []
verification: []
rollback: []
deviations: []
risks: []
evidence: []
owner: pending
updated_at: YYYY-MM-DDThh:mm:ss+08:00
```

`Blocked`补充 `blocked_from/reason/unblock_conditions`；`Superseded`补充后继编号。

## BUILD

```yaml
protocol_version: DEV-SUITE-5.0
id: BUILD-001
type: local-check-batch
change: CHG-001
version: 1
implementation: [IMP-001]
candidate_version: pending
sources: [IMP-001]
applies_to: []
supersedes: []
workspace: {repository: pending, directory: pending, dirty_summary: pending}
dependencies: {lockfiles: [], digest: pending}
environment: {os: pending, runtime: pending, tools: [], isolation: pending}
commands: []
artifacts: []
limitations: []
risks: []
evidence: []
owner: pending
status: Planned | Running | Passed | Failed | Blocked | Aborted
updated_at: YYYY-MM-DDThh:mm:ss+08:00
```

每条 `commands` 记录工作目录、完整命令或稳定引用、开始和结束时间、持续时间、退出码及结果摘要。不得包含凭据。

## HOF 摘要

按共享交接协议输出 `Prepared HOF`，至少包含 `from/to/reason/inputs/preserved_behavior/unresolved/invalidated/`
`expected_outputs/entry_conditions/owner`。面向 `dev-val` 时补充候选版本、环境、数据条件、测试入口、已知限制和
需要形成的 `RUN/EVD/GATE`；面向 `dev-rel` 时补充顺序、窗口、限速、观察、停止和恢复条件。
