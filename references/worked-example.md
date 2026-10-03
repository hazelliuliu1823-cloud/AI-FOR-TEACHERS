# 执行示例

以下人物、对白、时间码和场景全部虚构，仅演示“两轮 Structure + 两次外部 Direct + Execute”的流程。不得复制进真实素材库。这里没有真实视频，所有音画与切点均未验证。

## 示例输入

用户提供一集四十五分钟视频的字幕和九宫格。此时还没有明确要剪什么，只希望先把这一集的内容整理清楚。系统可读取图文，有抽帧工具，没有连续音画观察和渲染能力。

字幕中出现三个区间：

| 区间 | 提供的记录 |
|---|---|
| 00:08:00—00:08:22 | 甲问“明天你来吗”，乙答“我不保证，得先把这边忙完” |
| 00:19:10—00:19:25 | 无字幕；两张抽样图分别见乙站在柜前、乙手中拿着包 |
| 00:35:00—00:35:28 | 甲说“你来了”，乙说“忙完了，走吧” |

## 第一轮 Broad Structure

把字幕记录为 origin=subtitle、audio_verified=false。把两张抽样图分别记录，不写成“乙悄悄收拾东西准备赴约”，因为两张图片不能证明动作链与目的。

按全片顺序继续建立 scene / transcript / frame / coverage，而不是只围绕上述三段做关键词搜索。除 `frames.jsonl` 外，同时生成 `frame-observations.csv`：例如 19:10 的两张抽样帧分别写清乙的位置、手中物件、画面环境、硬字幕、原声核听状态、与前帧变化、主题判定、confidence 和未知项，而不是只把两张图丢给后续 Director 自己猜。三个区间都可以形成 provisional unit，但说话人来自字幕而未核听，第三段是否对应前面的“明天”尚待上下文确认。

## Content Map

在 `overview.md` 中按原片顺序记录事件；`action-node-candidates.csv` 与 `structure-questions.csv` 继续作为基础层保留，不被总结吞掉；在 `content-map.md` 中横向整理可供后续 Direct 浏览的线索，例如：

- “约定 / 是否出现”相关对白：S004、S017；
- “忙完后离开原地点”相关动作线索：S009，目前只有抽样帧；
- 甲乙多次关于时间安排的交流：S004、S012、S017；
- Unknown：S009 中拿包动作的目的未知；S017 是否是 S004 同一约定未知。

到这里，如果用户只要求 Structure，就可以正式交付。不能因为看到了三个可能有关联的片段，就自动宣布已经有一条成立的混剪主线。

## Direct 1：形成 Narrative Direction

用户或独立 Director 阅读正式的 Structured Observation Layer + Content Map 后，先提出 Narrative Direction：

> 想看“没有先答应，但最后还是出现了”这一关系变化。第一段用带条件的不保证建立悬念；中间如果有真实的收尾 / 出发动作可以作为推进；最后用出现和回应完成兑现。不要把“不保证”夸张成“绝不来”。

这份 plan 已经确定了创意方向，但还没有证明三个节点真的属于同一件事。

## 第二轮 Directed Deep Structure

此时才带着 Narrative Direction 回原片提高信息密度，并建立 `deep-observations.csv`。第二轮不能只写“这段可用”，而要把入选核心区域重新描述完整：画面里谁在哪里、做什么、如何看向谁、场景环境是什么，这一小段实际发生了什么，以及前一事件和后一事件怎样连接。

1. 回看 08:00 前后完整交流，核听“不保证”的语气、条件和说话对象，并记录画面站位、表情 / 视线、对话发生的场景背景与 before / after state；
2. 对 19:10 段落增加抽帧并连续观看，确认拿包之前和之后发生什么，把动作链、空间关系、内容描述和 narrative context 写入 deep observation；
3. 回看 35:00 前后完整事件，确认“你来了”是否与前面的约定有关，同时记录现场环境、说话对象、反应镜头与后续动作；
4. 检查三段是否处于同一天 / 同一关系阶段，查找可能推翻主线的前情；
5. 更新 Q001 的 answer / evidence / unverified items；将真正入选的 unit 补齐 context_ranges、protected_ranges 和 review refs。

### 分支 A：Narrative Direction 得到支持

如果核实首尾确为同一约定，中间动作也与出发直接相关，那么可以形成完整的 evidence-backed plan：

- 第一段：完整问答，保留“得先把这边忙完”的条件；
- 第二段：实际收尾并离开，保留必要动作链；
- 第三段：最后出现及回应。

此时先把 Detail evidence package 交回 Direct 2，由 Director 决定三段是否都保留、最终顺序、时间分配和声音 / 文字策略；只有 Editorial Execution Plan 确认后才进入 Execute。

### 分支 B：Narrative Direction 被证据推翻

如果发现最后的“你来了”是另一天的另一件事，就不能把它当作前面约定的兑现。

Directed Deep Structure 应把具体冲突返回 Direct：

- S017 与 S004 不是同一事件；
- 中间拿包也没有证据指向赴约；
- 当前素材不足以支撑“最后还是出现了”的兑现结构。

Director 可以改成有明确时空提示的行为比较，也可以放弃这条主线。执行层不能靠字幕卡把两个无关事件硬连成同一约定。

## Direct 2：形成 Editorial Execution Plan

当 Directed Deep Structure 已经把主线节点的完整画面、原声、前后文、反证和保护范围核实清楚后，证据包先回到 Director，而不是直接进入时间轴。Director 在这里确认最终选择哪些 verified units、怎样排序、哪些原声 / 动作必须完整、声音和文字如何承担叙事、各段时长和允许调整范围。只有这份 execution plan 确认后，Execute 才把它编译成 timeline。

## 时间轴如何记录

假设后续人工确认首尾片段可用于“不同事件的行为比较”，且另行确认使用二十五帧输出；下表仅演示换算，不能替代实际边界核查。

| 段落 | 源区间 | 时长 | 输出帧区间 |
|---|---|---|---|
| 第一段完整问答 | 480000—502000 ms | 22秒 | 0—550 |
| 后一次出现的交流 | 2100000—2128000 ms | 28秒 | 550—1250 |

成片合计五十秒；区间左闭右开。两段之间记录 relation=chapter_change，并说明其为后续另一事件，不能假装同场连续对话。是否加“后来”提示取决于画面能否清楚呈现时间变化，待实际粗剪决定。默认不做变速，不人为把二十二秒问答拆成四个亮点。

## 当前条件下的正确交付

因为示例环境没有连续音画观察和渲染能力：

- Broad Structure 可以交付 Content Map，但必须保留 audio / av review 的 coverage 差异；
- Narrative Direction 可以作为第一次外部 Direct 输入；
- Directed Deep Structure 无法完成的原声和连续动作核查继续标 pending；
- 不输出 ready_for_render，也不宣布粗剪通过。
