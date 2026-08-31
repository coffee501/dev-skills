# 验证输出契约

## 目录

- [使用原则](#使用原则)
- [RUN](#run)
- [EVD](#evd)
- [DEFECT](#defect)
- [GATE](#gate)
- [就绪诊断](#就绪诊断)
- [交接包](#交接包)

## 使用原则

正式产物遵循共享信封并引用版本化来源。未知内容明确标记，不虚构编号、环境、责任人或授权。下面字段是语义模板，不要求所有项目采用同一存储格式。

## RUN

```yaml
protocol_version: DEV-SUITE-7.1
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
protocol_version: DEV-SUITE-7.1
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
protocol_version: DEV-SUITE-7.1
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
protocol_version: DEV-SUITE-7.1
id: GATE-001
type: validation-gate
change: CHG-PENDING-001
version: 1
status: Pass
confirmation: Suggested
owner: validation-owner
sources: [VAL-001@v1, DVAL-001@v1, EVD-001@v1]
applies_to: {target: commit-or-build, environment: test-environment}
rule_version: gate-policy-version
validation_targets: [VAL-001@v1, DVAL-001@v1]
evidence_refs: [EVD-001@v1]
missing_or_expired: []
failures: []
quarantined_or_skipped: []
risk_acceptances: []
reason: 结论依据
invalidation_conditions: []
evidence: [EVD-001@v1]
risks: []
updated_at: 2026-01-01T00:00:00+08:00
```

## 就绪诊断

至少输出：目标和模式、有效输入、被测版本、环境与授权、预期来源、计划测试、安全门结果、P0/P1、可继续只读工作、解除阻塞条件以及所需交接。

## 交接包

使用共享 `HOF` 信封，并补充来源 `RUN/EVD/DEFECT/GATE`、首次失败、失败分类及置信边界、被测版本与环境、受阻测试和门禁、可继续范围、目标流程需要交付的内容以及重新验证条件。

向 `dev-rel` 的交接必须明确 `GATE` 结果和确认级别、适用发布候选、有效证据、例外、残余风险和失效条件；不得写成发布批准。
