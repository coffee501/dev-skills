# 测试设计产物最低契约

正式测试设计产物使用共享信封。以下JSON字段是机器校验的最低交换契约，不限制人类可读测试设计增加有价值内容。

全部正式产物先满足共享信封，再满足本模块增量字段。除特别说明外，状态统一使用
`Draft/Ready/NeedsReview/Deprecated/Superseded`。

## 产物族

| 类型 | ID | 增量必需字段 | `Ready` 时必须非空 |
| --- | --- | --- | --- |
| `test-scenario` | `TSC-*` | `name/traceability/risk_refs/preconditions/triggers/participants/input_classes/expected_outcomes/oracle_refs/state_and_data_effects/target_layers/priority/test_case_refs` | `traceability/expected_outcomes/oracle_refs/target_layers` |
| `test-case` | `TC-*` | 见下文TC模板 | `traceability/steps/expected_results/oracle_refs` |
| `test-data-partition` | `TDP-*` | `name/traceability/dimension/classes/boundaries/constraints/sensitivity/generation/cleanup/test_case_refs` | `traceability/dimension/classes/test_case_refs` |
| `test-data-set` | `TD-*` | `name/partition_refs/data_definition/generation/constraints/sensitivity/isolation/cleanup/test_case_refs` | `data_definition/generation/cleanup/test_case_refs` |
| `test-environment` | `TENV-*` | `name/topology/component_versions/contract_versions/configuration_refs/dependency_refs/data_refs/isolation/reset/limitations` | `topology/component_versions/isolation/reset` |
| `test-condition` | `TCOND-*` | `name/condition_type/setup/trigger/observation/reset/dependency_refs/test_case_refs` | `condition_type/setup/observation/reset/test_case_refs` |
| `automation-spec` | `AUT-*` | 见下文AUT模板 | `test_case_refs/target_layer/data_setup/assertions/entrypoint/stability` |

`TSC` 的优先级同样使用 `Critical/High/Medium/Low`。数据和环境产物中的敏感信息只记录分类、引用和准备方式，不保存凭据或生产数据值。

## TC

```json
{
  "protocol_version": "DEV-SUITE-8.0",
  "id": "TC-001",
  "type": "test-case",
  "change": "CHG-001",
  "version": 1,
  "status": "Draft",
  "owner": "test-owner",
  "sources": ["AC-001@v1"],
  "applies_to": ["candidate-family"],
  "risks": [],
  "evidence": [],
  "updated_at": "2026-09-12T12:00:00+08:00",
  "name": "observable behavior",
  "traceability": ["TSC-001@v1", "AC-001@v1"],
  "priority": "High",
  "preconditions": [],
  "data_refs": [],
  "steps": [],
  "expected_results": [],
  "oracle_refs": [],
  "cleanup": [],
  "execution_method": "Manual",
  "automation_refs": []
}
```

状态使用 `Draft/Ready/NeedsReview/Deprecated/Superseded`，优先级使用 `Critical/High/Medium/Low`，执行方式使用
`Manual/AutomationCandidate/Automated`。`Ready` 必须具有可执行步骤、可观察预期和独立判定依据；`Automated` 必须引用
对应 `AUT`。

## AUT

```json
{
  "protocol_version": "DEV-SUITE-8.0",
  "id": "AUT-001",
  "type": "automation-spec",
  "change": "CHG-001",
  "version": 1,
  "status": "Draft",
  "owner": "test-owner",
  "sources": ["TC-001@v1"],
  "applies_to": ["candidate-family"],
  "risks": [],
  "evidence": [],
  "updated_at": "2026-09-12T12:00:00+08:00",
  "test_case_refs": ["TC-001@v1"],
  "target_layer": "component",
  "data_setup": [],
  "dependencies": [],
  "assertions": [],
  "entrypoint": "pending implementation",
  "triggers": [],
  "isolation": [],
  "stability": {}
}
```

状态使用 `Draft/Ready/NeedsReview/Deprecated/Superseded`。`Ready` 表示自动化规格足以交给 `dev-impl`，必须明确关联用例、
层级、数据、断言、入口和稳定性要求；它不表示测试代码已经实现、构建、评审或执行。

使用 `../scripts/validate_test_artifact.py` 校验上述七类JSON最低契约。校验通过只表示结构和关键交叉字段有效，不证明覆盖充分、
预期正确或测试设计已获基线确认。
