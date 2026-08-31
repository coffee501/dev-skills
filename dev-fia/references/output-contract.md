# FIA 机器产物契约

自然语言对接文档是主要交付；机器产物用于版本、失效、调度和审计，不要求前端开发者直接维护。

## 公共信封

使用 `DEV-SUITE-7.1`，类型固定为 `frontend-interface-alignment`，ID 使用 `FIA-*`。必须包含统一字段：

`protocol_version/id/type/change/version/status/owner/sources/applies_to/risks/evidence/updated_at`

## FIA 字段

| 字段 | 含义 |
| --- | --- |
| `service` | 后端能力或服务逻辑名称 |
| `consumers` | 适用 Web、移动端、BFF 或其他消费方标识 |
| `contract_refs` | `API/EVT` 或外部正式契约编号与版本 |
| `contract_identity` | 每个机器契约的类型、定位器、版本、指纹、权威方和范围 |
| `scenarios` | 场景标识、目标、前置与结果摘要 |
| `operations` | 操作标识、契约引用及场景关联 |
| `semantic_gaps` | 严重度、状态、影响、责任模块和解除条件 |
| `compatibility` | 版本组合、发布顺序、回滚、废弃和退出条件 |
| `readiness` | 独立的联调就绪判断、阻塞、条件和评估时间 |
| `handoff_refs` | 缺口返回或下游协作的 `HOF` 引用 |

`sources/contract_refs/consumers/scenarios/operations/semantic_gaps/handoff_refs` 使用数组；`applies_to/compatibility/readiness` 使用对象。

## 状态与确认

- `Draft`：允许存在不完整字段和未决语义，但身份与来源仍需可追踪。
- `ReadyForReview`：至少具有一个场景、操作和版本化契约引用。
- `Baselined`：满足 `ReadyForReview`，没有 `Blocked` 就绪结论，并记录 `alignment_confirmation.confirmed_by/confirmed_at`。
- `NeedsReview`：上游契约、业务语义、实现、权限、消费范围或版本组合发生实质变化。
- `Superseded/Deprecated`：保留历史和后继关系。

`readiness.assessment` 使用 `NotAssessed/Ready/ConditionallyReady/Blocked`。存在开放 P0 语义缺口时不得标记 `Ready`。

## 最小示例

```json
{
  "protocol_version": "DEV-SUITE-7.1",
  "id": "FIA-001",
  "type": "frontend-interface-alignment",
  "change": "CHG-001",
  "version": 1,
  "status": "ReadyForReview",
  "owner": "integration-owner",
  "sources": ["API-001@v2"],
  "applies_to": {"backend": "2.0", "consumer": "web-current"},
  "risks": [],
  "evidence": ["openapi.yaml@sha256:abc"],
  "updated_at": "2026-08-21T12:00:00+08:00",
  "service": "order-service",
  "consumers": ["web-current"],
  "contract_refs": ["API-001@v2"],
  "contract_identity": [{"source_type": "OpenAPI", "locator": "openapi.yaml", "version": "2.0", "fingerprint": "sha256:abc", "authority": "api-owner", "scope": "order operations"}],
  "scenarios": [{"id": "SCN-001", "name": "提交订单"}],
  "operations": [{"operation_id": "submitOrder", "contract_ref": "API-001@v2"}],
  "semantic_gaps": [],
  "compatibility": {"supported_combinations": ["web-current/backend-2.0"]},
  "readiness": {"assessment": "Ready", "blockers": [], "conditions": [], "assessed_at": "2026-08-21T12:00:00+08:00"},
  "handoff_refs": []
}
```

使用 `python scripts/validate_fia_artifact.py <artifact.json>` 做最低结构校验。校验通过不替代语义评审和责任方确认。
