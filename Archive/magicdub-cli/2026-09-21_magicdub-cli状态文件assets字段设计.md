# 状态文件中 `assets` 字段设计

> 本文只定义状态文件里的 **assets（产物）** 子树。全文件字段（含 `run`、`ledger`、身份）见 [状态文件完整字段设计](2026-09-22_magicdub-cli状态文件完整字段设计.md)。  
> step 名：业务名原样保留（`demux`、`sep`、`asr`、`translation`、`tts`）；自拟步骤用名词（`clipping`、`duration_fitting`、`alignment`、`mixing`）。  
> 不以 JSON 格式写：一行为一个节点，缩进代表子节点；冒号后表示填什么；双斜线为注释。

## 约定

- 所有路径字段均为 **相对项目根目录的路径**（用 `/`，不以 `/` 开头）。
- 凡文件产物，除 `path` 外固定带校验字段（见下「文件引用」）。
- **校验：`sha256` + `size_bytes` 都存。**  
  - 仅字节数只能发现截断／空文件，发现不了内容被改。  
  - 仅哈希能验完整性，但排障时不如「先比大小再比哈希」方便。  
  - 写入后先核对 `size_bytes`，再核对 `sha256`；任一不符视为产物损坏，该步失败并可安全重做。
- 货币：费用金额一律 **CNY**；小数精度记录与比较到 **0.00000001**（八位小数）。
- ASR／TTS 等 adapter 若需特殊采样率或封装，由 **各 adapter 自行把输入转成所需格式**，pipeline 不统一产出「ASR 专用副本」路径。
- `non_speech` 语义 = 可混回的背景（BGM／环境声等）。若分离模型输出多轨（如 MVSep 的 Music+SFX），由 **sep adapter 在写出前合成** 为单一 `non_speech` 文件。
- 不在句级或 `tgt[]` 单条内记录 adapter／provider；实际采用的 adapter 只记在 `ledger`（见状态文件完整字段设计）。

### 文件引用（凡 `*_path` 或嵌套文件节点均同此形）

```text
path: 相对项目根的路径
sha256: 小写十六进制 SHA-256
size_bytes: 非负整数
```

下文为简洁，在树里写成 `某文件:` 块，即表示上述三键。

### 时长：窗口与 `src.audio_duration`

句在时间轴上的目标长度由 ASR 给出的 `start_ms`／`end_ms` 决定。

| 量 | 定义 | 用途 |
| --- | --- | --- |
| 窗口时长 | `end_ms - start_ms` | 切句区间；拟合分母与 alignment 目标的**定义来源** |
| `sentences[].src.audio_duration` | 由 **clipping** 按 `end_ms - start_ms` **计算并写入** 的毫秒数 | 便于下游直接读「本句目标时长」，避免处处重算 |
| `sentences[].tgt[].audio_duration` | 对该次 TTS 音频文件探测／按采样换算的实测时长（ms） | fitting 分子 |

**规则：**

1. `src.audio_duration` **不是** ffprobe 测切句文件得到的值；它与窗口时长在定义上相等：`src.audio_duration := end_ms - start_ms`。clipping 用这两个时间点调 ffmpeg 切句，并同时把算出的时长写入该字段。
2. `fitting_ratio = tgt.audio_duration / src.audio_duration`（等价于除以 `end_ms - start_ms`）。
3. `alignment` 把采用稿拉到 `src.audio_duration`（即窗口时长）；对齐后时长与目标差值不超过 **1 ms**。
4. 切句文件是否与窗口一致等实现校验，由 **clipping** 在本步内处理；不把「文件探测时长」存进 `src.audio_duration`，也不在 duration_fitting／alignment 里另立第二套时长标准。

### `tgt[].attempt` 与费用归属

| attempt | 含义 | 费用计入 |
| --- | --- | --- |
| `1` | 主链 translation + tts 的首次产物 | `cost_of_translation` / `cost_of_tts` |
| `≥2` | duration_fitting 触发的重译 + 重 TTS | `cost_of_duration_fitting.translation` / `.tts` |

---

## 字段树

```text
assets:
    src:
        video:          // input 视频
            path / sha256 / size_bytes
        audio:          // demux 纯音频
            path / sha256 / size_bytes
        silent_video:   // demux 无声视频
            path / sha256 / size_bytes
        speech:         // sep 说话／人声轨
            path / sha256 / size_bytes
        non_speech:     // sep 可混回背景（adapter 负责合成多轨）
            path / sha256 / size_bytes
        language: 语言名    // 原语言
        transcript: 文本   // asr 全文（便于浏览；权威句级仍以 sentences 为准）

    sentences: [
        {
            id: 数字              // 顺序号，稳定句 id
            start_ms: 毫秒值      // 句在原片时间轴上的起点
            end_ms: 毫秒值        // 终点；窗口时长 = end_ms - start_ms
            speaker_id: 文本       // 说话人标签，如 "SPEAKER_00"；adapter 统一转文本
            selected_attempt: 数字  // 最终采用的 tgt.attempt；须与该条 selection != rejected 一致

            src:
                text: 文本
                audio:              // 按窗口切出的原句音频
                    path / sha256 / size_bytes
                audio_duration: 毫秒数  // clipping 写入：等于 end_ms - start_ms，非文件探测值；见上文

            tgt: [
                {
                    attempt: 数字     // 见「attempt 与费用归属」；从 1 起
                    text: 文本
                    audio:            // 未对齐的 TTS 音频
                        path / sha256 / size_bytes
                    audio_duration: 毫秒数   // TTS 实测时长（未对齐）
                    fitting_ratio: 浮点数    // tgt.audio_duration / src.audio_duration
                    selection: "fitting_pass" | "forced" | "rejected"
                        // 每句非 rejected 至多一条。
                        // forced：次数用尽仍无合格稿时，在全部 attempt 中选最接近合格带者（见 pipeline §3.1），不是自动最后一次。
                    aligned_audio:    // 仅 selection != rejected 时存在
                        path / sha256 / size_bytes
                        // 对齐到 src.audio_duration（即窗口时长）后的音频
                }
            ]
        }
    ]

    tgt:
        language: 语言名
        srt:                // 最终字幕
            path / sha256 / size_bytes
        final_video:        // 成片视频
            path / sha256 / size_bytes
        final_audio:        // 最终混音音频（如母版 WAV）
            path / sha256 / size_bytes

    cost:                   // 均为 CNY，精度 0.00000001
        cost_of_sep: 浮点数
        cost_of_asr: 浮点数
        cost_of_translation: 浮点数     // 仅主链 translation（attempt=1），不含 fitting
        cost_of_tts: 浮点数             // 仅主链 tts（attempt=1），不含 fitting
        cost_of_duration_fitting:
            translation: 浮点数         // attempt≥2 的翻译
            tts: 浮点数                 // attempt≥2 的 TTS
        total: 浮点数                   // 以上之和；由 ledger 汇总
```

---

## 刻意不在本文的内容

- 项目 schema 版本、slot 配置、fallback 顺序  
- 整体／分步状态、幂等锁、输入指纹、失败原因码  
- 逐步／逐请求费用明细（可由总状态账本派生；本文 `cost` 仅为 assets 侧汇总）  
- speaker 级音色库或参考表（句级 `src.audio` 即参考来源）  
- 统一 ASR 转码副本路径  
