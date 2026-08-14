# CTX 上下文包

## 标识与状态

- `CTX-001`：一定范围和版本的可复用As-Is上下文包。
- `CTXF-001`：单一事实或受控推断。
- `CTXP-001`：从入口到结果的观察实现路径。
- `CTXG-001`：未知、冲突、证据缺口或动态边界。

`CTX` 状态使用：

> `Draft → Ready → PotentiallyStale → Ready / Stale → Superseded`

`Ready`只针对声明范围。发现适用版本或来源可能变化但尚未完成语义判断时进入 `PotentiallyStale`；确认不受影响后
回到 `Ready`，确认结论不再适用后进入 `Stale`。新版本替代旧版本时记录 `Superseded`，不得覆盖历史。

## CTX 信封

```yaml
protocol_version: DEV-SUITE-5.0
id: CTX-001
type: implementation-context
change: none
version: 1
status: Draft | Ready | PotentiallyStale | Stale | Superseded
owner: pending
sources: []
applies_to: []
supersedes: []
purpose: []
scope: []
out_of_scope: []
revision: []
facts: []
paths: []
gaps: []
risks: []
evidence: []
invalidates_when: []
updated_at: YYYY-MM-DDThh:mm:ss+08:00
```

可复用项目基线使用 `change: none`；为特定变更调查时关联对应 `CHG`。`revision`记录每个仓库、契约、配置集和环境
证据的版本或摘要。未知版本必须显式标记，不能用当前时间代替。

## 最小内容

根据消费者需要选择，不强制生成空章节：

1. 范围、版本、目的、来源和新鲜度。
2. 仓库、模块、构建单元与运行单元。
3. 入口、契约、数据、事件、任务、配置、外部依赖和部署表面。
4. 关键 `CTXP` 及状态、数据、副作用和失败路径。
5. `CTXF` 事实索引及证据。
6. `CTXG` 未知、冲突、仓外和动态边界。
7. 对目标消费者的可依赖内容与禁止推断内容。

图不是必选产物。只有系统边界、依赖网络或执行顺序无法用简短表格清楚表达时才生成对应图。
