---
record_id: rec_20260919_024023_16bf33
occurred_at: 2026-09-19T02:40:23+08:00
kind: state_change
domain: engineering
certainty: verified
related_artifacts:
  - https://github.com/shishengkai/magicdub-skills
  - Drafts/magicdub-skills/openrouter-fish-validation/RESULTS.md
  - Drafts/magicdub-skills/openrouter-fish-validation/README.md
supersedes: null
---

# OpenRouter Fish 两个入口已接入 MagicDub 本地模型选项

## 结果与适用范围

用户要求将两个 OpenRouter Fish 入口补充为 skills 的 TTS 选项。基于正式 v0.6.0 提交 7804adbaf6305c5bd0d9c4183dc82219d7e4ae81，新增 `openrouter-fish-s2.1-pro-free` 与 `openrouter-fish-s2.1-pro`；分别固定到 `fish-audio/s2.1-pro-free:free`、`fish-audio/s2.1-pro`，使用独立 OPENROUTER_API_KEY。新视频选择、setup、CLI、自检、费用、项目格式及说明已同步，TTS 共五个选项。

当前 MagicDub 逐句使用一份原声、ASR 原文及译文，故 OpenRouter 的单参考限制不阻断该流程；多说话人由各句自己的参考处理。直接 WAV 的限制通过接收 PCM16LE 后无损封装解决，再进入现有时长 QA、局部重译、对齐、混音与 SRT。短参考不补长，不创建音色 ID，不上传 fal；不透传尚未验证的高级参数，不保证与官方生成的音色、情绪或中文口音一致。

## 验证与恢复

- 318 项完整回归通过（312.37 秒），93 项专项通过（279.66 秒）；Ruff、差异格式与 53 个分发文件摘要通过，仅既有百炼 SDK 弃用提示。
- 两模型均通过受控响应加真实 FFmpeg 的 QA 改写、正常句缓存、成片／字幕／费用与继续项目流程；0.24 秒参考原样传输、缺 Key 提前拦截、入口隔离、未知提交不重发、明确失败三次上限及本地恢复均验证。
- 上轮 Free／Pro 两份真实 PCM 响应经新适配器回放，与此前试听 WAV 逐字节一致；删除输出后不新增请求即可恢复，原件摘要不变。本轮新增 API 调用及费用为 0，不把回放记作新远端验收。
- 实际 scripts/magicdub.py 列出五种 TTS，setup／create 可选两个新键；在隔离目录分别创建项目并冻结准确参数。22 个安装模块与源码相同，日常安装和已有视频未改动。

证据在代码仓库忽略目录 `acceptance-local/openrouter-tts-integration/`：validation.json、cli-validation.json、manifest-validation.json、pytest-full.txt；可分发说明见代码仓库 docs/acceptance.md 与 docs/parameters.md。凭据值和 Base64 参考不落入请求记录，成功费用按公开 UTF-8 字节价估算；失败或未知请求仍保留待核实状态。

## 交付边界

本轮仅完成本地源码与文档，未提交、推送、发布或升级日常安装。版本号保持 0.6.0，候选分发清单更新不改变正式不可变 Release；使用新选项须采用本地 checkout 的 skill 和程序入口。默认 IndexTTS、官方 Fish 入口、既有项目模型与运行快照保持原状。全长实际调用、并发、中文发音和音色／情绪效果仍待用户实测。Releases/05 尚未同步这些可选入口。
