# OpenRouter Fish S2.1 Pro API 对照验证

独立测试 OpenRouter 的 `fish-audio/s2.1-pro` 和 `fish-audio/s2.1-pro-free:free`，验证单次参考音频克隆、短参考、输出格式及官方参数可用性。不修改 MagicDub 模型配置或既有视频项目。

依赖 Python 3.12、httpx、FFmpeg。运行 `python validate.py --output <仓库外实验目录> --baseline <既有 Fish 实验目录> --port 8773`。通过本机 `/credential` 表单临时提供 OpenRouter Key，再以本机 POST `/run` 逐个执行有界测试；请求前写入 pending 凭据，每次只提交一次，结果未知不自动重试。Key 仅保存在进程内存，关闭服务后清除。

结果为逐请求脱敏 JSON、输出音频和汇总报告。HTTP 200 与完整解码不代表音色、情绪或发音已人工验收。

运行 `python render.py --output <实验目录> --baseline <既有 Fish 实验目录>` 构建六组五路试听。用本机静态 HTTP 服务打开 index.html；验证服务 `/finish` 会清空内存凭据并退出。

2026-09-19 已完成：[完整结果](RESULTS.md)。共 30 次真实请求，24 次生成成功、6 次预设边界返回 400；12 次基础克隆全部成功，含 0.24／0.28／0.38 秒未补长参考。42 份新旧试听媒体全部解码通过，旧音频与 PCM 封装数据逐字节一致。平台 Key 用量增量 $0.013785，折算 ¥0.096495。单份逐句克隆可用，标准接口多参考与直接 WAV 不兼容，部分高级参数未证实等价。

成果位于 MagicDub 项目根目录 `experiments/openrouter-fish-20260919/`。本轮测试凭据进程已清空并关闭；未写入密钥，未修改 magicdub-skills、默认模型或原视频项目。听感、标签效果、私有音色管理、WebSocket、并发与完整长片仍未验收。

后续接入（2026-09-19）：用户已要求将两个入口加入 skills，本地源码现已完成五种 TTS 选择、凭据、PCM 无损封装及公共 QA／导出流程；318 项回归和两份真实响应回放通过，未新增 API 费用，尚未发布。上述独立实测仍按原时点保留，详见 [接入检查点](../../../.records/events/2026-09/2026-09-19_024023_接入OpenRouterFish双模型并验证MagicDub逐句配音.md)。
