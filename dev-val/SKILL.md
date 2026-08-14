---
name: dev-val
description: Initial scaffold for executing approved backend and system-integration tests and governing validation evidence. Use when ready TC/AUT artifacts must be run against identified versions and environments, failures classified, VAL/DVAL aggregated, or a quality-gate recommendation produced. Until this skill is fully implemented and explicitly enabled, limit output to readiness analysis and structured handoffs; do not execute tests or change code, data, dependencies, or environments.
---

# Dev VAL

## 当前状态

本模块处于职责骨架阶段，尚未实现测试执行和证据聚合流程。显式调用时只评估执行就绪条件和缺口，不运行测试或修改任何目标。

## 接入 Dev 生命周期

复用输入中的 `CHG`，按 [产物协议](../dev-lc/references/artifact-contract.md) 将 `RUN/EVD/DEFECT/GATE` 绑定代码、契约、数据条件、环境和时间。按 [状态与阶段门](../dev-lc/references/lifecycle-state-model.md) 分离执行结果、证据状态、验证建议和发布授权。

失败或阻塞使用 [交接协议](../dev-lc/references/handoff-contract.md) 返回正确责任流程。实现、用例、预期或环境变化时使用 [失效传播规则](../dev-lc/references/invalidation-rules.md)，不得沿用不再适用的旧证据。

## 模块目标

在明确版本、环境和授权范围内执行已批准测试，生成可审计证据，并据此形成验证和质量门禁建议。

## 计划职责

- 检查 `TC/AUT/TD/TENV/TCOND` 的执行就绪状态。
- 执行适用测试并记录版本、环境、时间、命令、结果和原始证据。
- 区分产品失败、测试缺陷、环境问题和安全阻断。
- 管理重试、Flaky、Quarantine和证据失效。
- 根据明确聚合规则建议 `VAL/DVAL` 状态和质量门禁结论。

启用实际执行能力后，执行前必须读取 [references/execution-safety.md](references/execution-safety.md)。当前骨架状态只使用该文件评估就绪和阻塞，不执行操作。

## 职责边界

- 不发明预期结果，不改变需求、设计、测试场景或用例含义。
- 不负责修复产品代码、修改测试设计或批准生产发布。
- 不把覆盖率、测试数量或环境失败当作产品通过证据。
- 未通过执行安全门时只输出阻塞，不进行执行。

## 计划输入

- `dev-test` 的 `TSC/TC/TDP/TD/TENV/TCOND/AUT`。
- 共享 `CHG` 上下文、`dev-impl` 的 `IMP/BUILD` 和候选版本。
- 适用的 `CTX` 及其引用的 `CTXF/CTXP/CTXG`，用于定位执行入口、环境依赖和观察点，不作为通过证据。
- `VAL/DVAL` 聚合规则、机器契约、环境和授权信息。

## 计划输出

- `RUN-001`：测试执行批次。
- `EVD-001`：带适用范围和失效条件的验证证据。
- `DEFECT-001`：经分类的失败或缺陷。
- `GATE-001`：验证与质量门禁建议，不等同于发布批准。

## 计划交接

预期缺口交接 `dev-req`，架构或详细设计缺口分别交接 `dev-hld`、`dev-lld`，用例缺口交接 `dev-test`，实现失败交接 `dev-impl`。通过且证据有效时向 `dev-rel` 提供门禁输入。

## 后续实现主题

执行安全门、环境准备、批次模型、证据模型、失败分类、重试与隔离治理、VAL/DVAL聚合和门禁规则。
