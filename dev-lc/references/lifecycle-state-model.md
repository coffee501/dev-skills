# Dev 体系状态与阶段门

## 状态分离

不同对象使用不同状态，不用一个“完成”覆盖设计、执行、验证和发布。

| 对象 | 状态 |
| --- | --- |
| 实现上下文包 | `Draft → Ready → PotentiallyStale → Ready / Stale → Superseded` |
| 需求和设计文档 | `Draft → Reviewed → Baselined → Superseded / Deprecated` |
| 设计决策 | `Proposed → Accepted → Validated → Superseded / Deprecated` |
| 测试用例 | `Draft → Ready → NeedsReview → Ready / Superseded / Deprecated` |
| 自动化规格 | `Draft → Ready → NeedsReview → Ready / Superseded / Deprecated` |
| 实现单元主路径 | `Planned → InProgress → Implemented → Reviewed → Integrated` |
| 实现单元异常路径 | `Planned/InProgress → Blocked`；未集成状态可进入 `Aborted/Superseded` |
| 本地构建或检查批次 | `Planned → Running → Passed / Failed / Blocked / Aborted` |
| 自动化门禁状态 | `NotEnabled → Enabled → Quarantined / Disabled → Enabled / Deprecated` |
| 正式执行批次 | `Planned → Ready → Running → Passed / Failed / Blocked / Aborted` |
| 验证证据 | `Valid → Expired / Revoked` |
| 发布单 | `Draft → Approved → Deploying → Observing → Completed / RolledBack / Failed` |
| 事故 | `Detected → Triaged → Mitigating → Recovered → RCA → Closed` |

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
| G4 | 实现与评审 | 设计输入有效、变更可构建并经过评审 | `IMP/BUILD` 和实际变更 |
| G5 | 验证门 | 用例、环境、数据和实现版本就绪 | `RUN/EVD/DEFECT/GATE` |
| G6 | 发布门 | 必要验证有效、风险获授权、发布可恢复 | `REL/DEP/MIGRUN/OBS` |
| G7 | 运行闭环 | 生产交接、监控和处置入口存在 | `RUNBOOK/INC/RCA/CAPA` |

测试设计不是独立串行门。它从G1开始建立，在G2至G4持续细化，并在G5前达到执行就绪。

## 阶段门结论

阶段门记录两个独立维度：

- **评估结果**：`NotAssessed / Pass / Fail / Blocked / Expired`。
- **确认级别**：`Suggested / Confirmed`。

Skill 默认只能输出 `Suggested`。输入中存在明确授权记录时才能记录 `Confirmed`，并保留确认人、时间、范围和依据。

## 基线与通过的区别

- 文档基线只说明该阶段输入已经稳定，不说明实现完成。
- 实现完成不说明测试设计充分或验证通过。
- 测试设计基线不说明测试可以执行。
- 执行就绪不说明执行通过。
- 验证通过不说明发布已经批准。
- 发布完成不说明生产观察期已经稳定。

任何上游产物或证据失效时，重新评估受影响阶段门。
