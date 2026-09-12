# .records/ — Agent 留痕与当前状态

这里保存项目推进过程中已经形成的**重要决策、实质成果和状态变化**，主要供 AI agent 接手、检索和追溯。它不是给人类逐篇阅读的工作日志，也不是聊天、命令或操作过程的完整归档。

## 与其他目录的关系

- `Releases/` 保存已经确认、应当遵循的规范性事实。
- `.records/CURRENT.md` 保存项目实际进行到哪里的紧凑视图。
- `.records/events/` 保存已经发生过什么的追加式历史证据。
- `Drafts/` 保存仍在迭代、等待吸收或需要保全的实质成果。
- `Archive/` 保存已经失效或完成使命的历史材料。

当 Release 与当前观察状态不一致时，不静默覆盖任何一方；应在 `CURRENT.md` 标记漂移，并链接相关事件记录。

## 目录结构

```text
.records/
├── README.md
├── CURRENT.md
└── events/
    └── YYYY-MM/
        └── YYYY-MM-DD_HHMMSS_主题.md
```

模板不预建空的月份目录。第一次产生事件时，由 `.skills/checkpoint-recorder/SKILL.md` 创建对应目录。

## 阅读规则

用户明确要求正式接手、先了解项目或汇报当前状态时，由 `.skills/brain-handoff/SKILL.md` 编排接手；其中仍是先读 `Releases/` 的核心入口，再读 `CURRENT.md`。普通具体任务只建立完成任务所需的足够上下文，不因例行理解汇报停下来等待用户确认。只有当前任务需要、`CURRENT.md` 明确指向或确有追溯需求时，才搜索和打开少量相关事件。

**禁止为了“全面了解项目”而全文读取 `.records/events/`。** 历史事件应先按主题、类型、领域、关联成果或日期检索，再读取命中的少量文件。

## 写入规则

- 一件重要结果对应一条事件记录；同一连续工作阶段的细小动作合并成结果级记录。
- 事件文件创建后视为历史证据，原则上不回写；发现错误时新增更正记录，并通过 `supersedes` 指向旧记录。
- `CURRENT.md` 是可更新的派生视图，只保留仍影响当前工作的状态、近期关键变化、漂移和下一步。
- Record 保存结论、理由、影响和证据位置，不复制完整聊天、终端日志、diff 或审计日志。
- 任何写入都必须执行 `.skills/checkpoint-recorder/SKILL.md`。

## Git 边界

当前 brain-template 协议不提供自动 Git 协作：创建或更新 Record **不会自动执行** `git add`、`commit`、`pull`、`rebase` 或 `push`。Git 操作仍需用户在具体任务中明确要求。
