---
record_id: rec_20260915_025256_b812c9
occurred_at: 2026-09-15T02:52:56+08:00
kind: finding
domain: operations
certainty: verified
related_artifacts:
  - https://platform.snapany.com/zh/docs/transcription
  - https://platform.snapany.com/zh/docs/credits
  - https://platform.snapany.com/zh
  - https://fal.ai/docs/platform-apis/v1/models/pricing
  - https://fal.ai/models/fal-ai/whisper/api
  - https://help.aliyun.com/zh/model-studio/fun-asr
  - .records/events/2026-09/2026-09-14_065908_完成v030新版SteveJobs真实译制验收待用户试听.md
supersedes: null
---

# SnapAny Whisper、fal Whisper 与百炼 Fun-ASR 价格核对

## 已核实单价

- SnapAny 官方转录文档：Whisper large-v3，每分钟 4 积分，不足一分钟按一分钟；提交预扣、失败退回、轮询免费，支持说话人标签。按当前五档套餐的每积分价格，完整一小时音频依次摊销 ¥1.840000、¥1.675200、约 ¥1.459826、约 ¥1.291938、¥1.119840。不把充值积分文档的中档漂移数字用于计算，沿用已核实购买界面的 230,000／650,000。
- fal 官方价格查询 `GET /v1/models/pricing?endpoint_id=fal-ai/whisper` 本轮真实返回 HTTP 200：`unit_price=0.0008`、`unit=compute seconds`、`currency=USD`。固定 1 USD = 7 CNY 后为 ¥0.005600／计算秒；无法直接等同于每音频秒。Whisper 官方 API 文档明确开启 diarize 会增加与说话人分离推理时长相关的费用。
- 阿里云中国站官方文档：百炼 `fun-asr` 录音文件识别，北京 ¥0.000220／输入音频秒，即 ¥0.013200／分钟、¥0.792000／小时；新加坡地域为 ¥0.000260／秒、¥0.936000／小时。这里不采用实时识别价格，不包含限时活动或免费额度。

## 既有样片交叉核对

本轮只读打开视频项目 acceptance_v030_stevejobs_90s_20260914_064159 的 attempts/asr-e2a310318878e300c2bb/01/input.json、status.json、attempt.json。90 秒输入启用 diarize=true、batch_size=64，服务端 inference_time=4.429999828338623，按上述单价估算 ¥0.024808；账本 cost_status=estimated，未取得实际扣款额。样本表明 fal 可能具备较低成本，不能将短片推理速度推广成所有视频的固定音频时长单价。

## 结论与范围

用户补充要求统一按开启说话人分离折算音频时长单价。对应 SnapAny speakerLabels=true、fal diarize=true、百炼 diarization_enabled=true；SnapAny 与百炼公开价格未另列该功能附加费，按其统一转录价格比较。百炼说话人分离要求单声道，多个音轨独立计费，不把多轨价格混入当前单轨对比。

fal 上述样片的音频单价为约 ¥0.016539／分钟、¥0.992320／小时：计算式为 4.429999828338623 × 0.0008 × 7 ÷ 90，再乘 60 或 3600。这是开启说话人分离的单人演讲样本折算，非供应商固定音频时长报价、非一小时实测或已对账扣费。多人对话、其他参数和长度可能改变比率。

SnapAny 下载解析的低价格不能外推到 ASR：即使用最大充值套餐，其整小时转录摊销仍比北京 Fun-ASR 高约 41.39%；最低充值套餐则高约 132.32%。fal 须按真实计算量比较，不能误算成每小时音频固定花费 ¥20.16。

本次仅查询公开文档、fal 价格接口与既有本地记录，没有新建转录任务、上传音视频、消费 SnapAny 转录积分、修改程序、切换模型或执行 Git 交付。未进行三家同音频识别质量对比。
