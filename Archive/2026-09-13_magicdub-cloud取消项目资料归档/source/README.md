# MagicDub Cloud Transfer Pack

这是给 `magicdub-cloud` 的迁移启动包。它用于把当前 OSS 版 MagicDub 中已经确定的产品边界、架构原则、业务流程和 Codex 上下文迁入新的 Cloud 版 private monorepo。

迁移方式：

1. 在新建的 `magicdub-cloud` repo 中，把本目录内部的所有内容移动到 repo 根目录。
2. 不要把 `transfer/` 作为新 repo 的长期目录。
3. 移动后，新 repo 根目录应直接包含 `README.md`、`docs/`、`prompts/` 等内容。

OSS 参考仓库：

```text
https://github.com/OpenSiC-ai/magicdub.git
```

这个 OSS repo 是 Cloud 版的业务逻辑参考源。实现 Cloud 版时，如果需要确认 dubbing pipeline 的业务语义、provider contract、media resolver、媒体输入形态、顺序 pipeline 或命名约定，可以回查 OSS repo。

但 Cloud 版不应直接依赖 OSS repo 的运行时结构。Cloud 版应保留 OSS 的领域原则，重建适合异步 API/SaaS 平台的执行模型。

建议新 repo 初始阅读顺序：

1. `docs/product_scope.md`
2. `docs/architecture.md`
3. `docs/workflow.md`
4. `docs/domain_model.md`
5. `docs/api_design.md`
6. `docs/repo_structure.md`
7. `docs/oss_to_cloud_transfer.md`
8. `docs/adr/`
9. `prompts/codex_project_bootstrap.md`

