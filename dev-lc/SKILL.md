---
name: dev-lc
description: "定义并评估后端与集成变更的生命周期状态、阶段适用性、门禁、追踪、失效和交接。"
---

# Dev LC

建立一次后端或系统集成变更的统一生命周期视图，定义并评估阶段适用性、产物、版本、状态、证据、阻塞、失效和交接。专业 Skill 负责内容，本 Skill 是生命周期规则和状态权威，不负责运行时调度。

## 保持控制面边界

- 不生成或改写需求、架构、详细设计、测试预期或实现方案。
- 不接受设计决策、风险或阶段门。
- 不自动调用其他 Skill，不执行实现、测试、发布或生产操作。
- 不创建 `WIT/SWI`，不选择Agent、并行组、尝试次数或运行模式。
- 不把阶段完成、文档基线、实现完成和验证通过混为一谈。
- 不因缺少某个下游模块而伪造其正式产物。

## 读取体系协议

- 建立或检查编号、版本、产物清单和追踪链时，读取 [references/artifact-contract.md](references/artifact-contract.md)。
- 判断对象状态、阶段门和确认级别时，读取 [references/lifecycle-state-model.md](references/lifecycle-state-model.md)。
- 创建阶段推进、问题返回或责任转移时，读取 [references/handoff-contract.md](references/handoff-contract.md)。
- 上游、实现、测试或环境发生变化时，读取 [references/invalidation-rules.md](references/invalidation-rules.md)。
- 创建或校验 `CHG/HOF/LCV` 时，读取 [references/output-contracts.md](references/output-contracts.md)。
- 判断设计、实现、测试或调度是否存在无依据复杂度或机械拆分时，读取 [references/complexity-governance.md](references/complexity-governance.md)。
- 维护 Codex、Claude Code 或其他 Agent Skills 客户端的发现和触发适配时，读取 [references/tool-compatibility.md](references/tool-compatibility.md)。
- 向调度器提供路线或处理路线变更请求时，读取 [references/orchestration-interface.md](references/orchestration-interface.md)。
- 外置保存 `CHG/HOF/LCV` 或检查项目写入边界时，读取 [references/external-state-contract.md](references/external-state-contract.md)。

## 建立 CHG 上下文

优先复用现有正式 `CHG`。不存在权威编号时使用 `CHG-PENDING-001` 并标记临时，不宣称全局唯一。记录目标、范围、非范围、变更类型、目标版本、责任角色和验证边界。

识别新功能、已有功能变更、规则调整、缺陷修复、系统集成、契约变化、迁移实现、功能下线、架构迁移或紧急修复。纯文档整理且不改变语义时允许只进入相关阶段。

## 评估阶段适用性

| 模块 | 责任 |
| --- | --- |
| `dev-ctx` | 存量项目的业务、架构、流程、数据和运行上下文发现 |
| `dev-req` | 需求、规则、业务语义和验收基线 |
| `dev-hld` | 系统边界、模块职责和概要决策 |
| `dev-lld` | 实现级详细设计、契约和迁移方案 |
| `dev-fia` | 将后端接口、事件和机器契约转为前端消费与联调文档 |
| `dev-impl` | 代码、配置、契约和迁移实施 |
| `dev-cr` | 独立实现审查、问题分级、结论和整改复审 |
| `dev-test` | 测试场景、用例、数据和自动化设计 |
| `dev-val` | 测试执行、证据、失败分类和门禁建议 |

不要机械要求全部阶段串行出现。`dev-ctx` 是存量系统或上下文未知时的按需发现阶段，不是新项目的强制门；测试设计
可以从需求阶段开始；局部缺陷可以复用有效需求和设计基线。
存在前端消费方时，`dev-fia` 在适用的字段级契约形成后按需加入路线，不作为新的串行阶段门；它不生成前端代码，
也不替代 `dev-lld`、`dev-test` 或 `dev-val`。

将适用阶段、硬依赖、进入条件、预期产物、停止条件和不适用依据写入版本化 `LCV.route`。不要写入Agent、并行组、
尝试次数或执行状态。跨越三个以上专业阶段、需要并行协调、复杂迁移实现或反复交接时，可以把当前路线交给显式
`dev-orch` Skill/Agent；单阶段或简单双阶段请求直接使用专业 Skill。

## 执行治理流程

1. 建立 `CHG`、目标、范围、变更类型和当前事实。
2. 收集各阶段产物信封、版本、状态、来源、适用范围和证据。
3. 判断适用阶段、可复用基线、进入条件和缺失责任方。
4. 建立端到端追踪链，允许有依据的不适用节点。
5. 根据变化执行影响和失效传播，区分潜在影响与已确认失效。
6. 按阶段门分别输出评估结果和确认级别。
7. 对阶段推进、问题返回和失效通知创建标准 `HOF`。
8. 处理 `dev-orch` 提交的 `route_change_request`，产生后继 `LCV` 或拒绝变更并说明依据。
9. 输出当前状态、阻塞、风险、下一责任模块和重新评审条件。

使用 `scripts/validate_artifact_envelope.py` 校验任意正式JSON产物的统一信封，使用
`scripts/validate_lifecycle_artifact.py` 校验 `CHG/HOF/LCV` 增量规则，使用 `scripts/validate_suite.py` 检查整套
Skill的元数据、链接、共享契约和端到端行为用例。校验器不替代内容评审、权限确认或实际阶段推进。

## 管理阶段门

使用G0至G5阶段门，但只输出 `Suggested` 结论。输入存在明确授权证据时才记录 `Confirmed`，同时保留责任人、时间、范围和依据。P0只阻塞受影响分支，未受影响且输入可靠的工作可以继续。

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

`dev-lc` 的生命周期结论与 `dev-orch` 的调度完成状态相互独立；不得根据任务均已终止直接确认阶段门或关闭 `CHG`。

局部请求只输出相关视图，不强制生成完整开发生命周期报告。
