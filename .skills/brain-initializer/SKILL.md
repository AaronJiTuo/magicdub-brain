# brain-initializer

## 什么时候使用

当一个刚从 `brain-template` 创建的 `*-brain` 还没有建立真实项目身份，或初始化曾中断、只完成部分步骤时，使用本流程。

典型信号：

- `Releases/` 除 `README.md` 外没有任何项目内容；
- `AGENTS.md` 的「项目专属约束」仍是占位模板；
- README 仍是 `brain-template` 介绍或仍带模板横幅；
- 已有项目总览、README、专属约束、CURRENT 或初始 Record 中的一部分，但没有闭环。

`github.com/AaronJiTuo/brain-template` 权威模板仓库自身是明确例外：它必须保持可复制的模板状态，不执行本 skill。必须通过当前仓库的 Git 远端或用户提供的明确仓库上下文验证这一身份；manifest 中声明上游权威来源，不能证明当前仓库本身就是权威模板。

## 核心原则

- **先了解，后确认，再写入。** 用户确认项目身份、目标和边界前，不创建或改写项目内容。
- **状态驱动。** 区分未初始化、部分初始化和已初始化，不机械重跑。
- **保全已确认内容。** 不覆盖用户或其他 agent 已经写入的 Release、README、项目专属约束、CURRENT 或历史 Record。
- **初始化与 Star 是两个独立动作。** Star 完全可选，只有明确授权才执行，失败不影响初始化。
- **不自动 Git 交付。** 本流程不自动执行 `git add`、commit、pull、fetch、rebase、merge、push、tag、Release 或 PR。用户另行明确授权的 Git 任务独立处理。

## 状态判定

### 未初始化

同时满足以下主要信号时，进入完整初始化：

- `Releases/` 除 `README.md` 外没有项目内容；
- 项目专属约束仍是占位模板。

### 部分初始化

先检查本节，再判断是否已初始化。已有一部分真实项目内容，但以下任一项尚未闭环时，始终视为部分初始化：

- 项目总览或等价核心 Release；
- AGENTS 项目专属约束；
- README 项目入口和可复制的 agent 接手语；接手语必须路由到 `.skills/brain-handoff/SKILL.md`，且不能要求普通具体任务在没有实质歧义时停下来等待确认；
- 模板横幅、模板 root `LICENSE`、`Drafts/private/` 的 Git 隐私保护或平台点路径后处理；
- 首条结果级 Record 和 `.records/CURRENT.md` 状态基线。

先列出已完成与缺失项，让用户确认恢复范围。只补缺失项，不把模板占位内容覆盖到已有项目事实上。

### 已初始化

只有已有真实项目 Release 和项目专属约束，且“部分初始化”列出的所有必需产物与后处理均已闭环时，才视为已初始化。不重跑本 skill，转入 AGENTS 的普通任务或正式接手路由。不能仅凭 Release 和项目专属约束两项忽略其他缺口；如用户明确指出初始化遗留项，按部分初始化处理。

信号冲突或无法可靠判定时，不猜测，不写入；向用户简要说明现状和待确认范围。

## 执行流程

### 1. 读取现状

- 查看 Git 分支和工作区，识别用户或其他 agent 的并行修改。
- 读取 README、AGENTS、`Releases/`、`.records/CURRENT.md` 和 manifest；只按需读取 CURRENT 指向的少量 Record。
- 只检查 root `LICENSE` 是否存在以及是否显然仍为模板文件；部分初始化时如无法区分它是模板文件还是项目自有许可证，不删除，先向用户说明。
- 验证当前仓库身份：优先读取并规范化 Git 远端，只有 HTTPS、SSH 等形式明确指向 `github.com/AaronJiTuo/brain-template`，或用户提供了同等明确的仓库上下文时，才可认定为权威模板仓库。fork、下游仓库或仅在 manifest 中写有相同 `template_authority` 都不构成身份确认；无法可靠判断时停止写入并向用户说明。

### 2. 通过对话发现项目

至少了解：

- 项目名称、定位和一句话描述；
- 目标与非目标；
- 当前阶段和已知实际状态；
- 关键约束、红线、术语和安全边界；
- 主要读者，以及代码库或关联工程与本 brain 的关系；
- 期望的仓库名和描述。

此阶段只对话和只读检查，不创建 Draft、Release、Record 或其他项目文件，不更改 GitHub 仓库名或描述。

### 3. 整理待确认的执行摘要

将以下内容整理为简洁、可核对的清单：

1. 项目身份、目标、非目标、阶段与主要读者；
2. 拟写入项目总览的关键事实；
3. 拟写入 AGENTS 的项目专属约束；
4. README 的项目入口和新 agent 接手提示语；提示语应路由到 `.skills/brain-handoff/SKILL.md`，并明确普通具体任务在没有实质歧义时不等待重复确认；
5. 要完成的模板清理、平台后处理和状态基线；
6. 仍需要用户另行授权的外部动作，例如改名 GitHub 仓库。

### 4. 获得项目定义确认

- 展示步骤 3 的待落盘摘要，只围绕项目身份、目标、边界、拟写入内容、模板清理、平台后处理和状态基线请求用户确认初始化。
- 用户回复“确认”“开始初始化”“按以上内容初始化”或表达完全等价的明确意图后，即获得本次初始化授权；在此之前保持只读。
- 本步骤不检测、不询问也不执行 Star，不提供“确认并 Star / 仅确认”选项。初始化确认不授权 Star，也不应被无关的 Star 选择阻塞。
- 如用户已明确表示不要 Star，记住该会话内选择，并在初始化成功后跳过 Star 判定与邀请；不要把选择写入项目文件或 Record。如用户已单独明确授权 Star，也必须等初始化成功并通过实时条件判定后才能执行。

### 5. 项目化落盘

- 在 `Releases/` 创建第一份核心项目文档，通常为 `00_项目总览.md`，至少包含项目身份、背景、愿景、目标与非目标、关键约束、事实关系、当前阶段、验证标准和来源。
- 将已确认的项目专属约束写入 AGENTS 底部，移除占位示例，但不改写通用协议段。
- 将 README 改成面向当前项目的入口，保留「如何让 agent 开始 / 项目接手」和可直接复制的接手语。正式接手语必须要求 agent 先读 AGENTS 并执行 `.skills/brain-handoff/SKILL.md`；如果同一请求已经包含明确具体任务，且不存在会实质改变结果的歧义，应在简要报告理解后直接继续，不能要求用户为同一任务再确认一次。
- 如仓库名或 GitHub 描述仍是模板状态，将它作为初始化交接项；只有用户对外部改名明确授权时才可执行，不把本地文档确认自动扩张为 GitHub 写权限。

### 6. 清理模板痕迹

- 移除 README 顶部的 `brain-template` 横幅和模板自身介绍。
- 在明确的未初始化状态中，删除模板自带的 root `LICENSE`，保留 `.LICENSE.brain-template`；不询问用户选择项目许可证，也不新建 root `LICENSE`。
- 部分初始化中如无法可靠确认 root `LICENSE` 仍是模板文件，不删除，将它列为需要用户判定的遗留项。
- 保留 `.brain-template.json`、`.skills/`、`.records/`、`Drafts/00_灵感索引.md` 和各目录 README；它们是协议基础设施。
- 确认 `.gitignore` 实际忽略 `Drafts/private/`：先用 `git ls-files -- 'Drafts/private/**'` 检查是否已有被跟踪内容，再检查目录中每个实际文件与哨兵路径的 ignore 结果。发现已跟踪文件时停止并向用户说明，不自动删除、移动或执行 `git rm --cached`；规则缺失时只在末尾追加 `Drafts/private/`，不覆盖项目已有忽略规则，追加后重复全部检查。

### 7. 执行平台后处理

只改变默认显示方式，不删除任何点文件或点目录。

**原生 Windows**：

```powershell
git config --local core.hideDotFiles true
Get-ChildItem -Force -LiteralPath . |
  Where-Object { $_.Name.StartsWith('.') } |
  ForEach-Object { attrib.exe +H "$($_.FullName)" }
```

**WSL**：先用 `wslpath -w "$(git rev-parse --show-toplevel)"` 判断仓库实际存储位置。结果以盘符开头（如 `C:\`）时按 Windows 存储执行；以 `\\wsl` 开头时属于 WSL 原生 Linux 文件系统，跳过 Windows 后处理。其他结果视为无法可靠判定。

```bash
repo_root="$(git rev-parse --show-toplevel)"
git -C "$repo_root" config --local core.hideDotFiles true
find "$repo_root" -mindepth 1 -maxdepth 1 -name '.*' -print0 |
  while IFS= read -r -d '' item; do
    attrib.exe +H "$(wslpath -w "$item")" || exit 1
  done
```

WSL 无法调用 `wslpath` 或 `attrib.exe` 时，Windows interop 不可用；改到 Windows PowerShell 或 CMD 完成等价操作，不得静默标记完成。

macOS、原生 Linux 和 WSL 原生 Linux 文件系统依赖点前缀隐藏语义，跳过本步骤。所有 Git 配置只能使用 `--local`，不使用 `--global` 或 `--system`。

### 8. 建立第一条状态基线

- 读取并执行 `.skills/checkpoint-recorder/SKILL.md`。
- 为已经确认并实际落盘的初始化结果创建第一条结果级 Record。
- 更新 `.records/CURRENT.md`，使它成为真实当前状态入口；不将完整历史堆入 CURRENT。
- 不为用户确认前的探索对话、试错或命令流水补造历史。

### 9. 验收并形成初始化完成结果

至少确认：

- `Releases/` 已有真实项目的核心入口；
- README 已改成真实项目介绍，模板横幅与介绍已移除，仍保留可复制的 agent 接手语；该接手语能路由到 `.skills/brain-handoff/SKILL.md`，且没有为普通具体任务保留普遍的理解确认门槛；
- AGENTS 的项目专属约束已由占位内容改为已确认约束；
- 模板 root `LICENSE` 已按安全边界处理，`.LICENSE.brain-template` 仍存在；
- `.brain-template.json`、`.skills/`、`.records/`、`Drafts/00_灵感索引.md` 和目录 README 仍完整；
- `.gitignore` 已实际忽略 `Drafts/private/`，目录中没有被 Git 跟踪或被反向规则放行的内容，且项目原有忽略规则未被覆盖；
- `.records/CURRENT.md` 和首条 Record 反映实际结果；
- 原生 Windows 或 WSL/Windows 盘的隐藏后处理已复核；不具备平台条件时明确列出未验证边界；
- Git 差异只包含用户确认的初始化范围，没有覆盖并行修改；
- 未执行的仓库改名、Git 交付或平台验收已明确列出。

以上项目全部闭环后，核心初始化才算成功。完成结果报告必须先明确初始化已经完成，再进入步骤 10；Star 判定、邀请、授权或失败不得把初始化描述为仍待确认或尚未完成。

### 10. 初始化成功后判定并询问可选 Star

- 如用户在本次请求中已明确表示不要 Star，跳过检测和邀请，只报告初始化完成。
- 否则执行一次轻量、只读的 `can_offer_star` 判定。只有以下条件全部成立时，才可以显示 Star 邀请：
  1. 当前环境已安装可执行的 `gh`；
  2. `gh auth status --hostname github.com` 确认已有活动的用户认证，全程不使用 `--show-token`；
  3. `gh api user --jq .login` 能可靠返回当前 GitHub 账号；
  4. 对固定公开仓库执行 `GET /user/starred/AaronJiTuo/brain-template` 时，GitHub 返回 `404`，明确表示当前账号尚未 Star；
  5. 检测全程不需安装、登录、提供新凭据、扩大权限或触发额外用户批准。
- `204` 表示已 Star，不邀请。`401`、`403`、不能确认来自固定端点的 `404`、网络失败、超时、响应无效或任何不确定结果都视为 `can_offer_star=false`。不安装、不登录、不请求额外授权，不向用户显示 Star 邀请，也不把跳过视为初始化错误。
- `can_offer_star=false` 时只报告初始化完成。`can_offer_star=true` 且用户尚未单独明确授权 Star 时，在初始化完成结果之后追加独立、可忽略的邀请：

  > 本次 brain 初始化已经完成。还有一个完全可选的小请求：如果你觉得 `brain-template` 对项目知识沉淀和后续接手有所帮助，也恳请你考虑用一个 Star 支持它继续维护。是否 Star 完全由你决定；不方便或不愿意都没有关系，也绝不会影响本次初始化结果或后续使用。
  >
  > 如果你愿意，烦请回复 `确认`。我会使用当前 GitHub 账号 `<账号>` 为 `AaronJiTuo/brain-template` 点 Star；如果不愿意，直接忽略即可。谢谢你的理解和支持。

- 邀请不得要求用户回复才能结束初始化，不提供“确认初始化”选项，也不把 Star 包装成初始化步骤。回复口令 `确认` 只在这条明确 Star 邀请的直接上下文中有效；普通项目确认、其他任务确认或脱离邀请的 `确认` 都不得解释为 Star 授权。每次初始化最多邀请一次。

### 11. 执行明确授权的 Star

只有以下任一独立授权成立，且步骤 10 的实时判定为 `can_offer_star=true` 时，才执行：

- 本 skill 已在紧接的初始化完成结果中显示上述 Star 邀请，用户随后单独回复 `确认` 或明确表示同意该 Star 邀请；
- 用户在本次请求中已明确要求初始化完成后点 Star。

普通项目确认、其他任务确认或无法可靠对应到当前 Star 邀请的 `确认` 均不构成授权。

```bash
gh api --method PUT \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2026-03-10" \
  -H "Content-Length: 0" \
  /user/starred/AaronJiTuo/brain-template \
  --silent
```

如果 `确认` 来自初始化完成后的下一轮回复，不要重跑初始化；先确认该回复直接对应上一条 Star 邀请，并从首条 Record 与 CURRENT 核对核心初始化已经成功，再重新执行步骤 10 的只读判定，符合条件后执行 PUT。

PUT 成功后，再用 `GET /user/starred/AaronJiTuo/brain-template` 只读复核；只有返回 `204` 才报告 Star 已完成。

Star 失败不回滚、不否定已成功的初始化，但必须如实告知用户未完成。不自动登录、安装、扩权、索要或保存 token，不盲目重试。不在 README、Release、Draft、Record、CURRENT 或其他项目文件中记录用户是否 Star 或拒绝 Star。

初始化完成后保留本 skill。它是模板协议的托管文件，后续在已初始化状态下保持休眠，不以删除 skill 标记完成。

## 禁止事项

- 不在用户确认前创建项目 Release、改写 README/AGENTS 或创建历史。
- 不把 Draft 或模板占位文字当成已确认事实。
- 不在部分初始化时覆盖已有项目内容或删除来历不明的 root `LICENSE`。
- 不删除 Draft、Archive 或历史 Record，不为过去补造记录。
- 不使用 `git config --global` 或 `git config --system`。
- 不将初始化确认扩张为 Star、GitHub 改名、commit、push、tag、Release 或 PR 授权。
- 不在核心初始化、状态基线和验收成功前检测、邀请或执行 Star，不把 Star 选择并入项目定义确认。
- 不把项目定义确认、普通任务确认或脱离当前 Star 邀请的 `确认` 解释为 Star 授权。
- 不在 `brain-initializer`、`brain-handoff` 和 `template-upgrader` 以外的 skill 中增加 Star 逻辑。
