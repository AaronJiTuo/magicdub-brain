---
record_id: rec_20260913_035626_5c50a3
occurred_at: 2026-09-13T03:56:26+08:00
kind: milestone
domain: engineering
certainty: verified
related_artifacts:
  - https://github.com/shishengkai/magicdub-skills/tree/61f1778fd41e1f14579f88bb94ad9a765a22a1e5
  - https://github.com/shishengkai/magicdub-skills/blob/61f1778fd41e1f14579f88bb94ad9a765a22a1e5/docs/acceptance.md
supersedes: null
---

# 完成 magicdub-skills 首版实现、验收与 GitHub 安装升级

## 结果

- 用户授权实施、验收、README、commit / push，并以本机 Codex 能使用 GitHub 版本为交付目标。已在独立私有代码仓库实现 MIT / Python 3.12+ / uv / FFmpeg 程序，包含 magicdub、magicdub-setup、magicdub-upgrader；不依赖旧引擎，不做口型修正。
- 代码提交 d6869f7（0.1.0）及 61f1778（0.1.1）已推送。正式安装重新获取 GitHub 精确快照；实际执行 0.1.0 → 0.1.1 升级，凭据和配置校验值不变、旧快照保留。Codex app-server skills/list 实际返回三个 enabled=true 的 user skill，均指向 61f1778 快照。新入口处理旧项目时仍回到原 0.1.0 程序。
- 默认全局目录为用户 home 下的 .magicdub，视频项目独立位于 macOS 用户 Movies/MagicDub；skills 注册在 .agents/skills。安装使用普通 wheel，修复本机隐藏 .pth 被 Python 忽略的问题。

## 验收证据

- 18 项自动测试及 Ruff 通过；覆盖费用去重与失败、HTTP 202 队列恢复、提交结果未知禁止重提、翻译修订、路径边界、安装中断、版本固定和 Star 账号隔离。
- Steve Jobs 开头 90 秒：Demucs / Whisper diarization / 当前 Codex 翻译 / IndexTTS 2，21 句，回转写内容覆盖，画面哈希与原件副本一致，最大对齐误差 24.082ms。移动项目后请求数仍为 24；单句修订只新增 1 次对应 TTS 请求，旧成片哈希不变。
- GitHub 安装版完成 32 秒双人交替剪辑，识别两个主要说话人、5 句独立原声参考；画面一致，最大时长误差 18.367ms，回转写覆盖内容。已知 220/330Hz 背景信号在混音后保留。该素材不是自然对话，原生 s0001 跨剪辑说话人边界，未擅改已确认的原生分句算法。
- SAM Audio 实际分离通过；Fun-ASR 当前账号返回 Model.AccessDenied / HTTP 403，拒绝响应恢复后不重复提交。未把模拟测试当作该模型真实验收。
- 本轮开发验收共 35 次尝试，已知费用估算累计 ¥2.43：Steve Jobs 含单句修订约 ¥1.47、双人含回转写约 ¥0.59、候选分离约 ¥0.37。1 次 Fun-ASR 拒绝金额未知；失败尝试未删除。fal 账单权限不足，金额不是精确实账；宿主 Codex 未计量。

## 成果与后续

代码仓库 README、docs/parameters.md、docs/project-format.md 和 docs/acceptance.md 为实现交接入口。本机视频目录的 acceptance_stevejobs_90s、acceptance_two_speakers 项目保存请求、费用、QC 与成片；开发 checkout 的忽略目录 acceptance-local 保存安装、恢复与候选验证证据，不作为安装依赖。密钥和媒体未提交，未执行 Star 写入。

技术交付可用，不宣称新样片已获用户主观音色验收。Fun-ASR 权限、自然多人 / 重叠说话、中文→英文、完整长素材及 Windows / WSL / Linux 仍待独立验证。质量标记按用户要求继续导出。Release 05 的旧双币种表述仍是已知漂移，实际统一按 USD×7 计人民币；本次未改写 Release。
