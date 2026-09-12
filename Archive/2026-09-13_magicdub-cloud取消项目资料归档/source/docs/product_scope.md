# Product Scope

`magicdub-cloud` 是 MagicDub 的托管商业版主仓。它承载 MagicDub Cloud 的网站、Public API、任务编排、异步 workers、基础设施配置和共享 contracts。

## 产品定位

MagicDub Cloud 是一个异步视频配音 API/SaaS 平台。它面向两类主要使用方式：

- 普通用户通过 `magicdub.com` 网站上传视频、查看任务状态、下载结果。
- 专业用户通过 Public API 创建任务、集成自己的系统、接收 webhook、批量处理视频。

网站只是 Public API 的前端客户端。网站不拥有独立业务后端，不定义网站专属业务 API，不绕过 Public API 访问数据库、队列或内部 worker。

## 用户类型

- 普通网站用户：通过浏览器使用产品，关注上传、状态、结果、历史记录和用量。
- 专业 API 用户：通过 API key 使用产品，关注稳定接口、异步 job、webhook、成本和批量能力。
- 内部运维/管理者：关注任务排查、provider 成本、失败率、重试、用户用量和系统健康。

## OSS 与 Cloud 分工

OSS repo:

```text
https://github.com/OpenSiC-ai/magicdub.git
```

OSS 版是本地 reference pipeline，目标是让用户用自己的 provider key 在本地跑通完整视频配音流程。它重视可读性、可运行性和领域逻辑展示。

Cloud 版是异步 API/SaaS 平台，目标是提供可商用的网站和 API。它重视可恢复性、队列化、并发、幂等、计费、权限、可观测性和稳定的外部 contract。

Cloud 版可以参考 OSS 的业务逻辑，但不应照搬 OSS 的 CLI-first UX、本地 workspace 状态源或单进程顺序 runner。

