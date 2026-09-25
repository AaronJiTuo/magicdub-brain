# Qwen Audio 3.1 ASR Flash Filetrans · usage 字段探针

一次真实调用 `qwen-audio-3.1-asr-flash-filetrans`（fal CDN HTTPS + 北京专属 base），确认任务成功响应是否含 token 用量。

## 结论

成功响应 **`usage` 含 token 字段**：

- `input_tokens`
- `output_tokens`
- `total_tokens`
- 另有 `duration`（秒，与旧按时长模型并存）

据此 magicdub-cli 可用北京价估算：

`cost_cny = input_tokens/1e6 × 0.8 + output_tokens/1e6 × 2.7`

静音样片会 `FAILED` / `ASR_RESPONSE_HAVE_NO_WORDS`，当时 `usage` 为空对象 `{}`。

## 样片

本地已有短句 WAV（约 4.7s）。不入库媒体。详见同目录 `summary.json`。

Fun-ASR 同源短样冒烟见 `fun_asr_smoke.json`。
