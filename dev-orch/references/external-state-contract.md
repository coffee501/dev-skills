# 外置状态契约

本契约定义 Dev Skills 如何保存生命周期中间状态。它不改变专业产物语义，也不授权向项目写入任何文件。

## 存储边界

以下内容只能进入项目外部状态库：

- `dev-orch` 管理的 `CHG/HOF/LCV` 及其历史版本。
- ORCH拥有的 `WIT` 及其尝试和运行状态。
- Agent 运行身份、任务认领、尝试次数和阻塞原因。
- 尚未确认的需求、设计、测试和验证草稿信封。
- 失效记录、临时验证结果、日志摘要和证据引用。
- Promotion 准备和确认记录。

语义所有权不因存储位置改变：`CHG/HOF/LCV/WIT` 由 `dev-orch` 按共享协议管理。专业产物及结论归对应 Skill；交接接受、风险接受、阶段门确认和变更关闭必须具有相应责任方的明确证据。

状态根目录按以下优先级解析：

1. `DEV_SKILLS_STATE_HOME`。
2. `${CLAUDE_PLUGIN_DATA}/dev-state`。
3. 操作系统用户状态目录。

不得回退到项目目录、插件安装目录或系统临时目录。插件安装目录会随版本更新而变化，只能读取服务代码。

## 工作区身份

`workspace_resolve` 使用 Git common directory 或项目规范路径建立外部绑定，返回 `WS-*`。同一 Git 仓库的 worktree 应共享
工作区；项目移动时通过显式 `workspace_id` 重新绑定。Remote 指纹仅用于辅助识别，不单独决定身份。

所有状态引用使用：

```text
devstate://workspace/{workspace_id}/change/{change_id}/{object_type}/{object_id}@v{version}
```

## 生命周期对象操作

- `change_get`、`lifecycle_get`、`handoff_get/handoff_list` 是不创建、不推进对象的控制面读取接口，供路线评估与恢复使用。
- `change_get_or_create` 只复用或创建 `CHG`；后续使用 `change_put` 按 `Draft → Active → Completed/Cancelled/Superseded` 推进，并保留乐观版本控制。终态不得重新打开；归档只附加归档记录，不把状态改成协议外的 `Archived`。
- `lifecycle_put` 必须使用正式 `LCV-*` 作为 `lifecycle_id`，只接受 `Current/Superseded`。创建后不得原地改写内容；产生后继视图时，以新 `lifecycle_id`、旧ID和旧版本在同一事务中把旧视图置为 `Superseded` 并创建新的 `Current`。输入失效时也只能将旧视图标记为 `Superseded`，不得写入 `Active/NeedsReview` 等其他对象的状态。
- `handoff_prepare` 必须保存标准交接包的原因、输入、保留行为、决策、未决项、失效项、期望输出和进入条件；来源与目标必须不同。
- `handoff_acknowledge` 是目标责任方可选的收件留痕，不是接受或拒绝的前置条件；目标责任方可从 `Prepared` 或
  `Acknowledged` 直接调用 `handoff_accept/handoff_reject`，分别保存责任人、时间与证据。后继交接使用
  `handoff_supersede`，不得把接受与拒绝共用一个含糊的决定字段。

正式写入的控制对象在 `payload.protocol_version` 中声明协议版本。状态服务在写入 8.1 CHG 时拒绝 LCV 专属字段，在写入带路线的 8.x LCV 时检查节点结构、依赖图及 G3/G4/G5 约束；设计探针只允许 8.1。带阶段字段的路线缺少协议版本时拒绝写入。存量简化载荷仍可按原边界读取。完整信封和专业内容校验由对应校验器与 Skill 负责，责任方确认不由状态服务推断。

## WIT 工作项

工作项至少包含：

| 字段 | 说明 |
| --- | --- |
| `work_item_id` | 稳定 `WIT-*` 编号 |
| `skill` | 唯一目标专业 Skill |
| `input_versions` | 版本化输入引用 |
| `lifecycle_route_ref` / `route_version` / `node_id` | 创建工作项时的 LCV 来源版本和节点，保留供追踪 |
| `route_fingerprint` | 当前节点及其依赖闭包的内容指纹；关联路线内容变化时阻止认领或成功完成 |
| `input_fingerprint` | 按输入版本数组顺序生成的内容指纹 |
| `owned_paths` | 允许修改的项目路径；为空表示不授权写项目 |
| `owned_artifacts` | 责任产物编号 |
| `attempt` | 实际认领次数 |
| `agent_id` | 当前执行 Agent；未认领时为空 |
| `status` | `Prepared/Running/Completed/Blocked/Failed/Cancelled` |
| `expected_outputs` | 预期产物和证据 |

`work_prepare` 只创建新 `WIT`；已有编号不得重置为 `Prepared`、清空尝试次数或丢弃结果。正式调度时须绑定当前 `LCV.route` 中存在且 Skill 匹配的节点。`work_claim` 和成功完成 `work_complete` 前核对当前节点及其依赖闭包的指纹；仅修改 LCV 摘要或无关节点不使工作项失效，关联节点、依赖或 Skill 变化时不得进入 `Completed`。旧版无路线指纹的工作项沿用严格版本核对，必要时重新规划；失效任务按阻塞或取消路径保留证据。重试 `Blocked` 工作项沿用有效的输入和路线绑定；终态工作需要新编号与追踪关系。

`work_get/work_list/agent_run_list` 提供中断后的当前任务和运行身份恢复读取。`work_claim` 必须提供当前版本；`agent_run_bind` 只允许绑定处于 `Running` 的 WIT，并且必须匹配认领 Agent 和输入指纹；`work_complete` 同样必须匹配认领 Agent 和输入指纹，并在同一事务中关闭对应的 `Running` Agent Run。冲突时返回最新对象，不覆盖其他 Agent 的更新。

## 专业产物登记与历史读取

对应专业 Skill 保有产物的语义、状态和版本责任。正式持久化流程由具备专业执行权限的上下文先校验产物，再使用 `artifact_put` 登记自己的版本化产物和依据；Claude Code 由独立 `dev-specialist` Agent 执行，`dev-orch` 仅用 `artifact_list/artifact_get` 读取核对且不获得写权。专业上下文无登记工具时明确报告缺口，不宣称产物已经持久化。`artifact_get` 可按编号读取当前版本，或按 `version` 精确读取审计中的历史快照，不受 `audit_list` 最近事件窗口限制。状态服务保存信封和最小必要结构，不代替专业内容评审，也不把内部 JSON 当作用户报告。

## 并发与审计

- 每次写入必须提供 `expected_version`、`actor` 和 `source`。
- 状态服务使用事务和乐观版本控制；版本不匹配时拒绝写入。
- 每次变更写入不可变审计事件，记录对象、旧版本、新版本、操作者和来源。
- 输入失效时先停止运行任务，再登记失效对象和替代版本。

## Promotion

Promotion 只登记正式产物写入意图，不执行文件复制或写入：

1. `promotion_prepare` 记录来源版本、目标路径、预期哈希和授权要求。
2. 对应专业 Agent 在用户明确授权后写入最终产物。
3. `promotion_confirm` 记录实际路径、内容哈希、责任人和证据。

未确认 Promotion 不得被描述为已经进入项目。中间状态服务永远不能通过目标路径直接写项目文件。

## 失败与保留

状态服务不可用时不得在项目中创建备用目录。调度器默认退回 `route-only`；只有用户已经要求在当前会话实际推进、所需执行权限与独立隔离可用，且任务不要求
中断恢复或正式控制对象持久化时，才允许使用 `session-coordinate`。该模式只保留会话内工作状态，
必须报告 `state_persistence: none`，不得生成或宣称已持久化的 `CHG/HOF/LCV/WIT`。需要可恢复状态时仍为 `route-only`。

关闭的持久化变更可以归档但不自动删除，开放变更禁止自动清理。附件和原始日志的保留期由部署策略配置，控制对象及审计记录默认长期保留。

状态库不得保存凭据、访问令牌、私钥、完整生产数据或无界原始日志；只保存完成追踪所需的最小结构化信息、摘要、哈希和引用。
