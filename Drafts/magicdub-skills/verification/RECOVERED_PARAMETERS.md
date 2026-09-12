# test_by_step 最终调参恢复与对照验证

日期：2026-09-13。用户明确指定：以 `Drafts/test_by_step/` 最终保留下来的程序作为多轮实例测试后的调参基准。

后续变更：本文保留该轮 Wizper 样片的历史事实。当前入口已按用户要求改为 Whisper 说话人分离和人民币计费，见 [新验证说明](WHISPER_CNY_VERIFICATION.md)。如需复现本文对应代码，应使用该运行目录 `provenance/` 中保存的程序快照；下方命令描述的是当时的入口。

## 结论与证据边界

找到了完整参数链。当前证据不支持“多供应商改造把原参数整体覆盖”的判断：`magicdub` 首次发布 pipeline 的提交 `ae1a0e7`、当前 HEAD `2eb7f2404a752f8f5a8187ccefe63f596b26fb27`，以及 Git 中未被提交引用的旧源码，都保留了主要音频参数。旧代码经历模块拆分、音频格式抽象和供应商路由变更；当前根配置切换为 SAM / 百炼 Fun-ASR，而原实验最终程序是 Demucs / Wizper。

更直接的差异来自上一轮独立验证：它没有完整复现旧实验的 ASR 输入、分句、译文字数、限幅器及混音设置。不能把两套实现的结果差异直接归因于原仓库参数丢失。

`magicdub` 可达历史共 8 个提交；只读检查还找到 71 个未引用 tree、148 个 blob，无未引用 commit。关键旧 blob：

- `5c743913b1f358c470c1a7a27470a0ca15bed85b`：旧 `media/audio.py`；与当前版主要差异是输出格式抽象，16k 单声道、atempo 参数仍保留。
- `bceccd7fd00b0dd4c58c655f6fea78ae13888ce6`：旧 `media/mixing.py`；与当前版主要差异是导入路径、输出格式函数，主要混音滤镜未变。
- 旧 ASR / Demucs / IndexTTS provider 的未引用版本也保留相同模型参数。没有找到另一套已落地的动态 RMS / loudnorm 调参实现；讨论中的建议不能当作执行配置。

历史 `test_by_step/output/` 有 20 个包含最终视频的实例目录，覆盖 Steve Jobs、特朗普、采访、动画等素材。`20260511_124257_7ezs` 保存了 885 秒 Steve Jobs 成片，但其 ASR 从 55.66 秒开始，不能视为完整转写验收已通过。历史 run_manifest 没有逐请求模型参数快照，所以本次恢复的是**用户指定的最终存留程序**，不宣称能证明每个历史成片当时的所有配置，也不宣称全局最优或云端模型可逐比特复现。

## 恢复的参数

机器可读快照：[recovered_parameters.json](recovered_parameters.json)。新运行目录内还复制了原程序、原提示词，并保存每个文件 SHA-256；没有复制 `.env`。

| 环节 | test_by_step 最终值 | 证据 |
| --- | --- | --- |
| 提取 | WAV、PCM s16、16kHz、单声道 | `fetch_audio.py` |
| 分离 | `fal-ai/demucs`，`htdemucs_ft`，只输出 `vocals`，shifts=1，overlap=0.25，WAV | `separate_audio.py`；`.env` 无模型参数覆盖 |
| 背景 | 原音频 − 0.98 × 人声；公共时长减 20ms；`alimiter=level_in=1:level_out=0.95:limit=0.95` | `separate_audio.py` |
| ASR | `fal-ai/wizper` v3；输入分离干声；language=null；segment；max_segment_len=20；merge_chunks=false | `asr.py`、`build_sentences.py` |
| 翻译 | 全文语境，每批 12 句；目标中文字符数=round(秒数×4.5)，允许 ±2；场景与人物语气一致 | `translate_sentences.py`、`source/prompt_system_gemini.txt` |
| TTS | `fal-ai/index-tts-2/text-to-speech`；本句原干声同时作为音色及情绪参考；没有额外语速、温度参数 | `cut_speech.py`、`tts.py` |
| 对齐 | atempo=TTS时长/原句时长，0.5–4 分解，保留六位小数；s16 输出，维持 TTS 原采样率 | `refine_target_audio.py` |
| 混音 | 48kHz 单声道；原干声 -100dB；背景默认不衰减；TTS 不加全局增益；按起点 adelay；amix normalize=0 | `assemble_target_video.py` |
| 限幅与导出 | `alimiter=limit=0.98:attack=2:release=50`；视频 copy、AAC 192k、按视频时长截取 | `assemble_target_video.py` |

旧脚本没有在 atempo 后精确补齐/裁剪到样本数，所以会存在毫秒级时长误差；本次原样保留并测量，不把“完全相等”伪称为旧版行为。

翻译模型存在配置层次：代码默认 `google/gemini-3-flash-preview`，本地 `.env` 的 `OPENROUTER_MODEL` 会覆盖为 `~google/gemini-flash-latest`；旧请求启用 reasoning，未显式设 temperature 或输出长度。未验证这个历史别名现在指向什么。按本次用户明确选择，**不调用外部 Gemini**，由 Codex 恢复原提示词、字数及分批策略。因此这是媒体参数复现，翻译执行器保留当前产品决定。

接口核对：[Wizper](https://fal.ai/models/fal-ai/wizper/api)、[Demucs](https://fal.ai/models/fal-ai/demucs/api)、[IndexTTS 2](https://fal.ai/models/fal-ai/index-tts-2/text-to-speech/api)、[fal OpenRouter](https://fal.ai/models/openrouter/router/openai/v1/chat/completions)。未设置的云端默认值可能随服务更新，不能据此保证历史输出完全一致。

## 本次复现边界

- 用户已明确重新选择 Demucs `htdemucs_ft`，取代此前此样片选定的 SAM；这不是静默切换。
- 原视频复制到新项目，只处理相同的前 90 秒。画面沿用上一版样片的画面轨，便于 A/B；音频直接从完整原素材提取，避免上一版预裁视频的额外 AAC 转码。
- 独立程序 [recover.py](recover.py) 只复用本实验 [verify.py](verify.py) 的请求日志、文件及费用工具，不依赖旧 MagicDub 引擎，不在旧实验目录运行或修改代码。
- 保留原参数；新增安全请求记录、素材快照、费用及校验。最终滤镜输出以 float PCM 中转，避免插入整数削波；MP4 加 faststart 便于预览。
- 新项目：`runs/stevejobs_20260913_recovered_90s/`。上一版 `runs/stevejobs_20260913_90s/` 保留。

## 复现命令

在本验证目录执行，凭据文件路径由使用者提供：

```sh
uv run python recover.py prepare --run runs/NEW_RUN --baseline runs/stevejobs_20260913_90s --separation demucs
uv run python recover.py separate --run runs/NEW_RUN --credentials /path/to/credentials.env
uv run python recover.py asr --run runs/NEW_RUN --credentials /path/to/credentials.env
# Codex 按 transcript.json 与原提示词生成 translations.json，保留句子编号和时间轴。
uv run python recover.py tts --run runs/NEW_RUN --credentials /path/to/credentials.env
uv run python recover.py render --run runs/NEW_RUN
uv run python recover.py qc --run runs/NEW_RUN --credentials /path/to/credentials.env
uv run python recover.py billing --run runs/NEW_RUN --credentials /path/to/credentials.env
```

成品不覆写；已提交模型任务通过同一 request ID 续查，已有成功结果复用。要修改提示词或模型参数，应建立新运行目录。本工具仍是验证原型，尚未交付正式 skill。

## 本次实测结果

已完成新样片：`runs/stevejobs_20260913_recovered_90s/exports/stevejobs_zh-Hans_recovered.mp4`。

- 容器时长 90.023357 秒；H.264 482×360，AAC 48kHz 单声道、192k 配置。
- 完整解码通过；解码画面 SHA-256 与上一版画面轨相同；复制原片 SHA-256 校验通过。
- Wizper 直接输出 18 段，全部完成配音；18/18 译文在目标中文字数 ±2 范围内。
- 18 段音频均非静音；旧 atempo 流程的最大绝对时长误差 23.946ms，已逐句记录，不是精确样本数对齐。
- 最终音频经 Whisper 自动语言回转写为中文，18/18 句核心内容覆盖。归一化仅处理 `18/十八`、`理德/里德`、`她/他`，同音字不能据 ASR 文本判定为配音读错。音色相似度、自然度及背景主观听感待用户比较。
- 证据：运行目录的 `project.json`、`alignment.json`、`checks.json`、`qc/content_review.json`、`qc/translation_length_checks.json`、`cost/comparison.json`。没有修改旧 `magicdub` 引擎或旧 `test_by_step` 程序，没有覆盖上一版样片。

本次 21 次模型请求全部成功：

| 环节 | 请求数 | 已知估算 USD |
| --- | ---: | ---: |
| Demucs 分离 | 1 | 0.063000 |
| Wizper 转写 | 1 | 0.000761 |
| IndexTTS 2 | 18 | 0.128000 |
| Whisper 成片回转写 | 1 | 0.002038 |
| 本次合计 | 21 | 0.1937998600 |

本次显示 **$0.19 + ¥0.00**；含前轮全部尝试的累计已知估算 **$1.06 + ¥0.00**（未四舍五入值 $1.0574433350）。前轮 1 次失败金额仍未知；两个运行目录的请求与费用记录全部保留。账单接口 HTTP 403，费用依据响应计费单位或计算耗时及查询到的单价估算，未精确对账；不能把未知费用计为零。宿主 Codex 费用未计量、不包含在上述小计。

这份结果可作为下一轮调参和 skill 实现的比较基准；正式默认模型、是否修正旧版时长误差，应在用户试听后另行确定，不能仅凭技术检查判定旧效果已完全恢复或更好。
