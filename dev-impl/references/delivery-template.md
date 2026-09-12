# 实现交付模板

只保留适用字段；未知内容明确标记待确认，不虚构编号、版本、责任人或证据。

## IMP

```yaml
protocol_version: DEV-SUITE-8.0
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
review_refs: []
owner: pending
updated_at: YYYY-MM-DDThh:mm:ss+08:00
```

`Blocked`补充 `blocked_from/reason/unblock_conditions`；`Superseded`补充后继编号。

## BUILD

```yaml
protocol_version: DEV-SUITE-8.0
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

## 实现交付摘要（人类可读只读投影）

完整实现、跨多个 `IMP` 的候选或准备 `dev-cr` 交接时，按以下结构生成 Markdown、HTML 或等价可读摘要。局部修改允许在
当前回复中使用精简结构。摘要必须绑定不可变来源，不建立新的正式产物类型、编号、状态、owner或批准结论；来源变化后
旧摘要失效并应重新生成。`IMP/BUILD`、实际差异与摘要冲突时，以权威来源为准。

```markdown
# 实现交付摘要

> 来源：IMP-001@v1、IMP-002@v1、BUILD-001@v1
> 候选：提交、工作区摘要或制品版本
> 适用范围：仓库、模块或变更范围
> 生成时间：带时区时间
> 性质：IMP/BUILD 与实际差异的只读投影

## 目标与范围
- 变更目标和非目标
- 已实现、未实现及明确排除范围

## 需求与设计落实
| 需求/设计引用 | IMP | 文件或符号 | 已实现行为 |
| --- | --- | --- | --- |

## 实际修改与行为
- 关键文件、符号和实现单元
- 可观察行为变化
- 必须保持且已经保持的行为

## 契约与工程影响
- API、事件、Schema、数据、配置、迁移、任务、依赖和测试自动化影响
- 兼容、恢复、清理和失效传播

## 本地检查
| BUILD | 命令或检查 | 结果 | 限制 |
| --- | --- | --- | --- |

## 偏差、限制与剩余风险
- 设计偏差及对应 HOF
- 未运行检查、环境限制、剩余风险和失效条件

## 审查与验证交接
- dev-cr 需要检查的候选、敏感边界和重点风险
- dev-val 需要执行的测试入口、环境、数据条件和验证要求
```

摘要不得把 `Implemented` 写成 `Reviewed`，不得把 `BUILD Passed` 写成 `REV Approved` 或 `GATE Pass`，也不得复制完整源码、
原始日志或可以直接引用的机器契约。只保留帮助审查者和后续责任方理解候选所需的最小信息。

## HOF 摘要

按共享交接协议输出 `Prepared HOF`，至少包含 `from/to/reason/inputs/preserved_behavior/unresolved/invalidated/`
`expected_outputs/entry_conditions/owner`。先面向 `dev-cr` 补充候选身份、实现范围、设计依据、构建结果、实现交付摘要位置
及其 `IMP/BUILD` 来源、敏感边界和需要形成的
`REV`；评审批准后面向 `dev-val` 补充 `REV` 引用、候选版本、环境、数据条件、测试入口、已知限制和需要形成的
`RUN/EVD/GATE`；需要提供给套件外部交付流程时，补充顺序、窗口、限速、观察、停止和恢复条件。
