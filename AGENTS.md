# AGENTS.md — 给 AI agent 的操作指南

> 本文件是 AI agent 接入本仓库时的第一手指南，遵循 [agents.md](https://agents.md) 通用约定。支持这一约定的工具可以直接读取；其他工具也应先显式读取本文件。

## 这是什么仓库

这是一个 **`*-brain` 项目**：MagicDub 项目的「数字大脑」，是构思、信息收集、设计与文档的中心，而不是项目代码的主仓库。它让 AI agent 能够快速理解项目，并在不同工作阶段之间可靠接手。

**你很可能是中途接手的新 agent。** 不要依赖自己或其他 agent 的对话记忆；以本仓库保存的项目知识为主要交接依据。任务依赖外部代码、服务或运行状态时，仍应读取并验证对应的当前事实，不要把历史文档当成实时证据。

## 接入后先判断状态

开始项目任务前，先检查仓库现状并按以下分支处理：

1. **权威模板仓库**：只有在能从 Git 远端或明确上下文验证当前仓库本身就是 `github.com/AaronJiTuo/brain-template` 时，才把占位内容视为模板状态并跳过初始化；不能只根据 manifest 中的 `template_authority` 判断仓库身份。
2. **未初始化或部分初始化**：出现以下任一信号时，先完整读取 `.skills/brain-initializer/SKILL.md`，由该 skill 判断状态和恢复范围：
   - `Releases/` 除 `README.md` 外没有真实项目内容；
   - 下方「项目专属约束」仍是占位模板；
   - root `README.md` 仍是模板介绍或仍带模板横幅；
   - 项目总览、README、专属约束、CURRENT 或首条 Record 只有部分完成、彼此不一致。
3. **已初始化**：只有在已有真实项目 Release 和项目专属约束，且上一步列出的项目总览、README、模板清理、CURRENT 与首条 Record 等必需产物均已闭环时，才进入下方普通任务或正式接手路由；不能仅凭 Release 和专属约束两项就跳过其余缺口。
4. **无法可靠判断**：不要猜测或写入。读取 initializer 后，向用户简要说明现状和待确认范围。

初始化或恢复初始化时，用户确认项目身份、目标和边界前，不得创建或改写项目内容。

## 按任务加载项目内 skill

本仓库的 `.skills/` 目录存放只服务于 `*-brain` 项目的项目内流程技能。这些技能是仓库协议的一部分，但不假设会被 Codex / Claude Code / Cursor 等工具的全局 skill 系统自动发现。

当任务语义匹配以下场景时，必须先完整读取对应的 `SKILL.md`，再执行任务：

| 任务场景 | 必须读取 |
| --- | --- |
| 判断或恢复未初始化、部分初始化的 brain | `.skills/brain-initializer/SKILL.md` |
| 用户明确要求接手、先了解项目、汇报当前状态或形成正式交接 | `.skills/brain-handoff/SKILL.md` |
| 在 `Drafts/` 创建、续写、移动或整理文件，或编写验证程序 / 测试原型 | `.skills/draft-organizer/SKILL.md` |
| 抓取 AI 对话页面或分享链接并保存为 Draft | `.skills/chat-capture/SKILL.md`，再读 `.skills/draft-organizer/SKILL.md` |
| 保存重要决策、实质成果、发现、里程碑或状态变化 | `.skills/checkpoint-recorder/SKILL.md`；需要保全对话成果时再读 `draft-organizer` |
| 从 Draft 或 Record 生成、重写或升级 `Releases/` 文档 | `.skills/release-organizer/SKILL.md`，再按其要求读取 `.skills/draft-organizer/SKILL.md` |
| 升级模板协议、补齐协议文件或同步协议说明 | `.skills/template-upgrader/SKILL.md` |

只读取当前任务匹配的 skill，不要预读整个 `.skills/` 目录。`.skills/` 默认不作为项目内容参与总结，除非任务正是维护模板协议或项目内 skill。

用户只是讨论某个链接内容、没有要求保存或抓取时，不触发 `chat-capture`。

## 建立项目上下文

接到任务时，按以下顺序建立上下文：

1. **先读 `Releases/`** —— 这里是规范性事实来源。定稿的项目总览、设计、规范都在这里，默认「可照着做」。如有项目总览类文档（如 `00_项目总览.md`），从它开始。
2. **再读 `.records/CURRENT.md`** —— 这里是项目当前实际状态的紧凑入口，包含正在进行、近期变化、文档与现实的漂移以及下一步。
3. **按需查少量 `.records/events/`** —— 只读取 `CURRENT.md` 指向、当前任务命中或确有追溯需要的事件。禁止为了建立上下文而全文扫描历史事件。
4. **再按需读 `Drafts/`** —— 这里是草稿、灵感、外部资料以及与 AI 的对话记录。用于补充背景、理解意图与演进过程。**注意：草稿可能不准确、未定稿、甚至自相矛盾**，不要把它当作权威结论。
5. **必要时查 `Archive/`** —— 已归档或被弃用的内容，用于追溯「为什么当初这么决定 / 为什么放弃了某方案」。**不要据此执行**当前工作。

> 一句话：**`Releases/` 说明“应该是什么”，`.records/CURRENT.md` 说明“现在怎样”，`.records/events/` 保存“发生过什么”；三者不一致时标记漂移，不静默覆盖。`Drafts/` 只作参考，`Archive/` 只作历史。**

> 普通具体任务按上述顺序建立足够上下文后继续执行，不把例行理解汇报变成新的确认门槛。用户明确要求接手、先了解项目、汇报当前状态或形成正式交接时，读取并执行 `.skills/brain-handoff/SKILL.md`；是否暂停由该 skill 的确认语义决定。

## 始终遵守的工作原则

- **尊重用户的落盘边界。** 纯探索和临时讨论默认不落盘；形成重要决策、实质成果或状态变化时，按 `checkpoint-recorder` 判断并留痕。用户明确说“不记录”“不落盘”或“只在对话中回答”时，不写 Draft、Record 或 CURRENT。
- **保全事实与历史。** 未经用户明确意图，不改写 `Releases/` 中的定稿内容；不擅自删除 `Drafts/`、`.records/events/` 或 `Archive/` 内容。历史 Record 通过新增更正记录纠错，不回写或删除。
- **保持项目入口可接手。** root `README.md` 必须保留可复制的 agent 启动或接手入口；项目语境变化时同步更新。
- **遵守目录边界。** 内容目录只有 `Releases/`、`Drafts/`、`.records/` 和 `Archive/`，模板协议文件以 manifest 的 `managed_files` 为准。不要随意新增根级内容目录；获准编写的验证程序、测试页面或原型按 `draft-organizer` 放入 `Drafts/` 的独立目录。
- **保护并行工作。** 写入前检查当前分支、工作区和目标文件最新内容，保留用户或其他 agent 的无关修改；写给未来读者时优先使用可搜索标题、明确结论和可验证标准。
- **平台规则按需加载。** 初始化、升级或新增根级点路径时，必须按 initializer/upgrader 的平台规则处理 Windows 与 WSL 隐藏属性；只能修改当前仓库配置，无法可靠判断时不得静默完成。
- **不自动扩展 Git 授权。** 留痕、版本检查和升级不得自动执行 `git add`、commit、pull、fetch、rebase、merge、push、tag、Release 或 PR，也不得写入关联代码仓库。Windows 或 WSL/Windows 盘上的仓库级 `core.hideDotFiles=true` 是仅影响当前工作区显示方式的窄范围例外。用户另行明确授权的 Git 任务独立处理。

## 模板协议维护

### 完整性检查

接手已有 `*-brain` 时，检查根目录 `.brain-template.json`：

1. manifest 必须包含可信的 `template_authority`、`template_ref`、`update_channel`、符合 SemVer 的 `protocol_version`、发布日期、更新摘要和 `managed_files`；权威来源应恰好为 `github.com/AaronJiTuo/brain-template`，稳定通道应为 `stable`。
2. 检查 `managed_files` 是否重复，以及其中列出的每个文件是否存在；不要在 AGENTS 中另行维护一份文件名单。`managed_files` 表示文件必须存在并由协议同步或受控合并，不表示升级时可以整文件覆盖项目化内容。
3. 对 `.gitignore` 做语义检查：`Drafts/private/` 的哨兵路径和目录内实际文件都必须被忽略，且 `git ls-files -- 'Drafts/private/**'` 不得返回已跟踪内容。发现已跟踪或被反向规则放行的文件时，只说明隐私保护未闭环，不自动删除、移动或修改 Git 索引。
4. manifest 缺失、无效、权威来源不匹配、托管文件缺失或隐私检查失败时，先向用户说明，不要自行修补。用户明确同意升级后，再读取并执行 `.skills/template-upgrader/SKILL.md`。
5. 如果本地 upgrader 也不存在，只能从固定权威来源的同一个精确 commit 快照获取 bootstrap 指令；升级范围、历史保全和平台分支以 upgrader 为准，不在这里复制执行细节。

### 正常任务结束时检查新版本

正常项目任务完成并通过必要验收、准备给出最终回复时，执行一次轻量、只读的模板版本检查：

1. 仅当本地 manifest 有效、`template_authority` 恰好为固定权威来源且 `update_channel` 为 `stable` 时才检查。
2. 从固定 GitHub 仓库列出正式 Releases，排除 draft、prerelease 和非标准 `vX.Y.Z` tag，先按 SemVer 选出版本最高的一项；`v2.3.1` 及以后还必须由 GitHub 明确返回 `immutable: true`，更早的历史 Release 可兼容非不可变状态。再将其 tag 解析为精确 commit SHA，并从该 SHA 只读获取 manifest。tag 版本必须与 `protocol_version` 完全一致、权威来源必须匹配，且 `update_channel` 必须为 `stable`；为兼容字段引入前的正式版本，`2.3.1` 之前的 manifest 可以缺少 `update_channel`，但不能声明其他通道。最高版本验证失败时不回退到较低 Release，也不以 `main`、Release 日期或 `target_commitish` 代替正式版本边界。
3. 将最高有效稳定版本与本地 `protocol_version` 比较。没有有效 Release、没有新版、网络或权限失败、返回无效、tag 与 manifest 不一致或无法可靠判断时，完全不提示，也不影响原任务。
4. 只有确认稳定版本更高时，才在原任务结果末尾附加一条可忽略的提醒，写明当前版本、最新版本和 manifest 中的更新摘要，询问用户是否升级。提醒、忽略或拒绝不创建 Record、不更新 CURRENT、不执行任何写入。
5. 用户回复“升级brain模板”“升级”或表达完全等价的明确意图后，该回复即构成本次标准稳定升级的完整授权。下一轮读取并执行 `template-upgrader`，把版本、SHA、文件范围和保全边界作为非阻塞进度说明后直接完成升级，不再请求同一升级的第二次确认；只有发现破坏性变化、超出标准协议范围、需要开发快照、额外 Git 交付或其他实质性扩权时才另行请求相应授权。正式升级使用该 Release tag 所解析出的同一精确 SHA 获取 manifest、upgrader 和托管文件；核心升级与检查点成功后，才按 upgrader 规则独立判定并询问可选 Star。`template_ref` 只用于用户明确要求的未发布开发快照，不参与稳定版发现。
6. 用户明确禁止联网、任务尚未结束、仅在等待或过程汇报、当前任务本身是模板检查或升级、当前仓库是权威模板仓库时，跳过检查且不提示。

---

## 项目专属约束（MagicDub）

- 当前路线（2026-09-13）：取消 `magicdub-cloud`；原 `magicdub` 暂时保留、当前不推进；集中完成主要自用的 `magicdub-skills`。未来确有对外 Web 需求时再决定重启 `magicdub` 或新建仓库，不预建 Web / Cloud 平台。详见 `Releases/00_MagicDub项目总览.md`。

- 范围约束：本项目 **永远不做唇形/口型修正**，仅追求「译制片式」音频替换与时间轴对齐体验。
- 仓库定位：本仓库用于思考与文档沉淀，不承载业务代码与脚手架。
- 协作约束：当 `Drafts/` 与 `Releases/` 发生冲突时，一律以 `Releases/` 为执行依据。
