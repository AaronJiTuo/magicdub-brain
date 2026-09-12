# ADR 005: Stateless Workers, Stateful Storage

## Status

Accepted.

## Context

MagicDub Cloud 需要支持 retry、timeout recovery、webhook duplicate、partial rerun 和 worker 重启恢复。如果服务器实例保存业务上下文，系统会很难恢复。

## Decision

worker 和 API 实例尽量无状态。业务真相收敛在 DB，文件状态收敛在 R2，待执行事件收敛在 Queue。

## Consequences

任何 worker 或 Modal 实例挂掉后，只要 DB/R2/Queue 还在，任务应可恢复。

KV/Cache 可以做限流、缓存和短期幂等辅助，但不能作为唯一业务真相源。

