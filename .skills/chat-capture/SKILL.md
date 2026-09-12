# chat-capture

## 什么时候使用

当用户希望把 ChatGPT、Gemini、豆包或其他 AI 聊天页面 / 分享链接中的完整对话抓取下来，并保存为当前 `*-brain` 项目的 Draft 时，使用本 skill。

本 skill 负责抓取和输出格式；目标目录必须同时按 `.skills/draft-organizer/SKILL.md` 判断。

典型触发包括：

- 用户给出 ChatGPT / Gemini / 豆包等对话分享链接，并要求“保存”“抓取”“沉淀”“归档”“转成 Draft”。
- 用户要求“完整抓取长对话”“不断滚动直到加载完”“确保内容完整”。
- 用户要求从已登录浏览器里的 AI 对话页面提取内容。
- 用户说“把这段聊天保存到 brain / Drafts”。

仅当用户只是讨论某个链接内容、没有表达保存或抓取意图时，不自动落盘。

## 核心原则

- 使用真实浏览器自动化页面，不要只用 `fetch` 或静态 HTML 抓取。
- 长对话必须在滚动过程中持续采集和去重，不要等滚动结束后只抓一次 DOM。
- 默认只保存一个 Markdown Draft，不额外保存 `.html` 或 `.json`。
- 对话正文保持原样，不改写正文中的 Markdown 标题层级。
- 说话人边界用独立、整行高对比的 HTML marker 表示：用户使用蓝色，assistant 使用绿色；不使用 Markdown 标题，也不包裹正文。
- 最终 Draft 只保存正式对话消息，不保存 LLM 的思考过程；思考过程对后期阅读和项目沉淀无用。
- 平台展示的搜索过程、工具调用过程、调试日志等非正式消息默认不写入 Draft，除非用户明确要求保留。
- 如果无法证明完整，应在 Draft 中明确标记 `capture_status: partial` 或 `capture_status: uncertain`，不要假装完整。
- 采集页面地址在持久化前必须脱敏；Cookie、token、签名参数、认证信息和登录态私有 URL 不得写入 Draft。

## 推荐工具

优先使用 Playwright 或同等级真实浏览器自动化能力。需要登录态时，优先使用用户已经登录的浏览器页面或浏览器上下文。

不要把“页面打开成功”视为“内容抓取完整”。ChatGPT、Gemini、豆包等页面可能使用懒加载或虚拟列表，只有滚动到特定位置才加载更多消息。

## 采集流程

1. 确认输入。
   - URL 只在本次采集过程中临时使用；落盘时必须按第 2 步生成脱敏后的来源字段，不直接复制浏览器地址栏或用户提供的完整 URL。
   - 记录平台和期望主题名。
   - 如果用户未提供主题名，从页面标题、首条用户消息或对话主题中提炼一个简短文件名。
   - 文件名格式为 `YYYY-MM-DD_对话主题.md`，不要在文件名中加入平台名。
   - 按 `.skills/draft-organizer/SKILL.md` 选择路径：已有匹配主题目录时保存到该目录；加入后同主题达到 3 个文件时创建主题目录并归组；否则可暂存于 `Drafts/` 根目录。

2. 打开页面。
   - 优先打开用户提供的分享链接。
   - 如果分享链接无法访问、内容明显缺失或不是最新内容，改用已登录浏览器里的原始会话页面。
   - 持久化来源前移除 URL 中的用户名、密码、query 和 fragment；包含 token、签名、临时访问凭据或其他无法可靠脱敏信息时，不保留该 URL。
   - 只有确认是可公开、稳定访问的分享链接时，才写入脱敏后的 `source_url`。登录态原始页面、私有会话页或无法安全持久化的地址使用 `source_url: omitted`，并写 `source_access: authenticated_private_page`。
   - 如果安全分享链接和登录态原始页面都使用过，只保存安全分享链接；在“采集说明”中说明曾使用登录态页面补采，不保存其地址。
   - 不读取、记录或导出 Cookie、Authorization header、local storage token 或其他会话凭据。

3. 识别滚动容器和消息节点。
   - 不同平台只应在选择器、说话人识别、加载触发方式上做适配。
   - 通用流程保持一致：打开页面、滚动触发加载、持续提取、去重、完整性判断、写入 Draft。

4. 持续滚动并采集。
   - 不要只在最后抓取一次 DOM。
   - 每滚动一屏或每次触发加载后，立即提取当前可见消息。
   - 用 `role + normalized_text_hash + approximate_order` 去重并累积消息。
   - 如果页面是虚拟列表，旧消息可能从 DOM 中消失；持续累积可以避免丢失。

5. 自动探测滚动方向。
   - 默认使用 `auto` 模式：先尝试向上和向下滚动，观察消息数量是否增长。
   - 根据页面行为选择 `top-to-bottom` 或 `bottom-to-top`。
   - 如果页面初始停在中部或底部，应先尝试到达对话开头，再顺序采集到结尾。

6. 判断加载完成。
   - 至少组合以下条件，不要只依赖 `scrollHeight`：
     - 连续多轮滚动后消息数量不再增长。
     - 滚动容器位置和高度稳定。
     - 页面短暂进入网络空闲状态。
     - 页面没有明显 loading spinner、skeleton 或“加载更多”状态。
     - 首条和末条消息在多轮采集中保持稳定。
   - 如果用户提供了开头或结尾锚点关键词，必须用锚点验证是否抓到对应位置。

7. 过滤思考过程。
   - 在生成 Draft 前，必须从采集结果中移除 LLM 的思考过程、推理过程、分析草稿、搜索过程、工具调用过程和平台调试消息。
   - 只保留用户实际发送的内容，以及 assistant 面向用户的最终回复。
   - 如果思考过程和最终回复在 DOM 中混在同一条 assistant 消息里，应优先使用平台提供的最终回答容器；无法可靠拆分时，在“采集说明”中标记风险，不要把思考过程原样落盘。
   - 记录被移除的非正式消息数量或片段数量，用于完整性说明。

8. 生成 Draft。
   - 使用本 skill 下方的 Markdown 格式。
   - 正文不做标题降级，不重写用户或 assistant 的 Markdown。
   - 只在每条消息前插入带内联样式的 HTML speaker marker；用户和 assistant 必须使用不同颜色。
   - 不写入任何 LLM 思考过程。

9. 复核。
   - 确认文件路径在 `Drafts/` 或其主题目录中，并符合 `.skills/draft-organizer/SKILL.md`。
   - 确认文档只有一个 `#` 顶级标题。
   - 确认每条消息前都有 `<div data-speaker="..." style="...">` marker，且角色颜色、图标和标签符合本 skill 的映射。
   - 确认 frontmatter 中有采集状态和完整性说明。
   - 确认 frontmatter 位于文件第一行，且 `source_url` 不含用户信息、query、fragment、token、签名参数或登录态私有地址；无法安全保留时必须为 `omitted`。
   - 确认最终 Draft 中没有 LLM 思考过程、搜索过程、工具调用过程或调试日志。

## Markdown 输出格式

Draft 文件必须使用以下结构：

```md
---
source_url: "https://chatgpt.com/share/..."
source_access: public_share
source_platform: chatgpt
captured_at: 2026-07-12
capture_status: complete
message_count: 42
scroll_rounds: 18
removed_nonfinal_count: 3
capture_method: playwright
---

# 对话主题

## 采集说明

- 完整性：连续 5 轮滚动后消息数不再增长，首尾消息稳定，页面无加载状态。
- 内容过滤：已移除 LLM 思考过程、搜索过程或工具调用过程；最终 Draft 只保留正式对话。
- 备注：如使用登录态原始页面补采，在这里说明。

<div data-speaker="user" style="display:block; width:100%; box-sizing:border-box; margin:1.5em 0 0.75em; padding:0.7em 1em; border-radius:6px; background:#0969da; color:#ffffff; font-size:1.25em; font-weight:700; line-height:1.4;"><strong>👤 001 用户说：</strong></div>

这里是用户说原文。

<div data-speaker="assistant" style="display:block; width:100%; box-sizing:border-box; margin:1.5em 0 0.75em; padding:0.7em 1em; border-radius:6px; background:#1f883d; color:#ffffff; font-size:1.25em; font-weight:700; line-height:1.4;"><strong>🤖 002 ChatGPT 说：</strong></div>

## 这里仍然是 assistant 原文里的二级标题

正文内容不需要降级。
```

规则：

- frontmatter 必须从文件第一行开始，结束后空一行再写 `# 对话主题`；分隔线使用 `---`。
- 文档只允许一个 `# 对话主题` 顶级标题。
- `source_access` 使用 `public_share` 或 `authenticated_private_page`；后者必须配合 `source_url: omitted`。
- `source_url` 不得包含 userinfo、query、fragment、token、签名参数或登录态私有地址；没有可安全持久化的公开地址时使用 `omitted`。
- 说话人 marker 使用英文半角双引号。
- marker 必须保持为一行 HTML，独立成行；后面空一行，再写消息正文。
- 用户 marker 固定使用蓝色 `#0969da` 和 `👤`，assistant marker 固定使用绿色 `#1f883d` 和 `🤖`，不要按平台随意换色。
- marker 必须保留 `width:100%`、背景色、白色大号粗体和 `<strong>`；`<strong>` 与角色图标是渲染器过滤内联样式时的降级提示。
- marker 不包裹正文，避免 Markdown 渲染器在 HTML block 内不解析 Markdown。
- 消息正文保持原样；不要为了层级整洁而改写正文里的 `##`、`###`。
- 消息正文只允许是正式对话内容；不要把 LLM 思考过程作为正文保存。

## 思考过程过滤

最终落盘的 Draft 不保存 LLM 的思考过程。这里的“思考过程”包括但不限于：

- 平台以“思考中”“已思考”“推理”“Reasoning”“Thinking”等形式展示的中间过程。
- assistant 生成最终回答前的分析草稿、计划草稿、自我检查文字。
- 搜索过程、工具调用过程、浏览过程、调试日志、系统内部事件。
- 与用户可读最终回复并列展示、但明显不是正式回复正文的折叠块或过程块。

处理规则：

- 采集阶段可以临时读取这些节点，用于判断页面加载状态；生成 Draft 时必须移除。
- 如果平台把思考过程和最终回复分成不同 DOM 节点，只提取最终回复节点。
- 如果平台把思考过程折叠在同一条消息内，优先按可访问标签、按钮文案、CSS class、ARIA label 或相邻结构识别并剔除。
- 如果无法可靠区分，宁可在“采集说明”里标记 `capture_status: uncertain`，也不要把疑似思考过程写入正文。
- 被移除数量写入 frontmatter 的 `removed_nonfinal_count`；如果无法精确计数，使用 `removed_nonfinal_count: unknown` 并在“采集说明”解释。

## 说话人 marker

用户与 assistant 使用以下固定格式；只替换序号和 assistant 的展示名称，不改写样式：

```md
<div data-speaker="user" style="display:block; width:100%; box-sizing:border-box; margin:1.5em 0 0.75em; padding:0.7em 1em; border-radius:6px; background:#0969da; color:#ffffff; font-size:1.25em; font-weight:700; line-height:1.4;"><strong>👤 {index:03d} 用户说：</strong></div>

<div data-speaker="assistant" style="display:block; width:100%; box-sizing:border-box; margin:1.5em 0 0.75em; padding:0.7em 1em; border-radius:6px; background:#1f883d; color:#ffffff; font-size:1.25em; font-weight:700; line-height:1.4;"><strong>🤖 {index:03d} {speaker_label}说：</strong></div>
```

常见映射：

- 用户：蓝色背景、`👤`、`用户说：`。
- ChatGPT：绿色背景、`🤖`、`ChatGPT 说：`。
- Gemini：绿色背景、`🤖`、`Gemini 说：`。
- 豆包：绿色背景、`🤖`、`豆包说：`。
- 系统或工具消息：仅在用户明确要求保留时使用 `data-speaker="system"` 或 `data-speaker="tool"`。

如果平台无法可靠区分 assistant 名称，使用平台名作为 `speaker_label`；如果平台也无法确认，使用 `AI`。

`style` 可能被严格的 Markdown 渲染器清洗，因此 marker 不能只靠颜色表达角色：必须同时保留 `data-speaker`、`<strong>`、角色图标、序号和说话人文字。不要为了兼容性改用 Markdown 标题；这会重新引入正文标题层级冲突。

## 完整性状态

`capture_status` 只能使用以下值：

- `complete`：满足多条件稳定判定，且没有发现缺口。
- `partial`：已知缺失部分内容，例如页面无法继续加载、登录态不可用、平台限制访问。
- `uncertain`：没有明确缺口，但也无法证明完整，例如滚动行为异常、消息虚拟化严重、锚点未验证。

如果状态不是 `complete`，必须在“采集说明”里写明原因和下一步建议。

## 平台适配要求

适配 ChatGPT、Gemini、豆包等平台时，优先维护以下最小差异：

- 消息节点选择器。
- 说话人识别规则。
- 主要滚动容器识别规则。
- 加载状态选择器。
- 分享链接与登录态原始页面的 URL 识别规则。

不要为每个平台复制一整套流程。通用采集、去重、完整性判断和 Markdown 输出格式必须保持一致。

## 禁止事项

- 不要只抓首屏内容。
- 不要只滚动一次就认为完成。
- 不要把 Markdown 说话人写成 `## 用户说` 或 `## ChatGPT 说`。
- 不要包裹消息正文。
- 不要改写消息正文中的标题层级。
- 不要默认生成额外 `.html` 或 `.json` 文件。
- 不要把不完整采集标记为 `complete`。
- 不要保存 Cookie、token、签名参数、认证 header、浏览器存储凭据或未脱敏的登录态 URL。
- 不要删除或覆盖已有 Draft。只有在 `.skills/draft-organizer/SKILL.md` 的归组规则明确触发时，才可移动本次主题关系明确的 Draft，并必须修复路径引用。
