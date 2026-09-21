# MagicDub Brain

这是 MagicDub 项目的 **`*-brain` 仓库**。它不是代码仓库，而是项目的 **「思考 — 沉淀 — 交付」系统**：把零散灵感、外部信息、与 AI 的对话，逐步整理成可执行的设计与文档，并作为项目落地实现的规范性事实来源。

> 范围约束：本项目 **永远不做唇形/口型修正**，仅追求「译制片式」音频替换与时间轴对齐体验。

## 这个仓库是给谁看的？

- **主要给 AI agent 看**：让任何一个 agent 在介入项目时，能快速了解项目背景、规范、现实状态和历史变化。
- **人类重点看 `Releases/`**：定稿内容集中在这里；当前实际状态从 `.records/CURRENT.md` 进入。

如果你是一个刚接入本项目的 AI agent，请先阅读 [`AGENTS.md`](./AGENTS.md)。

如果要让 agent 正式接手或汇报当前状态，可以直接复制：

> 请先读 AGENTS.md，并按 .skills/brain-handoff/SKILL.md 接手当前项目。如果我同时给出了具体任务且不存在会实质改变执行结果的歧义，请在简要报告理解后直接继续，不要等待重复确认。

## brain 如何工作

```text
已经确认、应当遵循的规范 ─→ Releases/
项目当前实际状态         ─→ .records/CURRENT.md
重要决策与状态变化       ─→ .records/events/
尚未定稿或等待吸收的内容 ─→ Drafts/
已被替代或完成使命的内容 ─→ Archive/
```

- `Releases/` 表达项目“应该是什么、应当怎样做”。
- `.records/CURRENT.md` 表达项目“现在实际怎样”，并标记规范与现实的漂移。
- `.records/events/` 保存重要结果的追加式历史证据。
- `Drafts/` 保存仍在探索、迭代或等待吸收的内容。
- `Archive/` 保存被替代或只在追溯时需要的历史。

`.brain-template.json`、`AGENTS.md` 与 `.skills/` 共同组成 agent 使用的模板协议，通常不需要用户手工维护。

## 推荐工作流

1. 日常任务先从 `Releases/` 和 `.records/CURRENT.md` 建立足够上下文。
2. 未定稿材料进入 `Drafts/`；重要决策、实质成果和状态变化按 checkpoint 协议留痕。
3. 草稿成熟到读者无需追问也能照做时，整理进入 `Releases/`，写清来源、证据与替代关系。
4. 已完全吸收、被替代或完成使命的材料进入 `Archive/`；历史 Record 保持不可变。

## 当前方向

2026-09-13 起，MagicDub 以自用 `magicdub-skills` 为主线发布与维护；2026-09-22 起另定本地 CLI 线 `magicdub-cli`（见 [系统设计](Releases/06_magicdub-cli系统设计.md)）。`magicdub-cloud` 已取消，原 `magicdub` 暂时保留、当前不推进；未来确有对外 Web 需求时，再决定重启 `magicdub` 或新建仓库。

## 项目入口建议

- 首先阅读 [MagicDub 项目总览](Releases/00_MagicDub项目总览.md)，注意其中的方案适用范围。
- [magicdub-cli](https://github.com/shishengkai/magicdub-cli)：按 [系统设计](Releases/06_magicdub-cli系统设计.md) 第 2 节（v0.1.0）从 M0 实现。
- [magicdub-skills](https://github.com/shishengkai/magicdub-skills)（原 `magicdub-skill`）按技能集发展。[正式项目规划](Releases/05_magicdub-skill项目规划.md)已于 2026-09-12 统一最新决定：首版为译制、安装配置、升级三个 skill，采用 Python 3.12+ 与自身 API 调用程序；当前先跑通短视频，多音轨 / 多声道高级处理和长片延后；多人、候选模型选择、强制对齐和双币种费用要求见该文。当前实现与验收证据仍以 [CURRENT](.records/CURRENT.md)为准。
- 再阅读 [CURRENT](.records/CURRENT.md)，了解当前实际状态与文档漂移。
- 仅在追溯历史 Web 方案时按需阅读 [技术框架](Releases/01_MagicDub技术框架.md)、其他相关 Release 和少量必要 Record；这些方案已停止推进，其云基础设施要求不作为当前 skills 的实现依据。
- 只有需要理解方案演进时再按需查看 `Drafts/`；默认不读 `Archive/`。
