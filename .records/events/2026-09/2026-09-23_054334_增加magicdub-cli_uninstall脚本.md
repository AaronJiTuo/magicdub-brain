---
record_id: rec_20260923_054334_3be33c
occurred_at: 2026-09-23T05:43:34+08:00
kind: artifact
domain: engineering
certainty: confirmed
related_artifacts:
  - https://github.com/shishengkai/magicdub-cli
supersedes: null
---

# 为 magicdub-cli 增加 uninstall.sh

## 结果

新增 `uninstall.sh`：默认 `uv tool uninstall magicdub-cli` 并清理 `magicdub`／旧 `magicdub-cli` 入口；`--purge` 删除 `~/.magicdub/cli`；`--purge-tasks` 删除默认任务父目录。README 已说明。已 push（含 README 后续提交）。

## 对当前项目的影响

升级可先卸载再安装；用户停用有明确卸载路径。不默认删凭据与成片。
