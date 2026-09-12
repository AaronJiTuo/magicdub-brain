# ADR 006: Capability-First Providers

## Status

Accepted.

## Context

MagicDub 使用 ASR、TTS、LLM、vocal separation、asset store 等多种能力。供应商会变化，如果业务流程按 vendor 组织，会导致 pipeline 被供应商形态绑死。

## Decision

Cloud 版延续 capability-first provider 设计。provider 按能力组织，不按 vendor 组织。provider 声明 media requirement，由 resource/media 层按需准备。

## Consequences

新增 provider 不应迫使 pipeline/orchestrator 重写。

不同 provider 对 URL、base64、local path、same-provider storage 的需求，由 media/resource 层统一处理。

OSS repo 中的 provider 和 media resolver 设计是 Cloud 版的重要参考：

```text
https://github.com/OpenSiC-ai/magicdub.git
```

