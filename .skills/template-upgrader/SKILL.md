# template-upgrader

## 什么时候使用

当当前 `*-brain` 项目需要同步 `brain-template` 的模板协议时，使用本流程。典型触发条件：

- 根目录没有有效的 `.brain-template.json`。
- manifest 的 `managed_files` 存在重复，或清单内文件缺失、无效；下游额外存在项目文件是正常情况，不属于结构不一致。
- `.brain-template.json` 中的 `protocol_version` 低于模板权威来源最新有效稳定 Release 的协议版本。
- `AGENTS.md` 缺少初始化状态路由、事实读取顺序、项目内 skill 路由、长期安全边界或模板协议维护规则。
- 正常任务结束时的只读版本检查发现新版，且用户明确同意升级。
- 用户要求“升级 brain-template 协议”“同步新版模板”“给旧 brain 补新版机制”。

`github.com/AaronJiTuo/brain-template` 权威模板仓库自身不执行本 skill。必须通过当前仓库的规范化 Git 远端或用户提供的同等明确上下文验证身份；manifest 中声明相同 `template_authority` 不能证明当前仓库就是权威源仓。无法可靠排除源仓身份时保持只读并向用户说明。

## 核心原则

升级必须非破坏性：

- 不删除 `Drafts/`、`.records/events/` 或 `Archive/` 内容。
- 不改写 `Releases/` 正文。
- 不回写历史 Record，不用模板空白内容覆盖项目已有的 `.records/CURRENT.md`。
- 不覆盖 `AGENTS.md` 的「项目专属约束」。
- 不覆盖项目已经改写过的 root `README.md` 项目介绍。
- 可以补齐或更新 `.LICENSE.brain-template`，但不新增、删除或覆盖下游项目自己的 root `LICENSE`。
- 原生 Windows 以及 WSL 中位于 Windows 挂载盘的仓库，只允许为当前仓库设置 `core.hideDotFiles=true` 并维护根级点路径的 Hidden 属性；不得修改用户的全局 Git 配置。使用 WSL 时必须按仓库实际存储位置分流，不能仅因 shell 是 Linux 就跳过。
- 只补齐或更新模板协议相关文件和说明。
- 升级和 Star 是两个独立动作。Star 完全可选，只有用户显式授权才执行；Star 检测或写入失败不影响升级。
- 稳定升级只认可正式 GitHub Release 对应 tag 所固定的提交；`main` 和 manifest 中的 `template_ref` 不是稳定发布边界。
- `managed_files` 表示文件必须存在并由协议同步或受控合并，不表示可以整文件覆盖项目化内容。
- 当前本地 upgrader 是来源验证、授权和安全边界的引导器；固定目标 SHA 中的 upgrader 是用户明确授权标准稳定升级后采用的目标迁移合同。两者冲突时执行更严格的保护规则，目标版本不得削弱本地已有的保全、隐私、权限或 Git 边界。

发现新版不等于获得升级授权。正常任务结束时的版本检查只能读取 Release 元数据和候选 tag 精确 SHA 下的 manifest；不能预取或执行远端 upgrader。用户回复“升级brain模板”“升级”或表达完全等价的明确意图后，即已完整授权标准稳定升级：可以从固定 SHA 读取协议文件、分析差异、用非阻塞进度说明告知范围并直接完成写入、复核和检查点，不得再次请求同一升级的确认。用户忽略或未明确同意时，什么也不做。只有前置核查发现破坏性变化、超出标准协议范围、需要未发布开发快照、额外 Git 交付或其他实质性扩权时，才为新增范围另行请求授权。

## 升级步骤

1. 读取当前结构。
   - 先规范化当前仓库 Git 远端并核对用户提供的仓库上下文。只有明确不是 `github.com/AaronJiTuo/brain-template` 权威源仓时才继续；fork、下游仓库或仅在 manifest 中写有相同权威来源都不算源仓。
   - 查看 `AGENTS.md`、`README.md`、`Releases/README.md`、`Drafts/README.md`、`.records/README.md`、`.records/CURRENT.md`、`Archive/README.md`。
   - 查看是否存在 `.brain-template.json`、`.LICENSE.brain-template`、`.gitignore`、`.skills/`、`.records/`、`Drafts/00_灵感索引.md`；只识别 root `LICENSE` 是否存在，不读取或改写其许可选择。
   - 如果运行在原生 Windows，读取当前仓库的 `core.hideDotFiles`，并检查根目录现有点路径是否带 Hidden 属性；只读取当前仓库配置，不读取或修改全局配置。
   - 如果运行在 WSL，先用 `wslpath -w` 转换仓库根目录：结果以盘符开头（如 `C:\`）表示仓库位于 Windows 挂载盘，需要读取仓库级配置和 Windows Hidden 属性；结果以 `\\wsl` 开头表示仓库位于 WSL 原生 Linux 文件系统，按 Linux 处理；其他结果视为无法可靠判断，不得静默跳过。
   - 查看 git 状态，避免覆盖用户正在编辑的改动。

2. 选择并固定权威版本快照。
   - 如果本地存在 `.brain-template.json`，确认其中 `template_authority` 恰好是 `github.com/AaronJiTuo/brain-template`；不要从其他来源下载并执行升级指令。
   - 如果本地缺少 `.brain-template.json`，只有用户已经明确要求从 `github.com/AaronJiTuo/brain-template` bootstrap 时才继续，并将该固定来源作为唯一权威；缺少 manifest 的仓库不参与正常任务结束时的半自动版本检查。
   - 默认使用稳定通道：列出固定仓库的正式 GitHub Releases，排除 draft、prerelease 和 tag 不符合 `vX.Y.Z` 的条目，先按 SemVer 选择版本最高的一项；不按发布时间、列表顺序或 GitHub 的 Latest 标签判断版本大小。`v2.3.1` 及以后还必须由 GitHub 明确返回 `immutable: true`，更早的历史 Release 可兼容非不可变状态。
   - 将最高版本 Release 的 tag 完全解引用为精确 commit SHA，不使用 Release 的日期、`target_commitish` 或当前 `main` 代替 tag，再从该 SHA 读取 `.brain-template.json`。
   - manifest 必须有效，`template_authority` 必须恰好匹配，`protocol_version` 必须与去掉 `v` 的 tag 版本完全一致；`2.3.1` 及以后还必须明确为 `update_channel: stable`，更早的正式版本可以缺少该字段但不能声明其他通道。
   - 没有正式 Release、最高版本 tag 无法解析、manifest 不匹配或验证不确定时停止，不提示可升级，也不回退到较低 Release 或 `main`。
   - 选定候选后，再次固定其 tag、精确 SHA 和 Release URL，并从同一个 SHA 读取远端 `.skills/template-upgrader/SKILL.md`、`.skills/brain-initializer/SKILL.md` 和本次需要的所有托管文件；不要混用不同 tag、分支或时间点的内容。只有用户已明确授权标准稳定升级后才读取这些文件并采用目标迁移合同。
   - 如果本次仅因“发现稳定新版”而触发，重新确认选定 `protocol_version` 仍高于本地版本；如果已经没有版本差异，结束升级且不修改文件。
   - 如果本次是修复同版本的缺失协议文件或 bootstrap，可继续使用该可信快照；不得用低于本地 `protocol_version` 的远端内容降级现有 brain。
   - 只有用户明确要求 `main`、某个分支或某个未发布 SHA 时，才允许开发快照模式：解析 `template_ref` 或用户指定 ref 的精确 SHA，明确说明它不属于稳定 Release，并在执行前的范围说明中单独标注。不得把普通“升级到最新版”解释为开发快照授权，也不得在稳定检查失败时自动切换到开发快照。

3. 判断升级范围。
   - 对照本地 upgrader 与固定 SHA 中的目标 upgrader：本地版本继续约束来源、用户授权和安全底线；用户明确授权标准稳定升级后，以目标 upgrader 定义新增文件、字段和迁移步骤。任何一方要求保留而另一方未提及的项目内容仍必须保留。
   - 缺文件则补文件。
   - 旧说明缺少新版协议时，只追加或局部替换相关小节。
   - 已有项目内容优先保留，尤其是 `README.md` 顶部介绍和 `AGENTS.md` 项目专属约束。
   - 对每个 `managed_files` 明确采用“上游同步”还是“受控合并”；README、AGENTS 项目专属约束、CURRENT、`.gitignore` 等项目化文件不得整文件覆盖。
   - 从 1.x 升级到 2.x 会改变默认留痕行为，必须由用户明确要求升级；不要静默启用。

4. 说明升级范围并直接执行。
   - 在任何写入前，向用户说明更新通道、目标版本、Release tag 与 URL（稳定模式）、精确上游 SHA、拟修改文件、受控合并策略、目标 upgrader 将采用的迁移合同、保全边界和已知平台后处理。开发快照必须显著标明“未正式发布”。
   - 该说明是升级过程中的非阻塞进度信息，不是新的确认请求。用户已经明确授权标准稳定升级时，说明后直接继续步骤 5，不等待“确认”“仅确认”或其他重复回复。
   - 升级请求本身不授权 Star，也不在本步骤检测、询问或执行 Star。如用户已明确表示不要 Star，记住该会话内选择，并在核心升级成功后跳过 Star 判定与邀请；不要把选择写入项目文件或 Record。
   - 只有核查发现破坏性变化、超出标准协议升级范围、用户并未授权的开发快照、额外 Git 交付、需要处理冲突中的并行修改或其他实质性扩权时才停止，并只为新增范围请求授权。

5. 补齐模板协议文件。
   - `.LICENSE.brain-template`
   - `.gitignore`
   - `.brain-template.json`
   - `.skills/brain-handoff/SKILL.md`
   - `.skills/brain-initializer/SKILL.md`
   - `.skills/chat-capture/SKILL.md`
   - `.skills/checkpoint-recorder/SKILL.md`
   - `.skills/draft-organizer/SKILL.md`
   - `.skills/release-organizer/SKILL.md`
   - `.skills/template-upgrader/SKILL.md`
   - `.records/README.md`
   - `.records/CURRENT.md`
   - `Drafts/00_灵感索引.md`

   对旧 brain：

   - 如果 `.records/CURRENT.md` 不存在，创建模板中的空白状态入口，并注明“尚无新版协议记录，以 Releases 为准”；不要扫描旧 Draft、聊天或 Git 历史补造事件。若文件已经存在，保留项目内容，不用模板覆盖。
   - 先执行 `git ls-files -- 'Drafts/private/**'`；返回任何路径都表示已有私密内容被跟踪，必须停止并向用户说明，不自动删除、移动或执行 `git rm --cached`。
   - 再用 `git check-ignore --quiet --no-index Drafts/private/.brain-template-private-check` 检查哨兵路径，并对 `Drafts/private/` 中每个实际文件逐一检查 ignore 结果，防止反向规则只放行真实文件。未完全忽略时，创建或只在文件末尾追加 `Drafts/private/`；不得覆盖、重排或删除项目已有规则。追加后重复索引、哨兵和实际文件三项检查，仍未闭环则停止。

6. 更新说明文件。
   - `AGENTS.md` 维护初始化状态路由、按层读取、正式接手与其他项目内 skill 路由、长期安全边界和模板协议维护规则；skill 的详细执行步骤只保留在对应 `SKILL.md` 中。同步时保留下方「项目专属约束」及其项目内容。
   - `Drafts/README.md` 增加成果保全授权、无状态 Draft、主题归组、程序目录、AI 对话抓取、灵感索引和 Release 后处理说明。
   - `Releases/README.md` 增加规范性事实、当前状态、来源与证据关系说明。
   - `.records/README.md` 增加 Record 与 CURRENT 的职责、读取边界、不可变历史和 Git 边界。
   - `Archive/README.md` 增加已吸收 Draft 可归档、默认不读 Archive 的说明。
   - `README.md` 保留真实项目介绍，并确保可复制的最短 agent 启动 / 接手入口仍存在。正式接手语必须路由到 `.skills/brain-handoff/SKILL.md`；如果旧接手语要求 agent 对所有具体任务都先复述并等待确认，只局部替换这段提示，使没有实质歧义的已授权任务在简要报告理解后直接继续。不要为了同步协议追加目录树、内部文件清单或完整升级流程，也不把模板 README 整篇覆盖到下游 README。

   许可文件是例外边界：`.LICENSE.brain-template` 是上游模板材料的 MIT 声明，可以按权威快照同步；root `LICENSE` 属于下游项目自身选择，升级流程不得从模板仓库复制、替换或删除它。

7. 执行 Windows 存储上的隐藏属性后处理。
   - 原生 Windows 直接执行本步骤。
   - WSL 必须先确定仓库实际存储位置。使用 `wslpath -w "$(git rev-parse --show-toplevel)"`：盘符路径按 Windows 存储执行本步骤；`\\wsl` 路径属于 WSL 原生 Linux 文件系统，跳过；其他结果无法可靠判断时停止本后处理并向用户说明。
   - macOS、原生 Linux 和使用原生 Linux 文件系统的 WSL 跳过。
   - 如果当前目录是 Git 工作区，执行 `git config --local core.hideDotFiles true`。这是仅影响当前工作区显示方式的窄范围例外；不得使用 `--global` 或 `--system`，也不得据此执行任何其他 Git 写操作。WSL 中的 Linux Git 不会据此设置 Windows Hidden 属性，但保留该仓库级配置可供以后操作同一工作区的 Git for Windows 使用。
   - 所有协议文件和说明更新完成后，重新枚举仓库根目录中所有以 `.` 开头的文件与目录并设置 Hidden 属性。`core.hideDotFiles=true` 只兜底 Git for Windows 新创建的点路径，本步骤负责 agent、脚本、升级器或 WSL Git 直接创建以及属性丢失的路径。
   - 原生 Windows 使用 PowerShell：

     ```powershell
     Get-ChildItem -Force -LiteralPath . |
       Where-Object { $_.Name.StartsWith('.') } |
       ForEach-Object { attrib.exe +H "$($_.FullName)" }
     ```

   - WSL/Windows 盘使用 Bash，并通过 `wslpath` 把每个路径转换后调用 Windows `attrib.exe`：

     ```bash
     repo_root="$(git rev-parse --show-toplevel)"
     git -C "$repo_root" config --local core.hideDotFiles true
     find "$repo_root" -mindepth 1 -maxdepth 1 -name '.*' -print0 |
       while IFS= read -r -d '' item; do
         attrib.exe +H "$(wslpath -w "$item")" || exit 1
       done
     ```

   - WSL 无法调用 `wslpath` 或 `attrib.exe` 时，Windows interop 不可用，隐藏后处理尚未完成；改到 Windows PowerShell 或 CMD 中执行等价处理，不能静默当作成功。

8. 复核。
   - 确认 `AGENTS.md` 没有丢失项目专属约束。
   - 确认没有删除历史内容。
   - 确认 `.skills/brain-handoff/SKILL.md` 已存在，AGENTS 能在用户明确要求正式接手时路由到它；普通具体任务不因例行上下文汇报而等待重复确认。
   - 确认 root `README.md` 的可复制正式接手语也能路由到 `.skills/brain-handoff/SKILL.md`，且已移除“所有具体任务都必须复述后等待确认”的旧提示；真实项目介绍和其他 README 内容仍被保留。
   - 确认 `.skills/brain-initializer/SKILL.md` 已存在，AGENTS 能在未初始化、部分初始化和信号冲突时路由到它，且升级本身没有触发初始化。
   - 确认 `.skills/draft-organizer/SKILL.md` 已存在，AGENTS 能在 Draft 写入与程序原型任务中路由到它，skill 明确禁止程序平铺在 `Drafts/` 根目录。
   - 确认 `.skills/checkpoint-recorder/SKILL.md` 已存在，自动保全、关闭留痕、按需读取、敏感信息、不可变历史和禁止自动 Git 的边界完整。
   - 确认旧项目已有 `.records/CURRENT.md` 和 `.records/events/` 没有被覆盖或删除。
   - 确认 `.LICENSE.brain-template` 已存在，且升级没有新增、删除或改写 root `LICENSE`。
   - 确认 `git ls-files -- 'Drafts/private/**'` 没有输出，哨兵路径和 `Drafts/private/` 中每个实际文件均被 `.gitignore` 忽略，且项目原有忽略规则未被覆盖。
   - 确认 `.brain-template.json` 的 `template_authority`、`template_ref`、`update_channel`、`protocol_version`、`protocol_released_at`、`protocol_summary` 和 `managed_files` 与实际文件一致。
   - 稳定模式确认实际使用的 Release 非 draft、非 prerelease，`v2.3.1` 及以后不可变，tag 版本与 manifest 完全一致，所有远端文件来自该 tag 解析出的同一 SHA；开发快照模式确认执行前的范围说明已明确标注未发布状态。
   - 如果运行在原生 Windows，确认当前仓库 `core.hideDotFiles` 的值为 `true`，并重新读取根级点路径的文件属性；任何一项缺少 Hidden 属性都视为升级未完成。可用以下 PowerShell 验收：

     ```powershell
     if ((git config --local --get core.hideDotFiles) -ne 'true') {
       throw 'core.hideDotFiles is not true'
     }
     $visibleDotItems = Get-ChildItem -Force -LiteralPath . |
       Where-Object {
         $_.Name.StartsWith('.') -and
         -not ($_.Attributes -band [System.IO.FileAttributes]::Hidden)
       }
     if ($visibleDotItems) {
       throw "Dot paths are not hidden: $($visibleDotItems.Name -join ', ')"
     }
     ```

   - 如果运行在 WSL/Windows 盘，确认仓库级 `core.hideDotFiles` 为 `true`，并用 `attrib.exe "$(wslpath -w "$item")"` 逐一重新读取根级点路径的 Windows 属性；任何一项缺少 `H` 标记、路径转换失败或 Windows 命令不可用，都视为升级未完成。WSL 原生 Linux 文件系统只验证点前缀和文件存在性，不设置 Windows 属性。

   - 确认正常任务结束时只比较最高有效稳定 Release；main 领先、无更新、网络失败、tag/manifest 不一致、无法判断和用户未同意时均不修改、不提示、不阻塞。
   - 确认只有 `brain-initializer`、`brain-handoff` 和 `template-upgrader` 包含 Star 邀请与 PUT 端点；三者都先完成各自核心结果，再按条件静默或显示可选邀请，邀请统一要求用户回复 `确认`，并且只有直接对应当前 Star 邀请的确认才构成授权。标准升级授权不会触发 Star，upgrader 不会在核心升级完成前判定或邀请 Star，也不会为同一标准升级请求第二次确认。
   - 用 git diff 检查升级只触及模板协议相关内容。

9. 建立升级结果检查点。
   - 核心升级和复核成功后，完整读取并执行 `.skills/checkpoint-recorder/SKILL.md`。
   - 创建一条结果级 Record，至少记录升级前后版本、稳定 Release tag 与 URL（或开发快照标识）、实际使用的上游精确 commit SHA、实际修改文件、项目内容与历史保全结果，以及 Windows/WSL 已验证和未验证边界。
   - 更新 `.records/CURRENT.md` 中的当前协议版本、来源 SHA、近期变化、文档与现实漂移及仍需处理的事项；不把完整升级日志堆入 CURRENT。
   - Star 的邀请、选择、账号和执行结果均不得进入 Record 或 CURRENT。检查点失败时如实报告升级尚未闭环，不执行 Star。

10. 核心升级成功后判定并询问可选 Star。
   - 只有步骤 5—9 的核心升级、复核和检查点均已成功后，才进入本步骤。最终报告必须先明确升级已经完成；Star 判定、邀请、授权或失败都不得把升级描述为仍待确认或尚未完成。
   - 如用户在本次请求中已明确表示不要 Star，跳过检测和邀请，直接报告升级完成。
   - 否则执行一次轻量、只读的 `can_offer_star` 判定：
     1. 当前环境已有可执行的 `gh`；
     2. `gh auth status --hostname github.com` 确认已有活动的用户认证，不使用 `--show-token`；
     3. `gh api user --jq .login` 可靠返回当前 GitHub 账号；
     4. 对固定公开仓库执行 `GET /user/starred/AaronJiTuo/brain-template` 返回 `404`，明确表示当前账号尚未 Star；
     5. 以上检测不需安装、登录、提供新凭据、扩权或触发额外用户批准。
   - `204` 表示已 Star，不邀请。`401`、`403`、不能确认来自固定端点的 `404`、网络失败、超时、响应无效或其他不确定结果都视为 `can_offer_star=false`。不安装、不登录、不请求额外授权，不显示 Star 文案，也不影响升级。
   - `can_offer_star=false` 时只报告升级完成。`can_offer_star=true` 且用户尚未明确授权 Star 时，在升级完成报告之后追加独立、可忽略的邀请：

     > 本次 brain 模板升级已经完成。还有一个完全可选的小请求：如果你觉得 `brain-template` 本次带来的改进对项目知识沉淀和后续接手有所帮助，也恳请你考虑用一个 Star 支持它继续维护。是否 Star 完全由你决定；不方便或不愿意都没有关系，也绝不会影响本次升级结果或后续使用。
     >
     > 如果你愿意，烦请回复 `确认`。我会使用当前 GitHub 账号 `<账号>` 为 `AaronJiTuo/brain-template` 点 Star；如果不愿意，直接忽略即可。谢谢你的理解和支持。

   - 邀请不得要求用户回复才能结束升级，不提供“确认升级”选项，也不把 Star 包装成升级步骤。回复口令 `确认` 只在这条明确 Star 邀请的直接上下文中有效；普通升级确认、其他任务确认或脱离邀请的 `确认` 都不得解释为 Star 授权。每次升级最多邀请一次；此前拒绝不写入项目状态，后续新的升级仍可重新判定。

11. 执行明确授权的 Star。
   - 只有以下任一独立授权成立，且步骤 10 的实时判定为 `can_offer_star=true` 时，才执行：
     - 本 skill 已在紧接的升级完成结果中显示上述 Star 邀请，用户随后单独回复 `确认` 或明确表示同意该 Star 邀请；
     - 用户在本次请求中已明确要求升级完成后点 Star。
   - 普通升级确认、其他任务确认或无法可靠对应到当前 Star 邀请的 `确认` 均不构成授权。

   - 符合上述条件时执行：

     ```bash
     gh api --method PUT \
       -H "Accept: application/vnd.github+json" \
       -H "X-GitHub-Api-Version: 2026-03-10" \
       -H "Content-Length: 0" \
       /user/starred/AaronJiTuo/brain-template \
       --silent
     ```

   - 如果 `确认` 来自升级完成后的下一轮回复，不要重跑升级；先确认该回复直接对应上一条 Star 邀请，并从升级 Record 与 CURRENT 核对核心升级已经成功，再重新执行步骤 10 的只读判定，符合条件后执行 PUT。
   - PUT 成功后，再用 `GET /user/starred/AaronJiTuo/brain-template` 只读复核；只有返回 `204` 才报告 Star 已完成。
   - Star 失败不回滚、不否定已成功的升级，但必须告知用户未完成。不自动登录、安装、扩权、索要或保存 token，不盲目重试。
   - 不在 README、Release、Draft、Record、CURRENT 或其他项目文件中记录用户是否 Star 或拒绝 Star。

## `.brain-template.json` 建议内容

```json
{
  "template": "brain-template",
  "template_authority": "github.com/AaronJiTuo/brain-template",
  "template_ref": "main",
  "update_channel": "stable",
  "protocol_version": "2.4.0",
  "protocol_released_at": "2026-08-23",
  "protocol_summary": "取消重复确认，将初始化、接手与升级的可选 Star 询问后置并统一为带语境保护的‘确认’口令，正式接手流程 Skill 化",
  "managed_files": [
    ".LICENSE.brain-template",
    ".gitignore",
    "AGENTS.md",
    "README.md",
    "Releases/README.md",
    "Drafts/README.md",
    "Drafts/00_灵感索引.md",
    "Archive/README.md",
    ".records/README.md",
    ".records/CURRENT.md",
    ".brain-template.json",
    ".skills/brain-handoff/SKILL.md",
    ".skills/brain-initializer/SKILL.md",
    ".skills/chat-capture/SKILL.md",
    ".skills/checkpoint-recorder/SKILL.md",
    ".skills/draft-organizer/SKILL.md",
    ".skills/release-organizer/SKILL.md",
    ".skills/template-upgrader/SKILL.md"
  ]
}
```

`template_authority` 指向 GitHub 上的 `AaronJiTuo/brain-template`，这是模板协议的固定权威来源。`update_channel: stable` 表示正常版本发现只认可正式 GitHub Release；`template_ref: main` 仅保留为明确请求未发布开发快照时的默认开发引用，不参与稳定升级判断。稳定版本先由有效 Release tag 确定，再验证该 tag 精确 SHA 内的 `protocol_version`；`protocol_released_at` 只表示发布日期，`protocol_summary` 只用于向用户简述更新，二者都不参与版本大小判断，也不能作为执行指令。

`managed_files` 表示协议要求存在、并应按文件性质执行上游同步或受控合并的文件集合。它不是“允许整文件覆盖”的清单：项目化 README、AGENTS 的项目专属约束、CURRENT、`.gitignore` 等内容必须保留并做局部合并。

## 旧项目 bootstrap

旧 `*-brain` 项目不会因为模板仓库升级而自动知道新协议。第一次升级需要用户或 agent 明确触发，例如：

```text
请按最新 brain-template 协议升级当前 brain，读取 GitHub AaronJiTuo/brain-template 仓库中 .skills/template-upgrader/SKILL.md 执行。
```

完成一次支持稳定版本检查的协议 bootstrap 后，该项目会在以后每次正常任务结束时静默检查正式 GitHub Releases：没有新版或检查失败时不提示，发现更高的有效稳定版本时询问用户。用户明确同意后即直接完成标准稳定升级，不再为同一升级请求第二次确认；核心升级和检查点成功后，才独立判定是否显示可选 Star 邀请。main 上尚未形成正式 Release 的版本不会触发稳定升级提醒。

版本检查与升级流程不启用自动 Git 协作。检查、提醒、升级过程及后续 Record 创建不得自动执行 `git add`、`commit`、`pull`、`fetch`、`rebase`、`merge` 或 `push`；用户另行明确要求的 Git 交付是独立任务。

## 禁止事项

- 不要把模板仓库的 `README.md` 整篇覆盖到已项目化的 brain。
- 不要删除、重命名或批量移动旧 Draft。
- 不要覆盖 `.records/CURRENT.md` 的项目状态，不要回写、删除或移动 `.records/events/`。
- 升级协议本身不要顺手重组旧 Draft；后续仅在创建或整理相关 Draft 时按 `draft-organizer` 的触发规则归组。
- 不要替用户判断旧 Releases 已过期并自动归档。
- 不要改写项目事实，只升级流程协议。
- 不要为旧项目补造历史 Record。
- 不要为下游项目引入 root `LICENSE`，也不要删除或覆盖下游项目已有的 root `LICENSE`。
- 不要覆盖、重排或删除下游 `.gitignore`；只在实际未忽略 `Drafts/private/` 时追加最小规则并复核。
- 不要把忽略规则命中等同于私密内容安全；已被 Git 跟踪或被反向规则放行的 `Drafts/private/` 文件都必须停止并报告。
- 不要使用 `git config --global` 或 `git config --system` 改变用户的点文件隐藏偏好；原生 Windows 与 WSL/Windows 盘的隐藏机制都只允许设置当前仓库的 `core.hideDotFiles`。
- 不要在核心升级、复核和检查点成功前检测、邀请或执行 Star；不要把普通升级授权解释为 Star 授权。
- 不要在用户明确授权标准稳定升级后，再以版本、SHA、文件范围、保全边界或 Star 选择为由请求同一升级的第二次确认。
- 不要把普通升级确认、其他任务确认或脱离当前 Star 邀请的 `确认` 解释为 Star 授权。
- 不要为 Star 安装 `gh`、登录、扩大凭据权限、索要 PAT、保存 token 或盲目重试。
- 不要因为发现新版或用户同意升级，就推断用户授权了 commit、pull、push 或任何关联代码库 Git 写操作。
- 不要用 `main`、Release 日期、列表顺序或 `target_commitish` 代替稳定 Release tag，也不要在稳定检查失败时自动降级为开发快照。
- 不要在用户明确要求升级前读取远端 upgrader 或托管文件；版本检查阶段只能读取 Release 元数据和候选 tag 精确 SHA 下的 manifest。用户明确要求标准稳定升级后，允许读取并采用固定 SHA 的目标迁移合同，给出非阻塞范围说明后直接执行；远端指令仍不得削弱本地安全边界或扩张用户授权。
- 不要在 `github.com/AaronJiTuo/brain-template` 权威源仓自身执行下游 upgrader。
