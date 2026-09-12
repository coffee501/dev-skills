# REV 产物契约

## 通用信封

正式 `REV` 使用当前 `DEV-SUITE-8.0`；7.0和7.1存量产物继续兼容。包含 `protocol_version/id/type/change/version/status/owner/sources/applies_to/risks/evidence/updated_at`，按需提供 `supersedes`。

## REV 字段

类型为 `code-review`，ID使用 `REV-*`。该类型名为协议兼容标识，语义上表示对完整实现候选的独立审查，不限于源代码风格检查。至少包含：

- `review_scope`：仓库、文件/模块、包含与排除范围。
- `base`、`head`：不可变提交、摘要或工作区身份。
- `imp_refs`、`build_refs`、`requirement_refs`、`design_refs`、`test_refs`。
- `files_reviewed`、`generated_or_external`、`findings`。
- `required_actions`、`verification_requirements`、`limitations`、`handoff_refs`。
- 8.0 `reviewer`：评审者的 `identity/role/execution_context`。
- 8.0 `implementation_actors`：每个实现责任主体的 `identity/role/execution_context`。
- 8.0 `independence`：`status/basis/compensating_controls`；状态只能是 `Independent`、`CompensatingControls` 或
  `NotEstablished`。

`Approved`必须满足：base/head非空；评审文件或等价范围非空；没有开放P0/P1；`limitations`不包含阻塞项；至少记录一个
实现责任主体；`independence.status` 为 `Independent` 或 `CompensatingControls`。前者要求评审者与所有实现责任主体具有
不同的身份和执行上下文；后者必须记录非空补偿控制。`NotEstablished` 不得批准。

`ChangesRequested`必须包含至少一个开放P0/P1。`Blocked`必须说明阻塞原因和解除条件。外部平台批准必须记录来源、评审人权限、范围、时间和候选身份，不直接等同于体系内完整批准。

## 校验

```text
python scripts/validate_review_artifact.py <review.json>
```

校验器只检查最低结构、状态和跨字段不变量，不证明评审充分或发现正确。
