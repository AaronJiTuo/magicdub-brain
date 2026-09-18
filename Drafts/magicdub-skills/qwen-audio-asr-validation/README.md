# Qwen Audio 3.0 ASR Flash Filetrans 独立实测

使用既有 Fun-ASR 双人英语样片，测试一次真实百炼上传、异步识别、结果下载、时间戳与说话人标签。模型为 `qwen-audio-3.0-asr-flash-filetrans`，不修改正式模型列表、默认值或已有视频项目。

```sh
python validate.py --runtime /path/to/magicdub-skills --source /path/to/two-speakers-vocals.wav
```

凭据通过既有 MagicDub 配置读取。固定输入为 32 秒、16 kHz 单声道 PCM16 WAV，SHA-256 必须匹配旧 Fun-ASR 样片。参数与既有 Fun-ASR 相同，启用说话人分离，语言提示 en，不指定人数、不加热词或上下文。

本程序仅有一个固定轮次；先持久化提交意图，随后最多提交一次 ASR 任务。重复运行恢复同一 task_id；成功、明确失败或提交结果未知时不新建任务。上传策略与 API Key 不落盘；原始响应及临时地址仅保存在被忽略、权限受限的 `private/`。公开摘要和转写不包含凭据或媒体 URL。

预期：任务及文件子任务均 SUCCEEDED，取得非空文本、有效时间戳与说话人标签。技术通过不等于准确率或自然多人对话质量验收。价格以[官方北京原价](https://help.aliyun.com/zh/model-studio/qwen-audio-3-0-asr-flash-filetrans)每秒 ¥0.00022 估算，不把 usage 估算当作实际账单或免费额度核销。

状态（2026-09-18）：真实 API 链路成功，7 段转写、70 个词均有有效时间戳。双人样片仍输出 3 个说话人标签，与 Fun-ASR 同样把 “dots.” 独立成第三人。详见 [实测结果](RESULTS.md)、`summary.json`、`transcript.json` 与保留词级时间的 `provider_transcript.json`。重复运行已验证零网络调用，不会新增任务。

官方接口：[Qwen Audio / Fun-ASR HTTP API](https://help.aliyun.com/zh/model-studio/fun-asr-recorded-speech-recognition-http-api)。
