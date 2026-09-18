# Codex 与 Grok Bot 双宿主兼容评估

日期：2026-09-16。状态：基于当前源码和官方文档的可行性评估；尚未实施或在 Grok Bot 实机验收。

## 结论与范围

可以朝双宿主兼容改造。建议保留一个 magicdub-skills 仓库、一套 Python 核心程序和项目格式，抽离宿主交互与安装注册差异。核心无需因 Grok Bot 重写，但现有安装包不能直接宣称已兼容。

用户已明确目标是官方 Grok Bot，具有工作区与命令执行能力；不是普通 Grok 聊天或第三方机器人。当前任务是评估，不包含业务代码修改、安装、发布或付费样片执行；正式 Release 的首版 Codex 范围尚未改写。

## 已核实的基础

- 当前实现仓库 HEAD 为 `ffb0e31890ece9f2bf451652446b5e7b0c44d456`（v0.5.0），工作区另有未提交的时长 QA 改动。本次读取当前工作区，没有将本地 QA 当作已发布能力。
- `pyproject.toml` 的依赖为 Python、requests、fal-client、numpy、soundfile、filelock、dashscope 等，媒体处理使用 FFmpeg / ffprobe。未发现必须经 Codex SDK 才能执行的核心路径。
- `src/magicdub/pipeline.py` 的 `translation_batch` / `import_translation` 通过 JSON 交接句号、全文上下文和源摘要；`advance` 返回 `awaiting_translation` 或 `awaiting_duration_qa`，宿主生成文本后继续。不同 agent 可实现同一交接接口。
- Codex 的 SKILL.md 基于开放技能规范，但发现目录和 `agents/openai.yaml` 属于具体宿主约定。[Codex 官方技能文档](https://learn.chatgpt.com/docs/build-skills)
- Grok Bot 官方确认有持久云端计算机、文件、命令行和可按 Bot 启用的私有 skills；公开文档未说明其能直接扫描 Codex 的 `.agents/skills` 及符号链接。[计算机与应用](https://docs.x.ai/grok-bot/computer-and-apps)、[Skills 与 routines](https://docs.x.ai/grok-bot/skills-routines-and-automations)

## 复用与适配清单

| 部分 | 当前实现 | 双宿主建议 |
| --- | --- | --- |
| 转写、分离、TTS、对齐、混音、SRT、费用 | 独立 Python CLI 和供应商 API | 共用核心，在 Grok 执行环境验证依赖、网络和输出 |
| 翻译与时长 QA | 当前 agent 读取 JSON 并回写 | 两端各用自身模型，保持相同协议、有限重做和质量要求 |
| 流程说明 | SKILL.md 及翻译、QA 引用 | 共用业务规则，按宿主加载交互、安装和交付说明 |
| 参数选择 | interaction.md 指定 Codex request_user_input 工具 | 按实际能力调用；无工具时用明确文本收集。每视频三项实际提交后直接执行，不能超时自动代选 |
| 安装注册 | install.py 向单个 skills_dir 建立四入口符号链接 | 共用版本、快照和依赖校验；单独实现 Grok 的实际私有 skill 注册机制 |
| 入口定位 | 从 SKILL.md 的目录推断 ROOT | Grok 若保存指令副本，不能沿用父目录推断；须定位同版本程序与引用 |
| 密钥 | 普通输入后 save-credentials --stdin；环境变量优先 | 共用读取机制，输入按 Grok 能力适配；不能假定其安全输入可注入任意 API key |
| 路径 | home 下安装配置，Movies / Videos 下项目 | Grok 项目使用 /workspace 专用目录，配置安装与视频项目继续分离，验证恢复 |
| 交付 | Codex 本机预览及绝对路径链接 | Grok 返回可下载文件卡片和费用表；只打印云端路径不算交付 |
| 升级与 Star | 正式 Release 校验及可选原生交互 | 共用版本策略，按宿主实际工具处理选项；无工具按既有规则跳过可选动作 |
| 宿主标识 | current_codex、host_codex_cost、codex_discovery | 改为通用字段并兼容旧项目，准确记录执行宿主 |

上述建议不需要新增 Web 服务或恢复 magicdub-cloud。翻译可以由 Grok Bot 自己完成，无需为了适配再建一条 xAI API 调用链；供应商 Key 仍需在实际执行环境配置。

## 不能提前承诺的边界

1. **云端与本机是两套环境。** Grok 的共享工作区为 `/workspace`，手工安装的软件包可能在恢复后需要重建；本机素材和 Key 不会自动同步。多个 Bot 共享文件和命令行凭据，不构成隔离边界。[官方说明](https://docs.x.ai/grok-bot/computer-and-apps)
2. **附件能力需独立核对。** 当前桌面输入单视频上限 200 MB、音频 25 MB、最多六个附件；不代表核心处理上限，也不证明输出附件采用相同限制。大文件要验证其他可用传输方式。[文件与结果](https://docs.x.ai/grok-bot/files-and-results)
3. **审批由宿主决定。** Grok 的 Auto Review 可要求审批或拒绝动作；流程兼容不能承诺取消平台审批。安全密钥输入仅适用于支持的连接，FAL 等凭据的实际配置渠道待验证。[审批与隐私](https://docs.x.ai/grok-bot/approvals-security-and-privacy)
4. **同流程不保证相同听感。** 两端模型分别完成翻译和时长改写，忠实度、自然度、改写轮数和最终试听须分别验收。
5. **独立运行与跨端续跑是不同能力。** 后者须带齐项目和固定 runtime_commit 快照，准备本地环境与凭据，更新绝对路径报告，验证原账号下未完成请求的恢复。同一项目只由一端写入，不能靠复制文件宣称无缝接力。
6. **下载问题独立存在。** 当前 YouTube 下载入口尚未通过真实完整下载验收；Grok 网络出口不等于已解决 CDN 问题。首轮兼容样片使用已有本地视频。

## 最小验证顺序

1. Grok 无付费预检：实际系统、Python 3.12+、uv、FFmpeg / ffprobe、Git / gh、私库权限、持久目录、供应商网络，以及技能注册、选项、密钥和文件回传方式。
2. 固定快照、独立安装与项目目录，验证 doctor、入口发现和重启恢复；保留 Codex 已有安装。
3. 后续实施适配后，用同一段 30～60 秒视频和相同 Whisper / Demucs / IndexTTS 2 参数分别验证三项选择、翻译、QA、导出及视频 / SRT / 费用交付。付费调用属于后续执行任务。
4. 验证中断恢复不重复提交结果未知的请求，成片完整解码、字幕时间和实际试听通过；分别记录 Codex 回归与 Grok 真机证据。
5. 第一阶段验收两端独立译制；跨端搬迁、同机双宿主注册及下载扩展按实际需求另验。

工程判断：核心重写需求低，交互、注册、环境与验收工作量中等。完成 Grok 无付费预检后，才能给出可信排期和最终兼容承诺。
