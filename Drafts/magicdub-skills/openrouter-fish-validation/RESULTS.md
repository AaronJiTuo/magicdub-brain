# OpenRouter Fish S2.1 Pro API 实测结果

日期：2026-09-19。测试对象为 `fish-audio/s2.1-pro` 与 `fish-audio/s2.1-pro-free:free`，均通过 OpenRouter 的 `/api/v1/audio/speech` 调用。

## 结论

两个入口均跑通 MagicDub 的核心流程：原句参考音频＋ASR 原文＋中文译文，一次请求直接生成配音，不注册或删除音色。但 OpenRouter 当前接口不能作为 Fish 官方 API 的完整等价替代：标准入口限制单份参考、直接输出格式仅 MP3／PCM，部分官方高级参数的效果和校验不能确认等价。

本轮共 30 次真实请求，每个模型 15 次；24 次生成成功并通过完整解码，另 6 次为预设的边界测试，均返回 400。未自动重试、未替换模型。12 次基础克隆全部成功，另有 12 次参数／格式实验成功返回音频。HTTP 成功不等于音色、发音、情绪或完整文本已人工验收。

## 功能对照

| 能力 | Fish 官方 | OpenRouter 免费／付费实测 | 判断 |
| --- | --- | --- | --- |
| 单份原声＋原文，即时克隆 | `references`，MessagePack 内嵌音频字节 | `input_references`，JSON 内嵌 Base64 音频及原文；各 6/6 成功 | 核心调用流程可替代 |
| 0.24／0.28／0.38 秒未补长参考 | 前一日官方免费入口已全部生成 | 两个模型均全部生成 | 不构成本批接口阻塞；不保证短参考质量 |
| MP3 输出 | 支持 | 44.1 kHz、单声道，全部解码通过 | 已验证 |
| 无损 PCM 输出及 HTTP 分块传输 | 支持 | 两个模型都返回 PCM16，响应明确标注 44.1 kHz、单声道；本地 WAV 封装的 PCM 字节完全一致 | 已验证；不等于双向实时 WebSocket |
| WAV 直接输出 | 支持 | `response_format=wav` 均返回 400；改在 `provider.options.fish-audio.format` 指定 WAV 仍返回 MP3 | 不等价；可接收 PCM 后本地封装 |
| 一次多份参考音频 | 官方 `references` 支持多项，亦有多说话人结构 | `input_references` 加入第二份音频即返回 400，明确限制一份音频＋一份原文 | 标准接口不等价；多说话人未验收 |
| 语速 | 官方 `prosody.speed` | 顶层 `speed=1.5` 请求成功，两条输出均明显缩短 | 有正向证据，未证明精确比例或官方参数映射 |
| MP3 码率 | 官方 `mp3_bitrate` | 经 provider options 设 64，ffprobe 确认 128 kbps → 64 kbps | 两个模型均验证生效 |
| 指定采样率 | 官方 API 暴露 `sample_rate` | provider options 请求 24000，两个模型仍输出 44100 Hz | 本次未实现所请求的采样率；未定位责任在转接层还是上游 |
| temperature／top_p／latency／volume 等 | 官方 API 有相应字段 | 正常组合参数被接受；额外传 `temperature=2`（超出官方文档 0～1）仍生成 | 不能由 HTTP 200 推断逐项完整透传；可能忽略、覆盖或其他处理，未确定 |
| 情绪标签 | 模型支持文本表达控制 | 两个入口加入 `[whispering]` 均返回可解码音频 | 仅确认生成，语气是否遵循及是否读出标签待试听 |
| 音色管理、私有 voice ID、字典管理、双向实时流 | 官方平台有对应能力 | 本轮未做创建／修改或 WebSocket 调用 | 未验证，不能算已兼容 |

另将参考音频替换为无效字节，两个模型均被上游返回 400；结合正常参考生成与端点元数据 `supports_voice_cloning=true`，支持参考音频实际参与了接口处理。它仍不能代替对音色相似度的人工判断。

## 六组基础试听

每组提供：英文原声、此前 IndexTTS、此前官方 Fish Free、本次 OpenRouter Free、本次 OpenRouter Pro。原项目未写入；18 份旧音频复制前后字节一致，连同 24 份新音频共 42 份试听媒体全部通过 FFmpeg 严格完整解码。

| 原声／中文译文 | 参考秒数 | OpenRouter Free 输出秒数 | OpenRouter Pro 输出秒数 |
| --- | ---: | ---: | ---: |
| If you go to China…／如果你去一趟中国，你看待这个世界的方式，就再也不会和从前一样了。 | 5.84 | 6.008 | 6.661 |
| Having just returned…／我刚刚从自己的祖国新西兰回来。过去这整整十年，各种东西竟然都涨得这么贵，真让我大吃一惊。 | 8.06 | 9.535 | 8.986 |
| I think china…／我认为中国已经赢得了对美科技竞赛，把欧洲远远甩在身后。 | 5.72 | 5.486 | 5.721 |
| Never.／不会。 | 0.38 | 0.993 | 0.888 |
| Bye-bye.／拜。 | 0.24 | 0.287 | 0.287 |
| Right.／对。 | 0.28 | 0.444 | 0.392 |

MP3 时长可能包含编码填充，不等于纯语音有效时长。尤其“不会。”明显长于原句，仍需 MagicDub 时长 QA；短参考可调用不等于自动对齐。

原始结果没有裁剪、变速或重生成。旧官方输出是 WAV，本次基础输出为 MP3，且生成时间与参数不同，因此这些试听适合评估实用效果，不能作为严格同配置音质排名。不能承诺换到 OpenRouter 会改善此前听到的中文英语口音，也不能承诺付费版音质优于免费版。

六条基础请求的单次端到端耗时中位数：Free 5.976 秒、Pro 3.606 秒；首批音频字节中位数：Free 4.229 秒、Pro 2.959 秒。计时包含本机网络与服务处理，仅为本次小样本，不能代替并发或服务等级测试。顶层 1.5 倍速补测输出为 Free 4.624 秒、Pro 4.545 秒；采样随机性和编码填充使其不能直接证明精确倍率。

## 费用与可追溯性

付费成功请求目标文本共 919 UTF-8 字节，按公开 $15／百万字节计算为 **$0.013785，按项目固定 ×7 折算 ¥0.096495**；免费入口公开标价为 0。Key 累计用量从 0 增至 **$0.013785**，与全部付费成功请求的字节估价一致；初次终态查询尚为 $0.012345，延迟核对后最后一笔已体现。最后一条免费请求前后用量未变。证据为实验目录 `usage-before.json`、`usage-before-format-*.json`、`usage-after.json` 与 `usage-after-settled.json`。这是平台 API 用量核对，不是充值手续费或银行账单核对。

每份响应保存 `X-Generation-Id`、状态、格式、字节数、首字节时间、总耗时及音频哈希。本批即时查询 `/generation` 均返回 404，因此没有逐请求账单详情；账号 Key 累计用量是另外的对账证据，不能伪装为逐笔账单。

实验目录位于 MagicDub 项目根目录 `experiments/openrouter-fish-20260919/`，含 `index.html`、`report.md`、`summary.json`、`validation.json`、`requests/`、`baseline/`、公开文档快照及脱敏用量记录。API Key 仅经本机表单进入测试进程内存，没有写入代码、配置或实验文件。

## 接入含义

若后续希望用 OpenRouter 统一管理 TTS，可以为“单句单参考 Instant clone”单独做适配；需要把官方的 MessagePack 请求改成 OpenRouter JSON，把 WAV 输出改成 PCM 后封装，并为确实验证过的参数建立映射。不能只替换 base URL 和模型名就宣称兼容。

本次只完成独立实测，没有修改 magicdub-skills 或默认 TTS，没有启动新的全长译制。

## 官方资料

- [OpenRouter TTS 与单份参考克隆说明](https://openrouter.ai/docs/guides/overview/multimodal/tts)
- [OpenRouter Speech API schema](https://openrouter.ai/docs/api/api-reference/tts/create-speech)
- [OpenRouter 付费模型](https://openrouter.ai/fish-audio/s2.1-pro)与[免费模型](https://openrouter.ai/fish-audio/s2.1-pro-free:free)
- [付费端点元数据](https://openrouter.ai/api/v1/models/fish-audio/s2.1-pro/endpoints)与[免费端点元数据](https://openrouter.ai/api/v1/models/fish-audio/s2.1-pro-free:free/endpoints)
- [Fish 官方 TTS 参数](https://docs.fish.audio/api-reference/endpoint/openapi-v1/text-to-speech)与[单份／多份 Instant clone](https://docs.fish.audio/features/voice-cloning)
- [Fish 免费与付费模型定位](https://docs.fish.audio/developer-guide/models-pricing/choosing-a-model)：官方称同一模型，免费版无相同 TTFA／DPA 保证；本轮未审计服务端权重或内部配置。
