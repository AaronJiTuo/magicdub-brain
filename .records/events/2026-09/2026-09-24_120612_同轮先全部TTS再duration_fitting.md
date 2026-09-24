---
record_id: rec_20260924_120612_e1137c
occurred_at: 2026-09-24T12:06:12+08:00
kind: decision
domain: engineering
certainty: confirmed
related_artifacts:
  - Releases/06_magicdub-cli系统设计.md
  - https://github.com/shishengkai/magicdub-cli
supersedes: null
---

# 同轮先全部 TTS，再全部 duration_fitting

## 结果

用户实测 v0.2.0 后指出：同轮不应「一句 TTS 立刻 duration_fitting」，而应先串行完成本轮全部 TTS，再串行全部 duration_fitting／标 selection，再决定下一批翻译或 alignment。已改正 `pipeline` 与 Releases/06。未发版。

## 对当前项目的影响

行为与 v0.2.0 tag 不一致；需新 Release 或 `MAGICDUB_REF` 才能装到。
