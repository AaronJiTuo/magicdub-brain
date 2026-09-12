# Whisper 说话人分离与人民币计费验证

日期：2026-09-13。当前验证项目：`runs/stevejobs_20260913_whisper_cny_90s/`。

## 用户验收

2026-09-13，用户明确回复“OK，验证通过”。本轮 Steve Jobs 前 90 秒英语 → 简体中文成片已获验收，采用本轮模型组合、已确认参数与音频处理流程作为后续译制 skill 的验证基线。见[验收记录](../../../.records/events/2026-09/2026-09-13_024425_用户确认Whisper人民币计费样片验收通过.md)。此确认不扩大为多人场景、完整素材、其他候选模型或正式 skill 的验收；账单未精确对账的状态保持不变。

## 本次修改

将当前独立验证入口 `recover.py` 的 ASR 从 Wizper 改为 `fal-ai/whisper`，输入仍为 Demucs 分离后 16kHz 单声道人声。分离、原提示词和每秒 4.5 字目标、逐句 IndexTTS 2 音色与情绪参考、atempo、背景减法、混音及导出沿用上一轮恢复值。

Whisper 的说话人分离开启；保留每个 chunk 的 `speaker` 以及完整 `diarization_segments`，并传递到翻译和对齐文件。没有返回说话人时记录缺失，不凭空填造。单人演讲样片只能核验接口和字段，不能证明多人场景精度。

参数依据：[fal Whisper 官方接口](https://fal.ai/models/fal-ai/whisper/api)、[Wizper 官方接口](https://fal.ai/models/fal-ai/wizper/api)。本次参数文件为 [whisper_parameters.json](whisper_parameters.json)。

| 参数 | 处理 |
| --- | --- |
| `task` | 沿用 `transcribe` |
| `language` | 沿用 `null`，自动检测源语言 |
| `chunk_level` | 沿用 `segment` |
| `diarize` | 用户指定 `true` |
| `batch_size` | 用户已选择 `64` |
| `prompt` | 用户已选择空字符串 `""` |
| `num_speakers` | 用户已选择 `null`，自动判断人数 |
| 旧 `max_segment_len=20`、`merge_chunks=false`、`version=3` | 用户已确认不传入 Whisper；直接使用返回分句，不在本地额外合并或按 20 秒拆分 |

所有新增参数和兼容策略均已由用户确定，`pending_decisions=[]`。参数未齐全时，代码会在上传 ASR 输入或提交请求之前停止；此前已验证此保护逻辑。旧参数报告和原运行程序快照仍保留，当前程序不再作为旧 Wizper 运行的逐字复现入口。

## 人民币账本

[costs.py](costs.py) 统一使用 `CNY`，美元来源费用按用户指定的固定汇率 `1 USD = 7 CNY` 换算，人民币来源费用保持原值；不是实时汇率。

- 每条尝试的 `amount` / `estimated_amount` 都是人民币，`currency=CNY`，显示如 `¥1.23`。
- 原币金额和单价仅留在 `source_cost` / pricing 证据中供对账，不作为另一套汇总金额。
- 使用 `Decimal` 保留未舍入数值；逐项显示保留两位，累计按精确值相加后再显示，因此累计可能与各行显示值的直接相加相差一分钱。
- 每次重算从原币证据换算，防止重跑账单时重复乘以 7；同一 request ID 的确认账单替代估算，不重复收费。
- 失败、取消及结果未知的尝试继续保留；已经知道的失败支出纳入总额，未知支出不写零。宿主 Codex 成本未计量时仍单独说明不包含。

历史两轮的 61 次尝试已按新规则重算，旧摘要保存为各自的 `cost/summary_before_cny.json`：首轮已知估算 `¥6.05`，恢复轮 `¥1.36`，按未舍入金额计算的历史累计 `¥7.40`，其中一笔失败金额仍未知。这些人民币金额未完成精确账单对账，不代表完整最终账单。

## 验证结果

- `test_costs.py` 三项回归检查通过：人民币换算与重复换算保护；混合来源币种及失败/未知费用；确认金额替代估算、请求去重及最后舍入。
- 同一 Steve Jobs 原素材的前 90 秒已完成整条链路。成品：`runs/stevejobs_20260913_whisper_cny_90s/exports/stevejobs_zh-Hans_whisper.mp4`；H.264 482×360、AAC 48kHz 单声道、192k 配置，容器时长 90.023357 秒。
- Whisper 已完成转写：21 段文字、35 段 diarization 时间信息；识别到 `SPEAKER_00`，21 段均有说话人 ID。没有对返回分句进行额外合并或 20 秒拆分。
- 21 段 Codex 译文均符合目标中文字数 ±2，全部完成 TTS；说话人 ID 和时间范围从转写经翻译到对齐文件保持一致。
- 21 段音频均非静音，完整视频解码通过，解码画面 SHA-256 与输入片段相同，复制原素材 SHA-256 正确。
- 保留旧 atempo 参数和误差：最大绝对句长误差 22.766ms；`s0012` 变速比例约 1.447、`s0015` 约 0.719，按规则标记供试听，未偷偷改译文或参数消除这些标记。
- 成片回转写自动识别为中文、单一 `SPEAKER_00`，21/21 段译文内容覆盖。核对时明确归一化 `18/十八`、`理德/里德`、`她/他`；这是内容核验，不代替音色和自然度试听，也不证明多人场景准确率。

技术证据位于新运行目录的 `checks.json`、`qc/asr_parameter_checks.json`、`qc/pipeline_checks.json`、`qc/content_review.json`、`qc/translation_length_checks.json`。最终有效参数快照为 `provenance/effective_parameters.json`；原始模型输入及响应在每次 `attempts/` 内保存。既有两版样片和程序快照均保留。

本轮 24 次模型请求全部成功，人民币费用如下（包含此前已完成的 Demucs 分离）：

| 阶段 | 请求数 | 已知估算 |
| --- | ---: | ---: |
| Demucs 分离 | 1 | ¥0.44 |
| Whisper 转写及说话人分离 | 1 | ¥0.02 |
| IndexTTS 2 配音 | 21 | ¥0.99 |
| Whisper 成片回转写及说话人分离 | 1 | ¥0.02 |
| 本轮合计 | 24 | **¥1.47** |

含历史共 85 次尝试的累计已知估算为 **¥8.87**。每条尝试均以 CNY 记录和汇总，已验证从原币证据重复换算不会再次乘以 7。历史仍有一笔失败金额未知，不能计零；账单接口返回 403，上述金额未完成精确对账，不含未计量的宿主 Codex 费用。细目为 `cost/stages_cny.json`，本轮汇总为 `cost/summary.json`，历史累计为 `cost/cumulative_cny.json`。

本轮已完成 `asr → Codex 翻译 → tts → render → qc → billing`，并获用户验收通过。当前仍是独立验证原型；正式 skill 安装及多人场景尚未验收，自动技术检查也不替代其他素材的主观质量评估。
