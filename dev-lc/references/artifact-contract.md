# Dev 体系产物协议

## 目标

让所有 `dev-*` Skill 以相同方式标识变更、版本、来源、适用范围、风险和证据。专业 Skill 负责内容，`dev-lc` 只汇总元数据和关系。

当前协议版本为 `DEV-SUITE-7.1`。新增向后兼容字段时增加次版本；删除字段、改变含义、状态语义或 Skill 标识时增加主版本，并对存量产物提供迁移和兼容说明。

## Skill 缩写

| 当前名称 | 缩写含义 | 原名称 |
| --- | --- | --- |
| `dev-ctx` | Development Context | `project-understanding` |
| `dev-req` | Requirements | `dev-requirements` |
| `dev-hld` | High-Level Design | `dev-overview` |
| `dev-lld` | Low-Level Design | `dev-details` |
| `dev-fia` | Frontend Interface Alignment | 新增 |
| `dev-impl` | Implementation | `dev-implementation` |
| `dev-cr` | Code Review | 新增 |
| `dev-test` | Test Design | `dev-test-cases` |
| `dev-val` | Validation | `dev-validation` |
| `dev-rel` | Release | `dev-release` |
| `dev-ops` | Operations | `dev-operations` |
| `dev-lc` | Lifecycle Control | `dev-lifecycle` |
| `dev-orch` | Orchestration | 新增跨平台调度入口 |

`DEV-SUITE-2.0` 起只在新产物、交接和提示中使用当前名称。历史资料中的原名称按本表解释，不批量改写已有外部证据。

`DEV-SUITE-3.0` 为 `IMP` 增加 `Blocked/Aborted/Superseded` 状态并增强 `BUILD` 可复现字段。旧版
`Planned/InProgress/Implemented/Reviewed/Integrated` 状态含义保持不变；历史产物不重写，继续按其原协议版本解释。
旧产物迁入3.0时补充适用的新字段；无法补证的内容标记未知，不反推历史结论。

`DEV-SUITE-4.0` 将存量项目理解 Skill `project-understanding` 纳入 Dev 体系并更名为 `dev-ctx`。历史提示、文档和
外部记录中的原名称按别名解释，不批量重写；新调用、交接和产物只使用 `dev-ctx`。

`DEV-SUITE-5.0` 将 `dev-ctx` 从固定项目文档生成器重构为As-Is实现上下文模块，引入
`CTX/CTXF/CTXP/CTXG`、`Draft → Ready → PotentiallyStale → Ready / Stale → Superseded` 上下文状态和独立项目
基线。4.0及更早生成的项目说明继续作为普通来源文档，不自动升级为
`Ready CTX`；只有补齐范围、版本、证据、新鲜度和失效条件后才能迁入5.0。

`DEV-SUITE-6.0` 将 `CTXF/CTXP/CTXG` 明确为可独立版本化和失效的正式子制品，引入 `Eligible CTX` 聚合判定、
`CTXG Open/Resolved/Superseded` 生命周期和标准失效 `HOF`。5.0 的 `Unknown/Conflicted CTXF` 迁移为 `CTXG`，并保留
原事实、来源和版本作为迁移证据；缺少子制品版本或父 `CTX` 的5.0上下文在补齐前不得直接标记为 `Eligible CTX`。

`DEV-SUITE-7.0` 将代码评审纳入正式生命周期，引入 `dev-cr` 和 `REV`；为 `CHG/HOF/LCV` 补充机器可校验契约；
将正式产物的 `sources/applies_to/risks/evidence` 统一为必需字段；补齐 `MIGRUN/RUNBOOK` 追踪节点，并正式定义
发布、运行手册、事故、RCA和CAPA状态。6.0产物继续按原版本解释；迁入7.0时补齐公共信封和新状态依据，无法补证的
字段标记未知，不反推历史评审、授权或完成结论。

`DEV-SUITE-7.1` 新增 `dev-fia` 和 `FIA`，用于将后端接口、事件和机器契约转换为前端消费侧对接文档。
OpenAPI 等机器契约是输入和支撑制品，`FIA` 是最终对接产物；该能力不新增独立阶段门，也不改变 `API/EVT`、测试和
验证的责任边界。7.0产物继续有效；迁入7.1时只为适用的前端消费场景补充 `FIA`，不反推历史对接或验收结论。

## CHG 规则

- 一次具有共同业务目标、发布目标和回滚边界的变更使用一个 `CHG`。
- 优先复用用户、仓库或项目系统提供的正式 `CHG-001`。
- 没有权威登记源时使用 `CHG-PENDING-001`，明确标记为临时编号；不得宣称全局唯一。
- 正式编号建立后保留临时编号作为别名，不修改已经产生的历史证据。
- 独立缺陷、紧急事故或后续改进只有在目标、发布或回滚边界独立时才拆分新 `CHG`。

## 统一产物信封

正式产物至少记录：

| 字段 | 要求 |
| --- | --- |
| `protocol_version` | 使用的 Dev 体系协议版本 |
| `id` | 稳定产物编号，不因章节排序变化而重编号 |
| `type` | 需求、设计、实现、测试、证据、发布或运行产物类型 |
| `change` | 关联正式或临时 `CHG`；可复用项目上下文基线可以为 `none` |
| `version` | 产物版本或不可变摘要 |
| `status` | 使用产物类型自己的状态，不使用笼统“完成” |
| `owner` | 内容责任角色；未知时明确待确认 |
| `sources` | 上游编号及版本或已检查来源清单，不只记录无版本文件名 |
| `applies_to` | 适用代码、契约、数据、环境或发布版本 |
| `supersedes` | 被替代产物及版本；没有则省略 |
| `risks` | 未决风险、接受信息和失效条件 |
| `evidence` | 支撑当前结论的证据编号或可复核定位器 |
| `updated_at` | 明确时间和时区 |

未知字段保留为待确认，不虚构责任人、版本、环境或授权。

## 标识所有权

| 模块 | 主要标识 |
| --- | --- |
| `dev-lc` | `CHG`、`HOF`、阶段门视图 |
| `dev-ctx` | `CTX`、`CTXF`、`CTXP`、`CTXG` |
| `dev-req` | `REQ`、`RULE`、`AC` |
| `dev-hld` | `DEC`、`MOD`、`FLOW`、`VAL` |
| `dev-lld` | `DET`、`DDEC`、`DATA`、`MIG`、`API`、`EVT`、`JOB`、`CFG`、`DVAL` |
| `dev-fia` | `FIA` |
| `dev-impl` | `IMP`、`BUILD`，以及自动化代码的实现证据 |
| `dev-cr` | `REV` |
| `dev-test` | `TSC`、`TC`、`TDP`、`TD`、`TENV`、`TCOND`、`AUT` 规格 |
| `dev-val` | `RUN`、`EVD`、`DEFECT`、`GATE`，以及自动化门禁状态确认 |
| `dev-rel` | `REL`、`DEP`、`MIGRUN`、`OBS` |
| `dev-ops` | `RUNBOOK`、`INC`、`RCA`、`CAPA` |
| `dev-orch` | 不拥有专业标识；只协调 `dev-lc` 控制对象和专业产物引用 |

模块可以引用其他模块的编号，但不得重编号、改变其含义或冒充其责任方接受状态。`AUT` 的测试目标和规格归
`dev-test`，对应代码以 `IMP(kind=test-automation)` 记录，是否进入验证门禁由 `dev-val` 或项目质量责任方确认。

## 最小追踪链

按适用范围维护：

> `CHG → REQ/RULE/AC → DEC/MOD/FLOW → DET/DDEC → { IMP/BUILD → REV；TSC/TC/AUT } → RUN/EVD/GATE → REL/DEP/MIGRUN/OBS → RUNBOOK → { INC/RCA/CAPA，按事故适用 }`

花括号表示实现与测试设计可以并行推进，不表示串行先后。自动化实现单独建立
`TC → AUT → IMP(kind=test-automation) → BUILD → REV → RUN/EVD`。低风险自动化变更可以按项目评审政策将 `REV` 标记为
不适用，但必须记录依据。允许跳过其他不适用节点，但必须说明原因；健康发布不要求创建 `INC/RCA/CAPA`。

存在前端或其他交互式消费方时，按需建立 `REQ/RULE/AC → API/EVT/机器契约 → FIA → TC/VAL → EVD`。`FIA` 是
消费侧解释与协作制品，不要求插入所有变更的主串行链，也不替代机器契约、测试用例或执行证据。

`CTX/CTXF/CTXP/CTXG` 是可被任意适用阶段引用的As-Is证据侧输入，不属于强制串行门，也不替代
`REQ/DEC/DET/IMP/TC`。`CTXG` 传递未知、冲突和证据边界，不得被下游当作已确认事实。
特定变更调查关联 `CHG`；独立项目基线使用 `change: none` 并通过 `applies_to` 绑定版本和范围。

`CTXF/CTXP/CTXG` 均使用统一产物信封，通过 `parent_ctx` 关联父包，并使用各自的独立 `id + version` 被引用。下游只把
满足 `Ready`、适用范围匹配、消费者最小充分性、所需子制品 `Ready + Current` 且无命中当前分支的开放阻塞 `CTXG`
的上下文视为 `Eligible CTX`。具体字段见 [CTX上下文包](../../dev-ctx/references/context-package.md) 和
[CTX子制品契约](../../dev-ctx/references/context-artifacts.md)，其他模块不得自行放宽。

## 版本与证据

- 产物内容或适用范围发生实质变化时增加版本或创建后继编号。
- 修改含义不得静默覆盖旧版本。
- 执行证据必须绑定被测代码、契约、数据条件和环境。
- 缺少版本、环境或时间的证据只能标记为弱证据。
- 旧证据不得自动证明新版本、不同环境或不同适用范围。
