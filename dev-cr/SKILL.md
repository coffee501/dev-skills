---
name: dev-cr
description: "Independently review backend-service and system-integration implementations, pull requests, commits, patches, contracts, configuration, migrations, jobs, events, and test automation against approved requirements, HLD/LLD, repository rules, and current implementation evidence. Use for implementation review, PR or change-set review, pre-merge risk assessment, review-result import, remediation re-review, or G4 review evidence. Produce traceable REV findings and verdicts without modifying code by default. Do not invent requirements or design, approve external pull requests, waive validation, execute tests as formal evidence, deploy changes, or operate production systems. | 独立评审后端与集成实现，形成可追踪问题、结论和整改交接"
---

# Dev CR

独立评审后端与系统集成实现，形成范围明确、证据可复核、问题可整改、结论可追踪的 `REV`，补齐G4中“实现完成”与“评审批准”之间的责任边界。

## 保持职责边界

- `dev-impl` 实施和整改；本 Skill 默认只读，不修改被评审代码、测试、配置或迁移。
- `dev-cr` 拥有 `REV`，不改写 `IMP/BUILD/REQ/DEC/DDEC/TC/AUT/EVD/GATE`。
- 不用评审意见改变业务规则、架构边界、数据权威或测试预期；相应缺口交接原责任模块。
- `REV Approved` 只表示当前范围通过独立代码评审，不表示构建、验证、发布或生产稳定。
- 不因作者声明、CI绿灯或已有批准按钮而省略实际范围和证据检查。
- 不在未经用户授权时向GitHub、GitLab或其他外部系统提交评论、批准、请求修改或合并。

## 接入 Dev 生命周期

复用正式 `CHG`；没有权威编号时使用 `CHG-PENDING-*`。按 [产物协议](../dev-lc/references/artifact-contract.md) 管理 `REV`，按 [状态与阶段门](../dev-lc/references/lifecycle-state-model.md) 区分实现、评审、验证和发布。整改、语义缺口或责任转移使用 [交接协议](../dev-lc/references/handoff-contract.md)，代码或评审范围变化时按 [失效传播规则](../dev-lc/references/invalidation-rules.md) 使旧结论失效。

共享协议不可用时仍可独立进行只读代码评审和复审，使用本地 `REV-PENDING-*`，并将正式G4、HOF和全局状态标记为待确认。除非用户明确要求串联流程，否则只形成结构化交接，不自动调用其他 Skill。

## 选择工作模式

| 模式 | 使用条件 | 默认结果 |
| --- | --- | --- |
| 评审就绪诊断 | 基线、目标范围或设计依据不足 | 阻塞、缺口和可继续检查 |
| 实现单元评审 | 已有 `IMP/BUILD` 和实际修改 | `REV`、问题和结论 |
| PR/提交/补丁评审 | 给定基础与目标版本 | 变更集、影响和逐项发现 |
| 迁移或契约专项 | Schema、数据、API、事件或配置变化 | 兼容、恢复和副作用结论 |
| 整改复审 | 评审问题已处理 | 原问题处置、新增问题和新结论 |
| 外部评审导入 | 已有平台或人工评审记录 | 来源、范围、完整性和可信度 |
| 评审审计 | 检查既有批准是否充分 | 缺口、过期和重新评审条件 |

问题严重度：

- **P0**：存在可导致错误业务结果、越权/泄露、不可恢复数据损坏、破坏性兼容或范围不可判断的问题，阻塞批准。
- **P1**：存在显著正确性、失败处理、并发、性能、可运维性或验证风险，G4前必须解决或由有权限责任方接受。
- **P2**：不影响当前正确性与安全的维护性、清晰度、重复或局部工程改进。

严重度表示评审问题，不替代业务优先级、漏洞等级或事故等级。

## 建立可信输入

按优先级读取：仓库规则和实际变更；基础/目标版本及工作区状态；`IMP/BUILD`；适用 `REQ/RULE/AC/DEC/MOD/FLOW/DET/DDEC`；机器契约、迁移、配置和测试；`Eligible CTX`；历史缺陷、事故和外部评审记录。

评审必须绑定精确 `base/head`、候选摘要或不可变差异。只提供片段时明确未覆盖范围；无法确定完整变更集时不得建议完整批准。As-Is实现不自动证明To-Be正确，测试存在不自动证明覆盖充分。

## 按需读取参考文件

- 建立评审对象、状态、严重度和结论时读取 [references/review-model.md](references/review-model.md)。
- 检查正确性、数据、契约、安全、性能、测试和运维风险时读取 [references/review-checklist.md](references/review-checklist.md)。
- 整改复审、范围变化或旧批准失效时读取 [references/re-review.md](references/re-review.md)。
- 生成或校验正式 `REV` 时读取 [references/output-contracts.md](references/output-contracts.md)。

## 执行评审流程

1. 确认请求是只读评审、复审、外部记录导入还是审计；锁定允许的外部副作用范围。
2. 解析仓库、基础版本、目标版本、工作区、候选摘要、`CHG/IMP/BUILD/HOF` 和作者修改。
3. 读取实际差异及必要上下文，不只依赖提交说明、摘要或生成报告。
4. 建立直接与间接影响面，检查调用方、消费者、数据、配置、任务、依赖、部署和运行路径。
5. 对照已接受需求和设计，区分实现偏差、设计缺口、预期缺口、测试缺口和环境未知。
6. 按正确性、异常、事务/并发、数据/迁移、契约/兼容、安全、性能、可观测性、测试、发布/运行及维护性评审。
7. 每个发现记录位置、触发条件、证据、影响、严重度、责任路由、最小整改目标和验证要求。
8. 排除无证据偏好、纯风格争论、仓库工具已自动处理的问题和范围外历史缺陷；必要时作为非阻塞观察单列。
9. 检查评审范围、未查看文件、无法运行的确认、生成物、外部依赖和动态行为限制。
10. 形成 `REV` 状态与 `Prepared HOF`；整改后基于新差异创建新版本或后继评审，不覆盖旧结论。

JSON形式的评审产物可用 `scripts/validate_review_artifact.py` 检查最低契约。校验器不证明发现正确、评审充分或外部PR已批准。

## 控制评审结论

- `Approved`：评审范围明确，没有未解决P0/P1，必要证据和限制充分，且不存在阻止独立判断的缺口。
- `ChangesRequested`：至少一个未解决P0/P1需要整改，或批准条件尚未满足。
- `Blocked`：基础/目标、完整差异、权威预期、关键生成源、权限或必要上下文不足，无法形成可信结论。
- `Superseded`：代码、契约、配置、迁移、基础版本、评审范围或关键依据变化，旧结论被新 `REV` 替代。

没有发现问题不自动等于 `Approved`；必须同时说明实际覆盖和限制。P2可保留为非阻塞改进，但不得隐藏可能实际属于P1的问题。

## 管理整改与交接

- 实现缺陷和代码整改交给 `dev-impl`。
- 业务预期缺口交给 `dev-req`；架构边界交给 `dev-hld`；实现机制交给 `dev-lld`。
- 测试覆盖或预期问题交给 `dev-test`；正式执行和证据交给 `dev-val`。
- 已批准修复候选仍由 `dev-rel` 发布，生产问题由 `dev-ops` 处理。

`REV Approved` 后向 `dev-val` 提供评审范围、候选身份、残余风险、必要验证和失效条件。`ChangesRequested` 向 `dev-impl` 提供问题、位置、证据、预期结果和复审条件。只创建 `Prepared HOF`，不假定接收。

## 检查完成条件

只有以下条件同时满足才建议评审完成：base/head或候选身份明确；实际差异和关键影响面已检查；上游语义和仓库规则可追踪；发现具有证据、触发条件和影响；P0/P1处置明确；测试和运行风险已评估；范围限制和未检查内容公开；结论与状态一致；整改或验证交接已经形成。

## 组织输出

- **就绪诊断**：范围、输入、缺口、P0/P1和可继续只读检查。
- **评审发现**：按严重度排序的位置、证据、条件、影响、整改目标和验证要求。
- **评审结论**：`REV`、base/head、覆盖、限制、`Approved/ChangesRequested/Blocked`及依据。
- **复审结果**：原发现处置、差异变化、新增发现、保留风险和后继关系。
- **交接**：面向 `dev-impl/dev-val` 或上游责任方的版本化 `Prepared HOF`。

没有可执行问题时明确写“未发现阻塞问题”，同时保留评审范围和限制；不要为了填充报告制造问题。
