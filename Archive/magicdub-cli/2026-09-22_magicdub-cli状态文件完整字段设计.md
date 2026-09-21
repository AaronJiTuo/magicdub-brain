# magicdub-cli 状态文件完整字段设计

> 草稿。文件为任务根下的 `state.json`。  
> step 名：业务名原样保留（`demux`、`sep`、`asr`、`translation`、`tts`）；自拟步骤用名词（`clipping`、`duration_fitting`、`alignment`、`mixing`）。  
> 产物口径与时长／费用规则沿用 [assets 字段设计](2026-09-21_magicdub-cli状态文件assets字段设计.md)；路径约定见 [目录与路径设计](2026-09-22_magicdub-cli目录与路径设计.md)；控制流见 [pipeline 设计](2026-09-22_magicdub-cli_pipeline设计.md)。  
> 本文是状态文件的**全字段**清单。assets 专文仍保留时长与费用口径的细则；若冲突，以本文字段树 + assets 专文规则为准并应改到一致。

写法：一行为一个节点，缩进为子节点；冒号后为类型／取值；`//` 为注释。

---

## 1. 顶层

```text
schema_version: 整数          // 本设计为 1；不兼容变更时 +1
engine: "magicdub-cli"       // 固定；用于拒绝 skills 项目
task_id: ULID                // 任务身份；改文件夹名不改此值
title: 文本                  // 展示名，默认为安全化后的视频 stem；用户可改，不参与路径或校验
created_at: ISO-8601         // 创建时刻（带时区）
updated_at: ISO-8601         // 每次成功提交状态时更新

program:
    name: "magicdub-cli"
    version: SemVer           // 创建或最近一次写入本文件的程序版本

run: …                        // 见 §2 编排
assets: …                     // 见 §3 产物（含 cost 汇总）
ledger: [ … ]                 // 见 §4 逐次尝试账本
```

---

## 2. `run`（编排）

```text
run:
    status: "pending" | "running" | "done" | "failed" | "cancelled"
        // 整任务。start 创建后为 running；finish 成功为 done

    current_step: "start" | "demux" | "sep" | "asr" | "clipping"
                | "translation" | "tts" | "duration_fitting" | "alignment"
                | "mixing" | "finish" | null
        // pipeline 正在或即将调度的 step；空闲／结束为 null

    cursor:                   // 句级步骤的续跑位置；整片 step 可为空
        sentence_id: 数字 | null
        phase: "translation" | "tts" | "duration_fitting" | "alignment" | null

    fitting:                  // 创建任务时从 config.yaml（否则 constants.py）冻结
        lower_ratio: 浮点数   // 出厂 0.8，含边界
        upper_ratio: 浮点数   // 出厂 1.2，含边界
        max_rewrites: 整数    // 出厂 2；attempt 最大 = 1 + max_rewrites

    slots:                    // 创建任务时冻结。order[0] 为默认 adapter，其后为 fallback
        sep:
            order: [ adapter_id, … ]
        asr:
            order: [ … ]
        translation:
            order: [ … ]
        tts:
            order: [ … ]
        // 逐句实际用了哪个 adapter 只记在 ledger，不在这里记 used

    steps:                    // 整片步骤的执行态。句级步骤的「句子走到哪」不看 status，见下文「句级进度」
        <step>:
            status: "pending" | "running" | "done" | "failed" | "skipped"
                // translation／tts／duration_fitting／alignment：
                // running = 进程正在跑该 step；done 仅当全部句子都满足该步的键。
                // 续跑时以键是否存在为准，不因 status=done 的误写而跳过缺键的句子。
            started_at: ISO-8601 | null
            finished_at: ISO-8601 | null
            input_fingerprint: 文本 | null
            error_code: 文本 | null   // 取值见 pipeline §6.1
            message: 文本 | null

    lock:
        holder: 文本 | null   // hostname:pid；与任务根 run.lock 文件镜像
        step: 文本 | null
        acquired_at: ISO-8601 | null
        // 占用检测以任务根 run.lock 文件为准；同机 pid 已死则启动时清文件与本镜像

    last_error:               // 最近一次失败摘要；成功推进后可清空 message 但建议保留历史在 ledger
        step: 文本 | null
        error_code: 文本 | null
        message: 文本 | null
        at: ISO-8601 | null
```

句级「做到哪」只由该句 assets 键是否已有值决定，`cursor` 只是加速。缺键就必须补做，即使 `steps.*.status` 曾被写成 `done`。

| 句子已完成到 | 该句必须已有 |
| --- | --- |
| asr | `id`、`start_ms`、`end_ms`、`speaker_id`、`src.text` |
| clipping | 另有 `src.audio`、`src.audio_duration` |
| translation 的 attempt n | `tgt[]` 中该 attempt 的 `text` |
| tts 的 attempt n | 该 attempt 的 `audio` |
| duration_fitting | 该 attempt 的 `audio_duration`、`fitting_ratio` |
| pipeline 已选定 | `selected_attempt`，且该条 `selection` 为 `fitting_pass` 或 `forced`，其余为 `rejected` |
| alignment | 选定那条的 `aligned_audio` |

---

## 3. `assets`（产物）

文件节点一律：

```text
path: 相对任务根，用 /
sha256: 小写十六进制
size_bytes: 非负整数
```

```text
assets:
    src:
        language: 语言代码          // 如 en、zh-Hans
        video: 文件                 // media/src/video.<源扩展名>
        audio: 文件                 // media/src/audio.wav
        silent_video: 文件          // media/src/silent_video.mp4
        speech: 文件                // media/src/speech.wav
        non_speech: 文件            // media/src/non_speech.wav；可混回背景
        transcript: 文本 | null     // asr 全文；权威句级在 sentences

    sentences: [
        {
            id: 整数                // 稳定句 id，从 1 起，按 start_ms 升序编号；与路径 media/sentences/<id>/ 一致
            start_ms: 整数
            end_ms: 整数            // 窗口 = end_ms - start_ms；允许与相邻句重叠
            speaker_id: 文本        // 如 "SPEAKER_00"；adapter 统一转文本
            selected_attempt: 整数 | null

            src:
                text: 文本
                audio: 文件         // …/src.wav
                audio_duration: 整数
                    // := end_ms - start_ms，clipping 写入；不是文件探测值

            tgt: [
                {
                    attempt: 整数   // 从 1；1=主链，≥2=fitting 重做
                    text: 文本
                    audio: 文件     // …/tgt/attempt_<n>.wav
                    audio_duration: 整数 | null    // TTS 实测 ms
                    fitting_ratio: 浮点数 | null   // audio_duration / src.audio_duration
                    selection: "fitting_pass" | "forced" | "rejected" | null
                        // 只由 pipeline 写，duration_fitting 不写。
                        // 非 rejected 每句至多一条。
                        // forced：次数用尽后全体 attempt 中最接近合格带者。
                    aligned_audio: 文件 | 缺省
                        // 仅 selection 为 fitting_pass 或 forced 时存在
                        // …/tgt/attempt_<n>.aligned.wav
                }
            ]
        }
    ]

    tgt:
        language: 语言代码
        final_video: 文件           // exports/final.mp4
        final_audio: 文件           // exports/final.wav
        srt: 文件                   // exports/final.srt

    cost:                           // CNY，精度 0.00000001；由 ledger 汇总，可重算
        cost_of_sep: 浮点数
        cost_of_asr: 浮点数
        cost_of_translation: 浮点数          // 仅 attempt=1
        cost_of_tts: 浮点数                  // 仅 attempt=1
        cost_of_duration_fitting:
            translation: 浮点数              // attempt≥2
            tts: 浮点数
        total: 浮点数                        // 以上之和
```

时长、forced 选取、attempt 与费用归属的细则见 assets 专文与 pipeline §3.1，不在此重复展开。

---

## 4. `ledger`（逐次外部尝试）

每次对外请求（含失败、含 fallback 中未采用的 adapter）追加一条，**不删**。`assets.cost` 必须能由本数组加总得到。

```text
ledger: [
    {
        id: ULID
        at: ISO-8601
        step: "sep" | "asr" | "translation" | "tts"
        sentence_id: 整数 | null     // 整片调用（sep／asr）为空
        attempt: 整数 | null         // translation／tts 必填
        adapter_id: 文本
        ok: 布尔
        error_code: 文本 | null
        cost_cny: 浮点数 | null      // 未知不是 0；未知保持 null 并在 message 说明
        message: 文本 | null
    }
]
```

fixed step（demux／clipping／duration_fitting／alignment／mixing）无 API 费用时**不必**入账；若需审计耗时，可另加非费用事件，首版不强制。

---

## 5. 写入顺序（与文件约定一致）

1. 产物先落 `tmp/`。  
2. 校验通过后移到 §目录文档中的正式路径。  
3. 写入对应 `assets` 文件引用与标量。  
4. 若有 API，追加 `ledger` 并重算 `assets.cost`。  
5. 更新 `run.steps`、`run.status`／`cursor`、`updated_at`。  
6. 失败：不把半成品标成正式 `path`；`run.last_error` 与失败的 ledger 行仍要留下。

---

## 6. 不放进状态文件的内容

- API Key、全局 fallback 默认（在 `~/.magicdub/cli/`；任务内只冻结 `run.slots.order` 副本）
- 程序安装路径
- adapter 内部转码临时文件（留在 `tmp/`，不进 assets）
- 句级实际使用的 adapter（只在 `ledger`；`run.slots` 只有 `order`）
