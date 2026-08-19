# 生命周期控制产物契约

## 通用信封

`CHG/HOF/LCV` 使用 `DEV-SUITE-7.0` 统一信封：`protocol_version`、`id`、`type`、`change`、`version`、
`status`、`owner`、`sources`、`applies_to`、`risks`、`evidence`、`updated_at`。`supersedes`按需提供。

## CHG

类型为 `lifecycle-change`，ID使用 `CHG-*`。至少包含：

- `objective`、`scope`、`non_scope`、`change_types`。
- `route`：适用阶段、跳过阶段及依据。
- `gates`：G0至G7适用视图，不把所有阶段机械设为必需。
- `handoff_refs`、`open_handoffs`、`artifact_refs`、`completion`。

状态使用 `Draft → Active → Completed / Cancelled / Superseded`。`change`必须等于自身ID。`Completed`必须具有责任方确认、
适用阶段门结论、未决交接处置、运行/发布退出项和失效影响摘要；Skill不得仅凭所有文档存在而关闭变更。

## HOF

类型为 `handoff`，ID使用 `HOF-*`。除共享 [交接协议](handoff-contract.md) 字段外，保留接收或拒绝记录。

状态使用 `Prepared → Acknowledged → Accepted / Rejected → Superseded`。来源只能创建 `Prepared`；`Accepted`要求
`acceptance.accepted_by/accepted_at`，`Rejected`要求 `rejection.reason/rejected_by/rejected_at`。没有接收证据不得推断接受。

## LCV

类型为 `lifecycle-view`，ID使用 `LCV-*`，表示某个时间点的不可变生命周期快照。至少包含：

- `chg_ref`、`stages`、`gates`、`artifact_refs`。
- `open_handoffs`、`invalidation`、`blockers`。
- `next_responsibility`、`confirmation_scope`。

状态使用 `Current → Superseded`。新的汇总替代旧视图，不覆盖旧快照。`LCV`只汇总专业产物，不改变它们的状态或权威。

## 校验

```text
python scripts/validate_lifecycle_artifact.py <artifact.json>
python scripts/validate_suite.py
```

第一个命令检查单个控制面产物，第二个命令检查整套Skill的结构和跨模块契约。两者都不接受风险、确认阶段门或推进外部系统状态。
