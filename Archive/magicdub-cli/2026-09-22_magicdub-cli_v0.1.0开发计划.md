# magicdub-cli v0.1.0 开发计划

> 目标：**每个 slot 固定一个 adapter，一次新任务从 `start` 串行跑到 `finish`，产出成片、混音母版、SRT。**  
> 本版只服务「跑通并实测」；不做续跑、单步重跑、fallback、并行。实测后再决定要不要加什么。  
> 设计依据：[pipeline 设计](2026-09-22_magicdub-cli_pipeline设计.md)、[状态文件](2026-09-22_magicdub-cli状态文件完整字段设计.md)、[目录与路径](2026-09-22_magicdub-cli目录与路径设计.md)。

---

## 1. 范围

### 1.1 做

| 项 | v0.1.0 |
| --- | --- |
| CLI 入口 | `magicdub-cli run <video> --src <lang> --tgt <lang>`；缺参数直接报错，不做交互问答 |
| 任务生命周期 | **每次 `run` 只创建并跑完一个全新任务目录**；不接受已有任务目录、不续跑、不跳过已付费步骤 |
| pipeline | 串行主循环；句级进度仍按 assets 键推进（本进程内）；失败即停 |
| fixed steps | demux、clipping、duration_fitting、alignment、mixing 全部实现 |
| slots | 每个 slot 只有 **一个** adapter；`run.slots.*.order` 写成单元素数组；实现取 `order[0]` |
| duration_fitting 分支 | 合格／重译重 TTS（≤2 次）／forced 选最接近合格带，三条都做 |
| 状态文件 | 全字段照写，未用到的值填 null；`ledger` 逐请求追加 |
| 配置与凭据 | 读 `~/.magicdub/cli/config.yaml`（可缺省）、`~/.magicdub/credentials`、环境变量 |
| 任务目录 | 各平台默认路径、`<stem>_<时间戳>`、ULID `task_id` |
| 继承行为 | IndexTTS 短参考补静音；SRT 标点改空格；成片元数据清理 |
| 锁 | 任务根独立 `run.lock` 文件，state 内镜像锁字段；同机 pid 死则清、活则拒；他机只报错 |

### 1.2 不做

- 续跑／断点恢复／对已有任务目录再次 `run`
- `--only`、`--from`、`--sentence`、`--force`、`lock clear`
- 任何 slot fallback；遇 `external_fallback`／`adapter_exhausted` 直接任务失败
- `run.status = cancelled`；Ctrl-C → `failed` + `last_error`
- 并行；`concurrency` 读入配置但不生效，实际一律串行（=1）
- `input_fingerprint` 跳过；字段可写 null，**不**据此跳过任何步
- 下载上游、口型修正、第三方 adapter 热插

### 1.3 各 slot 的 adapter

| slot | adapter_id | 目录 | 凭据 |
| --- | --- | --- | --- |
| sep | `fal/demucs` | `adapters/sep/demucs/` | `FAL_KEY` |
| asr | `fal/whisper` | `adapters/asr/whisper/` | `FAL_KEY` |
| translation | `deepseek/deepseek-flash` | `adapters/translation/deepseek_flash/` | `DEEPSEEK_API_KEY` |
| tts | `fal/index-tts-2` | `adapters/tts/fal_index_tts_2/` | `FAL_KEY` |

三个 fal adapter 共用一个 `FAL_KEY`。本版只需两把 key。

### 1.4 本版已钉死的实现约定

| 项 | 约定 |
| --- | --- |
| 配置缺键 | 用 `constants.py` |
| 配置 `slots.<name>: []`（空列表） | **报错退出**，不静默当「无 adapter」 |
| 锁 | 任务根文件 `run.lock`（JSON：holder／step／acquired_at）+ `state.run.lock` 镜像；以文件为准做占用检测 |
| translation 批 | 首译：一次请求带**全部**句、`history=[]`；修正：一次请求带**当前全部不合格句**及各自 history |
| tts | 逐句串行，一次一句 |
| `end_ms == start_ms` 或窗口 ≤ 0 | `input_invalid`，任务失败 |
| ASR 某句 `src.text` 为空／仅空白 | `input_invalid`，任务失败（与 0 句同样严） |
| ASR 0 句 | `input_invalid`，任务失败 |
| start 缺参 | 直接报错；不提示、不问答 |
| 对齐容差 | 对齐后时长与 `src.audio_duration` 差 ≤ 1 ms |
| `speaker_id` | 一律文本 |
| 本版实际错误码 | 主要：`external_retryable`、`external_fatal`、`input_invalid`（同 adapter 可重试最多共 3 次） |

---

## 2. 里程碑

| # | 里程碑 | 验收 |
| --- | --- | --- |
| M0 | 仓库骨架 | `uv tool install .` 后 `magicdub-cli --version` 可跑；目录树与设计一致；`ruff` 通过 |
| M1 | 状态与路径 | state 读写、file_ref、tmp→正式路径、任务目录、ULID、`run.lock`、配置语义；单测覆盖 |
| M2 | start + demux | 新任务：`media/src/{video,audio.wav,silent_video.mp4}` 与 state |
| M3 | sep + asr | Demucs → speech／non_speech；Whisper → sentences；0 句或空文本句失败 |
| M4 | clipping + translation | 每句 src.wav／audio_duration；DeepSeek attempt 1；ledger 有费用 |
| M5 | tts + duration_fitting + 分支 | IndexTTS；ratio 与三分支；attempt 最多 3 |
| M6 | alignment + mixing + finish | `exports/final.{mp4,wav,srt}`；SRT／元数据规则；`run.status=done` |
| M7 | 端到端 | 30～90 秒英文样片**一次新任务**跑通；费用表正确；不测续跑 |

M2～M6 可先离线回放单测，再各做一次真实 API 集成。

---

## 3. 每个里程碑的工作项

### M0 仓库骨架

- `pyproject.toml`：包名 `magicdub-cli`，入口 `magicdub-cli = magicdub_cli.cli:main`，Python ≥ 3.12；依赖至少 `httpx`、`pyyaml`、`python-ulid`
- `src/magicdub_cli/` 按目录设计建模块树（四个 slot 的 adapter 目录）
- `constants.py`：路径骨架、合格带、`max_rewrites`、四 slot 单元素出厂列表、CNY 精度
- `README.md`：安装、两把 key、一行 `run` 示例；注明需系统 `ffmpeg`／`ffprobe`
- `ruff`；`tests/` 骨架

### M1 状态与路径

- state 原子写；`file_ref`／`commit`
- 任务目录命名与 ULID
- 配置：缺键 → constants；空 `slots.*` 列表 → 报错
- 凭据：`KEY=value`，环境变量覆盖
- `run.lock` 文件 + state 镜像；同机死 pid 清除

### M2 start + demux

- 每次 `run` **新建**任务目录；复制视频；写语言与骨架；`running`
- demux：原采样率／声道 float32 WAV；无声 mp4（`-an -c:v copy`）

### M3 sep + asr

- adapter 只写 `tmp/<step>/`；slot commit + ledger
- Whisper：adapter 内转 16 kHz 单声道；`diarize=true`；`speaker_id` 转文本
- 0 句或空文本 → failed

### M4 clipping + translation

- `src.audio_duration := end_ms - start_ms`；窗口 ≤ 0 → failed
- 同一 `translate` 入口；首译全句一批；修正不合格句一批 + history
- 费用按本批 attempt 归类

### M5 tts + duration_fitting + 分支

- IndexTTS 短参考尾补静音；逐句串行
- fitting 只写时长与 ratio；pipeline 写 selection／selected_attempt

### M6 alignment + mixing + finish

- atempo（必要时分段）；差 ≤ 1 ms
- final.wav 48 kHz float32；final.mp4 AAC 320k、画面 copy；清描述性元数据；SRT 标点规则
- finish：校验三文件与句数；打印路径与费用

### M7 端到端

- 样片 30～90 秒英文演讲（可用 Jobs 前 90 秒）
- 通过：`final.mp4` 可播且时长与源一致；SRT 条数 = 句数；`cost.total` = ledger 可加总部分之和
- **不**要求对同一目录再次 `run`

---

## 4. 与总设计的关系

- pipeline／状态／路径文档描述的是完整产品能力（含续跑、`--from`、指纹等）。
- **实现本版时以本文为准**：总设计里超出 §1 的能力一律不实现、不验收。
- 状态字段仍可按全 schema 写入（未用填 null），避免以后改 schema；但本版行为不依赖续跑相关字段。
