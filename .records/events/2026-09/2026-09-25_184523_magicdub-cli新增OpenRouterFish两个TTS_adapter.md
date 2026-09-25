---
record_id: rec_20260925_184523_fabf1e
occurred_at: 2026-09-25T18:45:23+08:00
kind: artifact
domain: engineering
certainty: verified
related_artifacts:
  - Releases/06_magicdub-cli系统设计.md
supersedes: null
---

# magicdub-cli 新增 OpenRouter Fish 两个 TTS adapter

## 结果

本地 magicdub-cli（未提交、未发版）新增：

- `openrouter/fish-audio/s2.1-pro-free` → 模型 `fish-audio/s2.1-pro-free:free`
- `openrouter/fish-audio/s2.1-pro` → 模型 `fish-audio/s2.1-pro`

Instant clone：`POST https://openrouter.ai/api/v1/audio/speech`；`input_references`＝参考音频＋`src.text`；`response_format=pcm` 按响应 Content-Type 无损封 WAV。免费 `cost_cny=0`；付费同 Fish 公开价（UTF-8 字节 × $0.000015 × 7）。

slot:tts：`openrouter/*` → `OPENROUTER_API_KEY`；仍传入 `source_text`。credentials 模板补 `OPENROUTER_API_KEY`。Releases/06 已同步。60 项测试通过。

## 未完成与下一步

- 未做真实 OpenRouter 冒烟；未 commit／发版；正式线仍为 v0.2.8
