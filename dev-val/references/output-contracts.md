# 验证输出契约

## 目录

- [使用原则](#使用原则)
- [RUN](#run)
- [EVD](#evd)
- [DEFECT](#defect)
- [GATE](#gate)
- [验证摘要视图](#验证摘要视图)
- [就绪诊断](#就绪诊断)
- [交接包](#交接包)

## 使用原则

正式产物遵循共享信封并引用版本化来源。未知内容明确标记，不虚构编号、环境、责任人或授权。下面字段是语义模板，不要求所有项目采用同一存储格式。

## RUN

```yaml
protocol_version: DEV-SUITE-8.0
id: RUN-001
type: validation-run
change: CHG-PENDING-001
version: 1
status: Passed
owner: validation-owner
objective: 验证目标
sources: [TC-001@v1, IMP-001@v2, BUILD-001@v1, REV-001@v1]
applies_to: {target: commit-or-build, environment: test-environment}
test_refs: [TC-001@v1]
commands: [safe-command-summary]
limits: {timeout_seconds: 600, concurrency: 1}
attempts: []
cleanup: {status: completed, residuals: []}
evidence: [EVD-001@v1]
risks: []
updated_at: 2026-01-01T00:00:00+08:00
```

## EVD

```yaml
protocol_version: DEV-SUITE-8.0
id: EVD-001
type: validation-evidence
change: CHG-PENDING-001
version: 1
status: Valid
owner: validation-owner
sources: [RUN-001@v1, TC-001@v1, AC-001@v1]
run_ref: RUN-001@v1
test_refs: [TC-001@v1]
expected_sources: [AC-001@v1]
observations: []
raw_locators: []
integrity: {algorithm: sha256, digest: value-or-pending}
applies_to: {target: commit-or-build, environment: test-environment}
validity: {freshness_until: null, invalidation_conditions: []}
redaction: {applied: false, notes: []}
evidence: []
risks: []
updated_at: 2026-01-01T00:00:00+08:00
```

## DEFECT

```yaml
protocol_version: DEV-SUITE-8.0
id: DEFECT-001
type: validation-defect
change: CHG-PENDING-001
version: 1
status: Open
owner: pending
sources: [RUN-001@v1, EVD-001@v1]
applies_to: {target: commit-or-build, environment: test-environment}
run_ref: RUN-001@v1
evidence_refs: [EVD-001@v1]
test_refs: [TC-001@v1]
classification: ProductFailure
expected_source: AC-001@v1
observed_result: 实际结果
reproducibility: confirmed-or-unknown
impact: 已观察到的影响
route_to: dev-impl
revalidation_conditions: []
evidence: [EVD-001@v1]
risks: []
updated_at: 2026-01-01T00:00:00+08:00
```

## GATE

```yaml
protocol_version: DEV-SUITE-8.0
id: GATE-001
type: validation-gate
change: CHG-PENDING-001
version: 1
status: Pass
confirmation: Suggested
confirmation_record: null
owner: validation-owner
sources: [VAL-001@v1, DVAL-001@v1, RUN-001@v1, EVD-001@v1]
applies_to: {target: commit-or-build, environment: test-environment}
rule_version: gate-policy-version
validation_targets: [VAL-001@v1, DVAL-001@v1]
run_refs: [RUN-001@v1]
evidence_refs: [EVD-001@v1]
defect_refs: []
target_results:
  - target_ref: VAL-001@v1
    result: Pass
    evidence_refs: [EVD-001@v1]
    unmet_conditions: []
  - target_ref: DVAL-001@v1
    result: Pass
    evidence_refs: [EVD-001@v1]
    unmet_conditions: []
execution_summary:
  selected: 1
  executed: 1
  passed: 1
  failed: 0
  blocked: 0
  skipped: 0
  not_run: 0
missing_or_expired: []
failures: []
quarantined_or_skipped: []
unverified_scope: []
risk_acceptances: []
reason: 结论依据
invalidation_conditions: []
revalidation_conditions: []
next_responsibility: dev-lc-or-project-owner
handoff_refs: []
evidence: [EVD-001@v1]
risks: [remaining-risk-or-ref]
updated_at: 2026-01-01T00:00:00+08:00
```

`GATE` 是一次完整验证或正式G5评估的闭环产物。`run_refs/evidence_refs/defect_refs` 分别引用执行、证据和已识别缺陷；没有缺陷时保留空列表。`target_results` 必须逐一覆盖 `validation_targets` 中的 `VAL/DVAL`，不允许总体结论掩盖局部失败或阻塞。`execution_summary` 只用于阅读，不能以数量或通过率替代聚合规则。`unverified_scope` 记录未被当前证据覆盖的适用范围；共享 `risks` 字段在 `GATE` 中表示结论形成后仍存在的剩余风险。

8.0 `GATE` 必须包含 `confirmation_record`。`Suggested` 时该字段固定为 `null`；`Confirmed` 时必须为对象，并包含非空的 `confirmed_by`、带时区的 `confirmed_at`、非空 `scope` 以及非空 `basis` 引用列表。只有确认级别和确认记录同时满足约束时，才能表达正式确认；不得仅把字符串从 `Suggested` 改为 `Confirmed`。

定向验证、缺陷复测或专项实验可以只产生 `RUN/EVD/DEFECT`；只有其改变阶段门结论或用户要求正式聚合时才创建或更新 `GATE`。代码、契约、配置、预期、环境、证据或规则变化时，创建新版本或后继 `GATE`，不得静默覆盖历史。

## 验证摘要视图

需要人类可读报告时，可以从一个明确版本的 `GATE` 及其引用生成 Markdown、HTML 或表格摘要。摘要应展示候选、范围、逐目标结果、执行概况、缺陷、未验证范围、例外、剩余风险、结论、确认级别、重新验证条件和下一责任方。

验证摘要是无独立状态的只读投影视图：必须标明来源 `GATE`，不得取得新的正式编号，不得独立确认、改变或覆盖 `GATE`，也不得被描述为外部交付批准。

## 就绪诊断

至少输出：目标和模式、有效输入、被测版本、环境与授权、预期来源、计划测试、安全门结果、P0/P1、可继续只读工作、解除阻塞条件以及所需交接。

## 交接包

使用共享 `HOF` 信封，并补充来源 `RUN/EVD/DEFECT/GATE`、首次失败、失败分类及置信边界、被测版本与环境、受阻测试和门禁、可继续范围、目标流程需要交付的内容以及重新验证条件。

向套件外部交付流程提供信息时，必须明确 `GATE` 结果和确认级别、适用候选、有效证据、例外、残余风险和失效条件；不得写成外部交付批准。
