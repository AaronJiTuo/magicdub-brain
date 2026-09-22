---
record_id: rec_20260923_070246_7ea016
occurred_at: 2026-09-23T07:02:46+08:00
kind: decision
domain: engineering
certainty: confirmed
related_artifacts:
  - Releases/06_magicdub-cli系统设计.md
  - https://github.com/shishengkai/magicdub-cli
supersedes: null
---

# Adapter 目录统一为 vendor_model

## 结果

用户确认目录名必须含供应商，与 `adapter_id` 的 `vendor/model` 对应（`-`→`_`）。已重命名：

- `asr/whisper` → `asr/fal_whisper`
- `sep/demucs` → `sep/fal_demucs`
- `translation/deepseek_flash` → `translation/deepseek_deepseek_flash`
- `tts/fal_index_tts_2` 不变

`adapter_id` 字符串未改。Releases/06 §2.3 已同步并写明命名规则。

## 对当前项目的影响

日后 `openrouter/whisper` → `openrouter_whisper/`，与 fal 目录不冲突。
