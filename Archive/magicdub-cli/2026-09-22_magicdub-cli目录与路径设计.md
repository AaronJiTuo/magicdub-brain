# magicdub-cli 目录与路径设计

> 草稿。与 [pipeline 设计](2026-09-22_magicdub-cli_pipeline设计.md)、[assets 字段](2026-09-21_magicdub-cli状态文件assets字段设计.md)、[流程图](2026-09-20_magicdub-cli流程图.md) 配套。  
> step 名：业务名原样保留（`demux`、`sep`、`asr`、`translation`、`tts`）；自拟步骤用名词（`clipping`、`duration_fitting`、`alignment`、`mixing`）。

---

## 1. 三类位置（已定原则）

| 位置 | 作用 | 与程序安装的关系 |
| --- | --- | --- |
| **程序安装** | 可执行入口 + 隔离依赖 | 由包管理安装，**不**放在配置目录下 |
| **用户配置** | CLI 设置、slot／fallback 等 | `~/.magicdub/cli/` **只放配置** |
| **任务目录** | 单次译制的状态与媒体产物 | 用户可见；与安装／配置分离 |

---

## 2. 用户配置：`~/.magicdub/cli/`

**已定：`~/.magicdub/cli/` 只用来放配置，不用来放程序。**

产品线共用根目录 `~/.magicdub/`，用子目录区分入口（类似 Cursor 的 `~/.cursor` + 不同文件／子路径）：

```text
~/.magicdub/
  cli/                 # magicdub-cli 配置（仅此）
    config.yaml        # 用户可改项；见 §2.1
  skills/              # 未来：magicdub-skills 配置迁入（现网仍可能扁平在根上，迁移另案）
  credentials          # 共用 API Key；cli／skills 只读，互不覆盖对方私有状态
```

- CLI **只写** `cli/` 下自有文件；**不写** skills 安装／升级状态。
- 凭据：优先 `~/.magicdub/credentials`；也可用同名环境变量覆盖。若 skills 旧布局仍有 Key，可 **只读** 兼容，不写回。
- **不**把合格带、工作目录、adapter 顺序放进 `.env` 或凭据文件。

### 2.1 数值放哪 — 已定

| 层 | 位置 | 内容 |
| --- | --- | --- |
| 程序默认 | 包内 `constants.py` | 出厂值与路径骨架。用户未配置时使用 |
| 用户设置 | `~/.magicdub/cli/config.yaml` | 可改默认；只影响**之后新建**的任务 |
| 任务冻结 | 该任务 `state.json` 的 `run.fitting`、`run.slots` | 创建任务时从「配置，否则常量」抄入；之后不跟全局配置变 |

`config.yaml` 字段（未写的键用 `constants.py`）：

```yaml
projects_dir: null          # null = 各平台 …/MagicDub/cli/
fitting:
  lower_ratio: 0.8          # 含边界
  upper_ratio: 1.2
  max_rewrites: 2           # attempt 最多 1+2
concurrency:                # 同时在飞的外部请求数
  sep: 1
  asr: 1
  translation: 3
  tts: 3
slots:                      # 第一项为默认，其后为 fallback
  sep: []
  asr: []
  translation:
    - deepseek/deepseek-flash   # 出厂默认；模型名 deepseek-flash
  tts: []
```

`sep`／`asr`／`tts` 的出厂列表在对应 adapter 登记 id 之后写入 `constants.py`。未在 `config.yaml` 里写的 slot 用出厂列表。`translation` 的出厂默认已定：`deepseek/deepseek-flash`（DeepSeek 的 `deepseek-flash`，一次 LLM 请求）。

**配置合并（已定）：** 某 `slots.<name>` **缺键** → 用 `constants.py`；若写了 **空列表 `[]`** → 视为无效配置，**报错退出**（不静默当成「无 adapter」）。

### 2.2 凭据文件 — 已定

`~/.magicdub/credentials`，一行一个 `KEY=value`，`#` 开头为注释。权限仅用户可读。同名环境变量优先于文件。

```text
FAL_KEY=
DASHSCOPE_API_KEY=
FISH_API_KEY=
OPENROUTER_API_KEY=
MVSEP_API_KEY=
DEEPSEEK_API_KEY=
```

adapter 只声明自己要的键名，不在目录里放 env 文件。

只留在 `constants.py`、不进 `config.yaml` 的：配置根与凭据路径、任务内相对路径（`media/`、`exports/`）、CNY 与 8 位小数、`schema_version`、目录命名规则。

---

## 3. 程序安装（一句命令）

采用 **`uv tool install`**（或等价 pipx）从 GitHub／PyPI 安装时，默认落点由 uv 决定，**不在** `~/.magicdub/` 下：

| 内容 | 典型默认位置（macOS／Linux） |
| --- | --- |
| 命令入口 | `~/.local/bin/`（须在 `PATH`） |
| 工具环境与代码 | `~/.local/share/uv/tools/<包名>/` |

本机可用 `uv tool dir`、`uv tool dir --bin` 查看。用户可用 `UV_TOOL_DIR`／`UV_TOOL_BIN_DIR` 覆盖，属用户环境，非产品配置约定。

入口命令名：**`magicdub-cli`**（与 skill 名 `magicdub` 区分）。

不在 `~/.magicdub/cli/` 或 `~/.magicdub/install/` 下放程序（若将来改版本化自管安装，须另开兄弟目录如 `install/cli/versions/`，且仍与 `cli/` 配置分离——当前不采用）。

---

## 4. 任务父目录与任务根

### 4.1 工作目录（任务父目录）默认 — 已定

与 skills 同属各平台「视频」可见区，但 **单独一级 `cli/`**，避免与 skills 项目平铺混放：

| 平台 | 默认工作目录 |
| --- | --- |
| macOS | `~/Movies/MagicDub/cli/` |
| Windows | `%USERPROFILE%\Videos\MagicDub\cli\`（即用户「视频」文件夹下；用 pathlib 解析为 `Path.home() / "Videos" / "MagicDub" / "cli"`） |
| Linux 及其他 | `~/Videos/MagicDub/cli/`；若可用则优先 `xdg-user-dir VIDEOS` 再拼 `MagicDub/cli`，否则回退 `~/Videos/MagicDub/cli/` |

可在 `~/.magicdub/cli/`（Windows 为 `%USERPROFILE%\.magicdub\cli\`）配置中覆盖。skills 项目仍在上一级 `MagicDub\`（非 `cli\`）；**单个任务格式不可混用**，CLI 不打开 skills 的 `project.json` 项目。

WSL：按 **Linux 侧 home** 用 Linux 规则；若任务故意放在 `/mnt/c/Users/.../Videos/...`，须用户配置指定，不自动跨到 Windows 资料库。

### 4.2 任务根命名与 task_id — 已定

**目录名（给人看）：**

```text
<安全化视频 stem>_<YYYYMMDD_HHMMSS>/
```

- stem：去扩展名；只保留 `[A-Za-z0-9_-]`，其它变 `_`；过长截断（建议最多 60 字符）。
- 时间为**本地**创建时刻。
- 若目录已存在：追加 `_` + 4 位小写随机（如 `_a1b2`）。

例：`stevejobs_keynote_20260922_163045/`

**task_id（给程序看，已定）：**

- 使用 **ULID**（或等价可排序的唯一 id）。
- 写入 `state.json` 顶层：`engine: magicdub-cli`、`task_id`、`title`（展示用 stem／原文件名）、`created_at`（ISO-8601）。
- **权威身份是 task_id**，不是文件夹名；用户改名目录不改 id。
- 同一源视频多次译制 = 多个任务、多个 id。

`start` 创建示例：

```text
macOS:    ~/Movies/MagicDub/cli/<stem>_<YYYYMMDD_HHMMSS>/
Windows:  %USERPROFILE%\Videos\MagicDub\cli\<stem>_<YYYYMMDD_HHMMSS>\
Linux:    ~/Videos/MagicDub/cli/<stem>_<YYYYMMDD_HHMMSS>/
```

目录内须能识别引擎；**禁止**用 CLI 跑 skills 的 `project.json` 项目（反之亦然），除非将来提供显式迁移。

### 4.3 任务根内部布局

```text
<task_root>/
  state.json
  run.lock          # 进程锁文件；与 state.run.lock 镜像，检测以本文件为准
  media/
    src/
    sentences/
  exports/
  tmp/
```

状态中的 `path` 一律为**相对任务根**、使用 `/`（见 assets 设计）。

### 4.4 各 step 输出文件约定 — 已定

#### 原则

1. **路径由 pipeline／step 定死**（下表）。adapter **只写 `tmp/<step>/`**，不碰正式路径；由 slot 校验后移入正式路径。
2. **先写 `tmp/`，成功后再移到正式路径并算 sha256／size_bytes，最后写 state**；失败不更新正式 path。
3. **同一逻辑产物路径固定**，便于 `--from`／`--only` 覆盖；不在文件名里加随机串（句级 attempt 用 attempt 编号区分版本）。
4. 音频中间／句级默认 **WAV**；成片 **MP4**；字幕 **SRT**；`src.video` 保留源扩展名。
5. 状态里的文本（transcript、句 text 等）**以 state 为准**，不强制另存 `.txt`（调试需要时可另加，非契约）。

#### 路径表（相对任务根）

| step | 产物 | 相对路径 |
| --- | --- | --- |
| start | 源视频副本 | `media/src/video.<源扩展名>` |
| demux | 纯音频 | `media/src/audio.wav` |
| demux | 无声画面 | `media/src/silent_video.mp4` |
| sep | 人声／说话 | `media/src/speech.wav` |
| sep | 可混回背景 | `media/src/non_speech.wav` |
| asr | （句级与全文） | 写入 state；无必需媒体文件 |
| clipping | 句原声 | `media/sentences/<sentence_id>/src.wav` |
| translation | 译文 | 写入 state `tgt[].text` |
| tts | 未对齐配音 | `media/sentences/<sentence_id>/tgt/attempt_<n>.wav` |
| duration_fitting | 时长字段 | 只更新 state（`audio_duration`／`fitting_ratio`）；`selection` 由 pipeline 写 |
| alignment | 对齐配音 | `media/sentences/<sentence_id>/tgt/attempt_<n>.aligned.wav` |
| mixing | 成片／母版／字幕 | `exports/final.mp4`、`exports/final.wav`、`exports/final.srt` |

说明：

- `<sentence_id>`：与 state 中 `sentences[].id` 一致，十进制、无必要补零（实现可统一 `%d`）。
- `<n>`：`tgt[].attempt`，从 1 起：`attempt_1.wav`、`attempt_2.wav`…
- `tmp/` 建议：`tmp/<step_name>/…`，文件名可与正式名相同，移入时覆盖正式路径。
- adapter 若需特殊采样率／封装：可在 `tmp/` 内自用转码文件，**对外契约路径仍是上表**（正式交付格式按上表；若某 adapter 只能出其它格式，由 adapter／slot 转成约定格式再提交）。

#### 与 assets 字段对应

正式路径写入对应 `assets.*.path`（及 sha256／size_bytes）。例如 `assets.src.speech.path = "media/src/speech.wav"`。

## 5. 源码仓库结构（程序目录）— adapter 位置已定

adapter **随程序包发布**，放在安装后的包内，不放进 `~/.magicdub/`，也不放进任务目录。

按 **slot 分子目录，每个 adapter 再独占一个目录**（一个外部 API 一套文件，不限单文件）。`adapter_id` 写在该目录的 `__init__.py` 里（如 `fal/index-tts-2`），目录名不用斜杠。

```text
magicdub-cli/
  pyproject.toml
  README.md
  src/magicdub_cli/
    __init__.py
    __main__.py
    cli.py
    pipeline/                         # 只调度 step，不 import 具体 API
    steps/
      fixed/                          # demux.py, clipping.py, duration_fitting.py, alignment.py, mixing.py
      slots/                          # sep.py, asr.py, translation.py, tts.py
                                      # slot 按 run.slots.*.order 调 registry，写 assets
    adapters/
      base.py                         # 统一入口：接收规范化输入，return 产物；不写 state
      registry.py                     # adapter_id → 实现
      sep/
        demucs/
          __init__.py
        sam_audio/
          __init__.py
        mvsep_dnr_v3/
          __init__.py
      asr/
        whisper/
          __init__.py
        fun_asr/
          __init__.py
      translation/
        deepseek_flash/             # id: deepseek/deepseek-flash
          __init__.py
      tts/
        fal_index_tts_2/              # id: fal/index-tts-2
          __init__.py
        fish_s2_1_pro/
          __init__.py
        openrouter_fish_s2_1_pro/
          __init__.py
    state/
    media/
  tests/
    adapters/                         # 与上面 adapter 目录对应
    steps/
```

约定：

- 新增 API = 在对应 slot 下新建一个 adapter 目录，并在 `registry.py` 登记；不改 pipeline 主循环。
- 该目录内可以有多个模块（请求、转码、响应解析等）；对外只暴露 `__init__.py` 里的实现。
- slot 与 adapter **分开**：`steps/slots/tts.py` 负责 fallback 与写状态；`adapters/tts/<adapter>/` 只做请求与格式转换。
- 首版不做「任务目录里丢目录即热插」；以后若要第三方 adapter，再用入口点（entry points）挂到同一个 registry，目录仍以包内为准。
---

## 6. 与 skills 路径关系（结论摘要）

| 项 | 结论 |
| --- | --- |
| `…/MagicDub/cli/`（Mac Movies／Win&Linux Videos） | **已定**为 CLI 默认工作目录；与 skills 项目隔离 |
| `~/Movies/MagicDub` 整根平铺 CLI 任务 | 已否定 |
| `~/.magicdub` 整根当 CLI 配置 | 不好；用 `cli/` 子目录 |
| `~/.magicdub/cli/` 装程序 | **已否定**；只放配置 |
| 共用 API Key | 可以；建议根级 credentials + 只读 |

---

## 7. 另文／未定

- skills 从扁平 `~/.magicdub/` 迁到 `skills/` 的兼容与迁移
- 可选：按 task_id 的轻量索引（非必需）

状态文件全字段见 [状态文件完整字段设计](2026-09-22_magicdub-cli状态文件完整字段设计.md)；分版本范围见 [v0.1.0 开发计划](2026-09-22_magicdub-cli_v0.1.0开发计划.md)。
