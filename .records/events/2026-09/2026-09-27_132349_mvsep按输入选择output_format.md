---
record_id: rec_20260927_132349_db2374
occurred_at: 2026-09-27T13:23:49+08:00
kind: decision
domain: engineering
certainty: confirmed
related_artifacts:
  - Releases/06_magicdub-cli系统设计.md
  - https://github.com/shishengkai/magicdub-cli
supersedes: null
---

# mvsep/dnr-v3 按输入探针选择 output_format

## 结果

`mvsep/dnr-v3` 不再固定 `output_format=1`（wav16）。按输入音轨：mp3→0；其它有损→3（m4a）；无损≤16→2（flac16）；≥24→5（flac24）；浮点／32bit→4（wav32）；探针失败→2。`Releases/06` 已同步。本地未提交／未发版。

## 背景与理由

有损源出 WAV 不提升质量且膨胀体积；Premium 可选 m4a／flac／wav32，按「不低于输入、尽量省空间」选型。

## 证据与成果位置

- `choose_output_format`／`choose_output_format_from_stream`；`tests/test_mvsep_dnr_v3.py`
- 规范：`Releases/06` mvsep 段

## 对当前项目的影响

分离轨扩展名随所选格式变化；music+sfx 混音仍解为 PCM WAV。已发布 v0.2.11 仍固定 wav16。

## 未完成与下一步

与其它本地改动一并提交／发版需用户授权。
