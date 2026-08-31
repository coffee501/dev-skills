# OpenAPI 与机器契约基线

## OpenAPI 最小检查

对 OpenAPI 3.0/3.1 至少检查：

- `info`、`servers` 或明确环境定位，以及版本含义
- 稳定且唯一的 `operationId`
- path/query/header/cookie/body 参数的位置、类型、必填和约束
- 成功、业务失败、认证失败、限流和服务失败响应
- 可解析 `$ref`、Schema 组合和 discriminator
- 安全方案、接口级覆盖和权限语义的外部说明
- 分页、排序、过滤、时间、金额、枚举、空值和二进制语义
- 可脱敏且与 Schema 一致的请求/响应样例

这些项目只构成结构基线，不能替代场景、状态、业务结果和发布协作说明。

## 缺失时的处理

可以从路由、控制器、DTO、Schema、测试和网关配置生成候选 OpenAPI，但必须：

- 标记 `candidate` 和生成来源版本
- 区分直接提取与推断
- 不编造业务描述、错误码、默认值或权限
- 交给 `dev-lld` 或契约责任方确认后再作为权威输入

候选 OpenAPI 不是 `FIA Baselined` 的充分条件。

## 非 HTTP 契约

| 交互 | 首选机器契约 |
| --- | --- |
| GraphQL | SDL、operation documents、schema registry |
| gRPC | Proto 和服务描述 |
| 消息/事件 | AsyncAPI、Schema Registry、Avro/JSON Schema/Proto |
| SSE/WebSocket | 握手契约、消息 Schema、事件类型和连接生命周期 |
| 文件/批处理 | 文件 Schema、编码、校验规则、清单和传输约定 |

不要为了统一格式而损失原协议语义。

## 契约身份

每个机器契约记录：`source_type`、`locator`、`version/fingerprint`、`authority`、`scope`、生成方式和适用环境。只写文件名或 URL 而没有版本不足以支撑对接基线。
