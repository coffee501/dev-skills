---
name: dev-rel
description: Execute approved backend-service and system-integration releases against precisely identified environments, including preflight checks, artifact and configuration deployment, data or state migration, progressive rollout, traffic or feature activation, observation, stop decisions, rollback, forward recovery, and production handoff. Use for release-readiness diagnosis, dry runs, non-production or production deployment, migration execution, canary or phased rollout, rollback, interrupted-release recovery, external release-record import, and release audit. Do not invent release strategy, modify product code, waive validation or authorization, perform unplanned production repair, or own long-term operations and incident RCA.
---

# Dev REL

把已经验证、具有明确发布设计并获得授权的后端与系统集成变更，按照可观察、可停止、可恢复和可审计的方式发布到目标环境。

## 保持职责边界

- `dev-hld/dev-lld` 决定发布、迁移、兼容、回滚和退出策略；本 Skill 只执行已经接受的方案。
- `dev-impl` 负责应用、配置、契约、迁移和发布自动化实现；本 Skill 不修改代码或脚本来促成发布。
- `dev-val` 或项目等价质量流程提供验证证据和门禁；本 Skill 不自行降低测试或质量要求。
- `dev-rel` 拥有 `REL/DEP/MIGRUN/OBS`，但不改写上游设计、实现或验证产物。
- 不把命令成功、迁移完成、观察健康、发布完成和生产长期稳定混为一谈。
- 常规发布后的运行交接给 `dev-ops`；事故止损、生产修复和RCA不属于常规发布执行。
- 不覆盖、清理或回退用户已有的无关修改。

## 接入 Dev 生命周期

复用正式 `CHG`；没有权威登记源时使用 `CHG-PENDING-001` 并标记临时。按 [产物协议](../dev-lc/references/artifact-contract.md) 维护 `REL/DEP/MIGRUN/OBS`，按 [状态与阶段门](../dev-lc/references/lifecycle-state-model.md) 分离发布授权、部署批次、迁移、观察和G6结论。

阶段推进、失败返回和运行交接使用 [交接协议](../dev-lc/references/handoff-contract.md)。候选产物、设计、迁移、配置、验证证据、环境或观察基线变化时，按 [失效传播规则](../dev-lc/references/invalidation-rules.md) 重新评估发布范围和已形成结论。

共享协议不可用时仍可进行非正式就绪分析、Dry Run、非生产发布和本地执行记录，但不得宣称正式全局编号、阶段门或标准HOF已确认。使用本地 `CHG-PENDING-*` 和发布产物编号，并将治理状态标记为待确认。

除非用户明确要求串联流程，否则只形成结构化交接，不自动调用其他 Skill。目标流程不存在时保留交接包，不阻塞其他输入可靠且安全的发布分支。

## 选择工作模式

| 模式 | 使用条件 | 是否改变环境 | 默认输出 |
| --- | --- | --- | --- |
| 发布就绪诊断 | 输入、授权、门禁或恢复条件不足 | 否 | 阻塞、预检和 `HOF` |
| Dry Run/预检 | 需要解析目标、清单和差异 | 通常否 | 预检记录和实际执行计划 |
| 非生产发布 | 专用测试、集成或预生产环境 | 是 | `REL/DEP/OBS` |
| 标准生产发布 | 精确范围已经批准 | 是 | 完整发布记录和运行交接 |
| 灰度或分批发布 | 已批准渐进策略 | 是 | 多批 `DEP/OBS` 和推进决策 |
| 迁移执行 | 数据、Schema、配置或运行状态迁移 | 是 | `MIGRUN`、校验和恢复状态 |
| 配置或契约发布 | 独立配置、开关或契约生效 | 是 | 版本、生效范围和兼容观察 |
| 回滚执行 | 已达到回滚条件且方案可用 | 是 | 回滚 `DEP/MIGRUN/OBS` |
| 发布恢复或续跑 | 中断后需要从检查点继续 | 是 | 已完成步骤、差异和剩余计划 |
| 外部发布记录导入 | 已有平台记录需要纳入治理 | 否 | 来源、完整性和可信度 |
| 发布审计 | 检查授权、版本、证据和偏差 | 否 | 按严重度排序的问题 |

问题严重度统一为：

- **P0**：目标环境、发布候选、授权、执行顺序、停止条件或恢复边界不明确，可能导致不可控生产影响，阻塞受影响发布分支。
- **P1**：可以继续部分准备，但存在显著兼容、数据、观察、容量、安全或运维风险，G6前必须解决或正式接受。
- **P2**：不影响当前安全发布的清晰度、维护性、效率或自动化优化。

P0/P1/P2只表示来源侧问题严重度，不替代发布优先级或事故等级。

## 建立可信输入

按以下优先级读取并保留版本：

1. 已接受的发布、迁移、兼容、回滚和退出设计，包括 `MIG/DDEC/CFG/DVAL`。
2. `dev-impl` 的 `IMP/BUILD`、不可变发布候选、机器契约、迁移文件和配置版本。
3. `dev-cr` 的适用 `REV Approved`，或项目等价独立评审记录与不适用政策。
4. `dev-val` 的有效 `EVD/GATE`，或具有等价治理能力的项目质量门与证据。
5. 符合共享资格规则的 `Eligible CTX` 及其 `CTXF/CTXP/CTXG`，仅用于定位运行单元、依赖、配置、监控和恢复入口。
6. 目标环境、发布窗口、批准记录、责任角色、凭据范围、观察指标、运行手册和外部依赖状态。

外部质量门必须映射来源、版本、环境、适用范围、例外和信任边界；不能仅因缺少 `dev-val` 编号就拒绝独立使用，也不能将未知CI状态当作通过。本 Skill 不自行接受风险，例外必须来自有权限责任方。

## 检查发布进入条件

至少确认：精确目标环境和所有者；不可变发布候选及摘要；适用独立评审；批准范围和窗口；有效质量门或授权例外；执行顺序和中间状态；混合版本兼容；数据、契约、配置和外部副作用；观察指标和基线；停止条件；回滚或前向修复；凭据最小权限；运行交接与责任人。

执行任何可能改变环境的命令前读取 [references/release-safety.md](references/release-safety.md)。以下问题阻塞受影响分支：环境或账号身份未知；候选版本不可证明；生产授权缺失或范围含糊；质量门失败、阻塞或过期且无有效例外；不兼容变化无过渡；不可逆迁移无校验和前向修复；停止或恢复条件不存在；观察入口不可用；真实副作用超出批准范围。

进入条件不足不阻止只读发现、Dry Run、差异检查或交接。

## 按需读取参考文件

- 改变任何环境、配置、数据或流量前读取 [references/release-safety.md](references/release-safety.md)。
- 建立发布单、批次、状态和工作模式时读取 [references/release-model.md](references/release-model.md)。
- 检查候选、授权、质量门、目标和窗口时读取 [references/preflight-authorization.md](references/preflight-authorization.md)。
- 执行应用、配置、契约、基础设施或渐进发布时读取 [references/deployment-execution.md](references/deployment-execution.md)。
- 执行Schema、数据、配置或运行状态迁移时读取 [references/migration-execution.md](references/migration-execution.md)。
- 建立观察窗口、推进、暂停和停止决策时读取 [references/observation-decision.md](references/observation-decision.md)。
- 执行回滚、补偿、前向修复或中断恢复时读取 [references/rollback-recovery.md](references/rollback-recovery.md)。
- 生成正式产物或交接时读取 [references/output-contracts.md](references/output-contracts.md)。
- 完整生产发布、回滚、审计或完成判断前读取 [references/review-checklist.md](references/review-checklist.md)。

## 执行发布流程

1. 读取仓库和平台规则、当前状态与已有修改，确认目标、工具和允许范围。
2. 选择工作模式，锁定 `CHG/HOF`、设计、候选、验证证据、环境、窗口和授权版本。
3. 执行只读发现、目标解析、候选完整性、兼容、容量、依赖、监控、凭据和恢复预检。
4. 创建 `Draft REL`，将部署、迁移、配置、流量、观察和恢复步骤拆成有后置条件的批次。
5. 只有存在精确授权记录时将 `REL` 置为 `Approved`；冻结批准清单，不在执行中静默扩展。
6. 保存发布前版本、配置、数据不变量、流量、指标、告警和依赖基线。
7. 按批准顺序逐批执行 `DEP/MIGRUN`，每一步记录实际命令或流水线、目标、时间、结果和原始定位器。
8. 每批完成后验证版本、健康、契约、数据不变量、业务指标和停止条件，再决定是否推进。
9. 只按预先批准的条件继续、暂停、有限重试、回滚、补偿或前向修复；未知异常停止扩大影响。
10. 创建并维护 `OBS`，覆盖灰度、全量和规定观察窗口；不得只检查进程存活或命令退出码。
11. 验证迁移差异、临时资源、旧路径、队列、任务和开关状态；记录未清理内容及退出条件。
12. 形成最终发布状态、残余风险、失效条件和面向 `dev-ops` 的 `Prepared HOF`。

使用项目已有CI/CD、IaC、迁移、配置和流量工具，不为统一入口引入通用部署框架。生成或交换JSON形式发布产物时可以使用 `scripts/validate_release_artifact.py` 校验最低字段和状态；脚本不替代授权、安全预检或语义评审。

## 管理执行和观察

- `REL` 状态使用 `Draft → Approved → Deploying → Observing → Completed / RolledBack / Failed`。
- `DEP`、`MIGRUN`、`OBS` 使用共享状态模型中的各自状态，不用一个“成功”覆盖全部对象。
- 发布候选、命令、目标、凭据身份、执行者、时间、输出、后置检查和恢复动作必须可追踪。
- 发布验证由 `OBS` 记录；若需要形成或更新正式验证证据，交接 `dev-val`，本 Skill 不创建 `EVD/GATE`。
- 部署成功但观察失败时，`REL`不得进入 `Completed`。
- 观察窗口内健康只支持当前范围和时间，不等于长期生产稳定。

## 控制停止、回滚和前向修复

继续、暂停、重试、回滚、补偿和前向修复必须具有预先定义的条件。重试仅适用于可幂等重放且失败原因明确的步骤；保留首次失败和全部尝试。

不要把“应用版本可回滚”写成“整个发布可回滚”。分别检查新数据、新状态、新消息、Schema、配置、外部副作用和在途业务能否由旧版本继续处理。无法安全回滚时停止受影响扩展，执行已批准的前向修复或交接事故流程。

## 交接问题

- 业务、架构或详细发布策略缺口交接 `dev-req/dev-hld/dev-lld`。
- 发布候选、迁移文件、配置、脚本或自动化问题交接 `dev-impl`。
- 质量门、验证证据或发布后重新验证问题交接 `dev-val`。
- 环境平台、审批、安全、合规、供应方或项目治理问题交给对应正式责任流程。
- 常规发布完成后交接 `dev-ops`；已经形成事故影响时立即进入事故流程，不继续扩大常规发布。

P0只阻塞受影响发布分支；其他批次只有在隔离、顺序和恢复边界仍然成立时才能继续。

## 检查发布完成

只有全部适用条件满足才建议发布完成：批准范围内的 `DEP/MIGRUN` 已进入终态；目标版本、配置、契约和数据状态可确认；观察窗口及强制指标满足；失败、重试、偏差和人工动作完整保留；停止和恢复决策有证据；迁移已经校验或明确残差；临时资源和旧路径具有清理或退出条件；发布前验证仍适用；残余风险和例外没有被隐藏；面向 `dev-ops` 的运行交接已形成。

发布完成不表示生产长期稳定、事故风险消失或后续兼容清理已经完成。

## 组织输出

- **就绪诊断**：目标、候选、环境、授权、质量门、预检、P0/P1、可继续工作和 `HOF`。
- **发布单**：`REL`、批准范围、批次、顺序、窗口、停止、恢复和责任角色。
- **执行记录**：`DEP/MIGRUN`、实际目标、版本、命令或流水线、结果、重试和原始定位器。
- **观察决策**：`OBS`、基线、指标、异常、推进/暂停/回滚决策和观察限制。
- **最终结果**：完成、回滚或失败状态，实际差异、残余风险、失效条件和退出项。
- **运行交接**：生产版本、配置、数据和迁移状态、监控、告警、人工入口及面向 `dev-ops` 的HOF。

局部请求只输出相关视图，不强制生成完整发布报告。
