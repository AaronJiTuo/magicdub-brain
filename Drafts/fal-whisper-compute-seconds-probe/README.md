# fal Whisper compute seconds 探测

## 用途

验证 `fal-ai/whisper` 成功返回中是否带有 **compute seconds**，并弄清 Usage 里为何同端点出现 **$0.0008** 与 **$0.00125** 两种单价。

## 运行

```bash
cd Drafts/fal-whisper-compute-seconds-probe
# 普通探测
"/path/to/magicdub-cli/.venv/bin/python" probe.py
# Admin billing 对照需临时 export FAL_ADMIN_KEY（勿写入本目录）
```

## 结论（2026-09-24）

### 用量从哪来

| 表面 | 结论 |
| --- | --- |
| 结果 JSON | **无** compute seconds |
| queue status | **`metrics.inference_time`** |
| 结果头 | **`x-fal-raw-time`**（近似） |
| `x-fal-billable-units` | 本轮常缺失 |
| billing-events（Admin） | 有 `quantity`／`unit=compute seconds`／`unit_price`／`cost_total` |
| Pricing API | 只返回 **`unit_price=0.0008`**，无 0.00125 分档 |

账单 `quantity` 对本轮请求 ≈ **ceil(inference_time)**。

### 为何 Usage 里有两种单价（已核实）

截图与 Admin API 一致：同为 `fal-ai/whisper`，有的事件是 **0.0008**，有的是 **0.00125**。

对照实验（同一 Key）：

| 条件 | unit_price |
| --- | --- |
| 短样例 diarize=false／true／word | **0.0008** |
| ~90s vocals diarize=false／true | **0.0008** |
| sync `fal.run` + diarize=true | **0.0008** |
| 历史请求 `01a0d188-…`（~65s 音频、有 diarization_segments、quantity=4） | **0.00125** |
| 今日同 quantity=4 的长音频 diarize=true | **0.0008** |

因此：**不能**用「是否 diarize」解释单价差。billing-events **也不带** diarize／机型字段；事件结构两边相同，只是 `unit_price` 不同。Pricing API 只公布 0.0008。根因未钉死（可能是历史机型／内部路由／未公开分档）；今日用常规参数**未能复现** 0.00125。

### 对费用估算的含义

热路径若只用 Pricing `0.0008 × ceil(inference_time)`，多数请求会准，但遇到账单实为 0.00125 时会**低估**。更稳：落盘 `request_id` + `inference_time`，需要精确对账时再用 Admin 查 billing-events（勿在热路径狂打）。

原始 JSON 见 `out/`（已 gitignore）。勿把 Admin Key 提交进 Git。
