# CTX 上下文包

## 标识与状态

- `CTX-001`：一定范围和版本的可复用As-Is上下文包。
- `CTXF-001`：单一事实或受控推断。
- `CTXP-001`：从入口到结果的观察实现路径。
- `CTXG-001`：未知、冲突、证据缺口或动态边界。

四类对象都属于正式产物。`CTXF/CTXP/CTXG` 的完整字段见
[context-artifacts.md](context-artifacts.md)，不得只以无版本列表项代替正式子制品。

`CTX` 状态使用：

> `Draft → Ready → PotentiallyStale → Ready / Stale`

> `Ready / PotentiallyStale / Stale → Superseded`

`Ready`只针对声明范围。发现适用版本或来源可能变化但尚未完成语义判断时进入 `PotentiallyStale`；确认不受影响后
回到 `Ready`，确认结论不再适用后进入 `Stale`。任何现存状态被新版本替代时都可进入 `Superseded`，不得覆盖历史。

## CTX 信封

```yaml
protocol_version: DEV-SUITE-7.1
id: CTX-001
type: implementation-context
change: none
version: 1
status: Draft | Ready | PotentiallyStale | Stale | Superseded
owner: dev-ctx
sources: []                    # 已检查的来源或上游产物
applies_to:
  repositories: []
  contracts: []
  configurations: []
  environments: []
supersedes: []
purpose: []
scope: []
out_of_scope: []
revision:
  repositories: []            # URL或根目录、commit、branch、dirty状态
  contracts: []               # 名称、版本或摘要
  configurations: []          # 配置集、版本或摘要，不记录密钥值
  generated_sources: []       # 生成源和生成版本
  deployments: []             # 部署清单或运行单元版本
  runtime_observations: []    # 环境、时间窗口和版本
  indexes: []                 # 工具、仓库、目标commit和索引时间
facts: []                     # { id: CTXF-001, version: 1 }
paths: []                     # { id: CTXP-001, version: 1 }
gaps: []                      # { id: CTXG-001, version: 1 }
risks: []
evidence: []                  # 支撑包级结论的证据定位器
invalidates_when: []
consumer_refs: []             # 或统一制品索引位置
updated_at: YYYY-MM-DDThh:mm:ss+08:00
```

可复用项目基线使用 `change: none`；为特定变更调查时关联对应 `CHG`。`revision`记录每个仓库、契约、配置集和环境
证据的版本或摘要。未知版本必须显式标记，不能用当前时间代替。`sources` 表示调查目录，`evidence` 表示直接支撑
结论的定位器，两者不得混用。

## 临时视图与正式上下文

- 单次回答“当前如何实现”时默认输出临时上下文视图，不分配正式编号、版本或状态，也不作为后续可直接复用的基线。
- 用户要求建立基线、跨两个以上阶段复用、需要失效传播或正式交接时，输出正式 `CTX` 及所需子制品。
- 临时视图升级为正式 `CTX` 时必须重新确认范围、修订、新鲜度、证据和失效条件，不能只补一个编号。

## 可消费资格与聚合规则

下游只消费满足以下条件的 `Eligible CTX`：

1. `CTX.status` 为 `Ready`，且 `applies_to` 与目标范围、版本、配置和环境匹配。
2. 当前消费者最小充分性所需的 `CTXF/CTXP` 均为 `Ready + Current`。
3. 不存在 `blocking_for` 命中当前消费者及分支的开放 `CTXG`。
4. 关键动态边界、仓外依赖、未覆盖范围和失效条件已经记录。

非关键子制品过期只影响引用它的消费者分支，不自动使整个包失效。关键子制品进入 `PotentiallyStale/Stale`，或无法
确定其关键性时，父 `CTX` 进入 `PotentiallyStale`，完成语义评估后再恢复 `Ready` 或进入 `Stale`。

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
