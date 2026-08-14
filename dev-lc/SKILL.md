---
name: dev-lc
description: Govern end-to-end backend and system-integration development across current-system discovery, requirements, architecture, detailed design, implementation, test design, validation, release, and operations. Use when a change needs stage routing, a shared CHG identifier, artifact and baseline coordination, version-aware traceability, invalidation analysis, stage-gate assessment, or structured cross-skill handoffs. Operate as a read-only control plane: do not replace specialist decisions, invoke other skills automatically, approve risks or releases, or mutate repositories, artifacts, environments, or workflow state unless the user explicitly expands scope.
---

# Dev LC

建立一次后端或系统集成变更的统一生命周期视图，协调阶段、产物、版本、状态、证据、阻塞和交接。专业 Skill 负责内容，本 Skill 只负责治理和路由。

## 保持控制面边界

- 不生成或改写需求、架构、详细设计、测试预期或实现方案。
- 不接受设计决策、风险、阶段门或发布授权。
- 不自动调用其他 Skill，不执行实现、测试、发布或生产操作。
- 不把阶段完成、文档基线、验证通过和发布批准混为一谈。
- 不因缺少某个下游模块而伪造其正式产物。

## 读取体系协议

- 建立或检查编号、版本、产物清单和追踪链时，读取 [references/artifact-contract.md](references/artifact-contract.md)。
- 判断对象状态、阶段门和确认级别时，读取 [references/lifecycle-state-model.md](references/lifecycle-state-model.md)。
- 创建阶段推进、问题返回或责任转移时，读取 [references/handoff-contract.md](references/handoff-contract.md)。
- 上游、实现、测试、环境、发布或事故发生变化时，读取 [references/invalidation-rules.md](references/invalidation-rules.md)。

## 建立 CHG 上下文

优先复用现有正式 `CHG`。不存在权威编号时使用 `CHG-PENDING-001` 并标记临时，不宣称全局唯一。记录目标、范围、非范围、变更类型、目标版本、责任角色、发布和回滚边界。

识别新功能、已有功能变更、规则调整、缺陷修复、系统集成、契约变化、数据迁移、功能下线、架构迁移、紧急修复或运行改进。纯文档整理且不改变语义时允许只进入相关阶段。

## 选择阶段路线

| 模块 | 责任 |
| --- | --- |
| `dev-ctx` | 存量项目的业务、架构、流程、数据和运行上下文发现 |
| `dev-req` | 需求、规则、业务语义和验收基线 |
| `dev-hld` | 系统边界、模块职责和概要决策 |
| `dev-lld` | 实现级详细设计、契约和迁移方案 |
| `dev-impl` | 代码、配置、契约和迁移实施 |
| `dev-test` | 测试场景、用例、数据和自动化设计 |
| `dev-val` | 测试执行、证据、失败分类和门禁建议 |
| `dev-rel` | 发布、迁移执行、观察和回滚 |
| `dev-ops` | 运行准备、事故恢复和持续改进反馈 |

不要机械要求全部阶段串行出现。`dev-ctx` 是存量系统或上下文未知时的按需发现阶段，不是新项目的强制门；测试设计
可以从需求阶段开始；局部缺陷可以复用有效需求和设计基线；生产事故可以直接进入运行止损，再补充永久修复链。

## 执行治理流程

1. 建立 `CHG`、目标、范围、变更类型和当前事实。
2. 收集各阶段产物信封、版本、状态、来源、适用范围和证据。
3. 判断适用阶段、可复用基线、进入条件和缺失责任方。
4. 建立端到端追踪链，允许有依据的不适用节点。
5. 根据变化执行影响和失效传播，区分潜在影响与已确认失效。
6. 按阶段门分别输出评估结果和确认级别。
7. 对阶段推进、问题返回和失效通知创建标准 `HOF`。
8. 输出当前状态、阻塞、风险、下一责任模块和重新评审条件。

## 管理阶段门

使用G0至G7阶段门，但只输出 `Suggested` 结论。输入存在明确授权证据时才记录 `Confirmed`，同时保留责任人、时间、范围和依据。P0只阻塞受影响分支，未受影响且输入可靠的工作可以继续。

## 管理变化与失效

上游或运行事实变化时，不直接删除或重写下游产物。沿追踪链先标记潜在影响，再将实际受影响文档、用例、证据和阶段门置为相应的 `NeedsReview`、`Expired` 或其他原生状态。保留旧版本、替代关系和恢复条件。

## 组织输出

按需输出：

1. `CHG` 摘要和临时/正式状态。
2. 阶段路线及适用性依据。
3. 产物、版本、状态和证据清单。
4. 端到端追踪链和缺口。
5. 阶段门评估与确认级别。
6. 潜在影响、已失效产物和恢复条件。
7. `HOF` 交接包。
8. 当前阻塞、风险和下一责任模块。

局部请求只输出相关视图，不强制生成完整生命周期报告。
