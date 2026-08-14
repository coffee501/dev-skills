---
name: dev-rel
description: Initial scaffold for preparing and executing controlled backend and system-integration releases. Use when validated artifacts, configuration, contracts, or migrations must be deployed through an approved rollout, observed, rolled back, or recorded. Until this skill is fully implemented and explicitly enabled, limit output to release-readiness analysis and structured handoffs; do not deploy, migrate data, change infrastructure, or affect production systems.
---

# Dev REL

## 当前状态

本模块处于职责骨架阶段，尚未实现发布执行流程。显式调用时只评估发布准备情况、依赖和阻塞，不部署、不迁移数据、不改变基础设施或生产状态。

## 接入 Dev 生命周期

复用输入中的 `CHG`，按 [产物协议](../dev-lc/references/artifact-contract.md) 将 `REL/DEP/MIGRUN/OBS` 绑定批准范围、产物版本、环境和证据。按 [状态与阶段门](../dev-lc/references/lifecycle-state-model.md) 检查G6输入，验证建议不等于发布授权。

准备不足、执行失败或运行交接使用 [交接协议](../dev-lc/references/handoff-contract.md)。产物、迁移、配置、环境或证据变化时使用 [失效传播规则](../dev-lc/references/invalidation-rules.md) 重新评估发布门和观察结论。

## 模块目标

把已经验证且获得授权的后端与集成变更安全地发布到目标环境，并记录迁移、观察、停止、回滚和最终结果。

## 计划职责

- 执行发布前检查和授权检查。
- 按批准顺序处理应用、配置、契约和数据迁移。
- 执行灰度、滚动、蓝绿或其他已选发布策略。
- 运行发布验证，观察关键指标并应用停止条件。
- 执行回滚或前向修复方案，记录不可逆影响。

## 职责边界

- 不替代 `dev-hld` 或 `dev-lld` 选择发布与迁移策略。
- 不绕过 `dev-val` 的必要门禁或风险接受。
- 不自行扩大目标环境、流量、数据或外部副作用范围。
- 不负责长期运行治理和事故根因闭环。

## 计划输入

- `dev-lld` 的发布顺序、`MIG`、兼容期、回滚和退出条件。
- 共享 `CHG` 上下文、`dev-impl` 的 `IMP/BUILD` 和候选发布产物。
- `dev-val` 的有效 `EVD/GATE`。
- 适用的 `CTX` 及其引用的 `CTXF/CTXP/CTXG`，用于定位运行单元、配置、依赖和观察入口，不替代发布设计或授权。
- 目标环境、发布窗口、授权、观察指标和责任人。

## 计划输出

- `REL-001`：发布单和批准范围。
- `DEP-001`：部署批次及目标环境。
- `MIGRUN-001`：迁移执行记录。
- `OBS-001`：发布观察与最终结果。

## 计划交接

实现或产物问题交接 `dev-impl`，证据或门禁问题交接 `dev-val`，策略问题交接 `dev-hld` 或 `dev-lld`。发布完成后向 `dev-ops` 提供部署状态、观察结果、残留风险和运行交接。

## 后续实现主题

发布授权门、预检、部署与迁移执行、灰度观察、停止条件、回滚、前向修复、发布证据和生产安全约束。
