# 生命周期控制产物契约

## 通用信封

新建 `CHG/HOF/LCV` 使用 `DEV-SUITE-8.0` 统一信封，7.0和7.1开发阶段存量产物继续兼容：`protocol_version`、`id`、`type`、`change`、`version`、
`status`、`owner`、`sources`、`applies_to`、`risks`、`evidence`、`updated_at`。`supersedes`按需提供。

## CHG

类型为 `lifecycle-change`，ID使用 `CHG-*`。至少包含：

- `objective`、`scope`、`non_scope`、`change_types`。
- `route`：适用阶段、硬依赖、进入条件、期望产物、停止条件，以及跳过阶段及依据；不包含Agent、并行组、尝试次数或运行状态。
- `gates`：G0至G5适用视图，不把所有阶段机械设为必需。
- `handoff_refs`、`open_handoffs`、`artifact_refs`、`completion`。

状态使用 `Draft → Active → Completed / Cancelled / Superseded`。`change`必须等于自身ID。`Completed`必须具有责任方确认、
适用阶段门结论、未决交接处置和失效影响摘要；Skill不得仅凭所有文档存在而关闭变更。

## HOF

类型为 `handoff`，ID使用 `HOF-*`。除共享 [交接协议](handoff-contract.md) 字段外，保留接收或拒绝记录。

允许 `Prepared → Acknowledged / Accepted / Rejected / Superseded`、`Acknowledged → Accepted / Rejected / Superseded`、
`Accepted / Rejected → Superseded`。来源只能创建 `Prepared`；`Acknowledged` 是可选收件留痕，8.0使用时要求
`acknowledgement.acknowledged_by/acknowledged_at`。`Accepted` 要求 `acceptance.accepted_by/accepted_at`，`Rejected` 要求
`rejection.reason/rejected_by/rejected_at`，8.0 `Superseded` 要求 `supersession.reason/superseded_by/superseded_at`。没有接收证据不得推断接受。

## LCV

类型为 `lifecycle-view`，ID使用 `LCV-*`，表示某个时间点的不可变生命周期快照。至少包含：

- `chg_ref`、`stages`、`gates`、`artifact_refs`。
- `open_handoffs`、`invalidation`、`blockers`。
- `next_responsibility`、`confirmation_scope`。
- 供ORCH调度使用的8.0 `LCV` 增加 `route`：每个节点包含稳定且唯一的 `node_id`，以及
  `stage/skill/applicability/dependencies/entry_conditions/expected_outputs/stop_conditions`；`dependencies` 只引用同一路线中的
  `node_id`，依赖图必须无环。`NotApplicable` 节点还必须提供 `applicability_reason`。评审节点不适用时还必须提供
  `applicability_decision: {basis, owner, residual_risks, invalidates_when}`；`owner`为非空字符串，其余三项为非空字符串列表。节点不包含Agent、并行组、
  尝试次数、运行状态或工作项编号。无需调度的普通生命周期快照可以省略该字段。
- 每个适用 `dev-impl` 节点必须沿依赖图到达对应 `dev-cr` 节点；正式G5的适用 `dev-val` 节点必须依赖全部适用
  `dev-cr` 节点。评审不适用只能由带依据的 `NotApplicable` 评审节点表达，不能通过删除评审节点绕过G4。

`LCV.route` 是 `dev-orch` 的权威生命周期路线输入。ORCH只可在硬依赖内生成执行投影；路线语义变化必须由
`dev-lc` 产生后继 `LCV`，不能覆盖当前快照。

状态使用 `Current → Superseded`。新的汇总替代旧视图，不覆盖旧快照。`LCV`只汇总专业产物，不改变它们的状态或权威。

## 校验

```text
python scripts/validate_lifecycle_artifact.py <artifact.json>
python scripts/validate_suite.py
```

第一个命令检查单个控制面产物，第二个命令检查整套Skill的结构和跨模块契约。两者都不接受风险、确认阶段门或推进外部系统状态。
