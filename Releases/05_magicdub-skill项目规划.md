# magicdub-skills 项目规划

## 1. 项目定位与边界

`magicdub-skills` 是面向 Codex、主要自用的视频处理技能集，也是 MagicDub 当前唯一主动推进的实现项目。首个业务 skill 为视频译制：使用者提供本地视频，由 Codex 协调自带程序与模型 API，完成转写、翻译、配音、时间轴对齐和视频合成，交付新视频。后续字幕等独立工作流复用同一个视频项目。

### 1.1 整体项目收敛

2026-09-13 用户决定取消 `magicdub-cloud`，原 `magicdub` 暂时保留，当前先完成 `magicdub-skills`。不并行推进旧引擎、Cloud 或对外 Web 产品，也不把这些工程作为 skills 的前置依赖。

未来确有 Web 版对外供用户使用的需要时，再决定重启 `magicdub` 仓库或新建仓库；不预设恢复 `magicdub-cloud`，也不预定 Web 架构或排期。技能集主要自用与未来可能公开源码是不同决定；MIT 及已确认首版功能继续保留，公开分发不是当前可用版本的前置条件。

## 来源、证据与替代关系

- [取消 Cloud 并收敛为自用技能集](../.records/events/2026-09/2026-09-13_013354_取消Cloud并收敛为自用magicdub-skills.md)：取消 Cloud、暂留原 magicdub，当前集中完成主要自用的 skills；未来 Web 按实际需要另行启动。
