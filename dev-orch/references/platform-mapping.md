# 平台调度映射

核心模式、路线、授权和产物语义由 `dev-orch/SKILL.md` 与 `dev-lc` 协议定义。本文件只映射宿主能力，不改变控制规则。

## Codex

显式使用 `$dev-orch`。运行时先检查原生多代理工具是否实际可用，不根据客户端名称猜测。

| 调度动作 | Codex 原生能力 |
| --- | --- |
| 创建独立专业任务 | `spawn_agent` |
| 向现有任务补充或纠偏 | `followup_task` / `send_message` |
| 查看运行任务 | `list_agents` |
| 停止失效分支 | `interrupt_agent` |
| 等待结果 | `wait_agent` |

规则：

- 使用子代理处理当前请求的有界专业子任务；不要用新任务/线程创建能力代替子代理。
- 系统、开发者、仓库指导或宿主策略禁止/限制子代理时，以高优先级规则为准并切换 `route-only`；不得用其他工具绕过限制。
- 调度器是根代理，负责路线、任务边界、集成和最终验证；子代理只执行被分配的责任。
- 子代理修改文件时必须明确拥有路径或责任对象，并被告知不要回退其他人的修改。
- 优先继承当前模型和仓库上下文，不硬编码模型名称；只有明确质量或速度理由时才选角色。
- 原生多代理不可用或达到限制时切换 `route-only`，不得把工具缺失解释为专业失败。
- 外置状态工具不可用但用户要求本会话实际推进时，可以使用 `session-coordinate`；状态只存在于当前会话，项目中不得建立备用状态目录。

### Codex 会话工作项

无外置状态时使用非正式 `SWI-*`，不要创建正式 `WIT`：

| 字段 | 含义 |
| --- | --- |
| `session_item_id` | 当前会话内稳定编号，如 `SWI-001` |
| `skill` | 唯一目标专业 Skill |
| `input_fingerprint` | 当前输入摘要或可复核指纹 |
| `scope` / `owned_objects` | 允许读取、修改或负责的对象 |
| `expected_outputs` | 预期专业产物和验证结果 |
| `stop_conditions` | 输入失效、授权缺口或责任冲突等停止条件 |
| `status` | `Prepared/Running/Completed/Blocked/Failed/Cancelled` |

`SWI` 不可跨会话恢复，也不能在最终报告中冒充正式生命周期状态。

Codex App、CLI 或其他 Codex 宿主可能暴露不同工具集合，以实际可调用工具为准。tmux/OMX 运行时不是本 Skill 的必要依赖。

## Claude Code

插件模式使用 `/dev-skills:dev-orch <任务>`，项目模式可以使用对应命令或 `dev-orch` Agent。薄适配层负责加载根 `dev-orch/SKILL.md`。

| 调度动作 | Claude Code 能力 |
| --- | --- |
| 创建专业任务 | `Agent` |
| 续接或纠偏 | `SendMessage` |
| 停止失效分支 | `TaskStop` |
| 外置状态 | `mcp__dev_state__*` |

Claude 的 `context: fork`、`agent: dev-orch`、工具白名单和斜杠命令只属于适配层，不得写进工具中立核心协议。

## 无子代理宿主

使用 `route-only`：输出最短充分路线、版本化任务包、依赖、阻塞、授权缺口和下一责任模块。不得声称专业阶段已执行，也不得把中间状态写入项目。

## 状态能力判断

- 外置状态服务存在且符合契约：允许 `durable-coordinate`。
- 只有当前会话与原生子代理：允许用户已要求执行的 `session-coordinate`。
- 用户要求可恢复工作但没有外置状态：使用 `route-only` 并报告持久化缺口。
- 任何平台都不得使用项目目录或系统临时目录冒充生命周期状态库。
