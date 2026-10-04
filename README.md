# Dev Skills

面向跨业务领域后端服务与系统集成开发阶段的套件。`dev-orch` 智能体理解目标、选择并主动调用专业 Skill，管理阶段路线、进度和交接；专业 Skill 也可独立使用。套件止于验证门，不执行发布、生产迁移、流量操作或生产运维。

当前插件版本由根目录 `VERSION` 定义，当前值为 `9.2.0`；正式产物协议最高版本为 `DEV-SUITE-8.1`。

## 架构与规则入口

本套件只有一个编排责任方：`dev-orch` 选择专业 Skill、维护生命周期路线和执行状态；各专业 Skill 对自己的内容与结论负责；`dev-state` 仅保存状态。有权限的责任方负责阶段门确认与风险接受。Codex 和 Claude Code 的入口只适配宿主能力，不另行定义专业流程或生命周期语义。

| 要判断的问题 | 权威规则 |
| --- | --- |
| 目标应进入哪个专业阶段、何时结束 | [智能体核心](dev-orch/AGENT.md)与[技能选择条件](dev-orch/references/capability-routing.md) |
| 路线、依赖、阶段门和执行任务如何分开 | [路线与执行投影契约](dev-orch/references/orchestration-interface.md)与[生命周期状态模型](dev-orch/references/lifecycle-state-model.md) |
| 责任转移时传什么、谁接收 | [交接协议](dev-orch/references/handoff-contract.md) |
| 输入变化后哪些结果需要复审 | [失效传播规则](dev-orch/references/invalidation-rules.md) |
| 专业产物的身份、版本和共同字段 | [产物协议](dev-orch/references/artifact-contract.md)与各专业 Skill 的增量规则 |
| 宿主工具不同或状态服务不可用时如何执行 | [平台映射](dev-orch/references/platform-mapping.md)与[外置状态契约](dev-orch/references/external-state-contract.md) |

只涉及单一专业阶段或简单双阶段时直接执行适用 Skill；跨阶段且需要协调时由 `dev-orch` 建立路线并按[调度协议](dev-orch/references/orchestration-protocol.md)推进。正式责任转移使用现有 `HOF`，任务派发使用现有 `WIT` 或会话内 `SWI`；二者不互相替代，也不创建第二套交接字段。新增规则先确定权威文件，其他入口只链接或说明平台差异。

## 平台兼容

专业流程维护在各目录的 `SKILL.md`，编排核心维护在 `dev-orch/AGENT.md`；Codex 的轻量启动入口位于 `.agents/skills/dev-orch/`。当前优先适配 Claude Code，并保留 Codex 显式启动入口：

- **Codex**：使用 `$dev-orch <任务>` 在普通主会话加载智能体核心；专业 Skill 仍可独立调用。`.codex/agents/dev-orch.toml` 用于派生智能体配置。
- **Claude Code项目模式**：在本仓库或保留 `.claude/skills` 结构的项目中启动，使用 `/dev-orch` 等命令。
- **Claude Code插件模式**：在仓库根目录使用 `claude --plugin-dir .` 加载，使用 `/dev-skills:dev-orch` 等命令。
- **前端接口对接**：使用 `/dev-skills:dev-fia <服务、消费方和契约位置>`；输出场景化对接文档，不生成前端代码。

`dev-*/agents/openai.yaml` 是专业 Skill 的 Codex 元数据；`.agents/skills/dev-orch/agents/openai.yaml` 仅控制启动入口；`.claude/skills/*` 是 Claude Code 薄适配器；
[Claude插件清单](.claude-plugin/plugin.json)负责可分发注册。适配层不复制核心流程，平台差异见
[工具兼容规则](dev-orch/references/tool-compatibility.md)。

Claude Code 的 `dev-orch` Agent 只管理控制状态，专业代码或文档工作由独立 `dev-specialist` Agent 执行并登记；Codex 主会话按实际工具权限执行或分派专业任务。具体能力边界见[平台映射](dev-orch/references/platform-mapping.md)。

调度中间状态不会写入项目。插件内置的 `dev_state` MCP 使用 `${CLAUDE_PLUGIN_DATA}` 或 `DEV_SKILLS_STATE_HOME` 保存
SQLite 状态库；项目中只写入用户已要求或已授权的最终文档、代码、配置或迁移产物。状态服务需要 Node.js 22.5 或更高版本。

## 模块

| 模块 | 责任 | 主要产物 |
| --- | --- | --- |
| `dev-ctx` | 理解存量实现与As-Is证据 | `CTX/CTXF/CTXP/CTXG` |
| `dev-req` | 需求、规则和验收 | `REQ/RULE/AC` |
| `dev-hld` | 系统边界和概要设计 | `DEC/MOD/FLOW/VAL` |
| `dev-lld` | 实现级详细设计 | `DET/DDEC/DATA/MIG/API/EVT/JOB/CFG/DVAL` |
| `dev-fia` | 将后端契约转为前端场景化对接文档，不生成前端代码 | `FIA` |
| `dev-impl` | 代码、配置、迁移和自动化实现 | `IMP/BUILD`；可读实现进度或交付摘要 |
| `dev-cr` | 独立实现审查、结论与整改复审 | `REV`；可读评审报告 |
| `dev-test` | 测试场景、用例、数据和自动化规格 | `TSC/TC/TDP/TD/TENV/TCOND/AUT` |
| `dev-val` | 测试执行、证据、缺陷和验证结论 | `RUN/EVD/DEFECT/GATE`；可读执行摘要或验证报告 |
| `dev-orch` | 生命周期路线、门禁、追踪、失效、交接与按需调度 | 内部 `CHG/HOF/LCV/WIT/SWI`；用户可读进度 |

各专业 Skill 的编号记录用于套件内部追踪与交接；面向用户的文档按对应的 `references/outline.md` 组织，正文不直接展示内部交互 JSON。

## 推荐主线

```text
CTX（按需）
  → REQ
     ├─→ TEST：从 REQ/RULE/AC 建立 TSC/TC 草案，吸收 HLD/LLD 后形成 Ready TC/AUT
     │       ├─→ 人工执行路径 ────────────────────────────────────────────────┐
     │       └─→ 测试自动化实现：IMP(kind=test-automation)/BUILD → CR ───────┤
     └─→ HLD → LLD ─┬─→ FIA（有前端消费方时）                               │
                    └─→ 产品实现：IMP(kind=code/config/contract/migration)/BUILD → CR ─┤
  → VAL：执行 Ready TC 的人工路径或已实现、已评审自动化路径 ─────────────────┘
       → RUN/EVD/DEFECT → 闭环 GATE
```

`dev-fia` 在适用的 `API/EVT` 或 OpenAPI 等机器契约稳定后，将其转为前端可消费的场景、字段、状态、错误、权限和版本协作说明；OpenAPI 是基础而非最终产物。测试设计从G1需求基线开始，在G2/G3吸收架构、契约、数据和验证点，并可与实现并行细化。需要自动化的 `Ready TC/AUT` 由 `dev-impl` 实现为 `IMP(kind=test-automation)`，产品实现与自动化实现均由 `dev-cr` 独立审查。完整实现或跨多个 `IMP` 的候选还应生成绑定当前 `IMP/BUILD`、候选身份和实际差异的人类可读实现交付摘要；该摘要只是只读投影，不新增权威产物或批准结论。进入G5前，每个必选用例必须具有可执行的人工路径，或具有已构建、已评审的自动化实现；最后由 `dev-val` 执行并以闭环 `GATE` 汇总执行、证据、缺陷、逐目标结果、未验证范围和剩余风险。完整验证报告来源于指定版本 `GATE`，未形成 `GATE` 的定向执行摘要来源于 `RUN/EVD/DEFECT`；两者都不形成新的权威产物。并非每个变更都需要所有阶段，跳过、人工执行或评审不适用时必须记录依据和剩余风险。

发布、生产迁移、流量切换、生产恢复和事故治理属于套件外部责任。开发阶段仍应在需求、设计、实现和验证中明确兼容、迁移、可回退性、可观测性及外部交付条件，但不得把这些准备工作描述为已经发布或完成生产验证。

## 调用入口与运行模式

- **专业 Skill 独立调用**：显式调用一个 Skill，使用本地临时编号，保留来源、范围、风险、证据和时间；不宣称正式阶段门或 HOF 已经确认。
- **`dev-orch` 统一入口**：Codex 使用 `$dev-orch <任务>`；Claude Code 使用 `/dev-skills:dev-orch <任务>` 或 `dev-orch` 主会话。智能体依据目标选择专业 Skill；简单任务直接执行，跨阶段且协调有价值时建立或复用路线并调度。专业 Skill 只创建 `Prepared HOF`，由接收方或正式责任系统确认接收。

入口之下的 `direct`、`route-only`、`session-coordinate` 和 `durable-coordinate` 是[智能体核心](dev-orch/AGENT.md)定义的运行模式，由目标、授权、宿主能力和持久化需求决定。发布及生产工作不进入本套件调度路线。

`dev-cr` 保持可被“审查实现、审查PR、验收实现”等明确请求隐式发现；普通实现请求不会因此自动扩展为完整评审。
进入调度模式后，适用 `dev-impl` 产生可评审候选并满足路线条件时，`dev-orch` 自动分派独立 `dev-cr` 上下文；
路线遗漏评审、`REV` 未覆盖候选，或既无独立评审又无符合项目政策的补偿控制时，不得进入正式G5。

`dev-ctx/dev-impl/dev-val` 默认要求显式调用，其中后两项属于执行型 Skill。真实数据、外部副作用和风险接受仍需精确目标及项目授权；发布和生产运维不属于本套件能力。

## 协议与验证

控制面新增产物使用 `DEV-SUITE-8.1`，并兼容 8.0、7.1 和 7.0 开发阶段存量产物；未变更的专业产物可继续使用 8.0。共享规则位于 [产物协议](dev-orch/references/artifact-contract.md)、[状态模型](dev-orch/references/lifecycle-state-model.md)、[交接协议](dev-orch/references/handoff-contract.md)和[失效传播](dev-orch/references/invalidation-rules.md)。

在仓库根目录运行：

```text
python scripts/validate_all.py
```

该命令是本地和CI共用的完整确定性门禁，会执行套件结构、所有现有 Skill 单元测试、`dev-req` PowerShell校验和
`dev-state` Node测试。需要单独定位失败时可运行：

```text
node --disable-warning=ExperimentalWarning --test dev-state/tests/state-store.test.mjs dev-state/tests/mcp-server.test.mjs
python dev-orch/scripts/validate_suite.py
python -m unittest discover -s dev-cr/tests -p "test_*.py" -v
python -m unittest discover -s dev-ctx/tests -p "test_*.py" -v
python -m unittest discover -s dev-fia/tests -p "test_*.py" -v
python -m unittest discover -s dev-hld/tests -p "test_*.py" -v
python -m unittest discover -s dev-impl/tests -p "test_*.py" -v
python -m unittest discover -s dev-lld/tests -p "test_*.py" -v
python -m unittest discover -s dev-orch/tests -p "test_*.py" -v
python -m unittest discover -s dev-req/tests -p "test_*.py" -v
python -m unittest discover -s dev-test/tests -p "test_*.py" -v
python -m unittest discover -s dev-val/tests -p "test_*.py" -v
powershell -NoProfile -File dev-req/scripts/validate.ps1
```

所有正式JSON产物都可先使用 `dev-orch/scripts/validate_artifact_envelope.py` 检查共享信封；存在模块专用校验器时再执行
模块增量规则。GitHub Actions在Windows和Linux上运行同一完整门禁，避免平台或漏跑造成假绿。

这些测试执行结构契约、验证器和外部状态机行为；场景JSON只是前向评估用例目录，不等同于真实Agent行为已经通过。模块自带的校验器和确定性测试仍不替代独立语义评审、真实测试证据、授权或阶段门确认；支持独立Agent运行的环境还应按场景目录执行前向评估，并把使用的套件版本、输入场景、独立执行上下文和结果摘要作为套件验收证据。
