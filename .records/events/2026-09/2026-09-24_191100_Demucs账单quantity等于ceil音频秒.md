---
record_id: rec_20260924_191100_demucsbill
occurred_at: 2026-09-24T19:11:00+08:00
kind: finding
domain: engineering
certainty: verified
related_artifacts:
  - Drafts/fal-whisper-compute-seconds-probe/out/demucs_billing_audio_check.json
supersedes: null
---

# Demucs billing quantity = ceil(音频秒)，与本地估算一致

## 结果

Admin billing-events 核对：

1. 控制实验：本地精确 **5.25 s** wav → 账单 `quantity=6`、`unit_price=0.0007`；等于 `ceil(5.25)`，**不等于** `ceil(inference_time≈3.11)`。
2. 历史请求 `01a0d187-…`：账单 `quantity=67`；下载产出 vocals 时长 ≈ **66.25 s**，`ceil=67` 一致。

故当前 `fal/demucs` 的 `ceil(输入音频秒)×$0.0007×7` 与账单口径一致（按音频秒，非 compute 秒）。
