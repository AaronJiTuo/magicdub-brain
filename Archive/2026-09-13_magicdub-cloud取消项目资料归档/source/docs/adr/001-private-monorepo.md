# ADR 001: Use `magicdub-cloud` Private Monorepo

## Status

Accepted.

## Context

MagicDub Cloud 初期会同时演化网站、Public API、orchestrator、workers、database schema、provider contracts、queue contracts 和 infra。它们的边界还会高频调整。

## Decision

使用 `magicdub-cloud` 作为 private monorepo。`magicdub` 继续作为 public OSS repo。

## Consequences

跨模块改动可以在同一个 PR 中完成。shared types、schema、SDK 和 worker contracts 可以同步演化。

暂不拆分 `magicdub-api`、`magicdub-web`、`magicdub-worker-*` 等多个 repo。只有当模块边界稳定、团队或发布节奏明显分离时，再考虑拆仓。

