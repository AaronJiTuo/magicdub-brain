---
record_id: rec_20260925_134520_6e1822
occurred_at: 2026-09-25T13:45:20+08:00
kind: milestone
domain: engineering
certainty: verified
related_artifacts:
  - https://github.com/shishengkai/magicdub-cli/releases/tag/v0.2.5
  - Releases/06_magicdub-cli系统设计.md
supersedes: null
---

# 发布 magicdub-cli v0.2.5（修复 --version）

## 结论

用户升级到 v0.2.4 后 `magicdub --version` 仍显示 0.2.3。根因：`cli.py` 读 `__init__.__version__`，该值在发 0.2.4 时未 bump（仍为 0.2.3）；`pyproject`／`constants.VERSION`／uv 包元数据已是 0.2.4，功能代码已装上。

正式 Release **v0.2.5**（`04e4f52`）：`__version__` 改为引用 `constants.VERSION`，避免再漂移。

## 升级

`magicdub update`
