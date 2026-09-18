# 百炼临时上传与 Fun-ASR 可用性验证

**最新状态（2026-09-18）：分阶段上传已在 magicdub-skills 本地实现，新程序自动完成百炼上传与 Fun-ASR 识别，真实链路通过。** 新过滤参数被接口接受；双人样片仍有说话人过分割。尚未发布或替换日常安装。原首轮 403 和第二轮独立上传证据保留，集成结果见文末第三轮。

独立验证程序，不修改正式 skill、默认配置或源媒体项目。

使用已有短音频，获取 `fun-asr` 上传凭证、上传至百炼临时存储，随后复用指定 MagicDub runtime 的 `pipeline.transcribe` 与 `fun_asr.transcribe`，验证真实提交、查询、下载和规范化转写。测试禁用 fal 上传；最多提交一个识别任务，结果未知或明确失败均不自动新增任务。

运行方法（使用 magicdub-skills 已有 Python 环境）：

```sh
python validate.py --runtime /path/to/magicdub-skills --source /path/to/vocals.wav
```

明确开始新一轮验证时追加 `--run-id RUN_NAME`。每轮使用独立私密数据目录和 `runs/RUN_NAME/` 脱敏结果目录；不能把已有任务编号切换到另一个 Base URL。没有新授权时只续查原轮次。

输入必须是 16 kHz、单声道、PCM16 WAV，最长 60 秒。凭据仅从当前 MagicDub 配置加载，不写入本目录。上传策略和临时签名仅存在内存；音频、临时媒体地址和模型原始响应留在忽略的 `private/`，权限限制为本机用户。公开证据去除临时地址。

预期结果：上传 HTTP 200、模型任务及文件均 SUCCEEDED、非空规范化文本、有效毫秒时间戳、说话人标签，并保留费用估算依据。

## 2026-09-18 实测结果

**百炼上传成功；当前 Key 调用 Fun-ASR 被拒绝，识别链路未通过。**

| 检查项 | 实测 |
| --- | --- |
| 音频 | 既有 `acceptance_two_speakers` 的 Demucs 人声，32.000 秒，1,024,078 字节 |
| 格式与完整解码 | 16 kHz、单声道、PCM16 WAV；`ffmpeg -xerror` 通过 |
| 上传凭证 | `GET /uploads?action=getPolicy&model=fun-asr` 返回 HTTP 200 |
| 文件上传 | 百炼返回的北京 OSS host 接受上传，HTTP 200，上传约 0.242 秒 |
| ASR 提交 | HTTP 403，`Model.AccessDenied`，`Model access denied.` |
| 任务与结果 | 无 task_id、无转写结果、无 usage，未进入轮询 |
| 请求次数 | 1 次上传凭证获取、1 次音频上传、1 次 ASR 提交；没有自动重提 |
| fal | 未调用 |
| 费用 | 官方临时存储免费；识别尝试账本保留 pending，未取得账单或实际扣费信息，不宣称零扣费 |

本次复用 MagicDub v0.5.1 的正式 ASR 实现（commit `86cba45d7bc07520a0571adf90ef8fe5927b8de8`），只在独立测试项目填入百炼上传所得媒体地址。提交参数为 `model=fun-asr`、`diarization_enabled=true`、`language_hints=["en"]`；请求带 `X-DashScope-Async: enable` 和 `X-DashScope-OssResourceResolve: enable`。没有切换模型、地址或凭据，也未改动正式代码。

当前兼容地址 `https://dashscope.aliyuncs.com/api/v1` 仍受官方 HTTP 文档支持。官方[错误码说明](https://help.aliyun.com/zh/model-studio/error-code)将 `Model.AccessDenied` 定义为无权调用对应模型；子业务空间需要模型调用授权。尚未进入账号控制台核实 Key 所属空间及具体缺失授权，不能把该分支原因视为已证实。

公开证据在 `summary.json`；原始响应及临时地址保存在忽略的 `private/`。排障请求编号为 `60824859-79f2-9c21-9ac7-63520b70db4e`。源音频 SHA-256 为 `df6d7f72173914e90757d66c4185ebcaca2eff432b7ec6217737f60e8465366e`，运行前后相同。

本轮当时需先解决 Key 的 Fun-ASR 调用权限。直接重复运行原轮次会复用拒绝响应，不会重新提交；不能用它判断权限是否已经修复。新 Key 与域名的验证见下一节。

## 第二轮：新 Key 与业务空间专属域名

用户已在本机凭据文件更新 Key，并提供北京业务空间专属域名。配置变更仅发生在本机 MagicDub 配置：`credentials.env` 增加 `DASHSCOPE_HTTP_BASE_URL`，并通过既有配置能力同步 `config.json` 的 `dashscope_base`；当前 v0.5.1 只消费后者，env 变量不能单独改变业务地址。没有更改默认模型或业务源码。

验证轮次 `workspace-base-updated-key` 使用相同音频 SHA-256，按原参数只提交一次识别；上传、提交、查询均使用同一北京业务空间专属 Base URL，未调用 fal。无需使用 OpenAI 兼容接口。

| 检查项 | 第二轮实测 |
| --- | --- |
| 上传凭证、文件上传 | 均 HTTP 200，上传约 0.142 秒 |
| 识别任务和文件子任务 | 均 SUCCEEDED |
| 提交到结果解析耗时 | 约 5.405 秒（包含轮询等待，不是纯推理耗时） |
| 本地结果 | 7 句，373 字符；毫秒时间有效，7 句均包含 speaker_id |
| 说话人 | 0、1、2 共 3 个标签；已知双人拼接样片存在过分割，孤立的 “dots.” 被标成 speaker 2，需要试听确认 |
| 原始媒体 / 有效语音 / usage | 32,000 ms / 21,120 ms / duration=21 |
| 费用估算 | 按官方北京原价 0.00022 元/秒乘返回 usage 21 秒，估算 ¥0.004620；实际账单、免费额度未对账 |

第二轮证据：`runs/workspace-base-updated-key/summary.json`、`transcript.json`、`assessment.json`。任务 ID：`7d8df730-4b80-4a6c-a5b9-67f68b2da09f`。原始响应及临时地址仍只在忽略的 `private/`。

官方[域名对比](https://help.aliyun.com/zh/model-studio/regions)推荐专属域名，说明并发承载、网络隔离、3600 秒服务端超时等优势；模型 RPM/TPM 配额仍按主账号合并，不能推导为模型限额增加或独享推理资源。长超时对异步文件识别的直接收益有限。Key 和 Base URL 同时变化，不能据此断言旧 403 单独由域名引起。

当前主程序还有一项已确认限制：费用估算仅匹配公共北京地址，使用专属域名时即便成功也保留 `pending`。本轮在 `assessment.json` 单独记录人工核对的估算，不改写原始账本、不改业务代码。正式 skill 的默认上传仍为 fal；本测试独立完成百炼上传后向正式 ASR 分支传入 `oss://`，不等于已交付自动按步骤选择上传服务的改造。

本轮通过的是上传、识别、结果下载与解析；未跑翻译、TTS、成片，也不代表自然多人对话识别质量通过。[官方价格](https://help.aliyun.com/zh/model-studio/fun-asr)、[有效语音计量说明](https://help.aliyun.com/zh/model-studio/fun-asr-recorded-speech-recognition-http-api)。

官方依据：[临时上传](https://help.aliyun.com/zh/model-studio/get-temporary-file-url/)、[Fun-ASR HTTP API](https://help.aliyun.com/zh/model-studio/fun-asr-recorded-speech-recognition-http-api)。

## 第三轮：正式代码的自动上传链路与新参数

新增 `validate_integrated.py` 直接使用当前源码的音频处理、按步骤上传、Fun-ASR 提交／查询及 pipeline 转写解析，不预先手动上传，也不填入外部媒体 URL。用同一 32 秒人声建立独立测试项目，启用 audio_policy 生成 ASR 专用副本；不会修改原素材项目。

```sh
python validate_integrated.py --runtime /path/to/magicdub-skills --source /path/to/two-speakers-vocals.wav
```

固定轮次为 `integrated-routing`，输入不超过 60 秒。保存任务后继续运行只恢复既有任务，明确失败不自动新建任务；结果已通过时直接返回。源音频、原始响应和临时 URL 在忽略的 `private/integrated-routing/`，脱敏摘要与转写在 `runs/integrated-routing/`。

实测：1 次上传凭证请求、1 次文件上传、1 次识别提交，均 HTTP 200；任务最终 succeeded，耗时约 6.026 秒。没有 fal 调用。实际使用北京业务空间专属地址，`diarization_enabled=true`，JSON 字符串 special_word_filter 包含 `filter_with_signed.word_list=["肏屄"]`、`system_reserved_filter=false`，语言提示为 en。接口接受参数，不代表本英语样片已验证过滤词替换效果。

处理后为 16 kHz、单声道、PCM16 WAV，时长 32 秒且完整解码通过；样片原本已合规，生成副本后字节相同，源文件保持不变。44.1 kHz 双声道 float32 输入转换、时长保持及原件保全另有本地测试覆盖。识别返回 7 句、时间戳有效、说话人标签为 0／1／2；已知双人样片仍有过分割，未完成自然多人对话或完整译制验收。

返回 usage.duration=21，程序已能对北京专属域名按既有公开单价估算为 ¥0.004620，状态 estimated；未对账实际扣费和免费额度。任务编号 `c9541d64-3470-417b-8926-716fdc6a2d23`。直接再次读取 Fun-ASR 已成功结果，没有新增网络调用。

代码验证：221 项完整回归通过；随后修复空凭据导入边界并增加测试，配置／上传／Fun-ASR 相关 29 项通过；Ruff、diff 空白检查及 49 文件发布摘要通过。实现仍基于 v0.5.1 的本地修改，未提交、发布或安装。业务参数、配置样例、上传步骤及缓存规则已同步到源码仓库文档。
