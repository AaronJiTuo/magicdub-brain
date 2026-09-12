# OSS To Cloud Transfer

OSS 参考仓库：

```text
https://github.com/OpenSiC-ai/magicdub.git
```

Cloud 版应把 OSS 版作为业务逻辑参考源，而不是运行时依赖。

## Inherit From OSS

继承 capability-first provider 思路。

业务层按能力组织 provider：ASR、TTS、LLM、vocal separation、asset store。不要让 Cloud 业务流程按 vendor 组织。

继承 provider 声明 media requirement 的思路。

provider 应声明自己需要的媒体输入形态，例如 URL、public URL、same-provider URL、base64 或 local path。pipeline/orchestrator 不应硬编码某个 provider 的上传方式。

继承 media resolver 思路。

media resolver 根据 provider 的声明，把已有 media source 转换成 provider 需要的 prepared media。Cloud 版可以把这个思想改造成 asset/R2/temporary file aware 的实现。

继承 asset store 边界。

asset store 只负责上传和下载，不应被 TTS、ASR、人声分离等 provider 直接调用。跨 provider 的媒体传输由 pipeline/resource 层处理。

继承 provider-local docs/config 的组织思想。

每个 provider 应有清晰文档、接口行为说明、环境变量说明和官方 API 链接。Cloud 版生产密钥管理可以不同，但文档仍应靠近 provider 实现。

## Do Not Directly Transfer

不要迁移 CLI-first UX。

Cloud 版对外是异步 Public API 和网站，不是本地命令行工具。

不要迁移本地 task workspace 作为业务状态源。

Cloud 版业务真相应在 DB，文件应在 R2，queue 应只表示待执行事件。

不要迁移单进程顺序 runner 作为生产执行模型。

OSS 的顺序 runner 是业务语义参考。Cloud 版应使用 job/stage/segment 状态机和 worker。

不要迁移 provider-local `.env` 作为生产密钥管理方式。

Cloud 版可以保留 provider-local docs 和 typed config，但生产密钥应由部署平台、secret manager 或环境绑定管理。

## When To Check OSS

当 Cloud 实现不确定以下问题时，应回查 OSS repo：

- 某个 stage 的业务输入输出。
- provider contract 如何表达。
- media requirement 如何影响上传、下载和 base64 转换。
- vocal separation、ASR、TTS、LLM 的业务顺序。
- task state 中哪些字段曾经被 pipeline 使用。
- 命名约定和 capability boundary。

