# 保留观众笑声的 Demucs 与 SAM Audio 研究

核对日期：2026-09-14。状态：第 1～8 节保留实测前研究与候选方案，第 9 节记录真实对比，第 10 节记录用户试听验收。用户确认本轮仅 Demucs 成品可用，SAM 各组未通过；尚未实施新的笑声恢复方案。

## 结论

Demucs 的 `stems` 是固定类别选择，不能把 `vocals` 替换为 `speech`、`talk` 或提示词。SAM Audio 支持自然语言描述及时间段提示，更适合研究“只替换讲话、尽量保留笑声”的目标，但不保证仅靠换词就解决。

最新验收已收敛到 Demucs：本轮 SAM 各组未达到可用标准。后续研究以保持 Demucs 整体听感、局部恢复观众反应为方向；下方 SAM 时间段提示等保留为实测前的研究过程，不作为当前已验证方案。

## 1. Demucs 的可调范围

[fal Demucs OpenAPI](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/demucs) 将 stems 限定为 vocals、drums、bass、other、guitar、piano，后两项用于支持它们的六轨模型。没有自由文本、speech、talk、laughter 或指定演讲者的字段。shifts 为 1～10、overlap 为 0～1；它们调节推理稳定性和分块重叠，不改变模型已训练的类别。

[Demucs 官方说明](https://github.com/facebookresearch/demucs#separating-tracks)说明，htdemucs_ft 是在音乐数据上训练的 htdemucs 微调版本，四类输出为 vocals／drums／bass／other；两轨模式也是先完成分离后再合并，不能创造新的声音类别。模型的最大分块长度还受 Hybrid Transformer 的 7.8 秒上限约束，不能机械地提高 segment_length。

具体源码快照为 `facebookresearch/demucs@e976d93ecc3865e5757426930257e200846a520a`：`demucs/separate.py` 检查 stem 是否属于 model.sources；`demucs/remote/htdemucs_ft.yaml` 是四个微调模型的组合。fal 的内部封装实现未公开验证，不能将上游 CLI 的全部选项当成 fal 可传参数。

据此推断：笑声进入 vocals 不一定是一次偶发错误，音乐人声／伴奏分类本身就不等价于讲话／非讲话分类。提高 shifts 或 overlap 可能改变局部效果，但没有“把笑声改分到背景”的语义控制。将另外三条轨相加，同样不能自动找回已经分入 vocals 的笑声。

## 2. SAM 的提示词与时间段

[SAM 官方使用说明](https://github.com/facebookresearch/sam-audio#prompting-methods)建议使用小写、简短的名词或动词短语，例如 `man speaking`。第一轮可对比当前的 `speech` 与 `man speaking`；`talk` 虽是合法文本，但未找到它优于前两者的官方证据。`audience laughing` 可用于后续针对观众声音的提取实验，但这是候选描述，不是官方固定类别。

不要依赖一大段“保留笑声、排除音乐、只删讲话”的指令；未发现 fal 为此提供 negative_prompt。正向描述应明确声音目标，复杂场景再补时间段提示。

[fal 文本分离接口](https://fal.ai/models/fal-ai/sam-audio/separate/api)为 `fal-ai/sam-audio/separate`，提供 prompt、predict_spans、reranking_candidates、acceleration 等参数。其[实际 OpenAPI](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/sam-audio/separate)限制候选数为 1～7；上游 README 的 8 候选示例不能原样传给 fal。输出格式保持 WAV。fal 未在此输入 schema 中开放模型大小、位深、声道或自由指定采样率。

当前 MagicDub 为 `prompt=speech`、`predict_spans=false`、`reranking_candidates=1`、`acceleration=balanced`、`max_chunk_duration=60`、`chunk_overlap=5`、`output_format=wav`。先保持这些参数只比较提示词；随后用胜出的提示词对比 `predict_spans=true`、`reranking_candidates=7`、`acceleration=quality`。后者是质量取向的实验组，延迟／费用可能增加，不是已验证最优值。7 候选属于一次请求内部的模型候选，不等于恰好调用或计费七次；费用按实际记录。

[fal 时间段接口](https://fal.ai/models/fal-ai/sam-audio/span-separate/api)是另一个 endpoint：`fal-ai/sam-audio/span-separate`，可同时传 prompt 与 spans。选仅讲话的片段作为 include=true 示例，选仅观众笑声且没有目标讲话的片段作为 include=false 示例，设置 `trim_to_span=false` 保持完整输出时间轴。

负时间段表示目标声音不在这里，不是简单地把这一段静音。若讲话与笑声同时存在，不能把整个重叠区标成“没有讲话”。[SAM 论文的时间段标注定义](https://arxiv.org/html/2512.18099v1#A1.SS2)与 [fal schema](https://fal.ai/api/openapi/queue/openapi.json?endpoint_id=fal-ai/sam-audio/span-separate)共同约束该用法。自动 predict_spans 也是模型估计，不能替代经过核对的标注。

## 3. 对 MagicDub 更重要的处理改进

当前 `magicdub-skills@9b48fc24667c688e56e9697a4c22c31b2993e482` 的 `src/magicdub/audio_quality.py` 只下载 Demucs vocals 或 SAM target，然后对整个时长做原音减人声；SAM residual 虽出现在响应中，未下载用于混音或对照。没有讲话区域保留原音的独立策略，也没有观众事件恢复。

建议把“识别／声音参考用的人声”与“最终需要替换的讲话”分开定义。模型选项仍可复用，但不能默认所有 vocals 都要删除。

候选混音表达为：最终音频 = 原音 − 讲话区域权重 × 待替换讲话估计 + 中文配音。讲话区域权重平滑变化；确认没有待替换讲话时为零。这样暂停时的笑声、掌声、呼吸与环境尾声可直接保留原始解码音频，避免依赖模型重建。实际导出仍可能经过最终限幅／AAC 编码，不宣称成片与原件字节一致。

不能把 ASR 没有文字直接当成无人讲话，也不能把一句 ASR 的大时间框当作持续讲话。建议结合语音活动、词级对齐和声音事件判断；笑声也可能被语音活动检测判成人声。首轮验证应人工确认少量片段作参照，再评估自动边界。边界需覆盖词尾及必要的混响，平滑衔接并检查英文残留、抽吸和爆音。

优先分离发生在原音上。若已有 Demucs 结果，对其中 vocals 再用 SAM 提取笑声并补回，可作为旧成品的局部修复备选，但不能直接叠加从完整原音提取的全量笑声，否则可能重复原背景中已经保留的部分；也要避免带回英文。该两次分离路径不作为首选常规链路。

## 4. 保真度与声道限制

SAM 官方[预处理源码](https://github.com/facebookresearch/sam-audio/blob/bb4c6999d2677c7402360e426afc01ddfad6dce0/sam_audio/processor.py#L23-L36)会平均声道形成单声道；fal schema 的 sample_rate=48000 是输出信息，不能据此推断原生立体声。是否在服务封装中另做声道处理、实际输出几声道仍需探测验证。

[SAM 论文](https://arxiv.org/html/2512.18099v1#S3)和模型源码说明 target 与 residual 由生成式模型联合生成；不能假设两者相加严格还原原波形，或 residual 必定比本地相减更保真。

因此实验应同时保存 target 和 residual，比较原音减 target、模型 residual 两种背景；核对时延、增益、讲话残留和笑声保真。输入立体声时，将单声道 target 等量从左右声道扣除不能保证消除偏向一侧的讲话。确认无讲话的区域直接保留原立体声可以缩小损失范围，但无法单独解决重叠区的空间重建。

不建议靠降低全局 Alpha 恢复笑声：这会同时放回原英文。也不建议用 TTS 新造笑声替代原观众反应。

## 5. 最小实测方案与验收

先从用户指出的具体成片中定位三类短片段，每类约 10～20 秒并保留边界上下文：纯讲话；讲话停顿后的笑声／掌声；讲话与观众反应重叠。保留相同输入和响度参考，不先重译或重新生成 TTS。

第一轮比较既有 Demucs 缓存、SAM speech、SAM man speaking。第二轮在较好提示词上比较自动时间段／质量参数和正负时间段示例，再比较两种背景及非讲话区原音保留策略。必要时才增加单一参数消融或同配置重复，以区分随机输出和真实改善，不一次重跑整片或所有组合。

验收观察：笑声／掌声是否完整且音色、尾声、左右空间感自然；英文是否有残留；纯讲话是否漏删或截尾；交界是否有突变；是否出现原片没有的声音。波形能量、声道数和回转写仅为辅助，最终使用同响度 A/B 试听原音、背景与译制混音。各次失败／重试费用均纳入人民币账本。

本轮完成文档与代码研究，没有模型请求、程序修改或成片修复。后续是否采用 SAM、时间段入口与新混音规则，应按小片段实测决定，并沿用每个视频独立选择模型的交互约定。

## 6. fal 其他模型的初步评估

2026-09-14 追加核对公开 Model Search API、Explore、模型页、OpenAPI 和原厂文档。目录查询 separation、isolation、stem、denoise、audio enhance 分别找到 SAM 三接口、ElevenLabs Audio Isolation、Demucs、DeepFilterNet 3，目录均返回 active。Lava SR 和 Nova SR 返回 deprecated。搜索目录存在关键词覆盖差异，另一次 music separation 查询触发 HTTP 429；本次不是所有社区部署的穷举，也没有验证实际推理授权或成功响应。

| 选项 | 官方公开功能 | 对本次目标的初步判断 |
| --- | --- | --- |
| SAM 文本／时间段 | 指定声音目标，返回 target 和 residual；时间段接口还可提供正负示例 | 语义控制最贴近讲话与观众反应的区分；优先测试时间段加简短描述 |
| SAM 视觉引导 | 通过视频中的目标遮罩分离对应声音，使用适配视觉提示的 -tv 变体 | 人物一直在画面中时值得后续尝试；需要遮罩，切镜头和画外讲话增加处理难度，不作第一轮首选 |
| ElevenLabs Audio Isolation | 提取／增强讲话；fal 输入仅 audio_url 或 video_url，输出清理后音频 | 是值得加入的独立对照；无提示词、目标说话人或 residual 输出，不能保证笑声归属和相减后的背景质量 |
| DeepFilterNet 3 | 降噪和语音增强；fal 可选 WAV／FLAC 等，输出增强后的音频 | 更适合噪声干扰问题；缺少声音类别／时间段控制，不优先承担现场背景重建 |
| Demucs／MDX 系列权重 | 音乐固定分轨 | 继续作基线；更换同接口权重无法新增讲话／笑声分类 |
| Lava SR／Nova SR | 语音增强／超分辨率，当前目录标为 deprecated | 不作为新的稳定依赖，且功能不等于声音目标分离 |

以上优先级是依据功能机制的判断，不是同场景胜率；没有依据提供 80%／90% 等成功概率。未找到公开的 fal Spleeter、BS-RoFormer、Resemble Enhance 独立端点；同名／同供应商品牌的 TTS 或音乐生成接口不计入分离候选。

来源：[ElevenLabs 的 fal API](https://fal.ai/models/fal-ai/elevenlabs/audio-isolation/api)、[ElevenLabs 原厂说明](https://elevenlabs.io/docs/overview/capabilities/voice-isolator)、[DeepFilterNet 的 fal API](https://fal.ai/models/fal-ai/deepfilternet3/api)、[DeepFilterNet 上游](https://github.com/Rikorose/DeepFilterNet)、[SAM 视觉接口](https://fal.ai/models/fal-ai/sam-audio/visual-separate/api)。fal ElevenLabs 的 OpenAPI 输入不含 output_format，页面示例为 MP3；不能据此保证所有返回一定是 MP3，也不能直接使用其他 ElevenLabs 接口的输出格式参数。相减前必须验证实际格式、时延、增益与波形失真。

## 7. 初步收敛后的推荐实验

以较高的目标匹配程度和较小实施范围为依据，建议第一轮采用“SAM 时间段分离＋确认无讲话区保留原音”，ElevenLabs 作为独立对照，旧 Demucs 作基线；第 5 节的完整提示词消融可在有歧义时补做，不必先跑遍所有模型。

候选 SAM 配置：span-separate、prompt=man speaking、经核对的纯讲话正例及纯笑声负例、reranking_candidates=7、acceleration=quality、trim_to_span=false、output_format=wav，分块 60 秒／重叠 5 秒。此接口不传文本接口专用的 predict_spans。仍需要处理单声道输出和原立体声的差异，不能为追求干净人声而把整个背景替换成单声道。

选择总计约 30～60 秒且覆盖三类场景的原片段，保存相同输入及原始两路结果。先独立比较原音、原音减 target、SAM residual，再按讲话区域权重保留停顿区原音，形成配音混音试听；同原片、同时间窗和同响度比较。可复用时间轴匹配的已有 TTS，不先重译全片。若需要人工标注少量片段作试验参照，须将其与后续自动执行能力区分；字幕空白不能自动等同没有讲话。

主要通过条件：确认无讲话区的观众反应保留；重叠区笑声明显改善且没有可辨英文残留；没有新的明显失真、空间感塌缩或切换突变。失败结果与费用照常保存，不直接替换默认链路。

价格仅作本次规划估算：fal SAM 页面为每 30 秒基础 USD 0.05，每个额外候选增加 USD 0.025，因此 7 候选、60 秒约 ¥2.80；ElevenLabs 为每分钟 USD 0.10，即约 ¥0.70；合计约 ¥3.50。按固定汇率 7 换算，未包含重试、额外对照／Demucs 重新推理或服务实际计费粒度差异，不作为已发生费用。来源：[SAM 时间段价格](https://fal.ai/models/fal-ai/sam-audio/span-separate)、[ElevenLabs 价格](https://fal.ai/models/fal-ai/elevenlabs/audio-isolation)。

本轮仍仅评估和推荐；方案尚未由用户选定实施，没有调用模型、改写代码或升级安装。


## 8. 成本核对与暂不优先使用 ElevenLabs

2026-09-14 用户要求先估算费用，并表示不太想使用 ElevenLabs：若组合成本已接近其整套 Dubbing，继续自建链路需要有足够的控制与效果价值。本节更新第 7 节的建议优先级；此前的 SAM 7 候选＋ElevenLabs 对照从未启动，也不是用户确认的新默认。暂不将 ElevenLabs 纳入必测组，先考虑成本较低的 SAM 配置与本地原音保留。

本轮重新读取 fal 官方模型页面；Demucs 页面正文读取器漏掉价格，直接读取同页公开 HTML，确认 endpointBilling 的 price=0.0007、billing_unit=seconds，与可见价格段一致。以下按固定 1 美元＝7 元人民币计算，为标价估算；时长按处理音频、输出时长与各接口的实际计费规则计算，不是 GPU 墙钟时间。表格金额各自四舍五入，不将显示后的单分钟值再乘时长。

| 方案 | 官方美元标价 | 1 分钟 | 10 分钟 | 60 分钟 |
| --- | --- | --- | --- | --- |
| Demucs | 0.0007／秒 | ¥0.29 | ¥2.94 | ¥17.64 |
| DeepFilterNet 3 | 0.001／秒 | ¥0.42 | ¥4.20 | ¥25.20 |
| SAM，1 候选 | 每 30 秒 0.05 | ¥0.70 | ¥7.00 | ¥42.00 |
| SAM，3 候选 | 每 30 秒 0.10 | ¥1.40 | ¥14.00 | ¥84.00 |
| SAM，7 候选 | 每 30 秒 0.20 | ¥2.80 | ¥28.00 | ¥168.00 |
| ElevenLabs Audio Isolation | 0.10／分钟 | ¥0.70 | ¥7.00 | ¥42.00 |
| ElevenLabs Dubbing（完整译制） | 0.60／分钟，向上取整分钟 | ¥4.20 | ¥42.00 | ¥252.00 |

前六行仅分离／增强，不包含 ASR、翻译、TTS、QA 重做。最后一行是完整 Dubbing 服务，每个请求分钟数向上取整，例如 90 秒按 2 分钟约 ¥8.40；这里是 fal 的按量价格，不混用 ElevenLabs 官网订阅套餐价格。其他接口的计费粒度、分块与重叠、实际生成长度及重做可能影响账单。

SAM 的文本、时间段、视觉三个接口公开使用同一价格规则：每 30 秒基础 0.05 美元，每个额外候选再加 0.025 美元。因此 7 候选是 1 候选的 4 倍费用，并非 7 倍；加入时间段提示本身没有单列附加费。视觉方案的遮罩准备不包含在模型标价内，暂不作为第一轮方案。

ElevenLabs 分离约为当前 Demucs 的 2.38 倍，与 SAM 单候选同价，不能笼统说它一定比 SAM 贵。未有本次素材的试听结果，也不能把价高或品牌当作保留观众笑声的证据。DeepFilterNet 虽便宜，但任务偏降噪，不因此成为首选。

IndexTTS 2 当前公开价为每生成音频秒 0.002 美元，约每分钟配音 ¥0.84。举例：10 分钟素材、第一次配音计费总时长也约 10 分钟，SAM 7 候选＋该次 TTS 约 ¥36.40，尚未包含 ASR、Codex／LLM 和 QA 重做，已经接近 fal ElevenLabs Dubbing 的 ¥42.00。SAM 单候选＋同样 TTS 则约 ¥15.40。该例不代表实际所有素材的总账单；逐句计费和重复生成以请求账本为准。Whisper 页面本轮显示 0／compute second，缺乏进一步可靠收费证据，不将它当成免费，也不据此补出虚构的完整 MagicDub 总价。

修订后的建议（尚待选择与实测）：Demucs 缓存作基线；先用 60 秒、含纯讲话／纯笑声／重叠的样片比较 SAM 时间段提示的 1 与 3 候选，其他参数一致，模型估算合计 ¥2.10；再比较确认无讲话区保留原音的混音方式，本地混音不新增模型费用。若已有同一输入、同一配置的可用候选缓存，可以复用，避免重复调用。只在少量困难片段考虑 7 候选，先证明效果增益再讨论整片默认。SAM 的开源背景也不等于 fal 托管免费。

定价来源（2026-09-14 核对）：[Demucs](https://fal.ai/models/fal-ai/demucs)、[DeepFilterNet 3](https://fal.ai/models/fal-ai/deepfilternet3)、[SAM 文本](https://fal.ai/models/fal-ai/sam-audio/separate)、[SAM 时间段](https://fal.ai/models/fal-ai/sam-audio/span-separate)、[SAM 视觉](https://fal.ai/models/fal-ai/sam-audio/visual-separate)、[ElevenLabs 分离](https://fal.ai/models/fal-ai/elevenlabs/audio-isolation)、[ElevenLabs Dubbing](https://fal.ai/models/fal-ai/elevenlabs/dubbing)、[IndexTTS 2](https://fal.ai/models/fal-ai/index-tts-2/text-to-speech)。

本轮仅核价、估算并保存用户偏好，没有付费推理、代码修改、默认切换、安装升级或 Git 交付。仍需小样片确认笑声保留、英文残留、声道与听感。


## 9. 首轮实际对比与计费口径更正

2026-09-14 用户同意执行 Demucs／SAM 对比，并提醒 compute seconds 与 audio duration 必须区别。现已完成 60 秒同源样片、五次请求及试听交付，详见 [实验结果](laughter-separation-compare/RESULTS.md)。本轮不是已验证的新默认。

Demucs 的计费 header 为 60 音频秒，推理实际约 5.224 秒；SAM 1／3 候选分别返回 2／4 个计费单位。Whisper 实时价格单位明确为 compute seconds，现有程序对此采用 inference_time 估算。因此第 8 节“不是 GPU 墙钟时间”的说法只应限定到已核定按音频输出收费的端点，不能泛化到 Whisper 或全部 fal 模型；前述 Demucs／SAM 价格估算本次被返回计费量支持。

两组 SAM 时间段 FLOAT 输入均近乎未提取讲话，补测 speech／balanced 文字 FLOAT 也相同；仅换 PCM24 输入后提取信号恢复，提示格式兼容／预处理问题值得进一步验证，但一次试验不能排除随机性。PCM24 相减背景讲话参考区仍只下降约 4.36 dB，Demucs 约 36.98 dB；当前不建议替换。Demucs 也将观众反应候选短窗降低约 16.45 dB。交付时具体事件与主观保真度尚待用户试听；后续整体听感验收见第 10 节，具体时间点仍未取得人工标注。

五次 API 成功及所有效果不合格结果均记费，合计估算 ¥3.794000，依据 billable units × 实时单价 × 7；账单读取 403，未宣称已确认扣款。未新增翻译、TTS 或 QA 调用。

已交付模型分离、相减／直接 residual 背景、复用中文配音以及局部保留原音的独立试听版本。固定窗口恢复不等于自动无讲话检测，也不计作模型能力。当前只增加验证程序与 brain 记录，没有业务代码、默认模型、安装或 Git 交付变更。

## 10. 用户试听验收

2026-09-14 用户实际试听后确认：Demucs 虽损失部分笑声，整体效果仍是最好的，也是本轮唯一达到可用成品标准的结果；SAM 各组最多只能算草稿，均未通过听感验收，包括 PCM24 补测。该结论针对本次素材和所测配置，不泛化为 SAM 在所有场景下无效。

继续保留 Demucs 作为实际使用基线。后续应在保住整体听感的前提下研究笑声恢复；固定时间窗保留原音仍是示范，未获得独立验收，更没有完成自动检测。此次仅补充用户反馈，没有新增测试、费用或业务代码修改。详见 [实验结果](laughter-separation-compare/RESULTS.md#用户试听验收2026-09-14)。
