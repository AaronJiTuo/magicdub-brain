# Codex Project Bootstrap Prompt

这是 MagicDub Cloud 主仓。

请先阅读：

- `README.md`
- `docs/product_scope.md`
- `docs/architecture.md`
- `docs/workflow.md`
- `docs/domain_model.md`
- `docs/api_design.md`
- `docs/repo_structure.md`
- `docs/oss_to_cloud_transfer.md`
- `docs/adr/`

OSS 版参考仓库：

```text
https://github.com/OpenSiC-ai/magicdub.git
```

当 Cloud 实现需要确认 pipeline 业务语义、provider contract、媒体转换逻辑、stage 命名、能力边界或命名约定时，应回查 OSS repo。尤其关注：

- `Drafts/程序流程.md`
- `pipeline/`
- `providers/`
- `media/resources.py`

默认约束：

- `magicdub-cloud` 是 private monorepo。
- `magicdub.com` 网站放在 `apps/web`，只是 Public API 的前端客户端。
- 不做单独网站后端，不做网站专属业务 API。
- Public API 是唯一业务入口。
- 外部 API 表现为异步 job。
- 内部也采用异步 orchestration。
- 使用 job/stage/segment 三层状态机。
- worker 尽量无状态。
- DB/R2/Queue 是状态源。
- Cloudflare 负责控制面。
- Modal 负责重执行任务。
- provider 延续 capability-first 思路。
- asset store 只负责上传下载，不被 ASR/TTS/separation provider 直接调用。
- Cloud 版参考 OSS 业务逻辑，但不直接依赖 OSS 的运行时结构。

实现时优先保持 contract 清晰、状态可恢复、worker 幂等、跨 provider 边界明确。

