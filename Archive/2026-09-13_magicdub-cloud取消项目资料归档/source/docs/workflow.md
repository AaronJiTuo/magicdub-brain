# Workflow

MagicDub Cloud 对外表现为异步 job，对内通过 stage 和 segment 状态机推进任务。

## Cloud 主流程

1. Client 调用 `POST /v1/uploads` 创建上传会话。
2. Public API 返回 R2 signed upload URL 和 `asset_id`。
3. Browser/client 直接上传 source video 到 R2。
4. Client 调用 `POST /v1/jobs`，传入 `source_asset_id`、目标语言和处理选项。
5. Public API 创建 job、初始 stage、usage 预估记录，并投递 orchestrator message。
6. Orchestrator 根据 job 状态调度下一个 stage。
7. stage worker 执行任务，写入 DB/R2，并通知 orchestrator。
8. 外部 provider 的异步 callback 先进入 webhook ingest，再由 orchestrator 幂等推进状态。
9. Client 通过 `GET /v1/jobs/{job_id}` 轮询状态，或通过 webhook 接收完成通知。
10. job 完成后，Client 通过 asset/result URL 下载最终视频。

## Stage Mapping

Cloud stage 与 OSS 顺序 pipeline 的业务语义对应如下：

- `prepare`：创建工作上下文、校验 source asset、记录输入元数据。
- `extract_audio`：从 source video 提取 source audio。
- `separate`：分离 speech/vocals stem。
- `create_instrumental`：生成 residual/instrumental track。
- `asr`：对 speech stem 做语音识别，生成 transcript 和 segments。
- `translate`：按 segment 翻译文本。
- `split_segments`：按 ASR timing 切割原始 speech segment。
- `tts`：按 segment 合成目标语言 speech。
- `align`：对齐每段合成语音时长。
- `compose`：混合 residual、aligned TTS segments 和 silent video。
- `export`：生成 final video asset，更新 job result。

## OSS 参考

OSS 参考仓库：

```text
https://github.com/OpenSiC-ai/magicdub.git
```

当 Cloud 实现需要确认业务语义时，优先回查 OSS repo 中这些位置：

- `Drafts/程序流程.md`
- `pipeline/`
- `providers/`
- `media/resources.py`

Cloud 不复用 OSS 的顺序执行模型。Cloud 复用的是领域语义、provider contract、media requirement 和 media resolver 思想。

## Retry, Cancel, Partial Rerun

每个 job、stage、segment 都必须可以独立表达状态。这样才能支持：

- stage retry
- segment retry
- provider fallback
- cancel
- timeout recovery
- partial rerun
- 只重跑 TTS 或 compose

worker 不应把“当前跑到哪一步”只保存在进程内存里。运行中断后，orchestrator 应能根据 DB/R2/Queue 中的状态恢复任务。

