# 运行产物契约

## 通用信封

JSON产物至少包含：

| 字段 | 说明 |
| --- | --- |
| `protocol_version` | Dev体系或本地协议版本 |
| `id` | 类型前缀编号；独立模式可用 `*-PENDING-*` |
| `type` | `operations-runbook / incident / root-cause-analysis / corrective-preventive-action` |
| `change` | 关联 `CHG` 或临时变更标识 |
| `version` | 产物版本 |
| `status` | 对应对象状态 |
| `owner` | 责任角色，不强制个人信息 |
| `sources` | 上游产物及版本或已检查来源 |
| `applies_to` | 适用服务、数据、环境、版本或事故范围 |
| `risks` | 未决风险、接受信息和失效条件 |
| `evidence` | 可复核证据编号或原始定位器 |
| `updated_at` | 带时区ISO-8601时间 |

引用正式产物时优先使用 `ID@version`，并保留来源和适用范围。没有共享治理协议时标记本地/临时，不伪造正式状态。

## RUNBOOK

类型 `operations-runbook`，ID前缀 `RUNBOOK-`。最低字段：

- `objective`、`triggers`、`scope`、`non_applicable`。
- `preconditions`、`target_resolution`、`permissions`。
- `steps`，每步包含动作、预期观察和失败/停止处理。
- `stop_conditions`、`recovery`、`verification`。
- `evidence`、`escalation`、`freshness`。

`Ready` 必须有非空评审/演练依据、复审日期、停止条件和恢复方式。

## INC

类型 `incident`，ID前缀 `INC-`。最低字段：

- `detected_at`、项目事故 `severity` 或明确 `unassigned`。
- `impact`、`scope`、`current_state`。
- `timeline`、`actions`、`communications`、`evidence`。
- `recovery_criteria`、`observation`、`residual_risks`。
- `release_refs`、`runbook_refs`、`rca_refs`、`capa_refs`（可为空）。

`Recovered` 必须包含非空业务和技术恢复信号、观察窗口和结论限制。`Closed` 还要有关闭权限记录及RCA/CAPA处置。

## RCA

类型 `root-cause-analysis`，ID前缀 `RCA-`。最低字段：

- `incident_refs`、`impact_summary`、`timeline_refs`。
- `facts`、`hypotheses`、`causal_chain`。
- `contributing_factors`、`control_failures`、`detection_response_gaps`。
- `excluded_paths`、`open_questions`、`evidence`、`limitations`。
- `capa_refs`、`review`。

`Accepted` 必须有评审和接受权限记录；因果链不能以空证据或浅层标签通过。

## CAPA

类型 `corrective-preventive-action`，ID前缀 `CAPA-`。最低字段：

- `incident_refs`、`rca_refs`、`action_type`。
- `objective`、`owner_role`、`due_at`、`route_to`。
- `implementation_refs`、`verification`、`residual_risk`。

`Verified` 必须有通过的验证结果和证据；`Closed` 还需关闭权限记录。`route_to`用于交接，不表示本 Skill 自动启动下游流程。

## 时间线与动作

时间线条目至少包含 `occurred_at`、`recorded_at`、`kind`、`source`、`content` 和 `evidence_refs`。生产动作至少包含目标、授权引用、执行者角色、开始/结束时间、实际动作、结果、前后状态和停止条件检查。

## 验证器

使用：

```text
python scripts/validate_ops_artifact.py <artifact.json>
```

校验器只检查最低结构、状态和少量跨字段不变量，不证明Runbook安全、生产动作获批、服务确已恢复、RCA因果有效或CAPA可以关闭。
