---
record_id: rec_20260915_023359_c75e2a
occurred_at: 2026-09-15T02:33:59+08:00
kind: finding
domain: operations
certainty: verified
related_artifacts:
  - https://docs.tikhub.io/419083091e0
  - https://github.com/TikHub/TikHub-API-Java-SDK/blob/main/docs/TikHubUserApiApi.md
  - https://platform.snapany.com/zh/console
  - https://platform.snapany.com/zh/console/usage
  - https://platform.snapany.com/zh/docs/credits
  - Drafts/magicdub-skills/2026-09-15_SnapAny解析与计费验证.md
supersedes: null
---

# 核实 TikHub 与 SnapAny 的 YouTube 解析单次成本

## 结果与直接证据

- 本轮通过 TikHub 官方 `GET /api/v1/tikhub/user/get_endpoint_info` 查询 `/api/v1/youtube/web_v2/get_video_streams_v2`，HTTP 200：`endpoint_cost=0.003`、`allow_free_credit=false`、`allow_discount=false`。当前单次列价为 USD 0.003，按项目固定 1 USD = 7 CNY 换算为 **¥0.021000**；该端点不适用通用免费额度或阶梯折扣。
- SnapAny `POST /openapi/v1/extract/post` 每次成功解析扣 **1 积分**。本轮重新读取账户积分明细，2026-09-15 00:43:06 的测试扣 1 个赠送积分，余额 49；此测试实际现金支出 ¥0.00。
- 本轮读取 SnapAny 已登录控制台的支付宝充值选项，套餐为：¥69 / 9,000；¥349 / 50,000；¥1,399 / 230,000；¥3,499 / 650,000；¥6,999 / 1,500,000。每次摊销成本依次为 ¥0.007666666…、¥0.006980、¥0.006082608…、¥0.005383076…、¥0.004666。以套餐金额除以积分数为精确公式，六位小数展示属于舍入值。
- SnapAny 部分积分文档的中档积分数与当前购买界面不同；以本轮实际控制台的 230,000 和 650,000 为本次计算依据，不沿用文档的 225,000 或 700,000。

## 口径与边界

- 计费单位是接口解析；同一次返回的独立视频和音频链接不需要各付一次解析费。再次调用解析接口刷新链接则可能再次产生费用；成功解析后媒体下载失败不能据此认定解析退款。
- 这里核对的是 API 余额扣费或套餐摊销，不含充值支付手续费、真实支付汇率差异、网络服务或后续译制费用。赠送积分与现金支出分开记录。
- TikHub 当前端点列价已直接核实，但未核对历史各次调用的账户扣费流水；旧账本的估算和未知费用不能因此改称已对账。端点信息查询响应带有通用计费提示，未核对该查询自身是否实际收费，不宣称本轮总现金支出为零。
- 本轮未调用新的视频解析、未下载媒体、未修改业务代码、未变更正式规划或执行 Git 交付。此前完整下载验收状态保持不变。
