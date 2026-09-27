---
record_id: rec_20260927_124220_399bfe
occurred_at: 2026-09-27T12:42:20+08:00
kind: decision
domain: engineering
certainty: confirmed
related_artifacts:
  - Releases/06_magicdub-cli系统设计.md
  - https://github.com/shishengkai/magicdub-cli
supersedes: null
---

# magicdub-cli demux 优先按原编码流拷贝

## 结果

`fixed:demux` 改为：探测首条音轨 codec，能映射常见封装则 `-c:a copy` 落盘 `media/src/audio.<ext>`（AAC→`.m4a` 等）；未知或 copy 失败回退 `pcm_f32le` WAV。无声视频仍 `-c:v copy`。`Releases/06` §5.2／M2 已同步。本地未提交／未发版。

## 背景与理由

YouTube 等片源多为 AAC；一律转 float32 WAV 不提升音质却增大体积，并加重后续上传体积压力。

## 证据与成果位置

- `src/magicdub_cli/steps/fixed/demux.py`、`tests/test_demux.py`
- 规范：`Releases/06` §5.2

## 对当前项目的影响

新任务 `src.audio` 扩展名随源编码变化；sep／asr 仍按 path 读入。已发布 v0.2.11 仍为固定 WAV。

## 未完成与下一步

与交付物调整一并提交／发版需用户授权。
