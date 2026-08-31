---
name: dev-fia
description: "Turn backend API, event, and schema contracts into frontend integration alignment documents（前端接口对接文档、联调说明、接口消费语义、OpenAPI对齐、契约变更影响）for cross-domain backend and system-integration work. Use when frontend teams need scenario-oriented guidance for calling backend capabilities, interpreting fields and states, handling errors and asynchronous results, or coordinating compatibility and release. OpenAPI is a machine-readable foundation, not the final deliverable. Do not generate frontend code, SDKs, hooks, mocks, components, or UI designs."
---

# Dev FIA

将后端 API、事件和数据契约翻译为前端能够直接用于开发、联调和发布协作的接口对接文档。最终产物是 `FIA`（Frontend Interface Alignment），OpenAPI、AsyncAPI、Proto、GraphQL SDL、JSON Schema 或实现证据只是输入和支撑制品。

## 接入 Dev 生命周期

复用当前 `CHG`，以版本化 `FIA` 关联 `REQ/RULE/AC`、`API/EVT`、机器可读契约、实现版本和消费方范围。需要公共字段、状态与追踪规则时读取 [产物协议](../dev-lc/references/artifact-contract.md)；发生责任转移或缺口返回时读取 [交接协议](../dev-lc/references/handoff-contract.md)；上游契约变化时读取 [失效传播规则](../dev-lc/references/invalidation-rules.md)。

共享协议不可用时可以独立生成或评审对接文档，但必须使用局部临时编号，记录来源、契约身份、适用范围、风险和未知项；不得宣称正式基线、全局唯一编号、阶段门或标准 `HOF` 已被确认。

草稿、扫描结果、契约快照、差异和联调工作状态只保存在宿主提供的项目外状态区。除非用户明确要求将最终文档写入指定位置，否则不在业务项目中创建中间文件。

## 保持职责边界

本 Skill 回答“前端在具体业务场景中如何正确消费后端契约”，不拥有后端契约和业务规则。

默认不要。尤其不生成任何前端代码：

- 生成或修改前端类型、客户端、SDK、hooks、mocks、组件、页面、状态管理或 UI/UX 设计
- 把 OpenAPI 原样排版成最终对接文档，或把自然语言说明当作机器契约的替代品
- 自行新增、重命名或改变字段、接口、错误码、状态、权限、分页或一致性语义
- 用前端展示需要反推业务规则、数据权威或后端实现机制
- 把推断的请求样例、默认值、空值含义或错误处理写成已确认契约
- 生成完整测试用例、自动化脚本或宣布联调、验收已经通过
- 访问生产环境、真实数据或外部系统来“验证”文档，除非用户明确授权

业务语义缺口交给 `dev-req`；系统边界和数据权威问题交给 `dev-hld`；字段、接口、错误码、事件和实现契约问题交给 `dev-lld`；实现漂移交给 `dev-impl`；完整测试设计交给 `dev-test`；执行证据和门禁交给 `dev-val`。本 Skill 可以给出消费侧建议，但必须与协议事实和业务语义分栏，不能越权修订上游。

## 选择工作模式

| 模式 | 使用条件 | 默认输出 |
| --- | --- | --- |
| 对接诊断 | 来源不完整、契约冲突或语义不足 | 输入清单、缺口、阻塞、风险和补证路线 |
| 新建对接文档 | 新接口或新消费方首次接入 | 场景化 `FIA` 草案和就绪评估 |
| 增量更新 | 接口、规则、实现或消费范围变化 | 差异、受影响场景、兼容与发布说明 |
| 漂移评审 | OpenAPI、代码、设计和已有文档可能不一致 | 逐项差异、权威来源、影响和修复责任 |
| 联调就绪检查 | 前后端准备进入联调 | `Ready/ConditionallyReady/Blocked` 评估 |
| 联调问题定位 | 前端反馈行为、字段或状态不符合预期 | 请求链、契约预期、实际证据、归属与下一步 |

就绪评估不是验收结论；`ReadyForReview` 不是 `Baselined`。

## 建立可信输入

按需收集：

1. 已确认的 `REQ/RULE/AC` 和业务状态、权限、数据口径
2. 已接受的 `DEC/MOD/FLOW` 与数据权威、同步/异步边界
3. `API/EVT` 详细设计以及 OpenAPI、AsyncAPI、Proto、GraphQL SDL、JSON Schema 等机器契约
4. `Eligible CTX`、当前代码、测试、网关、配置和可复核运行证据
5. 已有前端对接文档、调用方清单、联调问题和版本计划

使用三类陈述并保持可辨识：

- **协议事实**：机器契约或已确认详细设计直接定义的结构和约束。
- **业务语义**：已确认需求、规则和状态定义的含义与结果。
- **消费建议**：不改变契约的前端调用、展示和容错建议。

冲突时不静默选择来源。读取 [来源权威与冲突处理](references/source-authority.md)；机器契约缺失或不完整时读取 [OpenAPI 与机器契约基线](references/openapi-baseline.md)。

## 执行对接设计

1. 确认服务、消费方、场景、版本、环境和目标发布范围。
2. 建立契约身份：来源类型、定位器、版本或摘要、权威方、适用范围和生成关系。
3. 按用户任务而不是 URL 顺序组织场景，建立场景到操作、事件和状态的映射。
4. 对每个场景说明调用前提、调用顺序、请求数据来源、响应字段用途、状态变化、错误与恢复、异步最终性。
5. 补充认证、权限、数据范围、脱敏、分页、缓存、新鲜度、上传下载或流式交互等适用语义。
6. 对存量变更建立旧/新契约差异、前后端版本组合、发布顺序、回滚、废弃和退出条件。
7. 记录语义缺口和责任方，生成前端联调检查项以及给 `dev-test/dev-val` 的验证输入。
8. 执行就绪检查，输出 `FIA` 状态建议和独立的联调就绪评估。

具体消费语义读取 [消费侧语义检查](references/consumer-semantics.md)；涉及存量接口、版本并行或下线时读取 [兼容与版本协作](references/compatibility-and-versioning.md)；评审或就绪判断时读取 [对接就绪检查](references/readiness-checklist.md)。

## OpenAPI 的位置

OpenAPI 是 REST/HTTP 接口的结构化基础，可用于发现操作、参数、Schema、安全方案和样例，但不能单独回答业务调用顺序、字段来源与消费目的、状态含义、异步最终性、权限数据范围、版本共存和失败后的业务结果。

- 已有权威 OpenAPI 时引用其稳定定位器和摘要，不复制维护另一份完整 Schema。
- 只有代码或零散接口资料时，可以生成“候选 OpenAPI”作为补证草案，必须标记推断项并交 `dev-lld` 或契约责任方确认。
- GraphQL、gRPC、事件和流式接口使用各自机器契约，不强行转成 OpenAPI。
- 最终交付仍是面向消费方的 `FIA`；机器契约作为附件、链接或可追踪输入。

## 管理 FIA 产物

`FIA` 使用：

> `Draft → ReadyForReview → Baselined → NeedsReview → ReadyForReview/Baselined`

任一现存状态可进入 `Superseded` 或 `Deprecated`。本 Skill 默认最高只建议 `ReadyForReview`；`Baselined` 必须记录有权限责任方、时间、范围和依据。上游业务、接口、实现、权限、版本或消费方范围变化时，先标记 `PotentiallyAffected`，确认影响后将相关 `FIA` 置为 `NeedsReview`。

追踪链按适用范围建立：

> `REQ/RULE/AC → API/EVT/机器契约 → FIA → TC/VAL → EVD`

`FIA` 不新增独立阶段门，也不替代 `API/EVT`、测试用例或验证证据。

## 检查联调就绪

独立给出：

- `Ready`：当前场景的结构、业务语义、错误、权限、版本和环境条件足以开始联调，没有开放 P0。
- `ConditionallyReady`：可以开始受限联调，但必须列明条件、不可覆盖范围、责任人和解除标准。
- `Blocked`：缺少关键契约、业务结果、权限、可访问环境或兼容路径，继续联调会产生误实现或不可判定结果。

该判断只说明联调输入是否可用，不表示接口实现正确、测试通过或发布获批。

## 组织最终输出

创建完整文档时使用 [FIA 输出模板](references/output-template.md)，删除不适用章节，不生成空表。至少包含：

- 适用范围、消费方、契约身份和版本
- 场景与接口/事件映射、关键调用顺序
- 请求字段来源、响应字段消费语义、状态和错误处理
- 异步结果最终性、权限与数据范围
- 兼容、发布、回滚和废弃说明
- 可脱敏复现的样例、开放问题、联调检查项和追踪关系

输出深度选择最低充分级别：单场景局部接口用轻量版；多场景、多系统或版本共存用标准版；关键交易、异步链路、复杂权限或迁移使用完整版本。

最终交付前读取 [FIA 机器产物契约](references/output-contract.md)，并运行 `scripts/validate_fia_artifact.py` 校验机器可读
`FIA` 信封；文档正文仍需按就绪检查人工评审。若用户只需要自然语言文档，可以附带精简元数据块，不强制暴露内部治理细节。
