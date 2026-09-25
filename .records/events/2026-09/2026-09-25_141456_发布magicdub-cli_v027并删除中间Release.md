---
record_id: rec_20260925_141456_cca38e
occurred_at: 2026-09-25T14:14:56+08:00
kind: milestone
domain: engineering
certainty: verified
related_artifacts:
  - https://github.com/shishengkai/magicdub-cli/releases/tag/v0.2.7
  - Releases/06_magicdub-cli系统设计.md
supersedes: null
---

# 发布 magicdub-cli v0.2.7 并删除 v0.2.4～v0.2.6

## 结论

正式 Release **v0.2.7**（`c2dd4c0`）已发布，为当前 `latest`。修复 URL 上传任务须 `get-remote` → `get` 两阶段轮询。

按用户要求删除 GitHub Release 及 tag：**v0.2.4**、**v0.2.5**、**v0.2.6**（含 `--cleanup-tag`）。历史 Record 仍保留当时事件，但远端已无这些正式版。`releases/latest` → v0.2.7。

## 升级

`magicdub update`
