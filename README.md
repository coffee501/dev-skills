# Dev Skills

面向跨业务领域后端服务与系统集成开发阶段的 Skill 套件。各模块可以独立使用；需要正式编号、阶段门、失效传播和跨模块交接时，由 `dev-lc` 提供共享控制面。套件止于验证门，不执行发布、生产迁移、流量操作或生产运维。

当前插件版本由根目录 `VERSION` 定义，当前值为 `8.0.2`；正式产物协议为 `DEV-SUITE-8.0`。

## 平台兼容

核心流程只维护在模块表列出的活动根目录 `dev-*/SKILL.md`，当前优先适配 Claude Code，并保留 Codex Skill 兼容：

- **Codex**：安装或引用根目录 `dev-*` Skill；单阶段使用对应 `$dev-*`，多阶段显式使用 `$dev-orch`。
- **Claude Code项目模式**：在本仓库或保留 `.claude/skills` 结构的项目中启动，使用 `/dev-lc` 等命令。
- **Claude Code插件模式**：在仓库根目录使用 `claude --plugin-dir .` 加载，使用 `/dev-skills:dev-lc` 等命令。
- **前端接口对接**：使用 `/dev-skills:dev-fia <服务、消费方和契约位置>`；输出场景化对接文档，不生成前端代码。
- **Claude Code多阶段调度**：使用 `/dev-skills:dev-orch <任务>` 启动同步调度子会话，或使用 `claude --plugin-dir . --agent dev-orch` 启动调度主会话；单阶段任务仍直接调用专业 Skill。
- **Codex多阶段调度**：使用 `$dev-orch`；原生子代理可用时协调专业任务，不可用时基于LC路线输出只读执行投影和任务包。

`dev-*/agents/openai.yaml` 是 Codex 展示和触发元数据；`.claude/skills/*` 是 Claude Code 薄适配器；
[Claude插件清单](.claude-plugin/plugin.json)负责可分发注册。适配层不复制核心流程，平台差异见
[工具兼容规则](dev-lc/references/tool-compatibility.md)。

`dev-orch` 是可选的只读调度 Skill/Agent，适用于LC路线跨三个以上开发阶段、复杂迁移实现或端到端开发交付。它通过
[生命周期—调度接口](dev-lc/references/orchestration-interface.md)消费 `dev-lc` 的路线，再按
[调度协议](dev-lc/references/orchestration-protocol.md)准备任务包、协调依赖和收敛状态；不自行增删阶段，不编写专业产物，也不替代授权。
Codex 显式执行 `$dev-orch`；Claude Code 执行 `/dev-skills:dev-orch <任务>`，或用 `--agent dev-orch` 启动调度主会话。两端共享根 `dev-orch/SKILL.md`，达到子代理限制后退回路由。

调度中间状态不会写入项目。插件内置的 `dev_state` MCP 使用 `${CLAUDE_PLUGIN_DATA}` 或 `DEV_SKILLS_STATE_HOME` 保存
SQLite 状态库；项目中只允许出现用户明确确认的最终文档、代码、配置或迁移产物。状态服务需要 Node.js 22.5 或更高版本。

## 模块

| Skill | 责任 | 主要产物 |
| --- | --- | --- |
| `dev-ctx` | 理解存量实现与As-Is证据 | `CTX/CTXF/CTXP/CTXG` |
| `dev-req` | 需求、规则和验收 | `REQ/RULE/AC` |
| `dev-hld` | 系统边界和概要设计 | `DEC/MOD/FLOW/VAL` |
| `dev-lld` | 实现级详细设计 | `DET/DDEC/DATA/MIG/API/EVT/JOB/CFG/DVAL` |
| `dev-fia` | 将后端契约转为前端场景化对接文档，不生成前端代码 | `FIA` |
| `dev-impl` | 代码、配置、迁移和自动化实现 | `IMP/BUILD` 及人类可读实现交付摘要 |
| `dev-cr` | 独立实现审查、结论与整改复审 | `REV` |
| `dev-test` | 测试场景、用例、数据和自动化规格 | `TSC/TC/TDP/TD/TENV/TCOND/AUT` |
| `dev-val` | 测试执行、证据、缺陷和验证结论 | `RUN/EVD/DEFECT` 和闭环 `GATE` |
| `dev-lc` | 生命周期状态、阶段适用性、门禁、追踪、失效和交接 | `CHG/HOF/LCV` |
| `dev-orch` | 将LC路线转换为任务图，协调Agent、并行执行和结果收敛 | `WIT/SWI` 和调度状态 |

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

`dev-fia` 在适用的 `API/EVT` 或 OpenAPI 等机器契约稳定后，将其转为前端可消费的场景、字段、状态、错误、权限和版本协作说明；OpenAPI 是基础而非最终产物。测试设计从G1需求基线开始，在G2/G3吸收架构、契约、数据和验证点，并可与实现并行细化。需要自动化的 `Ready TC/AUT` 由 `dev-impl` 实现为 `IMP(kind=test-automation)`，产品实现与自动化实现均由 `dev-cr` 独立审查。完整实现或跨多个 `IMP` 的候选还应生成绑定当前 `IMP/BUILD`、候选身份和实际差异的人类可读实现交付摘要；该摘要只是只读投影，不新增权威产物或批准结论。进入G5前，每个必选用例必须具有可执行的人工路径，或具有已构建、已评审的自动化实现；最后由 `dev-val` 执行并以 `GATE` 汇总执行、证据、缺陷、逐目标结果、未验证范围和剩余风险。人类可读验证报告只是指定版本 `GATE` 的只读视图，不形成新的权威产物。并非每个变更都需要所有阶段，跳过、人工执行或评审不适用时必须记录依据和剩余风险。

发布、生产迁移、流量切换、生产恢复和事故治理属于套件外部责任。开发阶段仍应在需求、设计、实现和验证中明确兼容、迁移、可回退性、可观测性及外部交付条件，但不得把这些准备工作描述为已经发布或完成生产验证。

## 三种使用方式

- **独立模式**：显式调用一个 Skill，使用本地临时编号，保留来源、范围、风险、证据和时间；不宣称正式阶段门或HOF已经确认。
- **体系模式**：先用生命周期治理 Skill 建立或复用 `CHG` 和阶段路线，再显式调用专业 Skill；Codex使用 `$dev-lc`，Claude Code项目模式使用 `/dev-lc`，插件模式使用 `/dev-skills:dev-lc`。专业 Skill只创建 `Prepared HOF`，接收方或正式责任系统确认接收。
- **调度模式**：Codex 使用 `$dev-orch`；Claude Code 使用 `/dev-skills:dev-orch <任务>` 或 `dev-orch` 主会话。小型请求绕过调度器；套件外部的发布和生产工作不进入调度路线。

`dev-cr` 保持可被“审查实现、审查PR、验收实现”等明确请求隐式发现；普通实现请求不会因此自动扩展为完整评审。
进入调度模式后，适用 `dev-impl` 产生可评审候选并满足LC路线条件时，`dev-orch` 自动分派独立 `dev-cr` 上下文；
路线遗漏评审、评审上下文与实现上下文不独立或 `REV` 未覆盖候选时，不得进入正式G5。

`dev-ctx/dev-impl/dev-val` 默认要求显式调用，其中后两项属于执行型 Skill。真实数据、外部副作用和风险接受仍需精确目标及项目授权；发布和生产运维不属于本套件能力。

## 协议与验证

当前协议为 `DEV-SUITE-8.0`，并兼容7.0和7.1开发阶段存量产物。共享规则位于 [产物协议](dev-lc/references/artifact-contract.md)、[状态模型](dev-lc/references/lifecycle-state-model.md)、[交接协议](dev-lc/references/handoff-contract.md)和[失效传播](dev-lc/references/invalidation-rules.md)。

在仓库根目录运行：

```text
python scripts/validate_all.py
```

该命令是本地和CI共用的完整确定性门禁，会执行套件结构、所有现有 Skill 单元测试、`dev-req` PowerShell校验和
`dev-state` Node测试。需要单独定位失败时可运行：

```text
node --disable-warning=ExperimentalWarning --test dev-state/tests/state-store.test.mjs dev-state/tests/mcp-server.test.mjs
python dev-lc/scripts/validate_suite.py
python -m unittest discover -s dev-lc/tests -p "test_*.py" -v
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

所有正式JSON产物都可先使用 `dev-lc/scripts/validate_artifact_envelope.py` 检查共享信封；存在模块专用校验器时再执行
模块增量规则。GitHub Actions在Windows和Linux上运行同一完整门禁，避免平台或漏跑造成假绿。

这些测试执行结构契约、验证器和外部状态机行为；场景JSON只是前向评估用例目录，不等同于真实Agent行为已经通过。模块自带的校验器和确定性测试仍不替代独立语义评审、真实测试证据、授权或阶段门确认；支持独立Agent运行的环境还应按场景目录执行前向评估，并把使用的套件版本、输入场景、独立执行上下文和结果摘要作为发布证据。
