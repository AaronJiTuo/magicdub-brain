# ADR 002: Public API Is The Only Business Entry

## Status

Accepted.

## Context

MagicDub Cloud 同时服务网站用户和专业 API 用户。如果为网站单独做业务后端，会形成两套产品能力和两套路由。

## Decision

Public API 是唯一业务入口。网站和专业客户都调用同一套 API。

## Consequences

产品能力只实现一次。鉴权可以区分 session/JWT 和 API key，但业务路由、job 模型、asset 模型和状态机保持一致。

前端不能绕过 Public API 直接访问 DB、Queue、R2 私有规则或 worker 内部逻辑。

