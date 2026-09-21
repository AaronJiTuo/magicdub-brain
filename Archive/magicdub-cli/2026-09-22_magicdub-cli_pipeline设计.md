# magicdub-cli pipeline 设计

> 草稿。控制流与步骤职责；产物与编排字段见 [状态文件完整字段设计](2026-09-22_magicdub-cli状态文件完整字段设计.md)（assets 细则见 [assets 字段设计](2026-09-21_magicdub-cli状态文件assets字段设计.md)）；环节对照见 [流程图](2026-09-20_magicdub-cli流程图.md)；目录与安装见 [目录与路径设计](2026-09-22_magicdub-cli目录与路径设计.md)。  
> 本文只定 pipeline 与 step 的边界及每步 in／out／作业。

---

## 1. 分层与编排

```text
CLI
  └── pipeline（编排器）
        ├── start / finish          （起止，可视为特殊 step）
        ├── fixed:*                 （无 adapter）
        ├── slot:*  → adapter(s)    （可 fallback）
        └── 状态文件 + 任务目录
```


| 层                | 职责                                                                                                   |
| ---------------- | ---------------------------------------------------------------------------------------------------- |
| **pipeline**     | 读 CLI 与状态；决定下一步；调用某个 step；根据 step 结果更新编排态；处理分支／循环；支持 `--from`／`--only`；**不**做具体 demux／API            |
| **fixed / slot** | 并列 step：读本步 input → 执行 → 校验 → **写入 assets** → 向 pipeline **return 本步结果**（成功／失败／可重试等）。**禁止调用其他 step** |
| **adapter**      | 仅挂在 slot 下：被动接收规范化输入；写媒体文件到 `tmp/<step>/`；**return** 契约产物（含 path／sha256／size_bytes）。**不写状态文件，不碰正式路径**                 |


### 1.1 硬规则

1. step 与 step **不互相调用**；demux 作业末尾不得出现「进入 slot:sep」。下一步只由 pipeline 根据状态与流程图决定。
2. adapter **只 return**；由 **slot**（在 pipeline 调度下）把成功结果写入 assets，再向 pipeline 报告成功。
3. fixed 无 adapter，但仍是 step：自己算、写文件、写 assets、return 结果。
4. 大文件落在任务目录；状态里只存文件引用（path + sha256 + size_bytes）及标量字段。
5. 路径均为相对任务根；费用 CNY、精度 `0.00000001`（见 assets 文）。

### 1.2 pipeline 主循环（逻辑）

```text
loop:
  若 CLI 指定 --only STEP：只跑该步（校验 input 已就绪），然后结束
  否则根据状态选择 next_step（见 §3）
  若 next_step == finish：收尾并退出
  标记步骤 running / 加锁
  调用 step.run(从状态注入的 input)
  若失败：按错误码决定停或（仅 slot）fallback 换 adapter 重试本步
  若成功：step 已写 assets；pipeline 更新步骤 done、清锁、记费用汇总指针
  继续 loop
```

step 标识：业务名原样保留，不论词性：`demux`、`sep`、`asr`、`translation`、`tts`。自拟步骤用名词：`clipping`、`duration_fitting`、`alignment`、`mixing`。

本文的 pipeline 是**编排式**：由 pipeline 调度各 step，step 之间不串联调用。不是「上一步结尾跳进下一步」的链式写法。首版实现为进程内编排循环即可。

---

## 2. step 结果约定（对 pipeline）

每个 step 向 pipeline return 至少：

```text
ok: 布尔
error_code: 可选；取值只能是 §6.1 表中的码
message: 可选
# slot 成功时还可带：
adapter_id: 实际采用的 adapter id（写入 ledger，不写入句级 assets）
```

assets 的写入在 step **return ok 之前**完成；失败时不得留下半套已提交字段。adapter 只写 `tmp/<step>/`，正式路径由 slot 校验后移入（见目录文档 §4.4）。锁与覆盖规则见 §6。

---

## 3. 控制流（pipeline 拥有，step 不拥有）

主链（首版串行。依赖上 `clipping` 与 `translation` 在 asr 之后互不依赖，都完成才能 `tts`；首版不并行）：

```text
start → demux → sep → asr → clipping → translation → tts → duration_fitting
         →（见下分支）→ alignment → …（每句对齐完成后）→ mixing → finish
```

### 3.1 duration_fitting 之后（按句）

由 **pipeline** 读该句各 attempt 的 `fitting_ratio` 与已尝试次数（默认：首次 + 最多再 2 次重译重 TTS，即 attempt 最大为 3）。合格带默认约 `[0.8, 1.2]`（含边界），以项目冻结配置为准。


| 条件                      | pipeline 动作                                                                                                                |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| 当前 attempt ratio 落在合格带内 | 该条 `selection=fitting_pass`，其余已有 attempt 保持／标为 `rejected`；`selected_attempt=当前` → 调度 **alignment**（该句）                         |
| 不合格且次数未到                | 当前 attempt 标 `rejected` → 调度 **translation**（新 attempt≥2；本批仅不合格句，每句带 `history` 与全文 `transcript`）→ 再 **tts** → 再 **duration_fitting** |
| 不合格且次数已到                | **不**默认采用最后一次。在该句**全部** attempt 中，选 **最接近合格带** 的一条：`selection=forced`，`selected_attempt=该条`；其余全部 `rejected` → 调度 **alignment** |


**「最接近合格带」**：对合格带 `[lo, hi]`，每条 attempt 的距离为  

- ratio ∈ `[lo, hi]` → 0（本分支不会出现）  
- ratio `< lo` → `lo - ratio`  
- ratio `> hi` → `ratio - hi`

取距离最小者。若距离相同，取 `|ratio - 1.0|` 更小者；仍相同则取 **attempt 编号较小** 者。

`switcher`／`switcher2` 是流程图上的分支，**不是**独立 step 程序；实现为 pipeline 内分支逻辑。

### 3.2 句级与整片

- `asr`／`clipping`：一次处理整片（写出全部 `sentences[]` 或按实现分批，但一步语义完整）。
- `translation`／`tts`／`duration_fitting`／`alignment`：可按句或按批；pipeline 负责「还有未对齐的句则继续」，全部句都有 `aligned_audio` 后再 **mixing**。
- 句级进度**不**靠 `run.steps.<step>.status` 判断句子走到哪。只看该句 assets 里哪些键已经有值（见状态文件「句级进度」）。`steps.*.status` 对这四步只表示当前进程是否正在执行该 step。
- 具体批大小实现可调；控制权仍在 pipeline。首版外部并发见目录文档出厂值。

### 3.3 失败即停

- ASR 得到 **0 句**，或任一句原文为空／仅空白：任务 `failed`，报错退出，不进入 clipping 及之后。
- 任一句子在 translation／tts／duration_fitting／alignment 上无法得到该步所需产物（含该句 fallback 全部失败）：任务 `failed`，报错退出。**不**跳过该句，**不**进入 mixing，**不**把缺句成片标为完成。
- 已写入的句级产物与 ledger 保留，便于修好后续跑（完整产品可续跑；**v0.1.0 不做续跑**，失败任务需重新 `run` 开新目录）。

### 3.4 句子顺序与重叠

- `sentences[].id` 按 `start_ms` 升序从 1 编号。
- 允许相邻句时间窗重叠（多说话人）。clipping 各切各的；mixing 按 `start_ms` 叠加；SRT 按 `start_ms` 排序输出。

### 3.5 `--from`／`--only`

- `--only <step>`：仅跑该 step；对句级步骤默认处理全部缺该步键的句子，可加 `--sentence <id>` 收窄。input 必须已在 assets 中且校验通过。
- `--from <step>`：从该 step 起按 §3 走到 finish（或失败停止）。
- 重跑时的覆盖／保留见 §6.2。

---

## 4. slot 与 adapter

### 4.1 slot 通用作业

1. 从状态（或 pipeline 注入）读取本步 input，校验齐全。
2. 按本任务冻结的 `run.slots.<slot>.order` 依次调用 adapter。第一项为默认，其后为 fallback。创建任务时从 `config.yaml` 抄入；未配置则用 `constants.py` 的出厂顺序。运行中不回读全局配置。
3. adapter：转格式（若需要）→ 调外部 API → 写 `tmp/<step>/` → return 产物对象。
4. 遇可 fallback 错误：试下一个 adapter；全部失败则本步失败。
5. 成功：slot 校验后移入正式路径；写入 assets 对应字段；追加 ledger 并重算 `assets.cost`；return ok + `adapter_id`。

错误分类与 fallback 规则见 §6.1。

### 4.2 本版 slot 列表


| slot        | 典型 adapter 方向（名未定）                                 |
| ----------- | -------------------------------------------------- |
| sep         | Demucs／SAM／MVSep 等；多轨须在 adapter 内合成单一 `non_speech` |
| asr         | Whisper／Fun-ASR／Qwen 等                             |
| translation | 出厂默认 `deepseek/deepseek-flash`（模型 `deepseek-flash`） |
| tts         | IndexTTS／Fish／OpenRouter Fish 等                    |


---

## 5. 各 step 规格

路径前缀省略 `assets.`。`.*` 表示文件引用三件套（path／sha256／size_bytes）。

---

### 5.1 start

**类型：** 起止（由 pipeline／CLI 驱动）

**input（CLI／交互）：**

- 视频文件 → `src.video.*`
- 原语言 → `src.language`
- 目标语言 → `tgt.language`

**output：**

- `src.video.*`、`src.language`、`tgt.language`
- 任务目录与状态文件已创建

**程序作业：**

1. 解析参数。v0.1.0：缺参直接报错退出，不做交互问答（见 [v0.1.0 开发计划](2026-09-22_magicdub-cli_v0.1.0开发计划.md)）。
2. 创建**新**任务目录与状态文件骨架（v0.1.0 不打开已有任务、不续跑）。
3. 复制视频入任务目录，计算校验，写入 `src.video.*`。
4. 写入 `src.language`、`tgt.language`。
5. return ok。（**不**调度 demux）

---

### 5.2 fixed:demux

**input：** `src.video.`*  
**output：** `src.audio.`*、`src.silent_video.*`

**程序作业：**

1. 用 ffmpeg 将视频分为纯音频与无声画面，写入约定相对路径。
2. 计算校验，写入 `src.audio.*`、`src.silent_video.*`。
3. return ok。

---

### 5.3 slot:sep

**input：** `src.audio.`*  
**output：** `src.speech.`*、`src.non_speech.*`

**程序作业：**

1. 注入 `src.audio.*` 给 adapter（按 fallback）。
2. adapter 分离说话／非说话（或等价轨并合成 `non_speech`），文件落盘，return 两套文件引用。
3. slot 写入 `src.speech.*`、`src.non_speech.*`，更新 `cost.cost_of_sep`。
4. return ok + adapter_id。

---

### 5.4 slot:asr

**input：** `src.speech.`*（及 `src.language` 等配置）  
**output：**

- `src.transcript`
- `sentences[]` 中每句：`id`、`start_ms`、`end_ms`、`speaker_id`、`src.text`

**程序作业：**

1. adapter 自行将输入转成所需格式并调用 ASR。
2. return 全文与句级列表；slot 写入上述字段（此时尚无 `src.audio`／`src.audio_duration`）。**0 句，或任一句 `src.text` 为空／仅空白 → `input_invalid`，任务失败**（v0.1.0 同此）。
3. 更新 `cost.cost_of_asr`；return ok + adapter_id。

---

### 5.5 fixed:clipping

**input：** `src.speech.`*；每句 `id`、`start_ms`、`end_ms`  
**output：** 每句 `src.audio.`*、`src.audio_duration`

**程序作业：**

1. 对每句用 `start_ms`／`end_ms` 从 `src.speech` 切出原句音频。窗口 ≤ 0（含 `end_ms == start_ms`）→ `input_invalid`。
2. 写入 `src.audio_duration := end_ms - start_ms`（**计算值**，非文件探测时长）。
3. 切句是否成功等校验在本步内完成。
4. return ok。

---

### 5.6 slot:translation

**同一 adapter 入口，两种请求负载。** 不拆「首译」「修正」两个函数。看每句 `history` 是否为空即可：空 = 首译；非空 = duration_fitting 回环修正。两种场景都**必带** `src.transcript` 全文，让 LLM 在理解整篇语境下译句。

**input（slot 组装后交给 adapter）：**

```text
transcript: 文本                      # assets.src.transcript，必带
src_language / tgt_language
sentences: [
  {
    id
    src_text                          # 原句
    target_duration_ms                # = src.audio_duration
    attempt                           # 本轮要写入的 attempt 编号
    history: [                        # 首译 = []；修正 = 已 rejected 的各稿
      { attempt, text, tts_duration_ms, fitting_ratio }
    ]
  }
]
```

**output：** `[{id, text}]`；slot 写入各句对应 `tgt[]` 的 `attempt`、`text`（尚无 audio）。

**程序作业：**

1. pipeline 指定本批句子与 `attempt`。首译：全部句、`attempt=1`、`history=[]`。修正：仅不合格句、`attempt≥2`，从该句已 `rejected` 的 `tgt[]` 填 `history`（含 `text`、`audio_duration`→`tts_duration_ms`、`fitting_ratio`）。
2. adapter **一个入口** `translate(transcript, sentences, …)`：提示词固定三段——系统（忠实、口语、只出 JSON）；全文（`transcript`，说明仅作语境、勿整篇翻译）；任务（逐句 `id`／原文／原句时长；若 `history` 非空再追加上一稿文本、TTS 实测时长、比值，并说明比值>1 缩短、<1 加长，意思不变）。返回 `[{id, text}]`。
3. 同一次请求内各句 `attempt` 同属一类（首译全为 1，或修正全为 ≥2）。slot 按 `id` 写回；费用：本批 `attempt==1` → `cost_of_translation`；本批 `attempt≥2` → `cost_of_duration_fitting.translation`（一次请求记一条 ledger；修正批内各句 attempt 若不同，整笔归 fitting.translation）。
4. return ok + adapter_id。

---

### 5.7 slot:tts

**input：** 该句 `src.audio.`*、`src.text`；当前 attempt 的 `text`  
**output：** 该 attempt 的 `audio.`*（未对齐）

**程序作业：**

1. adapter 用参考音频与译文合成；自行转码；return 文件引用。
2. slot 写入 `tgt[attempt].audio.*`。
3. 费用：`attempt==1` → `cost_of_tts`；`attempt≥2` → `cost_of_duration_fitting.tts`。
4. return ok + adapter_id。

---

### 5.8 fixed:duration_fitting

**input：** 当前 attempt 的 `audio.`*；该句 `src.audio_duration`  
**output：** 该 attempt 的 `audio_duration`、`fitting_ratio`。**不写** `selection` 或 `selected_attempt`。

**程序作业：**

1. 探测 TTS 音频得 `tgt.audio_duration`。
2. `fitting_ratio := tgt.audio_duration / src.audio_duration`。
3. 写入上述两字段。return ok。pipeline 读 `fitting_ratio` 与冻结阈值做分支（§3.1）。

**本步不算**切句校验；**不**改用文件探测值替代 `src.audio_duration`。

---

### 5.9 fixed:alignment

**input：** `selected_attempt` 对应那条的 `audio.*`（不是「最后一条」）；`src.audio_duration`  
**output：** 该条的 `aligned_audio.*`

**程序作业：**

1. 将 `selected_attempt` 的未对齐音频拉伸／压缩／补齐到 `src.audio_duration`；对齐后时长与目标差值不超过 1 ms。
2. 写入该条的 `aligned_audio.*`。该条的 `selection` 已由 pipeline 写成 `fitting_pass` 或 `forced`。
3. return ok。

---

### 5.10 fixed:mixing

**input：** 各句已采用的 `aligned_audio`、`text`、`start_ms`／`end_ms`；`src.non_speech.`*；`src.silent_video.*`  
**output：** `tgt.final_video.`*、`tgt.final_audio.*`、`tgt.srt.*`

**程序作业：**

1. 任一句子缺少 `selected_attempt` 或对应 `aligned_audio` 时不得开始；应已在更早步骤失败退出。
2. 按时间轴把各句采用稿与 `non_speech` 混音，再与无声画面合成。
3. 成片去掉容器与轨道中的描述性元数据、章节、封面及其他额外轨道。保留播放所需的时间轴、旋转、色彩／HDR 与格式标识。视频码流不重编码。
4. SRT 使用各句最终采用的译文与对齐后的时间。显示文本把中英文逗号（`,，`）和句号（`.。`）换成半角空格，合并连续空格并去掉行首尾空格；保留问号、感叹号和数字中的小数点。不把字幕烧进画面。
5. 写入 `exports/final.mp4`、`exports/final.wav`、`exports/final.srt`。
6. return ok。

---

### 5.11 finish

**类型：** 起止

**input：** `tgt.final_video.`*、`tgt.final_audio.*`、`tgt.srt.*`（及费用汇总可读）  
**output：** 任务 `done`；向 CLI 交付三个最终文件的路径与费用摘要

**程序作业：**

1. 校验三份最终产物存在且校验通过，且句子数与 ASR 句数一致。
2. 标记 `run.status=done`；打印路径与费用。
3. return ok。任一句未完成时不得进入本步（见 §3.3）。

---

## 6. 错误、覆盖与锁 — 已定

### 6.1 错误码

同一 adapter 先对 `external_retryable` 最多再试 **2** 次（连首次共 3 次）。仍失败再 fallback。`external_fallback` 不重试当前 adapter，直接下一项。`external_fatal` 与 `input_invalid` **不** fallback，任务失败退出。

| 码 | 何时 | 下一步 |
| --- | --- | --- |
| `external_retryable` | 超时、连接失败、HTTP 429／500／502／503／504 | 同一 adapter 有限重试，然后 fallback |
| `external_fallback` | HTTP 402、明确的额度用尽、模型暂不可用 | 下一个 adapter |
| `external_fatal` | HTTP 401、内容安全拒绝 | 任务失败 |
| `input_invalid` | 输入不符合该 step 契约（缺文件、0 句、校验和不符） | 任务失败 |
| `adapter_exhausted` | 该 slot 的 order 全部失败 | 任务失败 |

### 6.2 重跑与覆盖

- 输入指纹未变，且正式路径上的文件 `sha256`／`size_bytes` 与 state 一致：跳过该产物，不重复付费；该 step 记 `skipped`。
- 指纹变了，或文件校验失败：允许重做并覆盖正式路径。旧 ledger 行不删，新请求追加。
- 用户显式 `--force`：即使指纹未变也重做。同样只追加 ledger，不删历史费用。
- 指纹算法：该 step 全部输入文件的 `sha256` 与全部输入标量（如译文、语言、adapter id）按固定顺序拼接后再 `sha256`。句级步骤按句计算，存入该句对应 `tgt[]` 条目或句级字段（字段位置由 v0.2 实现时定），`run.steps.*.input_fingerprint` 只存整片步骤。

### 6.3 锁

**落点（已定）：** 任务根独立文件 `run.lock`（JSON：`holder`＝`hostname:pid`、`step`、`acquired_at`）。`state.json` 的 `run.lock` 为镜像，便于查看；**占用检测以文件为准**。

- 同一主机且 pid 已不存在：启动时自动清除文件与镜像，继续跑。
- 同一主机且 pid 仍在：拒绝第二个进程。
- 另一台主机：不自动清。完整产品可提供 `lock clear`；**v0.1.0 不做该命令，只报错**。

### 6.4 从 skills 继承的行为

- **IndexTTS adapter**（不是全部 TTS）：有转写且非静音、参考短于 0.5 秒时，只在尾部补静音到 0.6 秒；原参考保留。Fish 等 adapter 不套用这条。
- **mixing**：SRT 标点改空格、成片描述性元数据清理，见 §5.10。不做口型修正。

---

## 7. 与文档的关系

| 文档 | 内容 |
| --- | --- |
| 本文 | pipeline 编排、失败即停、错误码、锁、fitting 分支 |
| 目录与路径 | `config.yaml`、凭据、并发出厂值、adapter 目录 |
| 状态文件 | 全字段；句级进度看键 |
| 流程图 | 产物与分支示意 |

## 8. 仍待定／由分版计划收窄

- 完整产品里的续跑、`--from`／`--only`、指纹跳过、fallback 顺序等：总设计保留描述；**当前实现范围以 [v0.1.0 开发计划](2026-09-22_magicdub-cli_v0.1.0开发计划.md) 为准**（v0.1.0 不做续跑）。
- 下载上游（本 CLI 首版不做）
- `run.status=cancelled` 的产生方式（v0.1.0 不产生）
