# 工具兼容与分发

## 单一事实源

每个专业目录 `dev-*/SKILL.md` 及其 `references/scripts` 是专业能力的唯一核心。`dev-orch/AGENT.md` 是智能体判断与调度的唯一核心；`.agents/skills/dev-orch/SKILL.md` 只作为 Codex 显式启动适配器。专业 Skill 文件遵循 Agent Skills 的公共子集：

- `SKILL.md` frontmatter 只保留 `name` 和 `description`。
- 正文使用工具中立措辞，不依赖某个模型、客户端或专有工具名。
- 相对引用以对应 `dev-*` 目录为根解析。
- 平台特有的发现、展示和触发控制留在适配层，不复制核心流程。

## Codex 适配

`dev-*/agents/openai.yaml` 只负责专业 Skill 的显示信息、默认提示和隐式调用策略；`.agents/skills/dev-orch/agents/openai.yaml` 是 Codex 启动入口的元数据。专业核心来自同目录 `SKILL.md`；`dev-orch` 的核心来自 `AGENT.md`。`.codex/agents/dev-orch.toml` 只配置派生会话，不能把普通主会话自动变为 `dev-orch`。

## Claude Code 适配

`.claude/skills/<name>/SKILL.md` 是薄适配器：保留适合发现的描述，通过 `${CLAUDE_SKILL_DIR}` 定位根目录核心 Skill，
并要求完整读取核心文件后再执行。`dev-orch` 的命令适配器完整读取 `AGENT.md`，通过 `context: fork` 启动同名 Agent。项目模式使用 `/dev-orch`；插件模式由 `.claude-plugin/plugin.json` 注册，使用
`/dev-skills:dev-orch` 命名空间。

触发策略必须等价映射：

| Codex | Claude Code |
| --- | --- |
| `allow_implicit_invocation: true` | `disable-model-invocation: false` |
| `allow_implicit_invocation: false` | `disable-model-invocation: true` |

适配器不得添加、删除或改写业务流程、安全边界、产物、状态和阶段门语义。

Claude Code 是当前调度 Agent 的首要运行平台。`.claude/agents/dev-orch.md` 同时作为项目级 Agent，并由插件清单
注册为插件 Agent。推荐用 `claude --agent dev-orch` 启动为主会话调度器。作为子 Agent 时，可在宿主配置的派生深度内继续
分派；当 `Agent` 工具不可用或达到深度/并发限制时，先判断能否顺序执行或等待容量。治理和调度语义来自根 `AGENT.md` 及 `orchestration-protocol.md`，Agent 文件
不得复制共享生命周期协议。

插件通过 `dev_state` MCP 提供外置状态能力。每个适配器只能获得其职责所需的明确工具白名单；`dev-orch` 可以按证据写入
生命周期、交接、失效与调度状态，但不获得专业产物写入或晋升工具。任何角色都不得向项目创建
生命周期缓存目录。状态根目录优先使用 `DEV_SKILLS_STATE_HOME`，否则使用 Claude 的插件数据目录；MCP 不可用时 Agent
按需求选择 `route-only`，或在不要求恢复且允许会话内执行时使用 `session-coordinate`。

## 调度 Agent 的 Codex 兼容

共享核心 `dev-orch/AGENT.md` 是 Claude Code 与 Codex 共用的调度核心。Codex 显式使用 `$dev-orch` 加载核心，并在原生多代理能力可用时
通过子代理协调专业 Skill；不可用时判断可否在当前上下文顺序执行。Codex 没有符合外置状态契约的服务时，可以在用户要求本会话执行且
无需恢复的前提下使用 `session-coordinate`，但必须报告状态不持久化，并且不得向项目写入备用状态。

Claude Code 的 `.claude/skills/dev-orch` 和 `.claude/agents/dev-orch.md` 是薄适配层。两端工具对应关系维护在
[平台调度映射](platform-mapping.md)，不得改变 `CHG/HOF/LCV`、阶段门、专业责任或授权语义。

## 维护规则

修改 Skill 名称、描述或触发策略时，同步更新两端元数据；修改正文和参考文件时只改核心目录。新增或删除 Skill 时，
同步更新 Claude 项目适配目录、插件 `skills` 清单、根目录模块表和体系校验器。运行 `dev-orch/scripts/validate_suite.py`
检查核心与适配层一致性。
