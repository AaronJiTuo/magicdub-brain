# DeepSeek 费用与缓存探测（2026-09-25）

## 费用字段

- Chat Completions **无**花费字段；用 `usage` token × [人民币定价](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/) 估算。
- `usage` 含：`prompt_cache_hit_tokens`／`prompt_cache_miss_tokens`／`completion_tokens`（可含 reasoning）。

## 缓存是否要特殊写法

据 [Context Caching](https://api-docs.deepseek.com/guides/kv_cache)／[公告](https://api-docs.deepseek.com/news/news0802/)：

- **默认开启**，无需改 API／加特殊参数。
- 命中条件：后续请求与已落盘前缀 **从第 0 token 起完全一致**；中间局部相同不算。
- 缓存按约 **64 token** 为单位；过短内容可能不落盘。
- **不保证 100%** 命中；未用缓存会过期清理。
- 多轮对话续写、或多次请求共用长公共前缀（如长 system）是典型命中场景；公共前缀有时要 **前两次 miss 之后** 才被识别并落盘（见文档 Example 2）。

## 实测（`cache_hit_probe.json`）

同一长 system（约 1074 prompt tokens），连续 4 次 `deepseek-flash`（`thinking` disabled）：

| 次 | hit | miss |
| --- | --- | --- |
| 1 | 0 | 1074 |
| 2–4 | 896 | 178 |

字段始终有值；第 2 次起稳定出现非零 `prompt_cache_hit_tokens`。
