# Domain Model

MagicDub Cloud 的核心数据模型围绕 account、asset、job、stage、segment 和 provider_call 展开。

## Core Entities

`account`

代表一个用户、团队或客户主体。用于权限、计费、配额和资源归属。

`api_key`

代表专业 API 用户的访问凭证。API key 绑定 account，可配置权限、状态、限额和最后使用时间。

`project`

代表用户侧的业务容器。网站用户可以把多个 job 放在一个 project 下；API 用户也可以选择使用 project 做批量管理。

`asset`

代表 R2 中的文件资源，包括 source video、source audio、speech stem、residual audio、segment audio、TTS output、final video。asset 记录业务元数据和 object key，不把大文件放入 DB。

`job`

代表一次异步 dubbing 请求。job 是 Public API 暴露给用户的主要执行单元。

`job_stage`

代表 job 中一个可调度、可重试、可观测的处理阶段。

`job_segment`

代表句子或 chunk 级别的处理单元。ASR、translation、TTS、duration alignment 等阶段都可能围绕 segment 并行推进。

`provider_call`

代表一次外部 provider 或内部执行平台调用。它用于幂等、callback 去重、成本追踪、失败排查和 SLA 分析。

`webhook_endpoint`

代表客户配置的回调地址和事件订阅规则。

`usage_event`

代表可计费或可统计的使用事件，例如视频时长、TTS 字符数、provider 调用次数、存储占用和失败重试。

## State Hierarchy

job 是外部可见状态：

- `queued`
- `running`
- `completed`
- `failed`
- `canceled`

stage 是内部 workflow 状态：

- `pending`
- `queued`
- `running`
- `waiting_provider`
- `completed`
- `failed`
- `skipped`
- `canceled`

segment 是细粒度并行状态：

- `pending`
- `running`
- `waiting_provider`
- `completed`
- `failed`
- `canceled`

job 状态由 stage 和 segment 汇总产生。不要只用一个大 JSON 字段表达整个任务真相。

## State Placement

DB 存业务真相：

- job 当前状态
- stage 当前状态
- segment 当前状态
- asset 元数据
- provider_call 记录
- usage_event

R2 存大文件：

- 原始视频
- 中间音频
- segment 文件
- provider 返回的媒体
- 最终视频

Queue 存待执行事件：

- stage dispatch
- segment dispatch
- callback normalized event
- retry event

KV/Cache 只能做短期辅助：

- rate limit
- short-lived idempotency helper
- signed URL 临时状态
- dashboard 缓存

任何必须长期准确的业务状态都不能只存在 KV/Cache 或 worker 内存里。

