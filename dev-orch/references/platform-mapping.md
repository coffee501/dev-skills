# 平台调度映射

判断、主动调用、生命周期治理和调度语义由 `dev-orch/AGENT.md` 定义。本文件只映射宿主能力，不改变专业产物与责任方确认的边界。

## Codex

普通主会话显式使用 `$dev-orch` 加载智能体核心；`.codex/agents/dev-orch.toml` 仅用于派生会话配置，不能自行切换主会话身份。运行时先检查原生多代理工具是否实际可用，不根据客户端名称猜测。

| 调度动作 | Codex 原生能力 |
| --- | --- |
| 创建独立专业任务 | `spawn_agent` |
| 向现有任务补充或纠偏 | `followup_task` / `send_message` |
| 查看运行任务 | `list_agents` |
| 停止失效分支 | `interrupt_agent` |
| 等待结果 | `wait_agent` |

规则：

- 使用子代理处理当前请求的有界专业子任务；不要用新任务/线程创建能力代替子代理。
- 系统、开发者、仓库指导或宿主策略禁止/限制子代理时，以高优先级规则为准；有权限且无需独立评审隔离的工作可在当前上下文顺序执行，依赖独立判断且缺少合规补偿控制的分支保持阻塞；不得用其他工具绕过限制。
- 调度器是根代理，负责建立或复用路线、映射任务边界、协调执行和收集结果；子代理只执行被分配的专业责任。
- 子代理修改文件时必须明确拥有路径或责任对象，并被告知不要回退其他人的修改。
- 为 `dev-cr` 创建新的独立专业任务；不得使用 `followup_task`、`send_message` 或等价续接能力把实现 Agent 转为其自身候选的正式评审者。无法分离时保留独立性缺口；若缺少符合 `dev-cr` 契约、项目政策和证据要求的补偿控制，不得形成 `REV Approved`。
- 优先继承当前模型和仓库上下文，不硬编码模型名称；只有明确质量或速度理由时才选角色。
- 原生多代理不可用或达到限制时，优先在有权限的当前上下文顺序执行、等待容量；需要独立权限或评审隔离且无法获得、也没有合规补偿控制时，阻塞相应任务。不得把工具缺失解释为专业失败。
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

Codex App、CLI 或其他 Codex 宿主可能暴露不同工具集合，以实际可调用工具为准。tmux/OMX 运行时不是本智能体的必要依赖。

## Claude Code

插件模式使用 `/dev-skills:dev-orch <任务>` 启动子会话；`claude --agent dev-orch` 可启动主会话。项目模式可使用对应命令或智能体。薄适配层负责加载共享核心 `dev-orch/AGENT.md`，并传递任务目标、约束、已有证据与状态引用。

| 调度动作 | Claude Code 能力 |
| --- | --- |
| 创建专业任务 | `Agent` |
| 续接或纠偏 | `SendMessage` |
| 停止失效分支 | `TaskStop` |
| 外置状态 | `change_* / lifecycle_* / handoff_* / invalidation_apply / work_*` 按证据读写治理与调度状态；`artifact_list/agent_run_list/audit_list` 读取；不授予专业产物写入或晋升工具 |

Claude 的 `context: fork`、`agent: dev-orch`、工具白名单和斜杠命令只属于适配层，不得写进工具中立核心协议。

## 无子代理宿主

单阶段工作可使用 `direct`；多阶段且无需独立隔离或跨会话恢复时，可在有权限的当前上下文顺序执行并使用 `session-coordinate`。依赖独立权限、评审隔离或持久化而无法满足时，对受影响分支使用 `route-only`，输出执行投影、任务包、依赖、阻塞和授权缺口。有效输入不足时报告
`lifecycle_route_status: missing` 和恢复条件；不得声称专业阶段已执行或把中间状态写入项目。

## 状态能力判断

- 外置状态服务存在且符合契约：允许 `durable-coordinate`。
- 只有当前会话且无需跨会话恢复：允许用户已要求执行的 `session-coordinate`；无子代理时仅顺序执行无需独立隔离的任务。
- 用户要求可恢复工作但没有外置状态：使用 `route-only` 并报告持久化缺口。
- 任何平台都不得使用项目目录或系统临时目录冒充生命周期状态库。
