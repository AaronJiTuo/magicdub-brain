---
record_id: rec_20260925_133157_ff3055
occurred_at: 2026-09-25T13:31:56+08:00
kind: artifact
domain: engineering
certainty: verified
related_artifacts:
  - https://github.com/shishengkai/magicdub-cli
supersedes: null
---

# magicdub-cli 新增 mvsep/dnr-v3 sep adapter

## 结果

本地 `magicdub-cli` 已实现 `mvsep/dnr-v3`（目录 `adapters/sep/mvsep_dnr_v3/`），并完成 registry、sep slot 双凭据、`MVSEP_API_KEY` 默认凭据键与单测接线。39 项回归通过。尚未 commit／push／发版；默认 `slots.sep` 仍为 `fal/demucs`。

## 背景与理由

用户要求 apex `https://mvsep.com/api/separation/create`（不用 de2）、DnR v3 Mel+SCNet、直接提取、含独立模型结果、PCM16 WAV；输入经 fal CDN URL + `remote_type=direct`；输出 speech 保留，music+sfx 合成 `non_speech`。

固定参数：`sep_type=56`，`add_opt1=2`，`add_opt2=0`，`add_opt3=1`，`output_format=1`。API 轨类型实测为 `speech`／`music`／`sfx`（文档称 effects）。

## 证据与成果位置

- 代码仓 `magicdub-cli` 工作区未提交变更：`adapters/sep/mvsep_dnr_v3/`、`registry`、`steps/slots/sep.py`、`config.py` 凭据默认、`tests/test_mvsep_dnr_v3.py`
- 本机 `~/.magicdub/cli/credentials` 已有 `MVSEP_API_KEY`（未入库）
- 单测：helpers 与 registry 覆盖；未跑真实分离请求

## 对当前项目的影响

- 使用方式：`config.yaml` 设 `slots.sep: [mvsep/dnr-v3]`（或放在 `fal/demucs` 之前作首选）；需 `MVSEP_API_KEY` 与 `FAL_KEY`
- Releases/06 默认 sep 表仍只列 `fal/demucs`，与本地可选 adapter 存在漂移
- 与 skills 线差异：skills 用 de2 + 文件上传 + `add_opt3=0`；cli 本 adapter 用 apex + fal URL + `add_opt3=1`

## 未完成与下一步

- 用户授权后再 commit／push；发版另需明确授权
- 可选：真实样片端到端试跑；更新 Releases/06 的 sep adapter 表
