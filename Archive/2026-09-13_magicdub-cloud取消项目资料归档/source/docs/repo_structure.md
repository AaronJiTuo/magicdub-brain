# Repo Structure

`magicdub-cloud` 初始采用 private monorepo。repo 名称：

```text
magicdub-cloud
```

## Suggested Layout

```text
magicdub-cloud/
  README.md
  apps/
    web/
    api/
    webhook-ingest/
    worker-orchestrator/
    worker-media/
    worker-separation/
    worker-asr/
    worker-translation/
    worker-tts/
    worker-compose/
  packages/
    domain/
    db/
    sdk/
    provider-contracts/
    queue-contracts/
    media-contracts/
  infra/
    cloudflare/
    modal/
  docs/
    adr/
  prompts/
```

## Apps

`apps/web`

`magicdub.com` 网站前端。它是 Public API 的浏览器客户端，不是品牌主仓，不拥有独立业务后端。

`apps/api`

Public API。负责 auth、uploads、jobs、assets、webhooks、usage 等外部接口。

`apps/webhook-ingest`

接收 provider callback，做签名验证、原始事件记录、归一化和幂等，然后交给 orchestrator。

`apps/worker-orchestrator`

任务状态机和调度 worker。负责推进 job/stage/segment。

`apps/worker-*`

按能力拆分的执行 worker。worker 可以独立部署，但通过 shared packages 共享 contract。

## Packages

`packages/domain`

共享领域类型、状态枚举、错误码和业务 contract。

`packages/db`

数据库 schema、migration、query helper 和 repository 层。

`packages/sdk`

Public API client。网站和外部客户示例都应优先使用 SDK。

`packages/provider-contracts`

ASR、TTS、LLM、vocal separation、asset store 等 provider 接口和媒体需求类型。

`packages/queue-contracts`

queue message schema、event type、idempotency key 规则。

`packages/media-contracts`

asset、media requirement、prepared media、mime type、object key 约定。

## Frontend Boundary

前端可以和 API/worker 同仓，但不能同耦合。

允许：

- 使用 `packages/sdk`
- 使用公开 API type
- 使用 UI 专属状态

不允许：

- import worker 内部逻辑
- 直接访问 DB
- 直接投递 queue
- 依赖 R2 object key 私有规则
- 绕过 Public API 调用内部控制面

