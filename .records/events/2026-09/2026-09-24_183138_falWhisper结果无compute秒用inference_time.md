---
record_id: rec_20260924_183138_4252b7
occurred_at: 2026-09-24T18:31:38+08:00
kind: finding
domain: engineering
certainty: verified
related_artifacts:
  - Drafts/fal-whisper-compute-seconds-probe/README.md
supersedes: null
---

# fal Whisper 结果体无 compute seconds；用 status.inference_time

## 结果

对 `fal-ai/whisper` 用官方样例各跑 `diarize=false/true` 一次：

- **结果 JSON 不含** `compute_seconds` 或任何用量／时长计费字段（仅 text／chunks／diarization_segments／inferred_languages）。
- **queue status** 含 `metrics.inference_time`（本轮约 1.61 s／1.84 s）。
- 结果响应头有 `x-fal-raw-time`，与 inference_time 几乎一致。
- **`x-fal-billable-units` 本轮缺失**；billing-events 403。
- Pricing API 仅 `USD 0.0008`／`compute seconds`；**未见 0.00125** 单价分档。文档称 diarize 按分离推理时长加费，与「同单价 × 更长 inference」一致。

## 证据与成果位置

`Drafts/fal-whisper-compute-seconds-probe/`（`README.md`、`out/summary.json`）。历史 Steve Jobs ASR status 同样只有 `inference_time`，result 无用量字段。

## 对当前项目的影响

Whisper adapter 若要估 `cost_cny`，须从 status／headers 取 `inference_time`（或 raw-time），不能指望结果 body。0.00125 单价本轮未 empirically 证实；实现前宜再确认出处或继续用 Pricing API 的 0.0008。
