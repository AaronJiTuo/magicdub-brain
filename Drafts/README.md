# Drafts/ — 草稿与上下文素材库

这里存放 **零碎想法、灵感、外部信息，以及与 AI 的对话记录**。它是思路的「捕获区」和当前工作台，不是长期历史仓库。

## 放什么

- 任何一闪而过的想法、需求片段、待探索的方案。
- 收集到的外部资料（文章要点、截图要点、链接 + 摘要）。
- 与 AI 的对话记录（导出为 markdown 直接丢进来；从 ChatGPT / Gemini / 豆包等页面抓取完整对话时使用 `.skills/chat-capture/SKILL.md`）。
- 半成品的梳理、想要做但还没定的事。
- 已经在对话中形成、如果不落盘就会丢失的文案、内容或设计成果；由 `.skills/checkpoint-recorder/SKILL.md` 判断是否需要保全。
- `00_灵感索引.md`：从历史 Draft 中摘出的轻量灵感入口。

## 原则

- **允许混乱**，重在快速捕获，不追求完美。
- 根目录只作临时收件箱：单篇、尚不足以成组或无法可靠归类的普通 Draft 可以暂时平铺。
- 同一主题达到 3 个文件时，agent 应创建 `Drafts/<主题关键词>/` 并归组；已有匹配主题目录时，新文件直接写入该目录。
- 任何程序、验证脚本、测试页面或可运行原型，从第 1 个文件起就必须放进独立目录，绝不平铺在 `Drafts/` 根目录。
- 用户写 Draft 时不需要维护状态；无状态 Draft 默认视为 `unreviewed`。
- 这里的内容 **未定稿、可能不准确**。成熟后升级为 `Releases/`；已完全吸收、过时或完成使命后移入 `Archive/`。
- 如果 agent 读过某个 Draft 但没有完全吸收它，应在文件顶部补状态元信息。
- 已进入 Release 的内容不应长期重复留在 Drafts；如果仍有零散灵感可复用，摘入 `00_灵感索引.md`，再归档原始 Draft。
- 纯探索讨论默认不落盘；对话中已经形成的实质成果按 `checkpoint-recorder` 保全。用户明确要求本次不记录或只在对话中回答时，不自动保存。

## 状态元信息

用户不需要手写状态。Agent 在整理 Draft 时，如需保留部分吸收的 Draft，可在文件顶部补：

```yaml
---
status: partially_absorbed
absorbed_by: Releases/xxx.md
remaining_value: 命名方向、增长假设
last_reviewed: YYYY-MM-DD
---
```

常见状态：

- `unreviewed`：默认状态；尚未被整理流程判定过。
- `partially_absorbed`：部分内容已进入 Release，仍有剩余价值。
- `active`：仍在推进的草稿。
- `reference`：作为资料参考保留。

## 给 AI agent 的提醒

`Drafts/` 只作参考，不要当成权威结论。`Releases/` 表达应当遵循的规范，`.records/CURRENT.md` 表达当前实际状态。

凡是在 `Drafts/` 中创建、续写、移动或整理文件，必须读取并执行 `.skills/draft-organizer/SKILL.md`。不要为了整理而全文扫描所有 Draft；优先根据目录名、文件名和必要的 frontmatter 判断归属。

当 `checkpoint-recorder` 要保全对话中独有的实质成果时，也必须执行 `draft-organizer`。只保存当前有效成果和具有独立价值的备选方案，不保存每个试错版本；随后由 Record 引用成果路径。

从 AI 对话页面或分享链接抓取完整对话并保存为 Draft 时，必须读取并执行 `.skills/chat-capture/SKILL.md`。长对话不能只抓首屏，必须通过浏览器滚动加载并记录完整性状态。

从 Drafts 或 Records 生成、汇总、重写或升级 Release 时，必须读取并执行 `.skills/release-organizer/SKILL.md`。不要全量扫描 Drafts 或 `.records/events/`；只处理本次用户指定、实际读取或明确用于生成 Release 的文件。

## 约定

- 主题目录使用稳定、可搜索的关键词，通常不加日期；普通 Draft 文件名仍可保留 `YYYY-MM-DD_主题.md`。
- 普通主题目录默认只设一层。程序可以直接拥有根级目录，也可以作为已有主题目录下的二级目录。
- 新程序目录应有简短 `README.md`，说明用途、运行方法、预期结果和当前状态；依赖目录、虚拟环境、构建缓存和临时输出不应提交。

不便公开的私密草稿可放入 `Drafts/private/`（已在 `.gitignore` 中忽略）。
