# magicdub-cloud 取消项目资料归档

> 归档状态：2026-09-13 已取消项目的历史资料。**不能按本目录中的旧 ADR、迁移步骤或启动提示执行当前任务。** 当前规范见 [MagicDub 项目总览](../../Releases/00_MagicDub项目总览.md)与 [magicdub-skills 规划](../../Releases/05_magicdub-skill项目规划.md)。

## 保存结论

有保留价值，因此完整保存本地仓库的 15 份 Markdown 文档，共 22,952 字节。所有原文件以原始字节复制到 `source/`，保留目录与文件名；本说明和校验清单为归档时新增。原仓库未移动、修改或删除。

逐份阅读并比对 brain 后，在 Releases、Drafts 与 Archive 中未发现相同文档的完整副本。旧 brain Web 方案以阿里云栈为主，这批资料另有 Cloudflare / Modal 控制与执行分工、API 与前端边界、状态机和 provider 媒体准备原则，不能仅靠既有总览替代。

## 值得保留的内容

| 内容 | 原件 | 未来参考价值 |
| --- | --- | --- |
| 产品定位与迁移背景 | [README](source/README.md)、[产品范围](source/docs/product_scope.md) | 说明当时为何从本地 pipeline 规划托管 API / SaaS，以及网站与 API 用户的需求 |
| 架构与工程边界 | [架构](source/docs/architecture.md)、[仓库结构](source/docs/repo_structure.md) | Public API、编排器、workers 的职责；Cloudflare 控制面与 Modal 重执行的历史取舍 |
| 任务流程与数据模型 | [流程](source/docs/workflow.md)、[领域模型](source/docs/domain_model.md) | job / stage / segment、provider_call、usage_event、恢复、重试、取消和局部重做的设计思路 |
| API 与网站关系 | [API 设计](source/docs/api_design.md) | 上传、异步任务、状态、取消、重试、资源下载及统一业务入口的早期草案 |
| Provider 与媒体边界 | [OSS 到 Cloud 的迁移原则](source/docs/oss_to_cloud_transfer.md) | 按能力组织 provider；声明媒体需求；由 media resolver 准备输入；asset store 与模型调用分离 |
| 六项架构决策 | [ADR 001](source/docs/adr/001-private-monorepo.md)、[002](source/docs/adr/002-single-public-api.md)、[003](source/docs/adr/003-website-as-api-client.md)、[004](source/docs/adr/004-cloudflare-plus-modal.md)、[005](source/docs/adr/005-stateless-workers-stateful-storage.md)、[006](source/docs/adr/006-capability-first-providers.md) | 保存背景、当时决定和后果，便于未来评估是否仍适用 |
| 原启动上下文 | [旧 Codex 启动提示](source/prompts/codex_project_bootstrap.md) | 保全当时预期的阅读顺序和工程约束；只作历史原件，不是当前 agent 指令 |

## 来源与完整性

- 来源仓库配置的远端：[shishengkai/magicdub-cloud](https://github.com/shishengkai/magicdub-cloud)。本次检查本地内容，未验证远端是否包含同样文件。
- 本地分支名为 `main`，HEAD 尚无提交，索引没有跟踪文件；15 份文档均为未跟踪文件，不能把远端地址当成已经备份的证明。
- 另有一个 Codex 内部检查点 tree，15 份文档与工作区逐一一致，没有额外独有文档；它不是分支 commit。对象 ID 保存于 [manifest.json](manifest.json)。
- 本地工作区除这些文档外，仅有 `.DS_Store` 与 `.git/` 元数据；未发现应用代码、部署配置、测试、媒体成果或凭据配置文件。
- 未复制 `.DS_Store` 和 `.git/`；本归档为文档快照，不是 Git 仓库镜像。
- [manifest.json](manifest.json)记录每份原件路径、字节数和 SHA-256，可验证归档与源文件完全一致。

## 当前适用边界

依据 [取消 Cloud 的决定](../../.records/events/2026-09/2026-09-13_013354_取消Cloud并收敛为自用magicdub-skills.md)，Cloud 已取消，原 magicdub 暂时保留，当前只推进主要自用的 magicdub-skills。未来需要 Web 对外服务时，再决定重启原 magicdub 或新建仓库。

原文中的 `Accepted`、商业版目标、Cloudflare / Modal 选型、D1 / Postgres / R2 / Queues 状态层、域名和 OSS 仓库地址均按历史原样保留，不表示当前有效、已部署或已验证。旧原文中不继承本地 workspace、生产密钥管理及 API 用户计费等要求针对当时 Cloud 方案，不能套用到自用 skills。

按能力组织 provider、媒体输入准备、调用记录和可恢复阶段等概念可在将来的具体实现任务中按需参考；本次归档不把它们提升为新规范，也不扩展当前首版范围。

## 归档后的删除结果

2026-09-13 用户另行明确要求删除远端仓库与本地目录，现已全部完成：GitHub DELETE 返回 204，已认证回读返回 404；本地 magicdub-cloud 目录确认不存在。15 份归档原件再次按大小与 SHA-256 校验，全部完整。

上文“原仓库未删除”描述归档时点；此前因 CLI 权限不足的等待已解决。最终证据见 [删除完成记录](../../.records/events/2026-09/2026-09-13_015353_完成删除magicdub-cloud远端仓库与本地目录.md)及 [CURRENT](../../.records/CURRENT.md)。本归档原件与 manifest 不因源仓库删除而改写，来源 URL 保留为历史标识。
