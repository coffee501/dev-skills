---
name: dev-ops
description: Initial scaffold for backend and system-integration operational readiness, runbooks, incident response, recovery, root-cause analysis, and corrective-action feedback. Use when released services need production handoff, operational procedures, incident coordination, service restoration, or lifecycle feedback. Until this skill is fully implemented and explicitly enabled, limit output to read-only operational analysis and structured handoffs; do not modify production systems, data, infrastructure, traffic, alerts, or external services.
---

# Dev OPS

## 当前状态

本模块处于职责骨架阶段，尚未实现生产操作和事故响应流程。显式调用时只进行只读分析、准备检查和交接，不改变生产系统、数据、流量、告警或外部服务。

## 接入 Dev 生命周期

复用生产版本关联的 `CHG`；独立事故仅在目标和处置边界独立时建立新变更。按 [产物协议](../dev-lc/references/artifact-contract.md) 维护 `RUNBOOK/INC/RCA/CAPA` 与版本、发布和证据的关系，按 [状态与阶段门](../dev-lc/references/lifecycle-state-model.md) 区分恢复、根因完成和改进关闭。

生产反馈使用 [交接协议](../dev-lc/references/handoff-contract.md) 路由到需求、设计、实现或测试。事故和根因变化按 [失效传播规则](../dev-lc/references/invalidation-rules.md) 触发永久修复、回归测试和运行手册复审。

## 模块目标

管理后端与集成系统的运行准备、人工处置、事故恢复和持续改进反馈，使生产问题能够闭环回到需求、设计、实现和测试。

## 计划职责

- 建立和评审运行手册、值守入口、升级路径与恢复步骤。
- 检查SLO、监控、告警、审计和人工修复能力。
- 协调事故分级、止损、恢复、沟通和证据保全。
- 形成根因分析、纠正措施和预防措施。
- 将事故、运行偏差和容量风险反馈到上游研发模块。

## 职责边界

- 不自行修改业务规则、SLO、安全策略或架构目标。
- 不在缺少授权、精确目标、停止条件和恢复方案时执行生产操作。
- 不把临时止损措施自动登记为永久设计。
- 不替代 `dev-rel` 执行常规发布。

## 计划输入

- `dev-rel` 的 `REL/DEP/MIGRUN/OBS` 和运行交接。
- 适用的 `CTX` 及其引用的 `CTXF/CTXP/CTXG`，用于定位运行入口、依赖、日志、指标和恢复实现，不替代生产事实或RCA证据。
- 运行手册、SLO、监控、告警、日志、审计与资产信息。
- 事故报告、生产证据、历史问题和外部依赖状态。

## 计划输出

- `RUNBOOK-001`：运行与人工处置手册。
- `INC-001`：事故及时间线。
- `RCA-001`：证据支持的根因分析。
- `CAPA-001`：纠正与预防措施及责任追踪。

## 计划交接

业务目标或规则问题反馈 `dev-req`，架构问题反馈 `dev-hld`，实现机制与永久修复反馈 `dev-lld` 和 `dev-impl`，缺陷回归反馈 `dev-test` 与 `dev-val`。

## 后续实现主题

运行准备、Runbook模型、事故安全门、止损与恢复、证据时间线、RCA、CAPA、数据修复和研发反馈闭环。
