---
record_id: rec_20260923_053643_a7e012
occurred_at: 2026-09-23T05:36:43+08:00
kind: artifact
domain: engineering
certainty: confirmed
related_artifacts:
  - https://github.com/shishengkai/magicdub-cli
supersedes: null
---

# 为 magicdub-cli 增加 install.sh 一句安装

## 结果

代码仓新增 `install.sh`：检测／安装 uv、尽量安装 ffmpeg／ffprobe，再 `uv tool install` 得到 `magicdub`。README 主推：

`curl -fsSL https://raw.githubusercontent.com/shishengkai/magicdub-cli/main/install.sh | sh`

默认安装 ref 为 `main`（可用 `MAGICDUB_REF` 覆盖）。仅 macOS／Linux；Windows 单独说明。

## 背景与理由

冷启动机器常无 uv；单靠 `uv tool install` 无法补齐 ffmpeg。脚本提供尽力一句安装，失败时明确提示。

## 证据与成果位置

- `https://github.com/shishengkai/magicdub-cli`（push 后的 `install.sh`／README）

## 对当前项目的影响

公开／自用安装入口以 README 一句命令为准；系统设计 Release 未改安装权威细节。

## 未完成与下一步

未实测全新空机；Windows 安装脚本未做。brain 规范若需同步安装入口另议。
