# API Design

MagicDub Cloud 只维护一套 Public API。网站和专业客户都调用它。

## Authentication

默认两种认证方式：

- 网站用户：session/JWT。
- 专业 API 用户：API key。

两者进入同一套路由和同一套业务逻辑。差异只在认证方式、权限、配额和返回展示细节，不在业务 API 形态。

## Initial Resources

`POST /v1/uploads`

创建上传会话，返回 R2 signed upload URL 和 `asset_id`。浏览器或 API client 直接上传文件到 R2。

`POST /v1/jobs`

创建异步 dubbing job。请求应引用已上传的 `source_asset_id`，并携带目标语言、源语言、provider/profile 等选项。

`GET /v1/jobs/{job_id}`

查询 job 状态、进度、当前 stage、错误、result asset 和可展示摘要。

`POST /v1/jobs/{job_id}/cancel`

请求取消 job。取消应通过状态机推进，不能只删除 queue message。

`POST /v1/jobs/{job_id}/retry`

请求重试 job、stage 或 segment。初始版本可以只支持 job/stage 级重试，但 contract 应保留扩展到 segment 的空间。

`GET /v1/assets/{asset_id}`

查询 asset 元数据，并在有权限时返回下载信息或 signed download URL。

webhook endpoint 管理接口

用于专业客户配置 webhook 地址、事件类型、签名密钥和启停状态。

## Asynchronous Contract

Public API 不提供同步长任务接口。`POST /v1/jobs` 返回 job，后续通过 polling 或 webhook 获得结果。

外部用户只关心：

- job id
- job status
- progress
- result asset
- error code/message
- webhook event

内部 stage、segment、provider_call 可以通过 dashboard 或 debug API 暴露给内部用户，但不应过早成为稳定公开 API。

## Web Frontend Constraint

`apps/web` 只能使用 Public API 或生成的 SDK。它不能直接访问 DB、Queue、R2 object key 规则或 worker 内部函数。

这样网站和 API 客户共享同一套产品能力，避免出现两套业务后端。

