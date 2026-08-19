# 运行治理模型

## 对象与权威

| 对象 | 用途 | 本 Skill 权限 |
| --- | --- | --- |
| `RUNBOOK` | 运行或人工处置手册 | 创建、复审、建议状态 |
| `INC` | 事故、影响、动作和恢复时间线 | 创建、维护、建议状态 |
| `RCA` | 证据支持的因果分析 | 创建、维护、建议接受 |
| `CAPA` | 纠正与预防措施 | 创建、跟踪、建议验证/关闭 |
| `REL/DEP/MIGRUN/OBS` | 计划发布事实 | 只引用，由 `dev-rel` 或外部系统维护 |
| `EVD/GATE` | 正式验证事实 | 只引用，由 `dev-val` 或等价流程维护 |

Skill默认只能建议状态。接受风险、生产授权、事故等级、RCA接受和CAPA关闭必须来自项目有权限的责任方或权威系统。

## 状态机

- Runbook：`Draft → Reviewed → Ready → NeedsReview → Ready / Deprecated / Superseded`。
- 事故：`Detected → Triaged → Mitigating → Recovered → RCA → Closed`。
- RCA：`Draft → Investigating → Reviewed → Accepted / Superseded`。
- CAPA：`Proposed → Approved → InProgress → Verified → Closed / Cancelled / Superseded`。

状态不得被一个“完成”替代。`INC Recovered` 不表示 `INC Closed`，`RCA Accepted` 不表示所有 `CAPA Closed`。

## 事故与变更关联

- 发布或已知变更导致的事故复用对应 `CHG`，引用 `REL/DEP/MIGRUN/OBS`。
- 独立运行事故可以使用现有业务变更或临时 `CHG-PENDING-*`；不要为每个告警机械创建永久变更。
- 一个事故可以影响多个版本、租户、区域和依赖；不得只按单服务名称缩小真实影响面。
- 多个表象只有在证据表明共享因果机制时才合并；共享时间不等于共享根因。

## 运行准备模型

至少评估：服务所有权、SLO/SLI、监控与告警、值守与升级、资产和依赖、容量边界、Runbook、权限与审计、备份与恢复、数据修复入口、外部供应方、发布交接和已知风险。

结论使用 `Ready / ConditionallyReady / NotReady / NotAssessed`。只有责任方可以确认就绪；Skill输出默认是建议。条件就绪必须包含条件所有者、期限、监控和失效条件。

## 事件角色

按项目现有角色映射，不强制统一命名：

- 事故指挥：维护目标、优先级、决策和升级，不同时承担所有技术操作。
- 操作责任：执行批准动作并记录前后状态。
- 调查责任：形成假设、查询证据和排除路径。
- 沟通责任：维护内部/外部状态、受众和更新时间。
- 业务/数据责任：确认用户影响、数据不变量和恢复结果。
- 记录责任：维护时间线、决定、行动和证据定位器。

小型事件可由同一人承担多个角色，但角色责任仍需可识别。

## 运行信号

把信号分为业务结果、用户体验、应用、依赖、数据、消息/任务、资源、安全和平台控制面。事故声明必须说明覆盖了哪些信号、缺少哪些信号以及监控盲区。

## 生命周期反馈

- 业务规则或SLO歧义 → `dev-req`。
- 系统边界、单点、隔离或容灾缺陷 → `dev-hld`。
- 契约、事务、幂等、迁移或恢复机制缺陷 → `dev-lld`。
- 代码、配置、脚本或自动化修复 → `dev-impl`。
- 场景与回归缺口 → `dev-test`。
- 证据、门禁或环境可信度缺口 → `dev-val`。
- 紧急修复候选的受控发布 → `dev-rel`。

只生成交接，不自动启动下游 Skill。

