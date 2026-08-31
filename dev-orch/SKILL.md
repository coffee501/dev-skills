---
name: dev-orch
description: "Coordinate multi-stage Dev Skills work for backend services and system integrations across requirements, design, frontend interface alignment, implementation, review, test, validation, release, and operations. Use when the user explicitly invokes $dev-orch or requests end-to-end delivery, migration, incident follow-up, resumable lifecycle coordination, or work spanning three or more specialist Skills. Route one-stage work directly. Operate as a control plane: delegate specialist work, preserve authorization boundaries, and do not implement specialist outputs in the orchestrator."
---

# Dev ORCH

协调跨多个 `dev-*` Skill 的工作路线、依赖、并行任务、交接、失效和结果收敛。`dev-orch` 是调度控制面，不是需求、设计、实现、评审、验证、发布或运维责任人。

本 Skill 设计为显式调用：Codex 使用 `$dev-orch`；Claude Code 使用 `/dev-skills:dev-orch` 或 `dev-orch` Agent。平台入口共享本文件，不复制调度语义。

## 读取控制协议

开始前完整读取 [dev-lc](../dev-lc/SKILL.md)，再按任务需要读取：

- 多阶段路由、任务包、收敛和恢复：[调度协议](../dev-lc/references/orchestration-protocol.md)
- `CHG/HOF/LCV/WIT` 外置持久化与项目写入边界：[外置状态契约](../dev-lc/references/external-state-contract.md)
- Codex、Claude Code 与无子代理宿主的工具映射：[平台调度映射](references/platform-mapping.md)
- 输入或产物版本发生变化：[失效传播规则](../dev-lc/references/invalidation-rules.md)

套件协议不可用时，只能根据当前输入给出局部路线和任务包；不得宣称正式 `CHG/HOF/LCV`、阶段门或持久化状态已经建立。

## 选择最小运行模式

| 模式 | 条件 | 行为 |
| --- | --- | --- |
| `direct` | 单一专业阶段，或简单双阶段且没有协调价值 | 路由到相应 Skill，不创建调度任务图 |
| `route-only` | 用户只要求规划；子代理不可用；或任务要求可恢复状态但状态服务不可用 | 输出路线、任务包、阻塞和授权缺口，不假装已经执行 |
| `session-coordinate` | 用户要求本次会话实际推进，原生子代理可用，但外置状态服务不可用 | 在当前会话内协调；明确不可恢复，不创建项目内状态 |
| `durable-coordinate` | 用户要求实际推进，原生子代理和符合契约的外置状态服务均可用 | 以版本化 `CHG/HOF/LCV/WIT` 协调和恢复 |

不要因为用户使用 `$dev-orch` 就机械运行全部 Skill。预计跨三个以上专业阶段、需要并行、迁移、失效传播、反复交接或中断恢复时才进入协调模式。

## 建立调度上下文

1. 识别目标、范围、非范围、变更类型、完成条件和授权边界。
2. 复用权威 `CHG`；没有权威登记时只使用临时编号并说明局部性。
3. 核对已有需求、设计、实现、测试、证据、发布和运行产物的版本与适用范围。
4. 识别可复用基线、开放 `HOF`、失效影响、P0阻塞和下一责任模块。
5. 选择最短充分路线以及可以安全并行的节点。

聊天记录可以提供线索，但不能替代仓库事实、正式产物、验证证据、状态服务或授权记录。

## 协调专业工作

进入协调模式时，先确认系统、开发者、仓库 `AGENTS.md` 和宿主策略允许使用子代理；任何更高优先级限制都覆盖本 Skill。若不允许，切换 `route-only`，不得规避策略。随后：

1. 为每个节点创建最小任务包：目标 Skill、输入版本、范围、允许修改对象、保持项、期望产物、验证方式、停止条件和阻塞上报条件。
2. 每个子代理只拥有一个明确专业责任或互不冲突的文件范围；不得让多个子代理无边界修改同一对象。
3. 仅并行没有硬依赖、使用同一有效输入版本且不会争用同一责任对象的任务。
4. 优先续接已有子代理；输入失效时先停止受影响分支，再按新版本重新派发。
5. 专业结果返回后只做控制面检查：身份、版本、范围、证据、风险、交接和下游输入是否有效。
6. 内容正确性由相应专业 Skill 负责；调度器不重写专业结论，不替代代码评审或验证。
7. 子代理失败、超时或交接被拒绝时保留证据和原因，只重新规划受影响分支，禁止无界重试。

`session-coordinate` 不创建正式 `WIT`。使用会话内 `SWI-001` 任务包，至少包含目标 Skill、输入摘要/指纹、范围、责任对象、
期望输出、停止条件和状态；编号只在当前会话内有效。进入 `durable-coordinate` 时再由状态服务创建正式 `WIT`，不得把 `SWI` 冒充已持久化对象。

Codex 中使用原生子代理完成独立专业任务；不要为子任务创建用户可见的新任务或线程。Claude Code 中使用已注册 `dev-orch` Agent 的专业 Agent 调度能力。具体工具名称和降级规则读取平台映射。

## 保持权限和状态边界

- 调度器自身不编写专业产物、不修改业务仓库、不执行测试、发布或生产命令；实际工作交给对应专业 Skill 上下文。
- 子代理只能执行用户已授权范围内的普通阶段工作；真实数据、外部系统、副作用、发布和生产操作仍需到达目标边界时的精确授权。
- 不把 `Prepared` 当成 `Accepted`，不把 `Suggested` 当成 `Confirmed`，不把本地检查当成正式 `EVD/GATE`。
- 中间状态、草稿、任务运行记录和日志不得写入业务项目。
- `session-coordinate` 只能依赖当前会话内状态，必须报告 `state_persistence: none`；不得伪造可恢复性。
- 只有符合外置状态契约的服务可支撑 `durable-coordinate`。状态服务不可用时不得自行创建替代数据库或目录。

## 停止与完成

以下情况停止受影响分支：输入失效、责任冲突、缺少关键业务或设计决策、达到子代理深度/并发限制、授权不足、用户撤回范围，或继续工作会造成未授权副作用。独立且输入可靠的分支可以继续。

只有适用路线均取得可验证结果、开放交接和阻塞已处理、输入版本仍有效，且需要的正式确认来自有权责任方时，才能报告生命周期完成。调度器只能汇总证据，不能自行接受阶段门、风险或发布。

## 输出

每轮保持简洁并提供：

- `mode` 与 `state_persistence`
- `CHG` 或临时变更标识
- 当前路线/任务图以及串行与并行关系
- 已完成、运行中、阻塞和失效分支
- 开放授权、风险和交接
- 下一责任模块、恢复条件和停止条件

单阶段请求只给出直接路由；不要为了展示调度能力而生成空的生命周期报告。
