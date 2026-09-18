---
record_id: rec_20260918_230433_220fa3
occurred_at: 2026-09-18T23:04:33+08:00
kind: artifact
domain: engineering
certainty: verified
related_artifacts:
  - https://github.com/shishengkai/magicdub-skills
  - .records/events/2026-09/2026-09-18_223401_完成MVSepDnRv3MelSCNet免费API实测.md
  - .records/events/2026-09/2026-09-18_223909_记录用户试听MVSep明显优于Demucs.md
supersedes: null
---

# MVSep DnR v3 · Mel+SCNet 已作为可选分离模型接入源码

## 结果

用户在试听后要求给 magicdub-skills 加入此选项。关联代码在本地提交 b6352c5 之上新增 --separation mvsep-dnr-v3，与 Demucs、SAM 并列；主 skill、设置 skill、交互卡片、CLI、MVSEP_API_KEY 凭据保存和 doctor 同步。新项目冻结模型快照，现有默认模型和用户项目不变。

固定香港 API、sep_type=56、add_opt1=2（Mel+SCNet）、add_opt2=0（直接提取）、add_opt3=0（标准三轨）、output_format=1（PCM16 WAV）、is_demo=0。原声文件直接上传 MVSep。Speech 用于 ASR 和逐句声音参考，背景由 Music＋SFX 合成，不套用原音减人声。

保存提交意图与远端 hash；中断恢复查询同一任务，未知提交不重提。明确认证／限流拒绝或远端失败后继续最多三次；本地结果丢失只恢复下载及合成。原始三轨保留并校验，拒绝错误音轨集合、异常 URL 和无效时长。未修改账号 premium 开关，也没有充值。

单任务历史 credits=0 才确认人民币零费用；非零积分保存数量，现金单价未知则待核实。在途、未匹配历史、网络查询失败均不误报免费。凭据和无关账号历史不写入项目日志。

## 验证与证据

- 273 项完整回归通过（311.12 秒），含新增 MVSep 30 项；Ruff、diff 格式及 51 个分发文件摘要检查通过。仅既有百炼 SDK 弃用提示。
- 既有 60 秒真实 MVSep 回执和三轨经新模块离线回放，背景与 Music＋SFX 逐采样误差为 0；ASR 为 16 kHz 单声道 PCM16，0.24 秒声音参考保持原生规格。删除背景可无新查询／提交恢复，原始实验文件摘要保持不变。
- 开发 wheel 与全部源码模块逐字节一致，实际 scripts/magicdub.py models 入口已列出新模型。
- 核心实现 src/magicdub/mvsep.py，自动测试 tests/test_mvsep.py，说明 docs/acceptance.md、parameters.md、project-format.md；受忽略的 acceptance-local/mvsep-integration 保存完整测试日志、CLI 输出和真实响应回放摘要。

## 状态与边界

这次新增真实 API 请求和费用均为 0；回放与受控测试不等于新集成的远端全长验收。此前独立 API 实测和用户听感反馈另有记录。

源码修改尚未提交、推送、发布或升级日常安装；日常入口仍按已发布快照运行。后续全长测试应明确使用当前源码 checkout 的 skill 与程序入口，并配置 MVSEP_API_KEY。Releases/05 尚未同步此模型和背景合成分支，已在 CURRENT 标记漂移。
