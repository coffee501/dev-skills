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

## 确定性状态机证据

`dev-state/tests/state-store.test.mjs` 与 `dev-state/tests/mcp-server.test.mjs` 覆盖了路线摘要或无关节点变化后继续认领、关联依赖变化时阻止成功完成，以及跨越最近 500 条审计事件的精确产物历史读取。运行命令：`node --disable-warning=ExperimentalWarning --test dev-state/tests/state-store.test.mjs dev-state/tests/mcp-server.test.mjs`。这些测试只证明状态机和 MCP 接口行为；上表尚未运行的宿主前向场景继续标记 `NotRun`。
