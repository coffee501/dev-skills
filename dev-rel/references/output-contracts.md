# 发布输出契约

## 目录

- [使用原则](#使用原则)
- [REL](#rel)
- [DEP](#dep)
- [MIGRUN](#migrun)
- [OBS](#obs)
- [就绪诊断与交接](#就绪诊断与交接)

## 使用原则

正式产物遵循共享信封并引用版本化来源。未知内容明确标记，不虚构授权、目标、责任人或执行结果。以下是语义模板，不要求所有项目采用同一存储格式。

## REL

```yaml
protocol_version: DEV-SUITE-7.1
id: REL-001
type: release
change: CHG-PENDING-001
version: 1
status: Approved
owner: release-owner
sources: [MIG-001@v1, IMP-001@v2, REV-001@v1, GATE-001@v1]
applies_to: {candidate: artifact-digest, environment: production-a}
authorization: {scope: approved-scope, expires_at: timestamp}
window: {start: timestamp, end: timestamp}
batches: [DEP-001@v1, MIGRUN-001@v1]
stop_conditions: []
recovery: {rollback: plan-ref, forward_fix: plan-ref}
evidence: []
risks: []
updated_at: 2026-01-01T00:00:00+08:00
```

## DEP

```yaml
protocol_version: DEV-SUITE-7.1
id: DEP-001
type: deployment-batch
change: CHG-PENDING-001
version: 1
status: Succeeded
owner: release-owner
sources: [REL-001@v1, IMP-001@v2]
applies_to: {candidate: artifact-digest, environment: production-a}
rel_ref: REL-001@v1
objective: 部署目标
target: {environment: production-a, units: [service-a]}
candidate: {version: v2, digest: sha256-value}
execution: {entry: pipeline-or-command, started_at: timestamp, finished_at: timestamp}
postconditions: []
observation_refs: [OBS-001@v1]
recovery_refs: []
evidence: []
risks: []
updated_at: 2026-01-01T00:00:00+08:00
```

## MIGRUN

```yaml
protocol_version: DEV-SUITE-7.1
id: MIGRUN-001
type: migration-run
change: CHG-PENDING-001
version: 1
status: Verified
owner: release-owner
sources: [REL-001@v1, MIG-001@v1]
applies_to: {candidate: artifact-digest, environment: production-a}
rel_ref: REL-001@v1
mig_ref: MIG-001@v1
source_target: {source: old-state, target: new-state}
checkpoint: checkpoint-or-null
counts: {planned: 0, processed: 0, succeeded: 0, failed: 0, skipped: 0}
validation: {status: passed, differences: []}
recovery: {rollback_limit: description, action: none}
evidence: []
risks: []
updated_at: 2026-01-01T00:00:00+08:00
```

## OBS

```yaml
protocol_version: DEV-SUITE-7.1
id: OBS-001
type: release-observation
change: CHG-PENDING-001
version: 1
status: Healthy
owner: release-owner
sources: [REL-001@v1, DEP-001@v1]
applies_to: {candidate: artifact-digest, environment: production-a}
rel_ref: REL-001@v1
batch_refs: [DEP-001@v1]
window: {start: timestamp, end: timestamp}
baseline: []
signals: []
decision: {action: continue, reason: criteria-satisfied}
limitations: []
evidence: []
risks: []
updated_at: 2026-01-01T00:00:00+08:00
```

## 就绪诊断与交接

就绪诊断至少输出：目标、候选、环境、质量门、授权、执行顺序、预检、观察、停止与恢复、P0/P1、可继续只读工作和解除条件。

向 `dev-ops` 的HOF至少包含生产版本、配置、Schema和迁移状态、流量和开关、OBS、告警与面板、Runbook或人工入口、残余风险、未完成退出项、回滚下限、失效条件和责任角色。已经形成事故时同时提供发布时间线和原始记录。
