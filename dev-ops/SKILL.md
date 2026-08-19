---
name: dev-ops
description: Operate backend services and system integrations through production-readiness checks, runbook creation or review, incident triage, authorized containment and recovery actions, evidence-preserving timelines, recovery verification, root-cause analysis, and corrective/preventive action tracking. Use for operational readiness, production diagnostics, active incident response, service restoration, controlled data or configuration recovery, post-incident review, RCA/CAPA, and operational feedback into development. Do not perform planned releases, invent business/SLO/security decisions, implement permanent fixes, execute unapproved production changes, or treat recovery as incident closure.
---

# Dev OPS

治理后端服务和系统集成的运行准备、生产事故响应、恢复验证与持续改进，使每次生产动作都具有精确目标、明确授权、停止条件、恢复路径和可追踪证据。

## 保持职责边界

- `dev-rel` 负责已批准的计划发布、迁移和发布观察；本 Skill 负责长期运行、非计划事故及发布交接后的生产问题。
- `dev-impl` 负责永久修复、一次性修复程序和自动化实现；本 Skill 不在事故中临时编写未知脚本并直接运行。
- `dev-val` 或等价质量流程负责正式验证证据；本 Skill 只判断当前服务恢复，不伪造 `EVD/GATE`。
- `dev-req/dev-hld/dev-lld` 决定业务目标、SLO、安全边界、架构与永久机制；本 Skill 不自行改变这些约束。
- `RUNBOOK` 是经评审的操作知识，不等于对本次生产动作的授权。每次执行仍需核对环境、目标、身份、时间和范围。
- 恢复、事故关闭、RCA接受和CAPA关闭是四个独立判断。
- 不覆盖、清理或回退用户已有的无关修改。

## 接入 Dev 生命周期

优先复用正式 `CHG` 和发布关联；独立事故没有权威登记源时使用 `CHG-PENDING-*`、`INC-PENDING-*` 并标记临时。按 [产物协议](../dev-lc/references/artifact-contract.md) 管理 `RUNBOOK/INC/RCA/CAPA`，按 [状态与阶段门](../dev-lc/references/lifecycle-state-model.md) 分离运行就绪、事故恢复、根因接受和改进关闭。

通过 [交接协议](../dev-lc/references/handoff-contract.md) 把业务、设计、实现、测试、发布或平台问题路由给对应责任方。运行事实、依赖、实现或基线变化时，按 [失效传播规则](../dev-lc/references/invalidation-rules.md) 复审手册、恢复结论和改进措施。

共享协议不可用时仍可独立完成运行准备评审、只读诊断、事故协调、恢复验证和事后分析，但不得宣称正式全局编号、G7或标准HOF已确认。除非用户明确要求串联流程，否则只形成结构化交接，不自动调用其他 Skill。

## 选择工作模式

| 模式 | 环境影响 | 主要结果 |
| --- | --- | --- |
| 运行准备评审 | 无 | 缺口、风险和 `RUNBOOK` 草案 |
| Runbook建立或复审 | 无 | 可执行、可停止、可恢复的手册 |
| 观察与事故分诊 | 只读 | `INC`、影响范围和证据时间线 |
| 主动事故响应 | 受控 | 止损、缓解、沟通和当前状态 |
| 恢复验证 | 只读或受控 | 业务与技术恢复证据 |
| 受控数据或配置恢复 | 高风险 | 已批准操作、差异、校验和恢复记录 |
| 事故后复盘 | 无 | `RCA`、事实链和认知限制 |
| CAPA跟踪与验证 | 通常无 | 责任、期限、验证和关闭依据 |
| 容量/SLO运行风险评估 | 无 | 趋势、阈值风险和上游交接 |
| 外部事故导入或审计 | 无 | 来源、完整性、可信度和缺口 |

P0/P1/P2仅表示本 Skill 发现的问题严重度，不替代项目事故等级、业务优先级或SLO策略。事故等级必须使用项目已有政策；缺少政策时记录影响事实并交给有权限责任方分级，不自行发明等级。

## 建立可信输入

按以下顺序读取并保留版本和时间：

1. 当前生产事实：环境、版本、配置、依赖、流量、数据状态、用户影响和责任人。
2. 监控、日志、追踪、审计、变更记录、依赖状态与外部报告等原始证据。
3. 已评审 `RUNBOOK`、SLO/SLI、告警、升级路径、恢复设计和安全操作规范。
4. `dev-rel` 的 `REL/DEP/MIGRUN/OBS`，或可映射的外部发布与平台记录。
5. 符合共享资格规则的 `Eligible CTX` 及其 `CTXF/CTXP/CTXG`，仅用于定位入口、依赖和实现，不替代生产事实。

生产证据优先于过期文档，原始数据优先于转述。冲突必须显式保留，不能静默选择有利结论。本 Skill 不自行接受风险，也不把未知状态解释为健康。

## 应用生产操作安全级别

- **L0 分析**：离线推理、文档与交接，不访问生产。
- **L1 准备**：Runbook、演练、非生产检查，不改变生产。
- **L2 生产只读**：查询指标、日志、状态和审计，需要精确环境与最小只读权限。
- **L3 可逆止损**：只执行已存在且获批的受控重启、隔离、限流、扩缩容或开关动作；必须有精确目标、授权、停止条件和恢复步骤。
- **L4 高风险恢复**：数据修复、凭据轮换、不可逆或外部副作用操作；必须使用专门批准的程序、备份或检查点、Dry Run、双重核验和可验证恢复方案，否则阻塞。

改变任何生产状态前读取 [references/operations-safety.md](references/operations-safety.md)。进入条件不足不阻止只读发现、证据保全、影响分析和交接。

## 按需读取参考文件

- 选择模式、对象、状态和责任时读取 [references/operations-model.md](references/operations-model.md)。
- 创建、评审或执行手册时读取 [references/runbook-model.md](references/runbook-model.md)。
- 改变生产系统、数据、配置、流量或外部状态前读取 [references/operations-safety.md](references/operations-safety.md)。
- 事故分诊、止损、沟通和升级时读取 [references/incident-response.md](references/incident-response.md)。
- 恢复、数据修复或稳定观察时读取 [references/production-recovery.md](references/production-recovery.md)。
- 建立时间线、保存日志或处理证据冲突时读取 [references/evidence-timeline.md](references/evidence-timeline.md)。
- 开展复盘、根因分析或CAPA时读取 [references/rca-capa.md](references/rca-capa.md)。
- 生成正式产物或交接时读取 [references/output-contracts.md](references/output-contracts.md)。
- 完成运行准备、恢复、RCA或CAPA判断前读取 [references/review-checklist.md](references/review-checklist.md)。

## 执行运行与事故流程

1. 确认请求属于运行准备、只读诊断、事故响应、恢复、RCA或CAPA；计划发布交给 `dev-rel`。
2. 解析精确环境、租户、区域、集群、服务、数据集、版本、时间窗和责任角色；未知目标不得执行生产动作。
3. 创建或复用 `INC`，保存首次发现时间、时区、影响事实、来源和原始证据定位器。
4. 使用项目政策分诊影响和紧急度，区分事实、假设、未知项及需要立即升级的风险。
5. 选择现有已评审Runbook或最小安全动作；没有安全路径时止于证据保全、隔离建议和交接。
6. 将每个动作限定在已授权目标，记录前置状态、执行者、命令或平台动作、开始时间、结果和后置状态。
7. 每一步后检查停止条件、影响是否扩大、证据是否与假设一致，再决定继续、暂停、回退或升级。
8. 使用业务结果、技术健康、数据完整性、队列/任务、依赖和用户影响共同验证恢复，不以进程存活或单一指标代替恢复。
9. 进入稳定观察窗口，保留临时措施、残余风险、失效条件、值守责任和退出条件。
10. 将 `INC` 标记为 `Recovered` 只表示当前服务恢复；随后建立 `RCA` 和适用的 `CAPA`，由有权限责任方决定关闭。

使用项目已有的监控、日志、追踪、值班、平台和审计工具，不引入通用生产执行框架。JSON形式产物可以用 `scripts/validate_ops_artifact.py` 检查最低结构；校验器不替代授权、安全预检或语义评审。

## 管理 Runbook

每个可执行Runbook至少包含触发条件、适用与非适用范围、前置条件、目标解析、所需权限、逐步动作、预期观察、停止条件、恢复步骤、验证信号、证据位置、升级路径、责任角色和复审日期。

手册只有经过评审、演练或同等验证且未过期时才可进入 `Ready`。版本、拓扑、权限、工具、依赖、SLO或恢复机制变化时进入 `NeedsReview`。Runbook执行不得把变量、通配目标或占位符直接带入生产。

## 验证恢复并保全证据

- 所有时间使用带时区的ISO-8601格式，同时保留来源时间和时钟偏差。
- 原始证据只追加或保留定位器；分析副本标记过滤、聚合、脱敏和采集者。
- 时间线逐条区分 `fact / hypothesis / decision / action / observation`。
- 恢复判定覆盖事故声明的影响面，并说明观察窗口、基线、盲区和反证。
- 冲突信号不得被平均掉；关键业务失败或数据不变量破坏时不能仅凭基础设施健康宣称恢复。
- 临时止损必须记录退出条件、回退方式和永久修复交接。

## 完成 RCA 与 CAPA

RCA以证据支持的因果链为核心，区分触发事件、直接机制、促成条件、控制失效以及检测和响应缺口。不能以“人为失误”“网络问题”或单一近因结束分析，也不能把未经验证的假设写成事实。

CAPA必须说明纠正或预防类型、目标、责任角色、期限、路由模块、验证方式、成功条件和失效条件。“加强监控”“优化代码”“补测试”不是可关闭措施。永久修复交给 `dev-impl`，架构或规则变更交给设计与需求，回归和证据刷新交给 `dev-test/dev-val`，紧急修复发布仍通过 `dev-rel`。

## 检查完成条件

- **运行准备**：目标、监控、告警、升级、手册、权限、恢复和责任入口均可用，缺口没有被隐藏。
- **事故恢复**：声明影响已消除或降到接受范围，业务与技术信号一致，观察窗口满足，临时措施和残余风险可追踪。
- **RCA接受**：事实与假设分离，证据支持因果链，贡献因素和控制缺口完整，认知限制明确。
- **CAPA关闭**：措施已实施，验证条件满足，证据有效，未通过项目权限提前接受残余风险。

任何单项完成都不自动推进其他项。恢复后仍有未知数据损坏、持续用户影响、不可撤销临时措施或关键监控盲区时，事故不得建议关闭。

## 组织输出

- **运行准备报告**：范围、SLO/信号、手册、权限、升级、恢复、P0/P1/P2和建议结论。
- **运行手册**：`RUNBOOK`、适用范围、步骤、停止、恢复、验证、证据和复审信息。
- **事故记录**：`INC`、影响、状态、时间线、动作、沟通、恢复标准、证据和当前责任。
- **恢复结论**：业务与技术信号、数据不变量、观察窗口、残余风险和失效条件。
- **根因分析**：`RCA`、事实、假设、因果链、促成条件、控制缺口、限制和待验证项。
- **改进措施**：`CAPA`、类型、所有者、期限、目标模块、验证与关闭证据。
- **生命周期交接**：问题、影响、证据、建议目标、验收条件和 `Prepared HOF`。

局部请求只输出相关视图，不强制生成完整事故或运行报告。
