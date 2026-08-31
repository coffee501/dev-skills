# REV 产物契约

## 通用信封

正式 `REV` 使用当前 `DEV-SUITE-7.1`；7.0存量产物继续兼容。包含 `protocol_version/id/type/change/version/status/owner/sources/applies_to/risks/evidence/updated_at`，按需提供 `supersedes`。

## REV 字段

类型为 `code-review`，ID使用 `REV-*`。至少包含：

- `review_scope`：仓库、文件/模块、包含与排除范围。
- `base`、`head`：不可变提交、摘要或工作区身份。
- `imp_refs`、`build_refs`、`requirement_refs`、`design_refs`、`test_refs`。
- `files_reviewed`、`generated_or_external`、`findings`。
- `required_actions`、`verification_requirements`、`limitations`、`handoff_refs`。

`Approved`必须满足：base/head非空；评审文件或等价范围非空；没有开放P0/P1；`limitations`不包含阻塞项；结论依据和评审者角色可追踪。

`ChangesRequested`必须包含至少一个开放P0/P1。`Blocked`必须说明阻塞原因和解除条件。外部平台批准必须记录来源、评审人权限、范围、时间和候选身份，不直接等同于体系内完整批准。

## 校验

```text
python scripts/validate_review_artifact.py <review.json>
```

校验器只检查最低结构、状态和跨字段不变量，不证明评审充分或发现正确。
