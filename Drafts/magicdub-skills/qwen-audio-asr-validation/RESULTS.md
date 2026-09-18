# Qwen Audio 3.0 ASR Flash Filetrans：真实 API 通过，说话人仍过分割

2026-09-18，使用现有百炼凭据与北京业务空间专属地址，对既有 `acceptance_two_speakers` 的 32 秒英语 Demucs 人声提交一次识别。模型名为 `qwen-audio-3.0-asr-flash-filetrans`。上传凭证、音频上传、任务提交、两次查询及结果下载均为 HTTP 200；任务和文件子任务均为 SUCCEEDED。

## 实测结果

| 项目 | 结果 |
| --- | --- |
| 输入 | 32.000 秒，16 kHz、单声道、PCM16 WAV；完整解码通过 |
| 参数 | diarization_enabled=true，language_hints=[en]，special_word_filter 与此前 Fun-ASR 一致；未指定 speaker_count，未加热词或上下文 |
| 提交次数 | 1；重复运行命中本地成功结果，新增网络调用 0 |
| 耗时 | 提交至结果下载与解析 5.514 秒，包含 5 秒轮询间隔；不是纯推理耗时 |
| 服务端时间 | submit 23:52:12.422，scheduled 23:52:12.493，end 23:52:14.313（接口原文） |
| 结果 | 7 段、70 个词；句级和词级时间均有效，7 段都有 speaker_id |
| 说话人 | 0／1／2，共 3 标签；双人样片仍存在过分割 |
| 原媒体／有效内容时长／usage | 32,000 ms／22,520 ms／duration=23 |
| 费用估算 | 23 × ¥0.00022 = **¥0.005060**；实际账单和免费额度未核对 |
| 素材保全 | 运行前后 SHA-256 相同；未重新分离音频或修改原项目 |

任务编号 `d6e44be0-b099-4d0e-bca2-02a46045d9a2`。输入 SHA-256 为 `df6d7f72173914e90757d66c4185ebcaca2eff432b7ec6217737f60e8465366e`，与旧 Fun-ASR 集成实测一致。

## 完整转写

以下直接展示模型结果，不修正文字或标签。

| 起止（秒） | speaker_id | 原始文字 |
| --- | --- | --- |
| 0.08–2.88 | 0 | Your commencement from one of the finest universities in the world. |
| 6.64–7.72 | 0 | Truth be told. |
| 8.12–9.52 | 1 | fellow citizens. |
| 10.45–13.37 | 1 | The golden age of America begins right now. |
| 16.13–17.05 | 2 | dots. |
| 18.58–24.02 | 0 | i dropped out of reed college after the first six months but then stayed around as a drop in for another eighteen. |
| 24.02–31.98 | 1 | months we will be the envy of every nation and we will not allow ourselves to be taken advantage of any longer. |

## 与已有 Fun-ASR 结果对照

对照复用[先前集成实测](../fun-asr-upload-validation/runs/integrated-routing/summary.json)，本次未重跑 Fun-ASR。相同音频字节、语言提示、说话人和过滤参数；两次测试的模型与发生时间不同。

| 项目 | 既有 Fun-ASR | 本次 Qwen Audio 3.0 |
| --- | --- | --- |
| 分段 | 7 | 7 |
| 标签数 | 3 | 3 |
| 孤立 “dots.” | speaker 2 | speaker 2 |
| 第六段结尾 | another 18.，结束 24.22 秒 | another eighteen.，结束 24.02 秒 |
| 末段 | 25.26 秒起，We will… | 24.02 秒起，months we will… |
| 返回 usage 秒数 | 21 | 23 |
| 估算费用 | ¥0.004620 | ¥0.005060 |

接口易用性通过：可以沿用百炼异步文件识别方式，返回直接可读的文字、句级／词级时间和说话人标签。但当前样片没有显示说话人分离优于 Fun-ASR；“dots.” 的第三人标签问题仍在。末段多识别了 “months”，并与后面的另一段发言合在一起；该词是否实际存在以及应归属哪位说话人，需要对照音频人工复核，不能仅凭两份识别结果判断对错。

没有人工逐词标注或 WER／DER 计算，也没有中文、自然多人对话、重叠讲话或全长视频测试，不能据此认定整体准确率更高或更低。未修改 magicdub-skills 生产代码、默认模型或日常安装。

原始响应和临时地址只在忽略的 `private/`；公开摘要为 `summary.json`，标准化结果为 `transcript.json`，带完整词级时间与服务端文本的脱敏结果为 `provider_transcript.json`。Key 与上传签名未写入文件或报告。

依据：[官方 HTTP API](https://help.aliyun.com/zh/model-studio/fun-asr-recorded-speech-recognition-http-api)、[北京公开原价](https://help.aliyun.com/zh/model-studio/qwen-audio-3-0-asr-flash-filetrans)。
