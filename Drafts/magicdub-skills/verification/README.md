# MagicDub 独立 API 译制验证

独立于旧引擎的 Python 3.12 原型，先用用户指定素材的短片段验证真实 API 链路。首轮 90 秒样片已通过技术与回转写内容检查，主观试听待评估；不是已安装的 Codex skill。

2026-09-13 根据用户指定的 `test_by_step` 最终程序完成了 Demucs `htdemucs_ft`、Wizper v3、IndexTTS 2 和旧 FFmpeg 参数的对照验证，见 [调参恢复报告](RECOVERED_PARAMETERS.md)。这轮原程序快照和样片保留在对应运行目录。

随后按用户要求，当前 `recover.py` 改用 **Whisper 并开启说话人分离**，其余媒体参数保留；费用记录与汇总统一以 **人民币**计算，美元固定乘以 7，显示 `¥1.23`。见 [Whisper 与人民币计费验证](WHISPER_CNY_VERIFICATION.md)。Whisper 新参数必须在 [whisper_parameters.json](whisper_parameters.json) 中由用户确定，未确定时不会提交 ASR。翻译仍由 Codex 按旧提示词及每秒 4.5 字约束完成。

## 运行

在此目录运行 `uv sync --python 3.12`。凭据从进程环境或 `--credentials` 指定的本地 env 文件读取，不进入项目 JSON。后续命令参数见 `uv run python verify.py --help`。

顺序为 `init → separate / asr → agent 写 translations.json → tts → export → qc → billing`。ASR 可用 `--asr-input source/audio.wav` 先处理原音频，也可在分离后转写人声；实际输入写入项目。模型选择必须由使用者确定；当前验证仅实现 fal Whisper / Demucs / SAM Audio 和 IndexTTS 2 适配代码，是否实测通过以结果报告为准。翻译由当前 agent 读写项目文件完成，不调用额外 LLM API。

项目保存在忽略的 `runs/` 中，复制完整输入素材，同时记录片段偏移、时间轴、说话人、各次 API 请求、失败与费用。远端任务提交一次后保存 request ID；续跑只查询已有请求。提交结果不明时不会盲目重复付费 POST。技术失败保留现场，质量问题以标记和强制对齐继续。

## 预期验证

实际生成可解码的中文配音视频；每句配音完整变速到原时间窗口，环境音与配音混回，原始视频画面保留。费用按每个请求对账，未得到账单的项目不记为零，宿主 agent 费用另注明无法归集。单个演讲样本不能证明多人、音乐、跨平台或长片的质量。

## 首轮进度

见 [stevejobs 90 秒验证报告](RESULT_stevejobs_90s.md)。本地已验证四种强制时长比例（0.2、0.6、1.5、3.2 秒目标）达到准确样本数，已完成请求复用和 POST 结果不明时不重提。报告区分真实 API 成功、尚未执行的阶段与费用估算。

## 本轮采用的旧项目参数

用户要求先核对既有 `magicdub` 参数，随后明确选择 SAM Audio。读取的旧仓库提交为 `2eb7f2404a752f8f5a8187ccefe63f596b26fb27`，未写入旧仓库。

- SAM Audio：`prompt=speech`、`predict_spans=false`、`reranking_candidates=1`、`acceleration=balanced`、`max_chunk_duration=60`、`chunk_overlap=5`、`output_format=mp3`。
- IndexTTS 2：每句原声片段同时传入 `audio_url` 与 `emotional_audio_url`，`prompt` 为本句译文。
- 背景由原音减去 `0.98 × 分离人声` 得到；保留服务端 residual 供对比。
- ASR 保留用户先前已选择并完成的 Whisper，不替换为旧项目当前的 Fun-ASR 或历史 Wizper。
- 最终复验严格使用旧项目的 16 kHz 单声道人声分离输入和逐句声音参考；合成阶段使用 48 kHz。初次 48 kHz 双声道 SAM 调用返回近乎静音的人声，旧失败样片、信号检查和费用均保留。

当前同一项目内按 `--stage` 与 `--tts-revision` 保存独立尝试。质量标记不阻断导出；新参考需新 revision，避免错误复用旧声音。

费用对账可选从本地 `FAL_BILLING_KEY` 读取 Admin key，未配置时使用 `FAL_KEY`。403 时保持估算 / 待对账状态，不要求用户在聊天中提供密钥，也不把失败金额当零。
