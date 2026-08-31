# CTX 子制品契约

## 目录

- [公共规则](#公共规则)
- [CTXF 实现事实](#ctxf-实现事实)
- [CTXP 实现路径](#ctxp-实现路径)
- [CTXG 上下文缺口](#ctxg-上下文缺口)

正式上下文由一个 `CTX` 包和可独立引用、版本化、失效的 `CTXF/CTXP/CTXG` 子制品组成。子制品必须遵守
[统一产物信封](../../dev-lc/references/artifact-contract.md)，并通过 `parent_ctx` 归入上下文包。下游引用必须同时携带
`id` 和 `version`，不得只引用裸编号。

## 公共规则

- `sources` 记录检查过的上游产物或来源目录；`evidence` 只记录直接支撑本条结论的证据定位器。
- `applies_to` 绑定仓库、代码或契约版本、模块、配置组合和环境；未知值必须显式标记。
- 证据定位优先使用“仓库与版本 + 文件或机器契约节点 + 符号或配置键”；行号只作为辅助提示。
- 语义或适用范围发生变化时增加版本；含义被重新定义时创建后继编号并记录 `supersedes`，不得覆盖历史。
- `consumer_refs` 记录已知下游引用。若项目有统一制品索引，可仅记录索引位置，由 `dev-lc` 维护反向关系。
- `Ready` 的事实或路径必须为 `Current`；进入 `PotentiallyStale/Stale` 时同步更新同名新鲜度。`Draft` 可以为
  `Unassessed`，`Superseded` 保留被替代前的新鲜度以供审计。

## CTXF 实现事实

```yaml
protocol_version: DEV-SUITE-7.1
id: CTXF-001
type: implementation-context-fact
change: none | CHG-001
version: 1
status: Draft | Ready | PotentiallyStale | Stale | Superseded
owner: dev-ctx
parent_ctx: { id: CTX-001, version: 1 }
sources: []
applies_to: []
supersedes: []
statement: ""
truth_scope: implementation | runtime | business-claim | inference
claim_status: Observed | Corroborated | Inferred
freshness: Unassessed | Current | PotentiallyStale | Stale
risks: []
evidence: []
invalidates_when: []
consumer_refs: []
updated_at: YYYY-MM-DDThh:mm:ss+08:00
```

`CTXF` 只承载可陈述的事实或受控推断。未知、冲突和无法观察的结论必须建立 `CTXG`，而不是创建
`Unknown/Conflicted CTXF`。

## CTXP 实现路径

```yaml
protocol_version: DEV-SUITE-7.1
id: CTXP-001
type: implementation-context-path
change: none | CHG-001
version: 1
status: Draft | Ready | PotentiallyStale | Stale | Superseded
owner: dev-ctx
parent_ctx: { id: CTX-001, version: 1 }
sources: []
applies_to: []
supersedes: []
scenario: ""
entry: ""
preconditions: []
steps: []
state_and_data_changes: []
side_effects: []
transaction_and_consistency_boundaries: []
failure_and_recovery: []
observable_results: []
coverage_boundary: []
freshness: Unassessed | Current | PotentiallyStale | Stale
risks: []
evidence: []
invalidates_when: []
consumer_refs: []
updated_at: YYYY-MM-DDThh:mm:ss+08:00
```

每个步骤应注明参与模块、同步或异步关系、关键输入输出以及对应证据。路径在动态或仓外边界中断时，通过
`coverage_boundary` 指明中断点，并关联对应 `CTXG`。

## CTXG 上下文缺口

```yaml
protocol_version: DEV-SUITE-7.1
id: CTXG-001
type: implementation-context-gap
change: none | CHG-001
version: 1
status: Open | Resolved | Superseded
owner: dev-ctx
parent_ctx: { id: CTX-001, version: 1 }
sources: []
applies_to: []
supersedes: []
gap_type: Unknown | Conflicted | EvidenceGap | DynamicBoundary | ExternalBoundary | Unobservable
statement: ""
checked_scope: []
related_facts: []
related_paths: []
blocking_for: []
affected_scope: []
needed_evidence: []
responsible_party: pending
resolution: null
resolution_evidence: []
risks: []
evidence: []
consumer_refs: []
updated_at: YYYY-MM-DDThh:mm:ss+08:00
```

`Resolved` 必须记录解决结论和证据；不得删除旧缺口。`blocking_for` 使用消费者和具体分支，不用全局阻塞代替局部
影响。来源冲突时，`related_facts` 引用各自可成立的事实，`CTXG` 负责表达冲突本身及其解除条件。
