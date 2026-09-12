# 外置状态契约

本契约定义 Dev Skills 如何保存生命周期中间状态。它不改变专业产物语义，也不授权向项目写入任何文件。

## 存储边界

以下内容只能进入项目外部状态库：

- LC提供的 `CHG/HOF/LCV` 及其历史版本。
- ORCH拥有的 `WIT` 及其尝试和运行状态。
- Agent 运行身份、任务认领、尝试次数和阻塞原因。
- 尚未确认的需求、设计、测试和验证草稿信封。
- 失效记录、临时验证结果、日志摘要和证据引用。
- Promotion 准备和确认记录。

语义所有权不因存储位置改变：`CHG/HOF/LCV` 由 `dev-lc` 或有权限责任方创建和版本化；`WIT` 由 `dev-orch`
管理。ORCH只能保存LC提供的生命周期对象版本和引用，不得借助状态服务改写路线、门禁、交接接受或完成结论。

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

- `change_get`、`lifecycle_get`、`handoff_get/handoff_list` 是不创建、不推进对象的控制面读取接口，供只读调度与恢复使用。
- `change_get_or_create` 只复用或创建 `CHG`；后续使用 `change_put` 按 `Draft → Active → Completed/Cancelled/Superseded` 推进，并保留乐观版本控制。终态不得重新打开；归档只附加归档记录，不把状态改成协议外的 `Archived`。
- `lifecycle_put` 必须使用正式 `LCV-*` 作为 `lifecycle_id`，只接受 `Current/Superseded`。创建后不得原地改写内容；产生后继视图时，以新 `lifecycle_id`、旧ID和旧版本在同一事务中把旧视图置为 `Superseded` 并创建新的 `Current`。输入失效时也只能将旧视图标记为 `Superseded`，不得写入 `Active/NeedsReview` 等其他对象的状态。
- `handoff_prepare` 必须保存标准交接包的原因、输入、保留行为、决策、未决项、失效项、期望输出和进入条件；来源与目标必须不同。
- `handoff_acknowledge` 是目标责任方可选的收件留痕，不是接受或拒绝的前置条件；目标责任方可从 `Prepared` 或
  `Acknowledged` 直接调用 `handoff_accept/handoff_reject`，分别保存责任人、时间与证据。后继交接使用
  `handoff_supersede`，不得把接受与拒绝共用一个含糊的决定字段。

状态服务只执行结构、状态和并发边界；`Completed`、`Accepted` 等专业或治理结论仍由 `dev-lc` 校验其正式产物语义与授权证据。

## WIT 工作项

工作项至少包含：

| 字段 | 说明 |
| --- | --- |
| `work_item_id` | 稳定 `WIT-*` 编号 |
| `skill` | 唯一目标专业 Skill |
| `input_versions` | 版本化输入引用 |
| `input_fingerprint` | 排序后输入的内容指纹 |
| `owned_paths` | 允许修改的项目路径；为空表示不授权写项目 |
| `owned_artifacts` | 责任产物编号 |
| `attempt` | 实际认领次数 |
| `agent_id` | 当前执行 Agent；未认领时为空 |
| `status` | `Prepared/Running/Completed/Blocked/Failed/Cancelled` |
| `expected_outputs` | 预期产物和证据 |

`work_get/work_list/agent_run_list` 提供中断后的当前任务和运行身份恢复读取。`work_claim` 必须提供当前版本；
`agent_run_bind` 只允许绑定处于 `Running` 的 WIT，并且必须匹配认领 Agent 和输入指纹；`work_complete` 同样必须匹配
认领 Agent 和输入指纹。冲突时返回最新对象，不覆盖其他 Agent 的更新。

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

状态服务不可用时不得在项目中创建备用目录。调度器默认退回 `route-only`；只有用户已经要求在当前会话实际推进、宿主具有
原生子代理、任务不要求中断恢复或正式控制对象持久化时，才允许使用 `session-coordinate`。该模式只保留会话内工作状态，
必须报告 `state_persistence: none`，不得生成或宣称已持久化的 `CHG/HOF/LCV/WIT`。需要可恢复状态时仍为 `route-only`。

关闭的持久化变更可以归档但不自动删除，开放变更禁止自动清理。附件和原始日志的保留期由部署策略配置，控制对象及审计记录默认长期保留。

状态库不得保存凭据、访问令牌、私钥、完整生产数据或无界原始日志；只保存完成追踪所需的最小结构化信息、摘要、哈希和引用。
