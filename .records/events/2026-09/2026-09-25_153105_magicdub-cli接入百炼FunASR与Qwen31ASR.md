---
record_id: rec_20260925_153105_f2000f
occurred_at: 2026-09-25T15:31:05+08:00
kind: artifact
domain: engineering
certainty: verified
related_artifacts:
  - Releases/06_magicdub-cli系统设计.md
  - Drafts/qwen31-asr-usage-probe/README.md
  - Drafts/qwen31-asr-usage-probe/summary.json
  - Drafts/qwen31-asr-usage-probe/fun_asr_smoke.json
supersedes: null
---

# magicdub-cli 接入百炼 Fun-ASR 与 Qwen Audio 3.1 ASR

## 结果

本地 magicdub-cli（未提交、未发版）新增可选 ASR：

- `bailian/fun-asr`
- `bailian/qwen-audio-3.1-asr-flash-filetrans`

输入经 **fal CDN 公网 HTTPS URL** 提交百炼异步 transcription；**不做**百炼临时上传。凭据：`DASHSCOPE_API_KEY`、可选 `DASHSCOPE_HTTP_BASE_URL`（北京专属）、以及上传用的 `FAL_KEY`。默认 ASR 仍为 `fal/whisper`。

计费（北京人民币公开价）：

- Fun-ASR：`content_duration` 秒（缺则 `usage.duration`）× ¥0.00022／秒
- Qwen 3.1 filetrans：输入／输出 Token × ¥0.8／¥2.7 每百万；`usage` 无 token 时 `cost_cny` 为 null

实测：Qwen 3.1 成功响应含 `input_tokens`／`output_tokens`／`total_tokens`／`duration`；Fun-ASR 冒烟 `content_duration_s=4.48`，`cost_cny≈0.0009856`。单元测试 50 通过。Releases/06 §2.3／§3.3#5 已同步规范。

## 背景与理由

用户确认：传入文件用公网 URL／fal CDN；暂不接百炼上传；单价按北京人民币。

## 证据与成果位置

- 实现：magicdub-cli 工作区 `bailian_asr.py`、两 adapter 目录、registry／asr slot／credentials 模板（相对已发布 v0.2.7 为本地未提交改动）
- 探针：`Drafts/qwen31-asr-usage-probe/`
- 规范：`Releases/06_magicdub-cli系统设计.md`

## 对当前项目的影响

可选 ASR 已可在本地 checkout 启用（`slots.asr`）；正式安装／`update` 仍为 v0.2.7，不含本能力，直至用户要求提交并发版。

## 未完成与下一步

- magicdub-cli 本地改动尚未 git commit／push／Release
- 未做全长 ASR 质量验收；默认路径不变
