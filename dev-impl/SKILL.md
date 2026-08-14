---
name: dev-impl
description: Implement approved backend-service and system-integration changes from requirements, HLD, LLD, test-automation specifications, and current repository evidence. Use when Codex must modify application or test code, machine-readable contracts, database migrations, configuration, jobs, events, or integration adapters; apply a defect fix or behavior-preserving refactor; run local build, lint, type, static, contract, migration, or targeted-test checks; and produce traceable IMP/BUILD artifacts plus review and dev-val handoffs. Do not change business or architecture decisions, produce formal EVD/GATE validation evidence, deploy releases, or operate production systems.
---

# Dev IMPL

将已确认的后端与系统集成设计转化为范围受控、可追踪、可评审、可验证和可恢复的实际实现。优先遵循目标仓库的 `AGENTS.md`、工程约定和现有模式。

## 保持职责边界

- 复用 `dev-lc` 或项目系统提供的 `CHG`；没有正式编号时可以引用共享规则生成的
  `CHG-PENDING-*`，但不得宣称全局唯一、拥有登记权或自行决定变更拆分合并。
- 不改变 `REQ/RULE/AC`、系统边界、模块职责、数据权威或已接受 `DEC/DDEC`。
- 不用实现便利性替代业务、架构或失败语义决策。
- `AUT` 规格归 `dev-test`；本 Skill 只实现其对应测试代码并建立 `IMP(kind=test-automation)`。
- `BUILD` 只记录实现阶段本地检查；正式 `RUN/EVD/GATE` 归 `dev-val`。
- 不执行发布、生产迁移、生产流量或生产数据操作；分别交接 `dev-rel` 或 `dev-ops`。
- 不覆盖、清理或回退用户已有的无关修改。

## 接入 Dev 生命周期

按 [产物协议](../dev-lc/references/artifact-contract.md) 维护 `IMP/BUILD`，按 [状态与阶段门](../dev-lc/references/lifecycle-state-model.md) 区分实现、本地检查、独立验证和发布状态。阶段推进、问题返回和责任转移使用 [交接协议](../dev-lc/references/handoff-contract.md)。设计、契约、代码、数据或配置变化时按 [失效传播规则](../dev-lc/references/invalidation-rules.md) 标识潜在影响。

存在范围和版本匹配的有效 `CTX` 及其引用的 `CTXF/CTXP/CTXG` 时，将其作为As-Is和影响分析输入；实施前仍核对当前工作区与目标
版本，只刷新变更涉及的事实和路径。`CTX` 不替代批准设计、实际代码检查或 `BUILD` 证据。

## 选择工作模式

| 模式 | 使用条件 | 默认输出 |
| --- | --- | --- |
| 实现诊断 | 输入不足、冲突或无法安全修改 | 有效输入、P0/P1、影响和 `HOF` |
| 新功能实现 | 新模块或新能力 | `IMP`、实际变更、`BUILD` |
| 增量变更 | 已有功能、规则或契约变化 | As-Is/To-Be、保持项、最小修改和回归影响 |
| 缺陷修复 | 已知失败、缺陷或事故永久修复 | 根因条件、最小修复、邻近回归和 `BUILD` |
| 行为保持重构 | 外部行为和契约必须不变 | 行为基线、结构修改和等价验证 |
| 迁移实现 | 数据、契约、配置或运行状态迁移 | 迁移文件、校验、重复执行和恢复设计 |
| 自动化实现 | 已有稳定 `AUT/TC` | 测试代码、夹具、断言和执行入口 |
| 评审整改 | 已有评审或安全问题 | 问题到修改映射及重新检查结果 |

问题严重度统一为：

- **P0**：无法安全编码、会改变未确认行为、造成不兼容或不可恢复风险，阻塞受影响实现分支。
- **P1**：可以继续局部实现，但存在显著正确性、兼容性、安全、性能或运维风险，G4前必须解决或正式接受。
- **P2**：不影响当前正确性和交付的清晰度、维护性或工程优化。

严重度只表达来源侧问题，不替代目标流程的处理优先级。P0只阻塞受影响分支。

## 检查实现进入条件

以下高风险变更必须具有已基线的G3详细设计：不兼容API、事件或数据契约；Schema或历史数据迁移；跨模块事务和
一致性变化；权限或安全边界变化；公共接口或共享配置变化；分布式任务、并发或幂等机制变化；不可逆或只能前向
修复的变更。G3失效或对应设计缺失时阻塞受影响分支，不以实现经验补齐设计。

不涉及上述风险的局部修复或内部实现调整可以使用最小实现输入包：变更目标和范围、有效预期来源、必须保持内容、
目标仓库和允许修改范围、当前实现证据、验证方式以及恢复边界。无法证明属于低风险时按高风险处理。

以下问题阻塞受影响实现分支：业务结果或失败语义不明确；需要改变架构边界但没有决策；数据或契约不兼容且没有过渡方案；不可逆迁移没有恢复或前向修复原则；目标或影响范围无法识别；共享、生产或真实副作用未经授权。未受影响且输入可靠的分支可以继续。

## 按需读取参考文件

- 拆分、维护或汇报 `IMP/BUILD` 时读取 [references/implementation-unit.md](references/implementation-unit.md)。
- 修改代码、依赖、数据、配置或运行环境前读取 [references/execution-safety.md](references/execution-safety.md)。
- 已有代码、存量功能变更、缺陷修复或重构时读取 [references/brownfield-change.md](references/brownfield-change.md)。
- 涉及数据、Schema、契约、配置或运行状态迁移时读取 [references/migration-implementation.md](references/migration-implementation.md)。
- 实现 `AUT`、测试夹具或测试基础设施时读取 [references/automation-implementation.md](references/automation-implementation.md)。
- 需要输出正式实现记录或跨流程交接时读取 [references/delivery-template.md](references/delivery-template.md)。
- 输出实现完成建议或执行完整评审前读取 [references/review-checklist.md](references/review-checklist.md)。

## 执行实现流程

1. 读取仓库规则、工作区状态和当前用户修改，确认目标仓库与允许范围。
2. 接收并核对 `CHG/HOF`、上游产物版本、保持项、未决风险和实现进入条件。
3. 建立代码、测试、契约、数据访问、配置、任务、依赖和运行单元的As-Is证据基线。
4. 分析直接与间接影响，区分确定影响、潜在影响和不适用项。
5. 按单一主要目标拆分 `IMP`，明确依赖、修改范围、恢复方式和本地检查。
6. 变更既有行为前先确认可证明保持项的测试或其他回归证据。已有 `AC/TC`、权威契约或缺陷复现条件足以确定
   预期时，可以补充代码级最小回归保护并记录 `IMP(kind=test-automation)`；需要新增业务预期、判定依据或正式
   自动化规格时交接 `dev-test`，不得自行创建或改写 `AUT`。
7. 使用 `apply_patch` 实施小范围修改；优先复用现有模式、工具和依赖，避免无依据抽象。
8. 对机器可读契约、模型或Schema使用权威定义，避免维护易漂移的重复副本。
9. 先执行受影响范围内最小检查，再按风险扩展到类型、静态、构建、契约和相关测试。
10. 记录 `BUILD`、失败分类、未运行检查、设计偏差和剩余风险。
11. 更新 `IMP` 状态和追踪，传播需要复审的 `TC/AUT/EVD/GATE/REL`，不得自行改写其状态。
12. 形成代码评审输入和面向 `dev-val` 的 `HOF`；未达到完成条件时明确阻塞和可继续内容。

## 处理设计偏差

实现中发现设计不可行、成本或风险显著变化时，停止受影响分支并形成 `Prepared HOF`：说明问题证据、受影响编号、候选影响、已经完成的安全工作和恢复条件。业务问题返回 `dev-req`，架构问题返回 `dev-hld`，实现机制问题返回 `dev-lld`，测试预期问题返回 `dev-test`。不得静默修改设计以适配代码。

## 管理本地检查

按修改风险选择最小充分检查：格式或Lint、类型检查、编译构建、目标单元或组件测试、契约校验、迁移静态校验、兼容检查和必要的安全静态分析。读取每条命令的实际输出后再报告结果。

区分编译或实现失败、测试缺陷、环境或依赖失败、设计缺口和安全阻断。重试不得掩盖首次失败。无法运行的检查记录原因、影响和交给 `dev-val` 的验证要求。

## 检查实现完成

只有全部适用条件满足才建议实现完成：计划内 `IMP` 已实施；实际修改可追踪到有效输入；代码、契约、配置和迁移一致；必要 `BUILD` 检查通过；用户修改未被覆盖；迁移和不兼容变化可恢复；设计偏差已解决或交接；下游潜在影响已经标识；代码评审输入和 `dev-val` 交接已形成。

实现完成不表示代码评审通过、`VAL/DVAL`通过、发布获批或生产稳定。`Reviewed/Integrated` 状态只有存在相应评审或集成证据时才能使用。

## 组织输出

- **诊断**：有效输入、进入条件、As-Is、P0/P1、可继续工作和 `HOF`。
- **实施结果**：`CHG`引用、`IMP`状态、变更文件和符号、保持项、实际偏差。
- **BUILD**：候选版本、工作区、依赖摘要、环境、命令时间与退出码、产物、限制和失败分类。
- **影响传播**：需要复审或重新验证的测试、证据、门禁和发布产物。
- **交接**：代码评审输入、面向 `dev-val` 的版本化 `HOF`、剩余风险和验证要求。

完整实现或完成判断前读取评审清单；局部修改只执行与风险直接相关的检查。
