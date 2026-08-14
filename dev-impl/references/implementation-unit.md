# IMP 与 BUILD 模型

## IMP 实现单元

一个 `IMP`只承担一个主要实现目标。使用以下字段：

| 字段 | 要求 |
| --- | --- |
| `id` | 稳定 `IMP-001`，不得复用 |
| `change` | 引用现有正式或临时 `CHG` |
| `kind` | `code/config/contract/migration/test-automation` |
| `sources` | `DET/DDEC/DATA/API/EVT/JOB/CFG/AUT`及版本 |
| `scope` | 允许修改的模块、文件、符号和配置 |
| `preserved_behavior` | 必须保持的规则、契约和结果 |
| `changes` | 实际修改摘要，不写计划性空话 |
| `dependencies` | 前置 `IMP`、外部能力和顺序要求 |
| `verification` | 目标 `BUILD`检查与成功条件 |
| `rollback` | 恢复、禁用或前向修复方式 |
| `deviations` | 与批准设计的偏差和交接 |
| `risks` | 剩余风险、责任和失效条件 |
| `status` | 使用实现单元状态 |

实现单元状态主路径：

> `Planned → InProgress → Implemented → Reviewed → Integrated`

异常和替代路径：

> `Planned / InProgress → Blocked → 阻塞前状态`
>
> `Planned / InProgress / Blocked → Aborted`
>
> `Planned / InProgress / Blocked / Implemented / Reviewed → Superseded`

- 实际文件已经修改且目标检查完成后才能标记 `Implemented`。
- 只有存在独立代码评审证据时才能标记 `Reviewed`。
- 只有变更进入目标集成分支或等价集成基线时才能标记 `Integrated`。
- `Blocked`记录阻塞原因、受影响范围、解除条件和阻塞前状态；恢复后回到相应活动状态。
- `Aborted`表示停止且不计划继续；`Superseded`必须引用后继 `IMP`。二者均保留历史，不复用编号。

## 拆分原则

- 代码、契约、迁移和配置切换在具有不同顺序、恢复或验证方式时拆成不同 `IMP`。
- 一个小变更可以只有一个 `IMP`，不要为编号完整性过度拆分。
- 跨仓库、跨部署单元或不同责任团队默认拆分。
- `AUT`仍归 `dev-test`；测试代码实现使用 `IMP(kind=test-automation)`关联它。

## BUILD 本地检查批次

`BUILD`记录实现阶段检查，不是正式验证证据。至少包含：

| 字段 | 要求 |
| --- | --- |
| `id` | 稳定 `BUILD-001` |
| `change` | 关联 `CHG` |
| `implementation` | 关联 `IMP` |
| `candidate_version` | 提交、工作区摘要或产物版本 |
| `workspace` | 工作目录、仓库和脏工作区摘要 |
| `dependencies` | 关键锁文件或依赖摘要 |
| `environment` | OS、运行时、关键工具和隔离状态 |
| `commands` | 实际命令、开始和结束时间、持续时间、退出码和结果摘要 |
| `artifacts` | 构建物、报告、日志位置及适用的摘要或校验值 |
| `limitations` | 未运行项、Mock/沙箱/隔离数据集、环境差异和不可推广范围 |
| `status` | `Planned/Running/Passed/Failed/Blocked/Aborted` |

同一次批次重试保留首次失败。修改代码、依赖、配置、契约或测试断言后，旧 `BUILD`不得继续支撑新候选版本。

## 完成与证据边界

`BUILD Passed`只证明指定候选版本在记录环境中通过列出的本地检查。它不等于代码评审通过、`RUN/EVD/GATE`通过、可发布或生产稳定。
