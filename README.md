# Dev Skills

面向跨业务领域后端服务与系统集成的全生命周期 Skill 套件。各模块可以独立使用；需要正式编号、阶段门、失效传播和跨模块交接时，由 `dev-lc` 提供共享控制面。

## 平台兼容

核心流程只维护在根目录 `dev-*/SKILL.md`，同时兼容 Codex 与 Claude Code：

- **Codex**：安装或引用根目录 `dev-*` Skill，使用 `$dev-lc` 或其他 `$dev-*` 名称调用。
- **Claude Code项目模式**：在本仓库或保留 `.claude/skills` 结构的项目中启动，使用 `/dev-lc` 等命令。
- **Claude Code插件模式**：在仓库根目录使用 `claude --plugin-dir .` 加载，使用 `/dev-skills:dev-lc` 等命令。

`dev-*/agents/openai.yaml` 是 Codex 展示和触发元数据；`.claude/skills/*` 是 Claude Code薄适配器；
[Claude插件清单](.claude-plugin/plugin.json)负责可分发注册。适配层不复制核心流程，平台差异见
[工具兼容规则](dev-lc/references/tool-compatibility.md)。

## 模块

| Skill | 责任 | 主要产物 |
| --- | --- | --- |
| `dev-ctx` | 理解存量实现与As-Is证据 | `CTX/CTXF/CTXP/CTXG` |
| `dev-req` | 需求、规则和验收 | `REQ/RULE/AC` |
| `dev-hld` | 系统边界和概要设计 | `DEC/MOD/FLOW/VAL` |
| `dev-lld` | 实现级详细设计 | `DET/DDEC/DATA/MIG/API/EVT/JOB/CFG/DVAL` |
| `dev-impl` | 代码、配置、迁移和自动化实现 | `IMP/BUILD` |
| `dev-cr` | 独立代码评审与整改复审 | `REV` |
| `dev-test` | 测试场景、用例、数据和自动化规格 | `TSC/TC/TDP/TD/TENV/TCOND/AUT` |
| `dev-val` | 测试执行、证据、缺陷和质量门 | `RUN/EVD/DEFECT/GATE` |
| `dev-rel` | 发布、迁移执行、观察和恢复 | `REL/DEP/MIGRUN/OBS` |
| `dev-ops` | 运行准备、事故、RCA和CAPA | `RUNBOOK/INC/RCA/CAPA` |
| `dev-lc` | 变更路由、交接、状态和阶段门 | `CHG/HOF/LCV` |

## 推荐主线

```text
CTX（按需）
  → REQ
  → HLD
  → LLD
  → { IMPL → CR；TEST }
  → VAL
  → REL
  → OPS
```

测试设计从需求阶段开始并与设计、实现并行细化。局部缺陷可以复用有效基线；事故先由 `dev-ops` 止损，再通过 `RCA/CAPA` 返回需求、设计、实现和验证。并非每个变更都需要所有阶段，跳过时记录不适用依据。

## 两种使用方式

- **独立模式**：显式调用一个 Skill，使用本地临时编号，保留来源、范围、风险、证据和时间；不宣称正式阶段门或HOF已经确认。
- **体系模式**：先用生命周期治理 Skill 建立或复用 `CHG` 和阶段路线，再显式调用专业 Skill；Codex使用 `$dev-lc`，Claude Code项目模式使用 `/dev-lc`，插件模式使用 `/dev-skills:dev-lc`。专业 Skill只创建 `Prepared HOF`，接收方或正式责任系统确认接收。

`dev-ctx/dev-impl/dev-val/dev-rel/dev-ops` 默认要求显式调用，其中后四项属于执行型 Skill。生产、发布、真实数据、外部副作用和风险接受仍需精确目标及项目授权；Skill不会自行接受风险。

## 协议与验证

当前协议为 `DEV-SUITE-7.0`，共享规则位于 [产物协议](dev-lc/references/artifact-contract.md)、[状态模型](dev-lc/references/lifecycle-state-model.md)、[交接协议](dev-lc/references/handoff-contract.md)和[失效传播](dev-lc/references/invalidation-rules.md)。

在仓库根目录运行：

```text
python dev-lc/scripts/validate_suite.py
python -m unittest discover -s dev-lc/tests -p "test_*.py" -v
```

模块自带的校验器只证明最低结构，不替代语义评审、测试证据、授权或阶段门确认。
