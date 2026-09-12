# stevejobs 90 秒独立 API 译制验证（2026-09-13）

**结论：完成首轮技术与内容回转写验收。** 已生成 90 秒中文译制样片，音色相似度、背景纯净度和自然度仍需人工试听。不是整部 14 分 45 秒视频或已安装 skill 的验收。

- [最终中文样片](runs/stevejobs_20260913_90s/exports/stevejobs_zh-Hans_20260913_012911.mp4)
- [原视频片段](runs/stevejobs_20260913_90s/source/clip.mp4)
- [可编辑译文及时间轴](runs/stevejobs_20260913_90s/translations.json)
- [逐请求费用记录](runs/stevejobs_20260913_90s/cost/summary.json)

本机生成物和复制的原片存放在忽略的 `runs/` 中，不随源码提交；这里是本轮验证目录，不代表正式 skill 的默认用户项目路径。

## 验收证据

| 检查 | 结果 |
| --- | --- |
| 范围 | 原片开头 00:00–01:30；实际封装时长 90.023357 秒，受视频帧和编码时基影响 |
| 素材保全 | 已复制完整原片，SHA-256 `96b90d1d08ee8f8f78534355be12b100f15836aeb0a6b8190d9a83919febc3ae` |
| 转写与分句 | Whisper 返回 26 个片段，识别 1 个说话人；按标点、间隔与说话人合并为 14 句，保留原片段 ID 对应关系 |
| 译文生成 | 当前 agent 完成英语 → 简体中文；无额外 LLM API 调用 |
| 配音与对齐 | 14/14 句有非静音音频，全部对齐到目标样本数；48 kHz 合成 |
| 完整解码 | 最终 MP4 全片解码通过 |
| 画面一致性 | 最终视频与输入片段的逐帧解码 MD5 清单完全相同 |
| 内容回转写 | 未强制中文语言，Whisper 自动识别为 zh；agent 对照确认 14 句核心译文均覆盖 |
| 主观质量 | 未完成真人试听；不能据此宣称声音像本人或可直接用于运营发布 |

最终变速倍率范围 **0.594–1.044**。倍率小于 1 表示放慢；第 1、2、3、10 句低于本次提示阈值 0.75，已记录质量标记，按用户规则继续导出。

回转写有“里德 / 理德”“她 / 他”、简繁体和数字写法等差异；同音字差异不能直接当成配音错误。第 13 句“这儿”的儿化未被回识别。

## 实际采用的模型与输入条件

- ASR：`fal-ai/whisper`，`task=transcribe`、`language=en`、`chunk_level=segment`、`diarize=true`。本轮已成功的原音转写复用，没有因旧项目配置变化而替换 ASR。
- 分离：`fal-ai/sam-audio/separate`，**16 kHz 单声道 WAV 输入**；`prompt=speech`、`predict_spans=false`、`reranking_candidates=1`、`acceleration=balanced`、`max_chunk_duration=60`、`chunk_overlap=5`、`output_format=mp3`。
- TTS：`fal-ai/index-tts-2/text-to-speech`；每句对应的 **16 kHz 单声道原声片段** 同时作为 `audio_url` 与 `emotional_audio_url`，`prompt` 为本句中文。
- 背景：原音减去 `0.98 × 分离人声`，与对齐后的中文配音混回；同时保留 SAM 的原始 residual 供检查。
- 所有调用由本目录的新 Python 程序发起，不导入或运行旧引擎。

参数来源：[magicdub 提交 2eb7f24](https://github.com/shishengkai/magicdub/tree/2eb7f2404a752f8f5a8187ccefe63f596b26fb27)，主要为 `providers/vocal_separation/fal_sam_audio/provider.py`、`providers/tts/fal_index_tts_2/provider.py`、`media/audio.py`、`pipeline/synthesize_segments.py` 与 `config/settings.py`。旧仓库只读，未修改。旧任务有 completed 状态及真实成品，但缺少当时的模型参数快照，不能倒推每个历史成品用了哪套模型。

## 真实问题与处理

1. 初次 Demucs 使用 `htdemucs_ft` 而未显式指定 stems，服务端默认六声部与四声部模型冲突，返回 HTTP 422。显式四声部后技术成功。用户随后要求查旧项目，并明确改选旧参数的 SAM Audio；两次 Demucs 调用均保留，未用于最终成品。
2. 初次 SAM 虽复用了云端 JSON 参数，输入仍为 48 kHz 双声道，返回的人声近乎无声。40–49 秒窗口中，原声 RMS 约 0.04249，人声仅 0.0000697，相减后的背景保留了英文。其 14 句声音参考也受影响，整句倍率最高达 3.539；第一版样片内容验收失败，已保留。
3. 按旧项目改为 16 kHz 单声道重新调用同一 SAM 参数后，人声 RMS 为 0.03831，原声为 0.04229，相关系数约 0.934；同窗口背景 RMS 降为 0.01525。此轮输入与输出条件可用，因此重做逐句配音。**这是两次调用的实测差异，不足以断言 SAM 普遍不支持 48 kHz。**
4. 最终混音同窗口中文人声 RMS 约 0.08285，背景为 0.01525；自动语言识别和回转写均符合中文成品预期。背景仍可能有残留原声，纯净度需试听。

## 本次费用

**已知费用估算小计：$0.86 + ¥0.00**（USD 精度保留值 0.86364347503662109368）。包含所有成功、废弃、补验和质检调用；**1 次 HTTP 422 失败请求金额未知，未记为零，因此无法提供已对账的完整总额。**

| 模型 | 请求数 | 已知 USD 估算 | 金额未知请求 |
| --- | ---: | ---: | ---: |
| `fal-ai/whisper` | 4 | $0.009942 | 0 |
| `fal-ai/demucs` | 2 | $0.063700 | 1 |
| `fal-ai/sam-audio/separate` | 2 | $0.300002 | 0 |
| `fal-ai/index-tts-2/text-to-speech` | 32 | $0.490000 | 0 |

共 **40 次模型请求**：39 次获得成功结果，1 次 HTTP 422；其中部分“成功”结果因质量不合格被弃用，仍纳入费用。32 次 TTS 中，4 次来自已弃用 Demucs 参考，14 次来自失败的 48 kHz SAM 参考，14 次用于最终成品。Whisper 的 4 次包括初始转写、原始 TTS 抽查、两版成品回转写。

估算优先使用响应中的计费单位与账号可读单价，缺失时参考推理时长 / 音频时长与计价规则。当前 key 读取账单返回 403，所有估算均未对账；失败请求再次 GET 也未返回计费单位，未重复提交。没有 CNY 模型调用，人民币部分为 ¥0.00；宿主 agent 的未计量费用不包含在内。后续可用本地 `FAL_BILLING_KEY` 对原 request ID 对账，不重复加总估算与实际账单。

## 对后续 skill 开发的结论

- 当前 agent 翻译 + 独立 API 程序能完成短片段译制；可以开始封装最小业务 skill。此轮没有证据表明必须引入独立翻译 LLM。
- 应先固化已验证的输入采样率、声道、参考切片方式和模型参数，不能只记录模型名称。分离后、批量 TTS 前应检查人声信号强度，发现异常自动修复或标明降级，避免把无效参考继续送入付费步骤。
- 费用必须区分请求成功与质量可用，并保留失败 / 弃用尝试；普通 key 无账单权限时明确显示估算与未知。
- 本次仅为 macOS 独立验证原型；多人、配乐场景、完整两段素材、其他候选模型与系统、安装配置 / 升级 / Star 均没有因此完成验收。

## 复现入口

在本目录执行 `uv sync --python 3.12`，再用 `uv run python verify.py --help` 查看命令。已有项目的关键续跑命令如下，凭据文件使用自己的本地路径：

```sh
uv run python verify.py separate --run runs/stevejobs_20260913_90s --credentials /path/to/credentials.env --separation sam --stage separation_sam_16k_legacy --separation-input source/audio_16k_mono.wav
uv run python verify.py tts --run runs/stevejobs_20260913_90s --credentials /path/to/credentials.env --tts-revision legacy_v3_16k
uv run python verify.py export --run runs/stevejobs_20260913_90s
uv run python verify.py qc --run runs/stevejobs_20260913_90s --credentials /path/to/credentials.env --qc-stage qc_asr_16k
uv run python verify.py billing --run runs/stevejobs_20260913_90s --credentials /path/to/credentials.env
```

已完成 API 请求使用缓存结果；输入变更须使用新的显式 attempt / revision。首次运行须先 `init`、准备 16 kHz 单声道输入并经 agent 生成译文。此原型不等于生产级自动恢复或安装器。

## 参考文档

- [SAM Audio 参数与计价](https://fal.ai/models/fal-ai/sam-audio/separate)
- [IndexTTS 2 API](https://fal.ai/models/fal-ai/index-tts-2/text-to-speech/api)
- [fal 逐请求账单权限](https://fal.ai/docs/platform-apis/v1/models/billing-events)
