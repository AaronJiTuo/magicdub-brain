---
record_id: rec_20260918_202146_fa91c2
occurred_at: 2026-09-18T20:21:46+08:00
kind: finding
domain: engineering
certainty: verified
related_artifacts:
  - Drafts/magicdub-skills/fish-instant-clone-benchmark/README.md
  - https://docs.fish.audio/features/voice-cloning
  - https://docs.fish.audio/developer-guide/models-pricing/choosing-a-model
supersedes: null
---

# 完成 Fish S2.1 Pro 免费入口十二句 Instant clone 实测

## 结果

用户要求复用最近 MagicDub 原声与文本测试 Fish S2.1 Pro，特别验证不足 0.5 秒参考。首次付费入口因 API 余额为零返回 402；用户明确选择同款模型免费开发入口后，`s2.1-pro-free` 的 12 次请求全部返回音频，合计 46.393470 秒，生成和对照 36 份媒体全部通过严格完整解码。

当天三个已完成项目 HC4lPDHT15A、qmMIk13HOLQ、uDCm_OZ_b30 提供原句未补长参考、原文、最终中文译文与已有 IndexTTS 原始配音。0.24 秒「Bye-bye.」、0.28 秒「Right.」、0.38 秒「Never.」参考全部被接口接受，中文输出分别为 0.185760、0.325079、0.882358 秒。最后一项达到原句 2.322 倍；12 句中 10 句处于 0.8～1.2 倍范围。未变速、裁剪、重译、拼接参考或新调用分离／ASR／IndexTTS。

## 证据与成果

实验程序与结论见关联 README。用户 MagicDub 项目根目录下 `experiments/fish-s2.1-pro-free-20260918/` 保存 index.html、report.md、manifest、逐请求结果、原始 HTTP 音频、修正 WAV、validation 和脱敏余额记录；付费 402 在同级 `fish-s2.1-pro-20260918` 保留。

12 份返回 WAV 都使用占位 RIFF/data 长度。仅修正头部两处长度字段，PCM 数据逐字节一致；原始响应保留。36 份音频完整解码通过，源项目参考和 alignment 哈希不变。试听页核验 36 份音频全部加载、短参考过滤为 3 项，连听按钮可启动。

## 费用与边界

免费入口成功文本共 663 UTF-8 字节，本轮费用 ¥0.000000，余额前后均为零；付费价折算为 ¥0.069615，仅作测算。未充值或创建订阅；密钥仅在临时进程使用，未写入成果或配置，进程已退出。

HTTP 成功和非静音不等于克隆相似、情绪复现或正确读全译文，仍待用户试听。免费服务不替代付费可用性／时延保证验证。未改正式模型、安装或任何旧项目；未提交或推送。MVSep DnR v3 Mel+SCNet 与 Qwen Audio 3.0 ASR Flash Filetrans 尚未测试。
