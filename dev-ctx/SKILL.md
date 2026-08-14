---
name: dev-ctx
description: Build and refresh evidence-backed As-Is implementation context for existing backend services and system integrations. Use when Codex must understand how a repository or feature currently works; identify modules, entry points, call paths, contracts, data stores, events, jobs, configuration, dependencies, deployment units, tests, or operational surfaces; answer implementation questions; or prepare reusable current-state evidence and impact context for dev-req, dev-hld, dev-lld, dev-impl, dev-test, dev-val, dev-rel, or dev-ops. Prefer repository evidence and use GitNexus as an optional accelerator. Do not invent business intent, make design decisions, assess code quality unless asked, or modify the target implementation by default.
---

# Dev CTX

建立现有项目的可追溯As-Is实现上下文，让后续研发流程基于事实工作，而不是重新猜测代码。默认只读；只有用户明确
要求落盘时才写入上下文产物，并且不修改目标实现。

## 保持职责边界

- 描述系统现在如何实现，不把实现事实写成业务意图、正确需求或目标设计。
- 不创建 `REQ/RULE/AC`、`DEC/MOD/FLOW`、`DET/DDEC`、`IMP` 或 `TC`。
- 不因为代码存在就断言生产启用、运行正常、数据完整或行为符合业务预期。
- 不默认做代码质量、安全或性能评审；发现明显风险只记录证据和影响面，交给对应流程。
- 不要求所有项目生成固定文档集，也不强制依赖GitNexus或特定技术栈。

## 接入 Dev 生命周期

按 [产物协议](../dev-lc/references/artifact-contract.md) 输出 `CTX/CTXF/CTXP/CTXG`。发生正式责任转移或上下文缺口阻塞
下游时，按 [交接协议](../dev-lc/references/handoff-contract.md) 创建 `Prepared HOF`。代码、契约、配置、数据模型、部署
或运行证据变化时，按 [失效传播规则](../dev-lc/references/invalidation-rules.md) 重新评估上下文新鲜度。

## 选择工作模式

| 模式 | 使用条件 | 默认输出 |
| --- | --- | --- |
| 定向理解 | 用户询问功能、流程、接口、数据或某个符号如何工作 | 与问题相关的事实、路径、证据、未知项 |
| 项目基线 | 后续多个阶段需要共同的现状输入 | 范围受控的 `CTX` 上下文包 |
| 增量刷新 | 代码、契约、配置或部署发生变化 | 受影响事实、路径、失效项和新版本 |
| 上下文评审 | 已有项目说明或 `CTX` 需要核对 | 冲突、过期、无证据结论和修订建议 |

默认选择满足当前任务的最小范围。只有用户明确需要项目手册或全局基线时才扩展到整个项目。

## 按需读取参考文件

- 建立事实、证据等级、冲突和新鲜度时读取 [references/evidence-model.md](references/evidence-model.md)。
- 调查项目、功能或执行路径时读取 [references/discovery-playbook.md](references/discovery-playbook.md)。
- 输出正式上下文包和稳定编号时读取 [references/context-package.md](references/context-package.md)。
- 为后续 Dev Skill 准备定制视图或交接时读取 [references/consumer-views.md](references/consumer-views.md)。
- 增量刷新、代码变更或索引变化时读取 [references/incremental-refresh.md](references/incremental-refresh.md)。
- 输出 `Ready` 结论或评审已有上下文时读取 [references/review-checklist.md](references/review-checklist.md)。

## 执行上下文发现

1. 读取仓库规则，确定目标仓库、范围、版本或工作区状态，以及下游使用目的。
2. 选择定向、基线、增量或评审模式，定义明确的停止条件，避免无界扫描。
3. 建立来源清单：代码、机器契约、配置、迁移、测试、构建部署、文档、运行证据和可用索引。
4. 从入口和边界开始，识别模块、运行单元、外部系统、数据存储及权威实现位置。
5. 沿目标场景追踪调用、状态、数据、副作用、事件、任务、失败和恢复路径。
6. 将每个结论分类为实现事实、运行事实、业务声明或推断，并绑定文件、符号、版本和证据。
7. 对动态调用、反射、配置路由、消息、数据库耦合、生成代码和仓外依赖保留未知或潜在影响。
8. 生成适合当前消费者的最小 `CTX` 视图，记录覆盖范围、未覆盖范围、冲突、新鲜度和失效条件。
9. 需要正式传递时创建 `Prepared HOF`；不由本 Skill 接受下游决策或阶段门。

## 使用 GitNexus

GitNexus可加速仓库发现、符号上下文、调用路径、流程和影响半径分析。使用前确认目标仓库与索引版本；结果尽量回指
代码、契约或配置位置。索引缺失、过期或无法表达动态行为时，回退到仓库搜索、构建模型、测试和运行资料，不阻塞
上下文发现。图聚类是代码结构信号，不自动等于业务域；未发现路径也不证明路径不存在。

## 判断上下文就绪

`Ready` 只表示声明范围内具备足够、可追溯且当前有效的实现上下文，不表示理解了整个系统。至少满足：范围、版本和
消费者明确；关键事实与路径有证据；事实、推断和业务声明已分离；直接和重要间接依赖已检查；未知、冲突、动态路径
和仓外边界已记录；失效条件明确。否则保持 `Draft`，但仍可交付已确认部分。

## 组织输出

- **定向理解**：结论、实现路径、关键事实、证据、未知和下游影响。
- **项目基线**：`CTX` 摘要、系统与运行单元、实现表面、关键 `CTXP`、依赖、证据索引和 `CTXG`。
- **增量刷新**：变化来源、受影响 `CTXF/CTXP`、保留项、新增项、失效项和新版本。
- **上下文评审**：按严重度列出无证据、过期、冲突、范围遗漏和错误层级结论。
- **交接**：消费者、输入版本、可依赖事实、不得推断内容、未知项和建议的下一责任流程。

图只在关系明显比文字更易理解时生成；不要为文档完整性强制生成固定数量或类型的图。
