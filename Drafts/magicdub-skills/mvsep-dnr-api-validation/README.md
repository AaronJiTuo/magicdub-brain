# MVSep DnR v3 API 实测

独立验证 DnR v3 · Mel+SCNet 的创建任务、查询、下载与免费账号可用性。复用既有 Steve Jobs 前 60 秒，与此前 Demucs 输入字节一致；不重新运行 ASR、TTS 或基线分离，不修改正式技能。

## 运行

依赖 Python 3、requests 与 FFmpeg。程序目录只保留脚本和结论；音频、请求回执及日志放在用户 MagicDub 项目根目录的 `experiments/mvsep-dnr-v3-mel-scnet-20260918/`。

1. `python probe.py prepare --output <实验目录> --input <原有60秒WAV>`
2. `python probe.py serve --output <实验目录> --port 8768`
3. 打开本机 `/credential` 输入本轮临时 Key；它只存于进程内存，仅发送到官方 MVSep API，不打印或落盘。
4. 本机 POST `/start` 仅启动一次。程序先读取脱敏额度，再提交固定参数；已有 attempt.json 时拒绝重复提交。超时或未知状态保留证据，禁止盲目重投。

参数为 sep_type=56、add_opt1=2、add_opt2=0、add_opt3=0、output_format=1、is_demo=0。选择标准三轨 WAV PCM16 输出；不启用 Premium、不购买积分、不发布到演示页。查询和下载可重试；创建不自动重试。

原音频为 60 秒、44.1 kHz 双声道 float WAV，SHA-256 为 `c4b455548c987c60804d50852e42aeab6f84f4def2004aee41703dba23303759`。观察窗口：8.2–12.6 秒讲话、16–31 秒笑话与观众反应、26.8–28.2 秒候选观众反应。后者不是经标注的纯笑声真值，不能单凭能量判断笑声质量。

官方依据：[API](https://mvsep.com/en/full_api)、[套餐](https://mvsep.com/en/plans)。HTTP 成功及完整解码只证明接口和媒体可用，听感仍由试听判断。

## 当前结果

2026-09-18 已真实跑通一次免费 API 任务：约 115 秒查到完成、三轨下载通过、免费次数 45 → 44、Credits 前后均为 0。20 份媒体完整解码通过，用户已试听并明确认为 MVSep 比 Demucs 强很多；全长表现尚待验证。详见 [RESULTS.md](RESULTS.md)。

完成回执保存后，`python download.py <实验目录>` 只下载既有三轨，不重新提交。`python review.py <实验目录> <原Demucs实验目录>` 依赖 numpy 和 FFmpeg，生成相同增益的试听与验证报告。执行 `python serve.py <实验目录> --port 8769` 打开支持 HTTP Range 跳转、仅监听 `127.0.0.1` 的 index.html；临时凭据服务完成后应关闭。
