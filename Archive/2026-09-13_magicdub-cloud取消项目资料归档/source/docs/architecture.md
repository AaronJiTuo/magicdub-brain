# Architecture

MagicDub Cloud 采用三层架构：Public API、Orchestrator、Workers。服务器实例尽量无状态，业务真相收敛到数据库、对象存储和托管队列。

## Public API

Public API 是唯一业务入口。网站用户和专业 API 用户都使用同一套路由，只是认证方式不同。

Public API 负责：

- 鉴权和授权。
- 创建上传会话。
- 创建异步 job。
- 查询 job、asset、usage、webhook 配置。
- 接收取消、重试、partial rerun 请求。
- 返回稳定的外部 API contract。

Public API 不直接执行长任务，不在内存中保存 job 进度，不绕过 orchestrator 推进复杂 workflow。

## Orchestrator

Orchestrator 是任务状态机和调度中心。

Orchestrator 负责：

- 读取和更新 job/stage/segment 状态。
- 根据状态投递 queue message。
- 处理 provider callback 归一化后的事件。
- 做幂等控制、重试、超时、取消和 partial rerun。
- 决定下一步应该执行哪个 stage 或 segment。

Orchestrator 必须基于持久状态推进任务。任何实例重启后，只要 DB/R2/Queue 还在，任务应可以恢复或重新调度。

## Workers

Workers 是执行层，按能力拆分，不按前端/后端渠道拆分。

建议初始 worker 类型：

- `worker-orchestrator`
- `worker-media`
- `worker-separation`
- `worker-asr`
- `worker-translation`
- `worker-tts`
- `worker-compose`

worker 应尽量无状态。worker 可以在执行过程中使用临时文件或本地缓存，但完成后必须把业务结果写回 DB/R2，并通过 queue 或 orchestrator 推进后续状态。

## State Layer

状态分层：

- D1/Postgres：业务真相，包括 account、project、asset、job、stage、segment、provider_call、usage。
- R2：大文件和中间产物，包括 source video、source audio、speech stem、residual audio、segment audio、TTS output、final video。
- Queues：待执行事件和阶段调度消息。
- KV/Cache：短期缓存、限流计数、幂等辅助数据。它不能作为业务真相源。

严格来说，Cloud 版不是无状态系统；它是无状态 compute 加有状态托管存储。

## Cloudflare 与 Modal 边界

Cloudflare 负责控制面：

- Public API
- webhook ingest
- lightweight orchestrator
- queue consumers
- auth/rate limit
- R2 signed upload/download
- D1/Postgres 访问

Modal 负责重执行任务：

- ffmpeg
- 长时间 CPU 任务
- 需要本地文件系统的 media processing
- 未来可能需要 GPU 或自托管模型的任务
- 大文件拼装和转码

Modal 不做业务真相源，不独占状态机，不作为用户直接访问的公开 API。

## Webhook Ingest

provider webhook 不能直接改业务最终状态。所有 provider callback 必须先进入 webhook ingest。

webhook ingest 负责：

- 验证来源和签名。
- 记录原始 callback。
- 归一化 provider event。
- 根据 provider_call 做幂等去重。
- 投递事件给 orchestrator。

只有 orchestrator 可以基于当前持久状态决定是否推进 job/stage/segment。

