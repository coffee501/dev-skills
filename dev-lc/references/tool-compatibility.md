# 工具兼容与分发

## 单一事实源

每个根目录 `dev-*/SKILL.md` 及其 `references/scripts/assets` 是唯一核心实现。核心文件遵循 Agent Skills 的公共子集：

- `SKILL.md` frontmatter 只保留 `name` 和 `description`。
- 正文使用工具中立措辞，不依赖某个模型、客户端或专有工具名。
- 相对引用以对应 `dev-*` 目录为根解析。
- 平台特有的发现、展示和触发控制留在适配层，不复制核心流程。

## Codex 适配

`dev-*/agents/openai.yaml` 只负责 Codex 的显示信息、默认提示和隐式调用策略。核心行为仍来自同目录 `SKILL.md`。

## Claude Code 适配

`.claude/skills/<name>/SKILL.md` 是薄适配器：保留适合发现的描述，通过 `${CLAUDE_SKILL_DIR}` 定位根目录核心 Skill，
并要求完整读取核心文件后再执行。项目模式使用 `/dev-lc`；插件模式由 `.claude-plugin/plugin.json` 注册，使用
`/dev-skills:dev-lc` 命名空间。

触发策略必须等价映射：

| Codex | Claude Code |
| --- | --- |
| `allow_implicit_invocation: true` | `disable-model-invocation: false` |
| `allow_implicit_invocation: false` | `disable-model-invocation: true` |

适配器不得添加、删除或改写业务流程、安全边界、产物、状态和阶段门语义。

## 维护规则

修改 Skill 名称、描述或触发策略时，同步更新两端元数据；修改正文和参考文件时只改核心目录。新增或删除 Skill 时，
同步更新 Claude 项目适配目录、插件 `skills` 清单、根目录模块表和体系校验器。运行 `dev-lc/scripts/validate_suite.py`
检查核心与适配层一致性。
