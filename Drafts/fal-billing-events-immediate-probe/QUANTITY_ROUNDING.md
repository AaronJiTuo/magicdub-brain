# IndexTTS2 quantity 取整规则（对照实验）

数据：probe 的 22 个 `request_id` × billing-events `output_units`，对照 `tmp_tts/<id>.wav` 的 `wave` 时长。

## 结论

**按秒向上取整（ceil / 进一法），不是舍小数（floor），也不是四舍五入。**

有完整对照的 **21/21** 条满足 `output_units == math.ceil(wav_duration_s)`；  
`floor` 命中 0；四舍五入仅偶然命中 7/21。

样例：`4.191s → 5`，`5.224s → 6`，`1.253s → 2`，`2.054s → 3`。

本次样本中**没有恰好整秒**的 wav，因此无法从数据上区分「非整数才 ceil、整数保持」与「始终 ceil」（对整数两者相同）。实现上用 `math.ceil(duration_s)` 即可；若 `duration_s == 0` 需另议（本批无空音频）。

sid=12 当次 billing 查询因 429 未纳入统计；其余 21 条一致。

明细：`quantity_rounding_analysis.json`。
