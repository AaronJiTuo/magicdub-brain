---
record_id: rec_20260924_193605_dd44c8
occurred_at: 2026-09-24T19:36:05+08:00
kind: decision
domain: engineering
certainty: confirmed
related_artifacts:
  - Releases/06_magicdub-cli系统设计.md
supersedes: null
---

# 钉死 pipeline／step／adapter 三层隔离

## 结果

用户确认 magicdub-cli 分层：

1. **pipeline** 只认 step 与 `StepResult`，不感知具体 adapter 实现。  
2. **step**（fixed／slot）写 assets；slot 与 adapter 仅经窄契约交流。  
3. **adapter** 自洽完成供应商协议与本地计费；不知 pipeline／state／正式路径；同厂商也不得用包根融合层（如 `fal_api`）焊接。  
4. **`AdapterError` 等不得作为包级整仓异常**与 step 契约混放；属 adapter 边界契约。  
5. **本轮暂不开工**代码对齐；已知漂移：包级 `fal_api`、包级 `AdapterError`。  
6. **文件存储**（避免 CDN 上传等重复、又保持 adapter 独立）下一步再讨论后再实现。

已写入 [Releases/06](../../Releases/06_magicdub-cli系统设计.md) §1／§2.4／§3／§7.3。

## 对当前项目的影响

后续重构与文件存储设计以 §3 为准；在对齐完成前 CURRENT 保留漂移标记。
