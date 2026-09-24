# 生命周期路线与执行投影契约

本契约约束 `dev-orch` 内部的两个动作：先依据证据建立版本化生命周期路线，再按当前路线生成运行时任务图。`dev-state` 保存对象，不作语义判断；专业 Skill 保持内容责任。

## 权威对象与责任

| 对象或决策 | 责任 |
| --- | --- |
| `CHG`、阶段适用性、生命周期范围、`LCV` 和阶段门评估 | `dev-orch`，依据专业产物与责任方证据 |
| `HOF` 接收或拒绝 | 目标责任方决定；`dev-orch` 只记录有证据的状态 |
| `WIT`、会话内 `SWI`、Agent 和尝试状态 | `dev-orch` |
| 专业产物及其结论 | 对应专业 Skill |
| 风险接受、阶段门 `Confirmed`、`CHG Completed` | 有权限责任方确认；`dev-orch` 记录，不代为批准 |

## 路线快照

当前路线使用 `lifecycle_route_ref`、`route_version` 和输入摘要或指纹。每个 `LCV.route` 节点至少有稳定且唯一的 `node_id`、`stage`、`skill`、`applicability`、`dependencies`、`entry_conditions`、`expected_outputs` 和 `stop_conditions`。`dependencies` 只引用同一路线内的 `node_id`，依赖图必须无环图。`NotApplicable` 节点说明 `applicability_reason`。

评审节点标记为 `NotApplicable` 时，还须提供 `applicability_decision`，包含非空 `owner` 和非空 `basis`、`residual_risks`、`invalidates_when` 列表。每个适用 `dev-impl` 节点必须沿依赖图到达对应 `dev-cr` 节点；适用 `dev-val` 的正式 G5 节点依赖全部适用 `dev-cr` 节点。符合条件的候选由调度动作自动分派独立评审任务。

路线节点不得含 `agent`、`parallel_groups`、`attempt`、`runtime_status` 或 `work_item_id`；这些属于执行投影。若输入缺失，使用明确的 `LCV-PENDING-*` 草案；依据不足时报告 `lifecycle_route_status: missing`，不得生成权威任务图。

## 执行投影

`dev-orch` 从当前路线生成 `WIT/SWI`、Agent、尝试次数、运行状态、串并行关系与停止条件。不得在编译任务图时临时增加、删除或改写阶段、硬依赖或阶段门；如需变化，先依据证据评估 `route_change_request`，创建后继 `LCV` 并保留旧版本，再重新编译受影响任务。

输入失效、交接拒绝或范围变化时，先停止受影响任务，再评估失效与路线。`route-only` 可以建立路线及只读执行投影，不声称专业工作已经执行。状态服务不可用时不伪造持久化引用。

## 完成语义与能力边界

`coordination_status: Completed` 只表示任务均已终止并完成结果收集；`lifecycle_status` 引用当前 `LCV` 或标记 `NotAssessed`。调度完成不能推出阶段门通过、风险接受或 `CHG Completed`。

支持工具白名单时，授予 `dev-orch` 必要的 `CHG/HOF/LCV/WIT` 读写工具；不得借此代写专业产物或绕过责任方确认。仅有提示词隔离的宿主须标记 `capability_isolation: prompt-only` 并保留明确权限缺口。
