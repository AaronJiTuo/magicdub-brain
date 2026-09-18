# Demucs 与 SAM 现场声保留对比

用于独立验证声音分离与混音，不修改 magicdub-skills 稳定版。当前已完成 60 秒样片的五组真实请求、费用核对和试听输出；结论见 [RESULTS.md](RESULTS.md)。

## 运行

使用 magicdub-skills 的 Python 3.12+ 环境，依赖 fal-client、requests、python-dotenv、numpy、soundfile，系统须有 FFmpeg。示例（将 CODE_REPO 替换为代码仓库路径）：

```sh
uv run --project CODE_REPO python compare.py pricing
uv run --project CODE_REPO python compare.py run sam1
uv run --project CODE_REPO python compare.py download sam1
uv run --project CODE_REPO python compare.py billing
uv run --project CODE_REPO python analyze.py
uv run --project CODE_REPO python serve.py
```

在本目录运行。`run` 名称可选 demucs、sam1、sam3、baseline1、pcm24；已有结果直接复用，待完成请求读取原 request_id，提交状态未知时不会重提。`serve.py` 输出本机预览地址，仅监听 127.0.0.1。

## 数据与边界

实验固定在 `runs/stevejobs-first60/`：`experiment.json` 记录源项目、截取窗口与参数；`original.wav` 是高品质原音前 60 秒，`original-pcm24.wav` 是仅改变编码的兼容性副本。重建时需从所记录源项目重新准备这些输入，或明确另建实验，不能将其他素材覆盖为同一个请求身份。

`analyze.py` 复用源项目 alignment.json 和已对齐中文音频，只增加本地混音与对比页，不调用 TTS。输入及各请求身份、原始 target／residual、计费量、费用、35 组 WAV／FLAC 试听和测量保存在 runs/ 中；该目录已忽略。凭据仅从用户的 .magicdub/credentials.env 读取，不写入源码或文档。

该程序是一次研究验证工具，未作为正式安装 skill 交付。视觉或数值检查不能替代听感结论，固定时间窗原音保留示范不代表自动检测能力。
