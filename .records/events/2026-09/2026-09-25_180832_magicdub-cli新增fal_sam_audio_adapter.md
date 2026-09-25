---
record_id: rec_20260925_180832_4e908d
occurred_at: 2026-09-25T18:08:32+08:00
kind: artifact
domain: engineering
certainty: verified
related_artifacts:
  - Releases/06_magicdub-cli系统设计.md
supersedes: null
---

# magicdub-cli 新增 fal/sam_audio sep adapter

## 结果

本地 magicdub-cli（未提交、未发版）新增可选 `fal/sam_audio`：

- 端点 `fal-ai/sam-audio/separate`；输入经 fal CDN
- 参数对齐 skills（`predict_spans=false`、`reranking_candidates=1`、`acceleration=balanced`、`max_chunk_duration=60`、`chunk_overlap=5`、`output_format=wav`）；**`prompt=speaking`**（skills 为 `speech`）
- 下载 `target` → `speech`；本地原音减 target → `non_speech`（**不用** API `residual`）
- 计费：ceil(输出秒／30) × $0.05（多 rerank 候选另计）× 汇率 7
- 默认 sep 仍为 `fal/demucs`；启用：`slots.sep: [fal/sam_audio]`
- 53 项单元测试通过

Releases/06 §2.3／§3.3#5 已同步。

## 对当前项目的影响

正式线仍为 v0.2.8；本能力仅在本地 checkout，直至用户要求提交／发版。

## 未完成与下一步

- 未做真实 SAM API 冒烟或听感验收
- 未 commit／push／Release
