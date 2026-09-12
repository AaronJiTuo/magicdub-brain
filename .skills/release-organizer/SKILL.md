# release-organizer

## 什么时候使用

当用户要求或任务语义是在从 `Drafts/` 或 `.records/` 汇总、生成、重写或升级 `Releases/` 文档时，必须使用本流程。典型表达包括：

- “整理成 Release”
- “落到 Releases”
- “把这些 Drafts 汇总成正式文档”
- “基于 Drafts 生成项目总览 / 设计文档 / 规范”
- “把最近的 Record / 当前状态更新进 Release”

用户无需额外提醒“记录灵感并归档 Drafts”；这是本流程的一部分。

本流程必然会创建或修改 Draft 状态、灵感索引，或移动 Draft/程序目录，因此开始执行前必须完整读取 `.skills/draft-organizer/SKILL.md`；所有路径选择、归组和移动继续遵守该 skill。

## 输入边界

只处理本次相关 Draft 和 Record：

- 用户明确指定的 Draft。
- Agent 本次实际读取并用于生成 Release 的 Draft。
- Release 文档中明确声明吸收或部分吸收的 Draft。
- 用户明确指定的 Record。
- `.records/CURRENT.md` 中与本次 Release 直接相关的状态和链接。
- Agent 本次实际读取并用于生成 Release 的 Record。

不要为了整理而全量扫描整个 `Drafts/` 或 `.records/events/`。不要读取 `Archive/`，除非用户明确要求、当前 Release 来源关系指向、`Drafts/00_灵感索引.md` 指向，或确有追溯需要。

## 执行步骤

1. 确认本次输入清单。
   - 在动手前列出本次会处理的 Draft 和 Record。
   - 无状态 Draft 默认视为 `unreviewed`，不要要求用户补状态。
   - Record 的 `certainty` 必须与证据强度一致；`reported` 或 `tentative` 不能直接提升为 Release 权威结论。

2. 生成或更新 Release。
   - Release 必须达到“读者不用追问也能照做”的标准。
   - 不确定、未验证、仍只是灵感的内容不要写成权威结论。

3. 在 Release 末尾写入来源、证据与替代关系。

   ```md
   ## 来源与证据

   本文吸收并替代：
   - Drafts/主题/xxx.md
   - Drafts/主题/yyy.md

   本文依据：
   - .records/events/YYYY-MM/YYYY-MM-DD_HHMMSS_主题.md
   ```

   如果只是部分吸收：

   ```md
   ## 来源与证据

   本文部分吸收：
   - Drafts/主题/xxx.md：已吸收 A/B，未处理 C
   ```

4. 摘录遗留灵感。
   - 从本次相关 Draft 中找出未进入 Release、但未来可能有用的点。
   - 追加到 `Drafts/00_灵感索引.md`。
   - 每条尽量写清楚：灵感、来源、适用场景、状态。
   - 不要把未确认灵感直接写入 `Releases/` 作为事实。

5. 处理 Draft 去留。
   - 完全吸收：移动到 `Archive/`。
   - 完全吸收一个程序时，保持程序目录完整，不要把其中源码重新平铺。
   - 部分吸收：留在 `Drafts/`，在文件顶部补充或合并 frontmatter 状态字段。
   - 仍在推进：留在 `Drafts/`，必要时标 `active`。
   - 明显过期但仍需留痕：移动到 `Archive/`。
   - 不删除 Draft。
   - 每次移动前先解析确切目标路径并检查冲突；目标文件或目录已存在时不得覆盖、合并或删除，优先选择含日期或主题的可搜索新名称，仍无法无歧义处理时停止并向用户说明。

6. 给仍留在 `Drafts/` 的已审阅文件补状态。

   - 如果文件第一行已经是 YAML frontmatter，将 `status`、`absorbed_by`、`remaining_value` 和 `last_reviewed` 合并进同一个 mapping；保留 chat-capture 等流程写入的来源、采集状态和其他未知字段，不创建第二个 frontmatter，也不改变正文。
   - 如果文件尚无 frontmatter，才在第一行创建下面的单个状态块。
   - 无法可靠解析已有 frontmatter、字段类型冲突或合并结果无效时停止并向用户说明，不覆盖原块。

   ```yaml
   ---
   status: partially_absorbed
   absorbed_by: Releases/xxx.md
   remaining_value: 命名方向、增长假设
   last_reviewed: YYYY-MM-DD
   ---
   ```

   可用状态：
   - `partially_absorbed`
   - `active`
   - `reference`

7. 处理相关当前状态。
   - 如果本次 Release 更新解决了 `.records/CURRENT.md` 中的文档与现实漂移，更新对应漂移项。
   - 不把完整 Release 摘要复制到 CURRENT；只保留仍影响当前工作的状态和链接。
   - Release 是重大结果时，在全部后处理完成后执行 `.skills/checkpoint-recorder/SKILL.md`，创建一条结果级 Record；Record 的创建过程不得递归触发新 Record。

8. 复核。
   - `Releases/` 中的结论不能依赖未读 Archive 才能理解。
   - `Drafts/` 中不应继续堆放已完全吸收的原始材料。
   - `Archive/` 中的文件不应被日常执行默认读取。
   - 文件移动后，Release 和灵感索引中的路径要准确。
   - Archive 中不存在因本次移动被覆盖、隐式合并或丢失的同名内容。
   - 部分吸收的 Draft 最终只有一个位于第一行的有效 YAML frontmatter；已有元数据均被保留，文档仍只有一个顶级标题。
   - 部分吸收后仍留在 `Drafts/` 的文件继续符合 `.skills/draft-organizer/SKILL.md`，程序文件不得回到根目录。
   - 被引用的 Record 路径准确，且历史 Record 没有被移动、删除或回写。

## 命名建议

归档 Draft 时优先保留原文件名。必要时可加状态前缀：

- `Archive/已吸收_原文件名.md`
- `Archive/2026-07-11_已吸收_主题.md`

如果原文件名已经包含日期和主题，通常直接移动即可。

## 禁止事项

- 不要全量扫描 `Archive/`。
- 不要删除 Draft 或 Archive 内容。
- 不要移动、删除或回写历史 Record；若发现错误，按 `checkpoint-recorder` 新增更正记录。
- 不要把未确认灵感写成 Release 结论。
- 不要为了补状态而改写用户草稿正文。
- 不要处理与本次 Release 无关的 Draft。
- 不要为了生成 Release 全量扫描 `.records/events/`。
- 不要让移动操作覆盖或隐式合并 Archive 中的同名文件或目录。
- 不要在已有 YAML frontmatter 前再插入第二个 frontmatter，也不要为写入状态而覆盖已有采集或来源元数据。
