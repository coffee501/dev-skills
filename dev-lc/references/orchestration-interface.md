# 生命周期—调度接口

## 目的

本接口是 `dev-lc` 与 `dev-orch` 之间的最小稳定边界。`dev-lc` 是生命周期语义和状态权威；`dev-orch` 只消费
生命周期路线并管理执行任务。调度器无需默认读取完整 `dev-lc/SKILL.md`。

## 所有权

| 对象或决策 | 权威模块 | 调度器权限 |
| --- | --- | --- |
| `CHG`、阶段适用性和生命周期范围 | `dev-lc` | 只引用；缺失或变化时请求LC建立或重算 |
| `LCV`、阶段依赖、进入条件和门禁视图 | `dev-lc` | 只消费当前版本；不得增加、删除或改写阶段及硬依赖 |
| `HOF` 状态和接受/拒绝语义 | `dev-lc` 或有权限责任方 | 可转交和观察；不得把 `Prepared` 提升为 `Accepted` |
| `WIT`、会话内 `SWI`、Agent和尝试状态 | `dev-orch` | 创建、认领、停止和收敛 |
| 专业产物及其结论 | 对应专业 Skill | 只引用和检查返回包完整性，不重写内容 |
| 阶段门、风险接受和 `CHG Completed` | `dev-lc` 或有权限责任方 | 只引用确认结果，不自行判断或确认 |

## LC提供的路线快照

调度输入至少包含：

- `lifecycle_route_ref`：当前 `LCV-*` 版本；非持久化场景使用明确的 `LCV-PENDING-*` 快照。
- `route_version` 和输入摘要或指纹。
- 适用阶段及每个阶段的责任 Skill、硬依赖、进入条件、期望产物和停止条件。
- 有依据的不适用阶段。
- 当前阻塞、开放 `HOF`、失效影响和下一责任模块。
- 阶段门只读视图及其 `Suggested/Confirmed` 级别。

每个 `LCV.route` 节点至少包含稳定且唯一的 `node_id`、`stage`、`skill`、`applicability`、`dependencies`、`entry_conditions`、
`expected_outputs` 和 `stop_conditions`。`dependencies` 必须引用同一路线内的 `node_id` 并形成无环图；`NotApplicable`
节点必须说明 `applicability_reason`。`dev-cr` 节点标记为 `NotApplicable` 时还必须提供结构化
`applicability_decision`，其中 `owner` 是非空责任方，`basis`、`residual_risks` 和 `invalidates_when` 是非空字符串列表；不能只写笼统理由。
节点不得包含 `agent`、`parallel_groups`、`attempt`、`runtime_status` 或
`work_item_id`；这些字段属于ORCH执行投影。

开发闭环路线还必须保持以下语义约束：每个适用 `dev-impl` 节点必须沿依赖图到达一个对应的 `dev-cr` 节点；评审适用时
该节点为 `Applicable`，仅在项目政策允许且记录依据、责任和剩余风险时才可为 `NotApplicable`。正式G5的适用
`dev-val` 节点必须依赖全部适用 `dev-cr` 节点。ORCH按该路线自动分派已满足进入条件的评审任务，不依赖模型再次猜测
是否需要调用 `dev-cr`，也不得自行补造缺失的评审节点。

缺少当前路线快照时，`dev-orch` 应先调用或派发 `dev-lc` 建立路线；无法取得时停止权威任务图生成，只报告
`lifecycle_route_status: missing` 和恢复条件。

## ORCH生成的执行投影

`dev-orch` 可以在不改变生命周期语义的前提下生成：

- `coordination_mode` 和 `state_persistence`。
- `lifecycle_route_ref` 与 `route_version`。
- 每个路线节点对应的 `WIT/SWI`、Agent、尝试次数、运行状态和允许对象。
- 在硬依赖约束内的调度顺序和并行组。
- 执行阻塞、超时、取消、返回证据和待收敛结果。

`route-only` 只能输出基于当前 `lifecycle_route_ref` 的执行投影和任务包；不能生成新的权威阶段路线。

## 路线变化

出现新范围、阶段缺失、交接拒绝、输入失效或专业结论冲突时，`dev-orch`：

1. 停止受影响的未完成任务，保留其他独立分支。
2. 形成 `route_change_request`，记录触发证据、受影响路线版本、运行任务和建议重新评估范围。
3. 交给 `dev-lc` 产生后继 `LCV`；调度器不得直接改写原路线。
4. 只在收到新 `lifecycle_route_ref` 后重新编译受影响任务图。

## 完成语义

- `coordination_status: Completed` 只表示调度任务均已终止并完成结果收集。
- `lifecycle_status` 必须引用 `dev-lc` 的当前 `LCV` 或明确标记 `NotAssessed`。
- ORCH完成不得被表述为阶段门通过、`CHG Completed`、风险已接受或专业工作正确。

外置持久化时，`CHG/HOF/LCV` 只能保存LC或有权限责任方提供的版本；`WIT` 由ORCH管理。状态服务只保存对象，
不改变上述语义所有权。

宿主支持工具白名单时必须按能力隔离：ORCH仅获得状态读取、审计读取以及 `WIT/AGENT_RUN` 写工具，不得获得
`change_get_or_create/change_put/lifecycle_put/handoff_prepare/handoff_acknowledge/handoff_accept/handoff_reject/handoff_supersede/`
`artifact_put/invalidation_apply/change_archive/promotion_*`。
宿主无法限制单个MCP工具时，该运行模式只能视为受信任调度环境，并在结果中报告 `capability_isolation: prompt-only`；
不得宣称已实现强制生命周期权限隔离。
