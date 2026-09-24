# Dev 体系状态与阶段门

## 状态分离

不同对象使用不同状态，不用一个“完成”覆盖设计、实现、评审和验证。

| 对象 | 状态 |
| --- | --- |
| 变更 | `Draft → Active → Completed / Cancelled / Superseded` |
| 生命周期视图 | `Current → Superseded` |
| 交接包 | `Prepared → Acknowledged / Accepted / Rejected / Superseded`；`Acknowledged → Accepted / Rejected / Superseded`；`Accepted / Rejected → Superseded` |
| 实现上下文包及事实/路径 | `Draft → Ready → PotentiallyStale → Ready / Stale`；任一现存状态可进入 `Superseded` |
| 实现上下文缺口 | `Open → Resolved / Superseded` |
| 需求和设计文档 | `Draft → Reviewed → Baselined → Superseded / Deprecated` |
| 设计决策 | `Proposed → Accepted → Validated → Superseded / Deprecated` |
| 前端接口对接文档 | `Draft → ReadyForReview → Baselined → NeedsReview → ReadyForReview / Baselined`；任一现存状态可进入 `Superseded/Deprecated` |
| 测试用例 | `Draft → Ready → NeedsReview → Ready / Superseded / Deprecated` |
| 自动化规格 | `Draft → Ready → NeedsReview → Ready / Superseded / Deprecated` |
| 实现单元主路径 | `Planned → InProgress → Implemented → Reviewed → Integrated` |
| 实现单元异常路径 | `Planned/InProgress → Blocked`；未集成状态可进入 `Aborted/Superseded` |
| 本地构建或检查批次 | `Planned → Running → Passed / Failed / Blocked / Aborted` |
| 实现审查 | `Planned → InReview → Approved / ChangesRequested / Blocked / Superseded` |
| 自动化门禁状态 | `NotEnabled → Enabled → Quarantined / Disabled → Enabled / Deprecated` |
| 正式执行批次 | `Planned → Ready → Running → Passed / Failed / Blocked / Aborted` |
| 验证证据 | `Valid → Expired / Revoked` |

状态权威必须分离：`dev-test` 管理 `AUT` 规格状态，`dev-impl` 通过
`IMP(kind=test-automation)` 管理自动化代码的实现状态，`dev-val` 或项目质量责任方确认自动化门禁状态。
`BUILD` 只记录本地构建或检查，不产生正式 `RUN/EVD/GATE`。专业 Skill 可以基于证据建议状态，只有具有项目权限的
责任方才能接受决策、风险和阶段门确认。

## 阶段门

| 门 | 阶段 | 最小进入条件 | 主要退出产物 |
| --- | --- | --- | --- |
| G0 | 变更受理 | 目标、范围、类型和责任边界可识别 | `CHG` 和阶段路线 |
| G1 | 需求基线 | 业务语义、规则和验收可确认 | `REQ/RULE/AC` |
| G2 | 概要设计基线 | 系统边界、职责和关键决策可确认 | `DEC/MOD/FLOW/VAL` |
| G3 | 详细设计基线 | 实现机制、契约、迁移和验证点可编码 | `DET/DDEC/.../DVAL` |
| G4 | 实现与评审 | 设计输入有效；产品实现可构建且经过独立评审；适用的测试自动化实现可构建且经过独立评审，或仅在项目政策允许的低风险范围内记录评审不适用 | 产品实现 `IMP(kind=code/config/contract/migration)`、测试实现 `IMP(kind=test-automation)`、`BUILD/REV` 和实际变更 |
| G5 | 验证门 | 必选 `TC`、环境、数据和候选版本就绪；每个必选用例具有人工执行路径，或关联 `AUT Ready` 及已构建、已评审的自动化实现 | `RUN/EVD/DEFECT` 和闭环 `GATE` |

测试设计不是独立串行门。它在G1基于 `REQ/RULE/AC` 建立 `TSC/TC Draft`，在G2/G3吸收架构、契约、数据和
`VAL/DVAL` 持续细化；稳定的自动化需求形成 `AUT Ready` 后，由G4的 `dev-impl` 实现测试代码，并由 `dev-cr`
独立审查。进入G5前，每个必选 `Ready TC` 必须明确执行方式：人工路径需具备可执行步骤、数据和环境；自动化路径需
追踪到 `AUT Ready → IMP(kind=test-automation) → BUILD Passed → REV Approved`。项目政策允许人工执行、延期自动化或
评审不适用时，必须记录依据、责任、剩余风险和失效条件，不能用空缺默认通过。

测试自动化实现不新增独立阶段门；它是G4中由 `dev-impl` 承担、由 `dev-cr` 审查的实现分支。

`GATE` 是G5的版本化验证结论记录，必须可追踪到适用 `RUN/EVD/DEFECT`、逐 `VAL/DVAL` 结果、未验证范围、剩余风险和重新验证条件。面向人员生成的验证摘要只是 `GATE` 的只读投影视图，不新增产物类型、状态或阶段门。

G4 的 `REV Approved` 必须包含可验证的审查独立性：评审者与实现责任主体的身份和执行上下文均独立，或记录明确的补偿控制；
独立性未建立时不得通过实现审查门。

人类可读实现交付摘要是当前 `IMP/BUILD` 与实际差异的只读投影，用于帮助G4评审和G5交接；它没有独立状态，不新增阶段门，
也不能替代实际实现、`BUILD` 或 `REV`。

`FIA` 同样不是独立阶段门。存在前端消费方时，它在字段级 `API/EVT` 或机器契约足够稳定后形成，并可在实现、联调和
测试设计期间持续细化。`FIA Baselined` 只表示对接说明获责任方确认，不表示接口实现、联调或验收已经通过。

`CHG Completed` 是开发生命周期汇总结论，不替代各阶段原生状态。只有适用阶段门、未决交接和失效影响均已
处理，且存在有权限责任方确认时才能记录；Skill默认只建议，不自行关闭变更。

## 阶段门结论

阶段门记录两个独立维度：

- **评估结果**：`NotAssessed / Pass / Fail / Blocked / Expired`。
- **确认级别**：`Suggested / Confirmed`。

Skill 默认只能输出 `Suggested`。输入中存在明确授权记录时才能记录 `Confirmed`，并保留确认人、时间、范围和依据。

## 基线与通过的区别

- 文档基线只说明该阶段输入已经稳定，不说明实现完成。
- 实现完成不说明测试设计充分或验证通过。
- 实现或本地构建完成不说明实现审查已经批准。
- 测试设计基线不说明测试可以执行。
- 执行就绪不说明执行通过。
- 验证通过只说明当前候选满足记录范围内的验证规则，不说明已经发布或生产稳定。

任何上游产物或证据失效时，重新评估受影响阶段门。
