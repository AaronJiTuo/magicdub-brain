---
record_id: rec_20260918_223401_f96f70
occurred_at: 2026-09-18T22:34:01+08:00
kind: finding
domain: engineering
certainty: verified
related_artifacts:
  - Drafts/magicdub-skills/mvsep-dnr-api-validation/README.md
  - Drafts/magicdub-skills/mvsep-dnr-api-validation/RESULTS.md
supersedes: null
---

# MVSep DnR v3 Mel+SCNet 免费 API 实测通过

## 结果

用此前 Demucs／SAM 对比中的 Steve Jobs 前 60 秒原音，实际调用香港 MVSep API 一次。固定 DnR v3、Mel+SCNet、直接从混音提取、标准三轨 PCM16 WAV，不发布演示。创建 HTTP 200，21.13 秒收到回执，约 114.61 秒首次查到完成；三轨并行下载约 5.87 秒。原始输出都是 60 秒、44.1 kHz 双声道。

登录主页免费次数 45/50 → 44/50，API Credits 前后均为 0，没有充值，本轮现金支出 ¥0.000000。用户自行创建 Key；测试仅在内存使用，临时进程已退出，不保存密钥。

## 证据与成果

[程序说明](../../../Drafts/magicdub-skills/mvsep-dnr-api-validation/README.md)和[详细结果](../../../Drafts/magicdub-skills/mvsep-dnr-api-validation/RESULTS.md)。媒体与脱敏 API 回执位于用户 MagicDub 根目录的 `experiments/mvsep-dnr-v3-mel-scnet-20260918/`。20 份媒体完整解码通过；单播放器试听页已验证播放、短窗跳转、自动暂停和混音切换。

## 观察与边界

26.8–28.2 秒候选观众反应窗中，MVSep Music+SFX 相对原声 RMS 为 -0.63 dB，Demucs 背景为 -16.45 dB。讲话窗中 MVSep 背景能量也更高，不能单凭能量判定笑声完整、讲话残留更少或整体更优，仍待用户试听。此次只证明单个免费任务的接口与媒体可用性，不代表生产稳定性、付费并发或全长验收。

未改动正式 skill、默认分离器、配置、已有视频或 Git；Qwen Audio 3.0 ASR Flash Filetrans 尚待单独测试。
