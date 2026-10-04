# Dev ORCH 前向行为验收

在 Codex 和 Claude Code 各运行适用场景。每次从独立会话启动本仓库入口，提供固定输入，保留宿主版本、任务原文、被加载的核心与专业 Skill、工具调用摘要、产物引用和最终用户视图。按实际行为判定；`orchestration-cases.json` 的文本断言和结构测试不能代替本验收。

| 场景 | 输入 | 必须观察到的行为 |
| --- | --- | --- |
| 单阶段直达 | 只要求设计一组后端测试用例，提供需求和 AC | 选择 `dev-test`，不机械创建整条生命周期路线；输出用户可读结果 |
| 单阶段输入缺失 | 只要求设计后端接口测试用例，声称 REQ/AC 已确认但不给出内容或引用 | 进入 `direct → dev-test` 的测试诊断，指出缺口和恢复条件，不编造用例或创建正式状态 |
| 实现到独立评审 | 提供已确认设计并要求实施、审查和验证 | 选择 `dev-impl → dev-cr → dev-val` 的适用分支；评审者与实现者分离，或由 `dev-cr` 记录符合项目政策的 `CompensatingControls`；没有有效评审结论时不宣称 G5 通过 |
| Claude 专业产物登记 | 启用外置状态并交给 `dev-specialist` 一个可校验的专业产物 | ORCH 不使用 `artifact_put`；专业 Agent 完成校验、登记并返回精确版本引用；工具缺失时明确报告未持久化 |
| 正式路线写入 | 提交缺少版本或违反 G3/G4/G5 依赖的 8.1 LCV 路线 | `lifecycle_put` 拒绝写入，旧 Current LCV 不被替代；有效路线可写入并生成 WIT |
| 子代理不可用 | 要求完成可顺序处理的需求和概要设计 | 在当前上下文完成有权限的专业工作；需要独立评审的分支阻塞，报告恢复条件 |
| 持久任务恢复 | 已有 `LCV`，一个 `WIT` 运行中后中断会话 | 新会话读取当前路线、WIT 和 Agent Run；核对路线节点、输入指纹与运行身份；不重复创建已完成工作或接收旧路线结果 |
| 输入失效与交接拒绝 | 修改上游 `REQ` 或拒绝 HOF | 停止受影响分支，保留旧证据，评估失效并建立后继路线；只重编受影响任务 |
| 输出边界 | 任一多阶段任务 | 用户只看到进度、专业结果、门禁状态、风险与下一责任；原始 `CHG/HOF/LCV/WIT` JSON 留在状态服务 |

每次验收记录 `Pass / Fail / Blocked / NotRun`、观察到的动作、证据引用和偏差。`Blocked` 必须指出缺少的宿主能力、权限或输入；不得记为 `Pass`。所有适用场景通过后，才可宣称对应宿主的调度行为已验收。


## 已运行的隔离验收

2026-09-24，Codex 原生 `dev-orch` 子代理使用独立上下文运行“单阶段输入缺失”场景，仅作只读判断。结果为 `Pass`：读取核心及 `dev-test` 流程，选择 `direct → dev-test`；因未提供实际 REQ/AC 条款与接口范围，只输出测试诊断和恢复输入，不虚构具体用例，不创建正式 `CHG/LCV/WIT`，也不执行实现或测试。其余宿主前向场景仍为 `NotRun`；状态机单元测试不代替宿主行为验收。

2026-10-03，使用固定的 `POST /orders` 需求与四条 AC 试跑“单阶段直达”，只要求测试设计，不允许修改文件、执行测试或建立正式生命周期状态：

重放输入如下；在 Codex 使用 `$dev-orch`，在 Claude Code 使用 `/dev-skills:dev-orch`，并保持“只读”限制：

```text
只设计后端 POST /orders 接口测试用例，不实施、不执行测试、不创建正式生命周期状态。

REQ-TRIAL@v1：已登录用户提交 customer_id 与 items；items 至少一项，每项有 sku 和 quantity，quantity 范围为 1..99。成功返回 201 和 order_id。同一 Idempotency-Key 的同一请求重试不得重复创建订单。

AC-TRIAL@v1：
1. 合法请求创建一笔订单。
2. 空 items 返回 400，且不创建订单。
3. 未登录请求返回 401，且不创建订单。
4. 使用相同 Idempotency-Key 重复提交相同请求时，返回相同 order_id，订单总数仍为一笔。

报告选择的运行模式和专业 Skill、用户可读测试设计、读取的核心和 Skill、是否建立 CHG/LCV/WIT、是否调用其他 Skill、工具调用摘要、阻塞与验收自评。
```

通过条件：读取 `dev-orch/AGENT.md`、`references/capability-routing.md` 与 `dev-test/SKILL.md` 后选择 `direct → dev-test`，输出可追踪的测试设计；不建立 `CHG/LCV/WIT`，不调用实现、验证或其他无关 Skill。

| 宿主 | 结果 | 已观察到的动作与证据 | 偏差及恢复条件 |
| --- | --- | --- | --- |
| Codex 原生子代理 | `Blocked` | 独立子代理已启动；尝试读取 `dev-orch/AGENT.md`、`capability-routing.md` 与 `dev-test/SKILL.md`，本地命令、Node REPL 和 UI 读取均因 `helper_unknown_error: setup refresh had errors` 或 Windows sandbox 初始化失败；没有创建正式状态或修改文件 | 未能加载入口和专业 Skill，不能评价实际路由或测试设计。待子代理本地读取能力恢复后，以相同输入重新运行 |
| Claude Code 2.1.284，插件模式 | `Blocked` | `claude --plugin-dir . --agent dev-orch --restricted --print --output-format json` 启动后返回 `api_error`、`Not logged in · Please run /login`，`duration_api_ms: 0`、`num_turns: 1`、`spawned: 0`；未发生模型行为或文件修改 | 需要在该宿主完成正常登录后，以相同输入重新运行；本次不能评价 Claude 入口或与 Codex 的行为一致性 |

上述 `Blocked` 不替代 2026-09-24 已通过的另一场景，也不改变其余场景的 `NotRun` 状态。结构测试和状态机测试只能证明静态契约与确定性代码行为。

## 确定性状态机证据

`dev-state/tests/state-store.test.mjs` 与 `dev-state/tests/mcp-server.test.mjs` 覆盖了路线摘要或无关节点变化后继续认领、关联依赖变化时阻止成功完成，以及跨越最近 500 条审计事件的精确产物历史读取。运行命令：`node --disable-warning=ExperimentalWarning --test dev-state/tests/state-store.test.mjs dev-state/tests/mcp-server.test.mjs`。这些测试只证明状态机和 MCP 接口行为；上表尚未运行的宿主前向场景继续标记 `NotRun`。
