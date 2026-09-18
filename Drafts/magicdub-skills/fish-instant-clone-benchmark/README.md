# Fish S2.1 Pro Instant clone 实测

复用 2026-09-18 已完成的 MagicDub 原声、原文、最终译文及 IndexTTS 原始配音，独立生成 Fish 试听样本。包含 0.24、0.28、0.38 秒未补长参考；不创建 voice ID，不修改原项目或正式模型配置。

## 运行

依赖 Python、httpx、msgpack、numpy、soundfile、FFmpeg。可使用已安装的 MagicDub Python 环境。

`python benchmark.py prepare --output <独立实验目录> --model s2.1-pro-free`

`python benchmark.py serve --output <同一实验目录> --port 8766`

从本机浏览器访问 `http://127.0.0.1:8766/credential`，临时密钥仅进入进程内存。用本机 POST `/start` 启动固定的 12 句实验；真实计费请求，已有 result.json 不重复提交，提交未知时停止，不自动重试。服务仅监听 loopback，任务完成后清除内存密钥。

预期结果：每句保留原声、IndexTTS 原始配音、Fish 原始配音和时长／完整解码检查。HTTP 成功不代表音色、情绪、正确朗读或人工验收通过。原始输出不变速、不裁剪、不添加情绪标签。

生成完成后执行 `python finalize.py <实验目录>`，保留 API 原始 WAV 响应，仅修正流式文件头的长度占位值；程序断言 PCM 载荷逐字节一致，并完整解码。执行 `python render.py <实验目录>` 生成离线试听页面和 summary.json。生成服务完成后应终止；如需浏览器试听，改用仅监听本机的静态 HTTP 服务。

## 2026-09-18 实测结果

用户选择免费开发入口后，12 / 12 次 Instant clone 请求成功，合计 46.393470 秒。包含未补长的 0.24、0.28、0.38 秒参考，分别得到 0.185760、0.325079、0.882358 秒的中文配音。参考长度不是接口阻塞，但 0.38 秒「Never.」→「不会。」生成时长为原句 2.322 倍；12 句中 10 句处于 0.8～1.2 倍范围，未执行时长修正或重生成。

12 份响应均使用占位 WAV 长度头，按上述方法修正后，36 份试听媒体全部通过严格完整解码；原项目参考和 alignment 哈希未改变。页面已核验 36 份音频均加载、短参考过滤为 3 句、连续播放可启动。

实验成果位于用户 MagicDub 项目根目录下 `experiments/fish-s2.1-pro-free-20260918/`，包括 index.html、report.md、manifest.json、summary.json、validation.json、samples/ 和脱敏余额记录。此前付费入口 1 次 402 失败保存在 `experiments/fish-s2.1-pro-20260918/`；未重复提交或充值。

本批目标文本 663 UTF-8 字节，免费入口费用 ¥0.000000，余额前后均为零；按付费价折算 ¥0.069615，不能作为实际扣费。音色、情绪、正确朗读仍待用户试听，尚未接入正式 MagicDub 或替换默认模型。密钥没有写入实验、brain 或配置，临时进程已退出。

官方依据：[Instant clone](https://docs.fish.audio/features/voice-cloning)、[TTS API](https://docs.fish.audio/api-reference/endpoint/openapi-v1/text-to-speech)、[同模型免费入口说明](https://docs.fish.audio/developer-guide/models-pricing/choosing-a-model)、[价格](https://docs.fish.audio/developer-guide/models-pricing/pricing-and-rate-limits)。

## 用户试听反馈与同权重说明（2026-09-18 20:57）

用户已试听并反馈：本批 Fish 中文带明显英语发音习惯，听起来像刚学中文不久的外国人；已有 IndexTTS 中文发音更接近中文母语者。此前“待用户试听”现已有这项明确反馈；尚未获得逐句音色、情绪和读全文本的完整评分。结论限定当前英文参考 → 中文 Instant clone 批次，未推及 Fish 全部场景。

[Fish 官方推理技术文章](https://fish.audio/blog/tts-inference-optimization-s2-pro-free/)明确声明免费版与付费版使用相同模型权重；免费入口不应被视为音质降级模型。尚未独立审计服务端权重与每个请求实际配置，也没有成功付费输出的对照，不能保证每次随机生成逐字节相同，不能承诺充值可改善中文口音。

英文参考的口音特征迁移只是待验证解释；本批包含 5.72～13.88 秒参考，不能未经逐句定位就把整体反馈归咎于不足 0.5 秒。当前保留 IndexTTS 基线，尚未替换。此次未新增 API 请求。
