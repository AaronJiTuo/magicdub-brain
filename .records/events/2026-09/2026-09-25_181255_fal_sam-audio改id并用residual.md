---
record_id: rec_20260925_181255_47f3ae
occurred_at: 2026-09-25T18:12:55+08:00
kind: decision
domain: engineering
certainty: confirmed
related_artifacts:
  - Releases/06_magicdub-cli系统设计.md
supersedes: null
---

# fal/sam-audio：改 id 并用 API residual

## 结果

用户确认：

1. adapter_id 由 `fal/sam_audio` 改为 **`fal/sam-audio`**（目录仍为 `fal_sam_audio`）
2. fal 响应含 **`residual`**（与 `target` 并列）；`non_speech` **直接下载 residual**，取消本地原音减 target

Releases/06 与本地实现已同步；仍未提交／发版。
