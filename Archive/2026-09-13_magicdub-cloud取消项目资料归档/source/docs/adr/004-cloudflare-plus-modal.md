# ADR 004: Cloudflare Controls, Modal Executes

## Status

Accepted.

## Context

MagicDub Cloud 的任务特点是 IO 多、webhook 多、异步多、GPU/CPU 重执行可外包。Cloudflare 适合控制面和 serverless orchestration，Modal 适合 ffmpeg、长任务和未来可能的模型执行。

## Decision

Cloudflare 负责 Public API、webhook ingest、orchestrator、queues、R2、auth、rate limit 和轻量控制面。

Modal 负责 ffmpeg、长时间 CPU 任务、大文件处理、转码和未来可能的 GPU/self-host model tasks。

## Consequences

状态机和业务真相留在 Cloudflare/API/DB/R2/Queue 一侧。Modal 不作为业务状态源，不对外暴露为用户 API。

Modal job 中断后，orchestrator 应能根据持久状态重试或恢复。

