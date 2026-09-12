---
status: partially_absorbed
absorbed_by: Releases/05_magicdub-skill项目规划.md
remaining_value: 接口原始资料、模型版本地域参数与实测验证；候选和已确认传输及LLM策略已吸收
last_reviewed: 2026-09-12
---

# magicdub-skills 候选模型

用户提供的候选清单。候选不代表已接入或已通过新 skill 验收；各阶段的实际模型和参数需随任务保存。用户已明确：LLM 先使用 agent 自带模型，实测后再决定是否单独指定模型。

## ASR

https://fal.ai/models/fal-ai/whisper/api

Fun-ASR非实时语音识别Python SDK
https://docs.bailian.console.aliyun.com/zh/model-studio/funauidio-asr-recorded-speech-recognition-python-sdk


## 音频分离

https://fal.ai/models/fal-ai/demucs/api
https://fal.ai/models/fal-ai/sam-audio/separate/api

## TTS

https://fal.ai/models/fal-ai/index-tts-2/text-to-speech/api


## LLM

使用agent自带的LLM


## 云端对象存储

fal CDN
https://fal.ai/docs/documentation/model-apis/fal-cdn

阿里云百炼
https://docs.bailian.console.aliyun.com/zh/model-studio/get-temporary-file-url


## API Key

只记录需要配置的变量名：`DASHSCOPE_API_KEY`、`FAL_KEY`。原文件中的值已保存在 Git 忽略的本地私有配置，本文不包含密钥值。该临时保存位置不作为未来 skill 的用户配置目录约定。

## 当前选择边界

- ASR：fal Whisper / 阿里云百炼 Fun-ASR，由使用者选择；不自动替换为 SDK 示例里出现的其他模型。
- 音频分离：fal Demucs / fal SAM Audio，由使用者选择。
- TTS：当前候选为 fal IndexTTS 2.0；单个候选显示实际采用值即可，不制造无意义的选择题。
- LLM：先由当前 agent 完成翻译及必要的时长约束改写，实测后再决定是否引入独立模型 / API；当前不要求单独的 LLM API key。
- 媒体中转：fal CDN / 百炼临时存储，需与所选模型和调用方式匹配；不是任意模型都能互换使用的永久对象存储。

## 2026-09-12 文档核对

已打开上方四个 fal 模型 API 页面，确认对应文档存在；未调用模型或验证账号权限。Whisper 文档列出 `diarize` 和时间戳选项，并注明说话人识别可能增加费用，后续实测应包含这项用量。[Whisper API](https://fal.ai/models/fal-ai/whisper/api)

百炼控制台文档地址未能通过本次网页工具读取，改用相同文档路径的官方帮助中心核对：

- [Fun-ASR Python SDK](https://help.aliyun.com/zh/model-studio/funauidio-asr-recorded-speech-recognition-python-sdk)：当前文档明确 `file_urls` 支持 HTTP / HTTPS；Python SDK 不支持 `oss://` 临时 URL。
- [Fun-ASR RESTful API](https://help.aliyun.com/zh/model-studio/fun-asr-recorded-speech-recognition-http-api)：使用 `oss://` 需相应的资源解析请求头；具体组合在实现时验证。
- [百炼临时文件 URL](https://help.aliyun.com/zh/model-studio/get-temporary-file-url)：当前文档规定文件与模型 / 账号绑定、有效期为 48 小时，不能将该 URL 当作通用公网链接或项目长期素材。

2026-09-12 用户已接受兼容调用方案：使用可访问 HTTPS URL 时通过 Fun-ASR SDK 调用；使用百炼 `oss://` 临时 URL 时通过 REST 并携带所需资源解析请求头。实现根据实际选定的中转方式匹配调用路径，不因换调用方式而静默更换模型。此处确认兼容规则，尚未指定唯一默认中转服务，也没有将文档可读标记为端到端可用。见 [确认记录](../../.records/events/2026-09/2026-09-12_194517_确认FunASR媒体地址与调用方式匹配规则.md)。

项目格式、费用与 agent 翻译交接建议见 [首版约束与项目数据方案](2026-09-12_magicdub-skills首版约束与项目数据方案.md)。
