---
record_id: rec_20260923_060238_a25df9
occurred_at: 2026-09-23T06:02:38+08:00
kind: milestone
domain: engineering
certainty: verified
related_artifacts:
  - Releases/06_magicdub-cli系统设计.md
  - https://github.com/shishengkai/magicdub-cli
  - https://github.com/shishengkai/magicdub-cli/releases/tag/v0.1.1
supersedes: null
---

# magicdub-cli 公开并改为跟随最新正式 Release

## 结果

- 仓库 `shishengkai/magicdub-cli` 已改为 **public**。
- 安装／`magicdub update` 默认解析 GitHub `releases/latest`（非 draft／非 prerelease）；可用 `MAGICDUB_REF`／`--ref` 覆盖。
- 发布正式 **v0.1.1**（提交 `f3aeeb6`）；`/releases/latest` → `v0.1.1`；raw `install.sh` HTTP 200。
- README 按 public 一句 curl 安装／升级／卸载改写。`Releases/06` CLI 行已同步。

## 对当前项目的影响

用户侧以正式 Release 为准，不再默认追 `main` tip。变 public 后 curl\|sh 可用。
