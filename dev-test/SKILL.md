---
name: dev-test
description: "设计风险驱动、可追踪的后端与系统集成测试用例。"
---

# Dev TEST

将后端与系统集成的需求、设计和实现证据转化为可执行、可追踪的测试场景、用例、数据、环境和自动化规格。采用风险驱动覆盖，不预设行业模型、技术栈、测试框架或固定测试金字塔。

## 生命周期接入

复用输入中的正式 `CHG`；没有权威编号时使用 `CHG-PENDING-001`。测试设计从G1开始：用 `REQ/RULE/AC` 建立 `TSC/TC Draft`，在 G2/G3 吸收 `DEC/MOD/FLOW/DET/DDEC/DATA/API/EVT/JOB/CFG/VAL/DVAL` 后细化为 `Ready TC/AUT`。

统一追踪读取 [产物协议](../dev-orch/references/artifact-contract.md)；正式交接读取 [交接协议](../dev-orch/references/handoff-contract.md)；来源、设计、实现、数据、环境或预期变化读取 [失效传播规则](../dev-orch/references/invalidation-rules.md)；阶段门和治理状态遵循 [状态与阶段门](../dev-orch/references/lifecycle-state-model.md)。共享协议不可用时可独立输出测试诊断、设计、评审、回归选择和执行准备，但不得宣称全局编号、G5、自动化门禁或标准 `HOF` 已确认。

## 职责边界

负责说明测试什么、为什么测、如何准备、如何执行以及观察什么结果。默认不修改业务目标、规则、状态、数据口径、验收标准、系统边界、模块职责、接口字段、错误码、事务、幂等、迁移或失败语义；不执行测试、不写测试代码、不创建数据、不安装依赖、不改变环境；不覆盖客户端、前端组件、视觉或 UI/UX 测试。

语义缺口按责任交接：业务预期给 `dev-req`，架构和跨模块语义给 `dev-hld`，字段、契约、事务和实现机制给 `dev-lld`，自动化代码给 `dev-impl`，测试执行和证据治理给 `dev-val`。除非用户明确要求串联执行，只在当前输出中形成交接项。

交接项包含目标流程、问题与证据、受影响编号、来源侧严重度、目标侧影响、建议责任角色、缺失决策、受阻测试和可继续内容。`P0/P1/P2` 只表示问题严重度；测试优先级使用 `Critical/High/Medium/Low`。

## 可信输入

按优先级读取：已确认 `REQ/RULE/AC`；`DEC/MOD/FLOW/VAL` 与 `DET/DDEC/DVAL`；`DATA/MIG/API/EVT/JOB/CFG` 和机器契约；符合共享资格的 `Eligible CTX`；当前代码、现有测试、数据库、配置、部署和运行证据；历史缺陷、事故、变更记录和当前对话结论。有前端消费方时，`FIA` 可补充消费场景，不能替代需求、机器契约或预期责任。

区分已确认、实现证据、合理推断、待确认、冲突和已废止。现有测试只证明被检查的当前行为，不自动证明业务预期正确或覆盖充分。As-Is 行为不能直接成为预期；预期必须来自确认需求、权威契约、状态模型、数据不变量、独立参考实现、人工批准结果或其他可信 oracle。没有上游编号时使用 `SRC/RISK/CONTRACT/DEFECT`。

## 工作模式

选择最小充分模式：测试诊断、完整设计、增量完善、测试评审、回归选择、自动化交接、执行准备交接。识别新功能、已有功能变更、规则调整、缺陷修复、契约变更、系统集成、数据迁移、功能下线、架构迁移或非功能专项。只有纯新建且不共享契约、数据、配置、基础设施、部署单元或运行资源时，才跳过回归和兼容分析。

## 设计流程

1. 核对目标、范围、非范围、来源版本和未决问题；没有 G1 基线时只形成诊断或临时草案。
2. 识别模式、变更类型、风险和测试层级；选择能证明目标的最低充分层级。
3. 有实现时建立 As-Is 证据基线：现有测试、调用、数据、契约、环境、最近结果和失效条件。
4. 从 `AC/RULE/RISK` 提取 `TSC`，用 `VAL/DVAL`、状态、数据和契约补齐或修订。
5. 按风险展开 `TC/TDP/TD/TENV/TCOND/AUT`，明确前置、数据、步骤、观察点、预期、oracle、清理和自动化候选。
6. 对存量变更选择新增、修改、废止和回归测试。
7. 检查追踪闭环、覆盖缺口、证据有效性、冲突和基线条件；需要自动化时形成面向 `dev-impl` 的交接，并声明后续 `BUILD/REV` 要求。
8. 准备 G5 交接时核对每个必选 `Ready TC`：人工路径可执行，或自动化路径已闭合 `AUT Ready -> IMP(kind=test-automation) -> BUILD -> REV`。

主线：测试输入与范围 -> 被测对象与风险 -> 覆盖模型 -> 场景 -> 用例 -> 数据与环境 -> 兼容回归 -> 自动化交接 -> 追踪与基线。

## 硬门禁

`TC` 生命周期、执行方式和单次结果必须分离：生命周期 `Draft/Ready/NeedsReview/Deprecated/Superseded`；执行方式 `Manual/AutomationCandidate/Automated`；执行结果 `NotRun/Passed/Failed/Blocked/Skipped`。

`Ready TC` 必须具有可执行步骤、可观察预期、独立 oracle、可准备数据和环境、清理方式，并明确人工或自动化执行路径。语义、契约、实现、数据、环境或断言变化时，受影响 `Ready` 用例进入 `NeedsReview`，旧执行证据失效。

`AUT Ready` 只表示自动化规格足以交给 `dev-impl`，必须明确关联 `TC`、层级、数据、依赖、断言、入口、触发、隔离和稳定性；不表示测试代码已实现、构建、评审、执行或进入门禁。自动化代码由 `dev-impl` 以 `IMP(kind=test-automation)` 管理，测试代码评审由 `dev-cr` 产生 `REV`，执行和证据治理由 `dev-val` 管理。

分别判断四类结论：测试设计基线、自动化实现就绪、测试执行就绪、验证通过。`dev-test` 可以确认测试设计基线；其余结论必须来自对应实现、评审、环境或执行证据，不能互相暗示。

正式 `TC/AUT` JSON 读取 [references/output-contracts.md](references/output-contracts.md)，并使用 `scripts/validate_test_artifact.py` 校验最低契约。校验通过只证明结构有效，不证明覆盖充分、预期正确或基线通过。

## 参考文件

- 完整设计或文档结构：读取 [references/outline.md](references/outline.md)。
- 场景、用例、数据、环境和 Ready 用例质量：读取 [references/test-case-model.md](references/test-case-model.md)。
- 状态、规则、边界、组合、覆盖矩阵和冗余控制：读取 [references/coverage-model.md](references/coverage-model.md)。
- 已有功能变更、缺陷修复、迁移、下线、混合版本和回归选择：读取 [references/compatibility-regression.md](references/compatibility-regression.md)。
- 安全、性能、可靠性、容量、容灾、合规、敏感数据、多租户、外部暴露、可观测性或不可逆副作用：读取 [references/non-functional-testing.md](references/non-functional-testing.md)。
- 正式 `TC/AUT/TDP/TD/TENV/TCOND/TSC` JSON：读取 [references/output-contracts.md](references/output-contracts.md)。
- 完整评审、基线判断或高风险缺口检查：读取 [references/review-checklist.md](references/review-checklist.md)。
- 新增测试层、夹具、数据分区、自动化抽象或拆分大量用例：读取 [复杂度与拆分治理](../dev-orch/references/complexity-governance.md)。

局部问题只读取直接相关 reference。

## 输出规则

默认向用户展示可读的测试设计、评审、回归选择或交接说明。`TC/AUT/HOF` 的 JSON 形式用于内部追踪和正式交接，不把原始协议文件当作默认答复；用户明确要求协议内容时再展示。

完整设计使用 [references/outline.md](references/outline.md) 的适用章节且不生成空章节，至少包含范围与依据、风险与覆盖、`TSC/TC`、数据与环境、兼容回归、自动化映射、追踪与四类治理结论。诊断、增量完善、评审、回归选择和交接输出保持结论、证据、影响、阻塞、进入条件和结构化上游交接清晰可追踪。
