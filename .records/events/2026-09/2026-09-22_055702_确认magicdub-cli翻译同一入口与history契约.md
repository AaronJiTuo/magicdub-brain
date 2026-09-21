---
record_id: rec_20260922_055702_4fe68c
occurred_at: 2026-09-22T05:57:02+08:00
kind: decision
domain: engineering
certainty: confirmed
related_artifacts:
  - Drafts/magicdub-cli/2026-09-22_magicdub-cli_pipeline设计.md
  - Drafts/magicdub-cli/2026-09-22_magicdub-cli_v0.1.0开发计划.md
  - Drafts/magicdub-cli/2026-09-20_magicdub-cli流程图.md
  - Drafts/magicdub-cli/2026-09-22_magicdub-cli目录与路径设计.md
  - Drafts/magicdub-cli/2026-09-21_magicdub-cli状态文件assets字段设计.md
  - Drafts/magicdub-cli/2026-09-22_magicdub-cli状态文件完整字段设计.md
supersedes: null
---

# 确认 magicdub-cli 翻译同一入口与 history 契约

## 结果

用户确认 `slot:translation` **不拆**「首译／修正」两个函数：adapter 只保留一个 `translate` 入口；每句用 `history[]` 区分——空 = 首译，非空 = duration_fitting 回环修正。两种场景都**必带** `src.transcript` 全文作语境。修正批仅含不合格句，history 携带已 rejected 稿的 `text`、TTS 实测时长与 `fitting_ratio`，提示比值>1 缩短、\<1 加长且意思不变。费用仍按本批 attempt：`1` → `cost_of_translation`，`≥2` → `cost_of_duration_fitting.translation`。

上述契约已写入 pipeline §5.6、流程图 IO 表与 v0.1.0 M4。

## 背景与理由

首译与修正共享全文语境、同一返回形状 `[{id, text}]` 与同一 DeepSeek adapter；差异只在句级是否附带上一稿 TTS 实测。拆两个入口会重复提示词与槽位组装，且 fitting 回环本就以 history 为证据。

同期（仍在 Draft、未进 Releases）已定稿的 magicdub-cli 骨架：pipeline 编排器、slot／adapter、state／assets、路径（`~/.magicdub/cli` + `Movies|Videos/MagicDub/cli/`）、v0.1.0 范围（单适配器快乐路径、无 `--only`／`--from`／slot 回退／force／并行）。空仓库已建：`https://github.com/shishengkai/magicdub-cli`。

## 证据与成果位置

见 `related_artifacts`；实现尚未开始。

## 对当前项目的影响

不影响现行 `magicdub-skills` 发布与日常安装。magicdub-cli 仍为独立工程草案；实现时以 Drafts 为准，不得静默改 skills 行为。

## 未完成与下一步

按用户明确要求后再启动 `magicdub-cli` 仓库实现（建议从 v0.1.0 计划 M0 起）。设计是否升格进 `Releases/` 另按 release-organizer 授权。
