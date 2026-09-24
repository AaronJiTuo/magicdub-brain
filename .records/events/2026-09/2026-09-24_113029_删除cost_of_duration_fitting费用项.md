---
record_id: rec_20260924_113029_461598
occurred_at: 2026-09-24T11:30:29+08:00
kind: decision
domain: engineering
certainty: confirmed
related_artifacts:
  - Releases/06_magicdub-cli系统设计.md
  - https://github.com/shishengkai/magicdub-cli
supersedes: rec_20260923_080643_9d8c7f
---

# 删除 cost_of_duration_fitting 费用项

## 结果

用户要求去掉 `assets.cost.cost_of_duration_fitting`：duration_fitting 无模型费，不必保留空桶。凡 translation／TTS API 费（含返工）只进 `cost_of_translation`／`cost_of_tts`。Releases/06 与 magicdub-cli 代码已改（state 骨架、记账、汇总打印）。未发版。

## 对当前项目的影响

新任务 state 不再含该字段。v0.1 无续跑，旧任务不受影响。原先「恒 0 兼容保留」口径作废。
