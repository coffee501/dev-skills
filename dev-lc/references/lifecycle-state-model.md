# Dev 体系状态与阶段门

## 状态分离

不同对象使用不同状态，不用一个“完成”覆盖设计、执行、验证和发布。

| 对象 | 状态 |
| --- | --- |
| 变更 | `Draft → Active → Completed / Cancelled / Superseded` |
| 生命周期视图 | `Current → Superseded` |
| 交接包 | `Prepared → Acknowledged → Accepted / Rejected → Superseded` |
| 实现上下文包及事实/路径 | `Draft → Ready → PotentiallyStale → Ready / Stale`；任一现存状态可进入 `Superseded` |
| 实现上下文缺口 | `Open → Resolved / Superseded` |
| 需求和设计文档 | `Draft → Reviewed → Baselined → Superseded / Deprecated` |
| 设计决策 | `Proposed → Accepted → Validated → Superseded / Deprecated` |
| 测试用例 | `Draft → Ready → NeedsReview → Ready / Superseded / Deprecated` |
| 自动化规格 | `Draft → Ready → NeedsReview → Ready / Superseded / Deprecated` |
| 实现单元主路径 | `Planned → InProgress → Implemented → Reviewed → Integrated` |
| 实现单元异常路径 | `Planned/InProgress → Blocked`；未集成状态可进入 `Aborted/Superseded` |
| 本地构建或检查批次 | `Planned → Running → Passed / Failed / Blocked / Aborted` |
| 代码评审 | `Planned → InReview → Approved / ChangesRequested / Blocked / Superseded` |
| 自动化门禁状态 | `NotEnabled → Enabled → Quarantined / Disabled → Enabled / Deprecated` |
| 正式执行批次 | `Planned → Ready → Running → Passed / Failed / Blocked / Aborted` |
| 验证证据 | `Valid → Expired / Revoked` |
| 发布单 | `Draft → Approved → Deploying → Observing → Completed / RolledBack / Failed` |
| 部署批次 | `Planned → Ready → Running → Succeeded / Failed / Blocked / Aborted / RolledBack` |
| 迁移执行 | `Planned → Ready → Running → Verified / Failed / Blocked / Aborted / Compensated / ForwardFixed` |
| 发布观察 | `Planned → Active → Healthy / Degraded / Failed / Closed` |
| 运行手册 | `Draft → Reviewed → Ready → NeedsReview → Ready / Deprecated / Superseded` |
| 事故 | `Detected → Triaged → Mitigating → Recovered → RCA → Closed` |
| 根因分析 | `Draft → Investigating → Reviewed → Accepted / Superseded` |
| 纠正与预防措施 | `Proposed → Approved → InProgress → Verified → Closed / Cancelled / Superseded` |

状态权威必须分离：`dev-test` 管理 `AUT` 规格状态，`dev-impl` 通过
`IMP(kind=test-automation)` 管理自动化代码的实现状态，`dev-val` 或项目质量责任方确认自动化门禁状态。
`BUILD` 只记录本地构建或检查，不产生正式 `RUN/EVD/GATE`。专业 Skill 可以基于证据建议状态，只有具有项目权限的
责任方才能接受决策、风险和发布授权。

## 阶段门

| 门 | 阶段 | 最小进入条件 | 主要退出产物 |
| --- | --- | --- | --- |
| G0 | 变更受理 | 目标、范围、类型和责任边界可识别 | `CHG` 和阶段路线 |
| G1 | 需求基线 | 业务语义、规则和验收可确认 | `REQ/RULE/AC` |
| G2 | 概要设计基线 | 系统边界、职责和关键决策可确认 | `DEC/MOD/FLOW/VAL` |
| G3 | 详细设计基线 | 实现机制、契约、迁移和验证点可编码 | `DET/DDEC/.../DVAL` |
| G4 | 实现与评审 | 设计输入有效、变更可构建并经过独立评审 | `IMP/BUILD/REV` 和实际变更 |
| G5 | 验证门 | 用例、环境、数据和实现版本就绪 | `RUN/EVD/DEFECT/GATE` |
| G6 | 发布门 | 必要验证有效、风险获授权、发布可恢复 | `REL/DEP/MIGRUN/OBS` |
| G7 | 运行闭环 | 生产交接、监控和处置入口存在 | `RUNBOOK/INC/RCA/CAPA` |

测试设计不是独立串行门。它从G1开始建立，在G2至G4持续细化，并在G5前达到执行就绪。

G6内部保持三个独立判断：发布就绪、发布执行完成、观察窗口通过。`DEP Succeeded` 不自动表示 `MIGRUN Verified`、
`OBS Healthy` 或 `REL Completed`；发布单只有在全部适用批次、迁移、观察和运行交接条件满足时才能完成。

G7内部保持四个独立判断：运行准备就绪、事故影响恢复、RCA被接受、CAPA完成关闭。`INC Recovered` 不自动表示
`INC Closed`、`RCA Accepted` 或 `CAPA Verified/Closed`；任何结论都必须具有对应证据和责任方权限。

`CHG Completed` 是生命周期汇总结论，不替代各阶段原生状态。只有适用阶段门、未决交接、发布/运行退出项和失效影响均已
处理，且存在有权限责任方确认时才能记录；Skill默认只建议，不自行关闭变更。

## 阶段门结论

阶段门记录两个独立维度：

- **评估结果**：`NotAssessed / Pass / Fail / Blocked / Expired`。
- **确认级别**：`Suggested / Confirmed`。

Skill 默认只能输出 `Suggested`。输入中存在明确授权记录时才能记录 `Confirmed`，并保留确认人、时间、范围和依据。

## 基线与通过的区别

- 文档基线只说明该阶段输入已经稳定，不说明实现完成。
- 实现完成不说明测试设计充分或验证通过。
- 实现或本地构建完成不说明代码评审已经批准。
- 测试设计基线不说明测试可以执行。
- 执行就绪不说明执行通过。
- 验证通过不说明发布已经批准。
- 部署命令成功不说明迁移已验证、观察窗口健康或发布已经完成。
- 发布完成不说明生产长期观察已经稳定。
- 服务恢复不说明事故已经关闭、根因已经接受或纠正与预防措施已经验证。

任何上游产物或证据失效时，重新评估受影响阶段门。
