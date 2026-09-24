# fal billing-events 即时性探测

## 用途

对已有任务的 22 句译文各再跑一次 IndexTTS2，**在 TTS 结果返回后立刻**用 Admin Key 查 `GET /v1/models/billing-events?request_id=…`，记录是否第一时间有事件／费用。可选短重试以观察滞后。

## 运行

```bash
export FAL_ADMIN_KEY='…'   # Admin scope；不要写入本目录
# 模型调用默认读 ~/.magicdub/cli/credentials 的 FAL_KEY

cd Drafts/fal-billing-events-immediate-probe
../../../../magicdub-cli/.venv/bin/python probe.py \
  --task ~/Movies/MagicDub/cli/youtube-SwQPurSL7HI_20260924_114857
```

## 预期

- `results.jsonl`：每句一行（request_id、即时查询与可选重试）
- `SUMMARY.md`：即时命中率、首次命中延迟分布

## 状态

实验用；会产生真实 fal TTS 费用。勿把 Admin Key 提交进 Git。
