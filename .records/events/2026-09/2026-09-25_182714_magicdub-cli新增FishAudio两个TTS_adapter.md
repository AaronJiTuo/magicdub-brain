---
record_id: rec_20260925_182714_c984a2
occurred_at: 2026-09-25T18:27:14+08:00
kind: artifact
domain: engineering
certainty: verified
related_artifacts:
  - Releases/06_magicdub-cli系统设计.md
supersedes: null
---

# magicdub-cli 新增 Fish Audio Instant clone 两个 TTS adapter

## 结果

本地 magicdub-cli（未提交、未发版）新增：

- `fishaudio/s2.1-pro-free`
- `fishaudio/s2.1-pro`

Instant clone：`POST https://api.fish.audio/v1/tts`（msgpack）；`references[{audio, text}]`＝句 `src.audio`＋`src.text`；生成文本＝attempt `text`。参数对齐 skills（wav／44100 等）。免费 `cost_cny=0`；付费按目标 UTF-8 字节 × $0.000015 × 7。

**slot:tts**：原本已传入 `source_text`（`src.text`），IndexTTS2 与 Fish 共用；本轮仅按 adapter 分支凭据（`fishaudio/*`→`FISH_API_KEY`，其余仍 `FAL_KEY`）。缺 `source_text` 时 Fish adapter 报 `input_invalid`。

依赖新增 `msgpack`。credentials 模板补 `FISH_API_KEY`。Releases/06 §2.3／§3.3／§5.7 已同步。57 项测试通过。默认 TTS 仍为 `fal/index-tts-2`。

## 未完成与下一步

- 未做真实 Fish API 冒烟；未 commit／发版
- 正式线仍为 v0.2.8
