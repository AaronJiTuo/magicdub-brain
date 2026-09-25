---
record_id: rec_20260925_203808_c9f1a2
occurred_at: 2026-09-25T20:38:08+08:00
kind: artifact
domain: engineering
certainty: verified
related_artifacts:
  - Releases/06_magicdub-cli系统设计.md
  - https://github.com/shishengkai/magicdub-cli
supersedes: null
---

# 实现 magicdub config 交互选 slots

## 结果

本地 magicdub-cli 新增子命令 `magicdub config`（`questionary`）：一级四类模型＋完成；二级按 registry `slot` 单选 adapter（标 `✓` 当前项）＋返回。完成时相对启动 slots 有变更才只写 `config.yaml` 的 `slots` 块；非 TTY 退出码 2。64 项测试通过。**尚未提交／发版**。

## 证据与成果位置

- 代码：`configure.py`、`config.update_slots_in_config_file`、adapter `slot`、registry `adapter_ids_for_slot`
- 规范：`Releases/06` §2.3a

## 对当前项目的影响

安装正式版后可用交互改默认模型；当前日常仍为 v0.2.9，不含本功能直至下一正式 Release。

## 未完成与下一步

提交／推送／发版由用户另行授权。
