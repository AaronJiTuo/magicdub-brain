# ADR 003: Website Is An API Client

## Status

Accepted.

## Context

`magicdub.com` 需要给普通用户提供可用网站，但项目目标是只维护一套商用级 API。

## Decision

网站放在 `apps/web`，作为 Public API 的浏览器客户端。网站没有独立业务后端，不定义网站专属 API。

## Consequences

网站和 API 用户共享上传、创建 job、查询状态、下载结果、用量统计等能力。

网站可以使用 `packages/sdk` 和公开 API types，但不能 import 后端内部实现。

