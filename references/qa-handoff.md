# 检查与交接

## 区分四个验证层级

| 层级 | 实际做过什么 | 可以声明什么 |
|---|---|---|
| 静态核查 | 检查记录、引用、时间和文字逻辑 | 记录与计划已检查 |
| 源素材核查 | 回看候选原片并核听原声 | 入选片段的具体事实与切点已核实 |
| 粗剪核查 | 播放真实导出视频，检查接点与全片 | 该版本粗剪已看过，列实际问题 |
| 成片实看 | 检查最终导出、音画同步、文字和手机观看 | 该版本对应检查已通过 |

某一层通过不能代替后一层。用户未提供视频时可交付规范或方案，不得宣布完成实片验证。

## Structure 基础层回归检查

进入 Content Map、Direct 1、Direct 2 或 Execute 前，先确认 Structure 的最低信息地板没有被摘要替代：

- `frames.jsonl` 中每个已分析 sampled frame 都能在 `frame-observations.csv` 找到同一 `frame_id`；
- 每行基础观察显式保留帧号 / 时间 / 帧尾 ms、画面事实、动作 / 状态、`motif_tags`、硬字幕 / 可见文字、**原声要点及核听状态**、`change_from_previous`、`content_description`、**topic_judgment、confidence / confidence_basis**、unknowns；没有内容时使用 `none` / `unknown` / `not_applicable`，不留空；
- 动作 / 视线 / 站位 / 物件变化候选进入 `action-node-candidates.csv`；默认 4fps 局部窗口，偏离时有例外原因；
- 会改变场景理解、plan 或剪辑意义的问题进入 `structure-questions.csv`，其 unresolved / unverified 状态持续可见；
- Directed Deep Structure 先保留 `detail-intervals.csv` 的进入原因 / 前情 / 当前背景 / 后续 / 目标问题，再对核心区域保留完整画面、背景、动作链、关键变化、情绪线索、硬字幕、原声及核听状态、before / after、主题判定、confidence、说话人裁决引用、问题引用、反证和未验证项；
- `speaker-adjudications.csv` 在有说话人 / 对象歧义时保留帧级口型 / 原声 / 字幕 / ASR 裁决；无歧义时也保留带表头文件。
- Broad Structure 的正式出口首先是这些文字化结构表单；overview、Content Map、情绪大意、Narrative Direction、Execution Plan、最终文案或 edit plan 都不能反向替代上述基础记录。
- 抽样中未出现的动作 / 台词 / 物件不得直接写成“没有发生”；4fps 只用于加密观察和缩小窗口。negative fact 必须限定 source-time scope，并按事实类型使用覆盖完整机会窗口的连续视频、覆盖声明区间的连续原声，或能直接排除该事实的可靠反证。
- 硬字幕 / 原声 / ASR 冲突有显式记录；方言 / 强口音 ASR 未核听时只作 locator，不作为唯一台词事实。
- 每个关键证据保持稳定 `source_id + source time`；`frame-observations.csv` 与 `frames.jsonl` 的时间一致，Deep observation 落在对应 Detail interval，speaker adjudication 与 utterance 源区间相符。
- 每个 source 的 `time_mapping` 与可用物理边界已记录；会限制 Direct 的 `usable_ranges / downstream_constraints` 已进入 Content Map / handoff。

缺字段或缺结构且没有异常说明，属于 Structure regression，应补回 B / E。原字段 / 产物保留且已显式声明无法获得的原因、影响与下游处理时，继续可做的整理 / 草案 / 交接，不把未知项当成事实，也不豁免正式渲染门槛。

## Execute 前的规定动作

- Detail 的真实关键帧清单、可用图片、独立 `execution-handoff.md` 及异常随包交付；handoff 已直接写明下游完整输出要求。
- 已确认 Execution Package 同时包含计划与 `execution-reference.md`：必要文字全文 / 时间锚点、具体样式、音轨 / 接点、资产 / 约束和 QA 判据齐全，Execute 无需另定核心风格。reference 通常一两个，锁定整体规则，不逐镜头配对。

- `timeline.duration_budget` 已按整数帧对平；普通覆盖式文字未被重复加到总长，真正延时的 card / hold 已成为 event；有时长上限时不得超预算进入 ready_for_render。
- 每个进入执行的 source event 已显式列出 `deep_observation_refs`；只校验本次实际采用的 observation，确认 source 一致、source-time 覆盖采用区间、evidence_status 为 supported / partial；同 unit 其他未采用的 pending / contradicted 记录不作为阻断项。
- 每个 source event 已引用 `edit_boundary_ref`；默认 source_in/out 落在 safe-in / safe-out windows 并覆盖 must-keep ranges。若 boundary override=true，必须确认它是有意创作选择，并有 reason + review refs，而不是切点未核准。
- audio track 已标 `narrative_role` / `treatment_reason`，不会因为提取 vocals 就把 BGM / ambience 的叙事作用默认为无效。
- 本轮反馈已经按文字 / 声音 / 结构 / 创意分类，并按对应 invalidation 范围处理。
- source time → assembly/output frame 的映射仍能回查，结构改动后旧绝对成片坐标没有被偷用。

## 导出后的规定动作

按“渲染与工程检查”对每次最终导出进行完整解码，核对实际帧数和视频展示时长。固定帧率偏差超过1帧失败，恰好1帧查明并记录，不以done或exit 0通过。保存预期值、实测值、解码错误、成片哈希及manifest哈希。

全片扫描近静音；区分扫描成功且没有命中、发现待核听窗口、没有音轨、工具或解析失败。后两种不是“没有问题”。按项目声音要求复核和修复，不自动混入原片音乐。

从同一最终文件、按编译后的成片帧号生成全部接点对照表；叠化覆盖开始、中间与结束。之后逐接点播放动态及原声，并正常速度看全片。自动化减少定位工作，不替代观看。qa 分别记录技术检查、图表检查、动态听看、手机实看，不合并成一个pass。

## EVA 项目

| 项目 | 要检查的具体问题 | 优先修正 |
|---|---|---|
| Narrative | 陌生观众能否理解人物、事件和重组关系 | 补回必要前情或减少论点 |
| Meaning | 是否截掉否定、条件、回应或制造虚假因果 | 恢复完整单元，调整主线 |
| Context | 重排是否把不同日期、关系阶段当成同一事件 | 明确时空变化或换素材 |
| Audio | 句首句尾、语气、底噪、原片音乐、音画同步 | 移切点、延长原段，再调整声音 |
| Rhythm | 是否人为碎切、动作未完成、重要反应看不清 | 合并段落、删除重复例子 |
| Visual | 站位、道具、服装、光线变化是否造成误读 | 改接点或接受明确场景切换 |
| Text | 能否正常速度读完；是否与原字幕争抢 | 减字、固定区域、延长停留 |
| Redundancy | 画面、台词、花字、结尾是否重复解释 | 指定主要表达载体，删重复 |
| Source | 每个判断、画面、台词能否回查到正确版本 | 修复引用与时间映射 |
| Mobile | 手机上是否看清、字幕遮挡和裁切是否合适 | 以实际手机检查记录为准 |
| ReferenceCompliance | 是否遵守已确认的文字层级、位置、颜色 / 字号、画面关系、情绪强调与视觉规则，是否有风格漂移 | 对照少量 reference 和全片规则修正，不逐镜头匹配 |

qa.json 包含 project_id、artifact_version、checks、blocking_issues、open_questions、rough_cut_verified、final_playback_verified。checks 每项记录 name、status、method、evidence、finding、action。status 只用 pass、fail、not_tested、not_applicable。

无真实导出文件时 Audio 的计划逻辑可以检查，但实际听感必须记 not_tested；Mobile 未实看也记 not_tested；ReferenceCompliance 未实际对照查看最终导出时同样记 not_tested，静态规格检查另记。不能为了完成清单填全部 pass。

## 何时退回哪一步

- 指代、条件、动作因果或原声核听有误：退回 E Directed Deep Structure；必要时补 C Content Map 的场景理解。
- Narrative Direction 的核心节点没有证据、反差来自截断原话、或新前后文会改变核心表达：把 evidence gap / 冲突证据退回 D1 Direct 调整主线；执行层不擅自重写主题。
- Detail 证据已经成立但最终素材取舍、排序、声音 / 文字 / 时长策略尚未确认：停在 D2 Direct，不直接进入 Execute。
- Direct 1 只调整局部节点：优先复用 Broad Structure 与已验证证据，只补受影响的 E 区域。
- 新方向依赖此前低覆盖区域：先补 B/C 对应区域，再进入 E。
- 声音与画面不顺：先 F 调切点；若改变意义，退回 E。
- 来源版本不一致、时码漂移：退回 A，暂停精确导出。
- 工具失败或能力缺失：保留已完成产物，更新 capability-map 和待补区间；不要从头重做已验证部分。

## handoff.md 模板

```text
项目与产物版本：
本轮目标及已确认范围：
当前阶段与实际完成情况：
已处理素材和区间：
未处理或低可信区间：
关键决定及对应证据 ID：
当前 brief / Narrative Direction / Editorial Execution Plan 及来源：
第二轮 Directed Deep Structure 已补查节点与证据缺口（并确认 `deep-observations.csv` 是否已覆盖核心区域的画面 / 内容 / 背景 / 前后状态）：
关键帧清单 / 实际图片 / 提取异常：
Detail 的独立 execution-handoff 及其内嵌下游输出要求：
Execution Package（计划 / reference / 风格样本 / 资产 / 约束 / QA）及确认来源：
已有文件与路径：
实际使用的工具和能力缺口：
源版本及时间映射注意事项：
仍未验证的音画、语境与切点：
文字锚点、实际字号单位与稳定阅读时间：
成片manifest、导出哈希及预期/实测帧数：
近静音窗口、原因与修复记录：
全接点图表及动态复核完成情况：
可复用中间产物、缓存键及强制失效项：
下一步具体动作及输入文件：
不得改动的已确认内容：
```

交接时不只传此摘要；同时提供 sources、必要证据、候选和时间轴。长项目可按需传所选 scene/unit 及其引用的完整证据，但告知接收者其他区间尚未加载，不能把局部交接当成全片证明。

## 给另一模型的启动指令

首次任务可使用：

```text
请把随附《长视频混剪跨模型与MCP执行规范》作为本任务的工作说明。
先盘点我提供的素材、已有记录和实际可用的视频工具，输出能力映射。
第一轮先做 Broad / Board Structure，建立可回查的 `frames.jsonl`、逐抽样帧 `frame-observations.csv`（含帧尾、原声要点、主题判定、confidence）、`action-node-candidates.csv`（动作节点默认 4fps 局部窗口并记录最小有效单元候选）、`structure-questions.csv`、场景、overview 和 Content Map；如果当前只要求内容地图，到这里正式交付。
如果要继续混剪，先把 Broad Structure 的正式文字化表单 + Content Map 交给我或独立 Director，形成 Narrative Direction；不要默认替代第一次创意决策。
拿到 Narrative Direction 后，先建 `detail-intervals.csv` 明确精查区间的前情 / 当前背景 / 后续 / 目标问题，再回原素材做 Directed Deep / Detail Structure；补足完整音画、原声核听、说话人裁决、confidence、上下文、反证和保护范围。然后固定交付真实关键帧与独立 execution-handoff，并在其中直接写明 execution-plan、制作 reference、文字 / 声音 / 转场、Reference Application Rules、资源 / 约束和 QA 要求；再交回 Director 形成完整 Execution Package。一两个风格样本锁定全片规则，不逐镜头对应；只有第二次 Direct 确认后才进入 Execute。
优先同集，保留完整对白与动作，不根据抽样帧或摘要补造未验证内容。
已有确认信息直接沿用。遇到缺口先完成可做部分，并指出具体缺少哪段素材或哪种能力。
素材位置：
限定集数或范围：
目标人物或关系（如有）：
已有 brief / Narrative Direction / Editorial Execution Plan：
时长和比例要求：
交付目标：详细执行稿 / 粗剪 / 成片
已确认方案或禁改项：
```

续接任务可使用：

```text
请按随附执行规范续接这个项目。先读 handoff、project、sources、coverage、Structured Observation Layer、content-map、brief、`narrative-direction`、`execution-handoff`、`keyframe-references`、`execution-plan`、`execution-reference`、异常说明和 capability-map；兼容旧项目时再读 legacy `editorial-plan`。随后读取当前 narrative / execution mapping 引用的 scene / unit / Deep observation / review / 原始证据。
先核对当前能力与源版本；复用已有成果，只补齐缺口，不重新概括替代原记录。
继续完成 handoff 中的下一步。报告实际核验范围，不把前一模型的摘要写成自己的直接观察。
```

## 交付表达

交付时列清：完成的是规范、计划、粗剪还是成片；覆盖了哪些素材；实际核验到哪一层；仍有哪些具体问题。若没有材料可处理，就交付可执行规范和输入清单，不假装已经处理过长视频。

## v1.0.3 授权与证据交接

交接保留 execution-authorization.json、采用证据的 source_signature / time_mapping_digest、清单 input_digest / manifest_digest 与 render_allowed。规划清单不得当作已允许渲染；素材或确认文件改变后先判断证据 / 方案失效范围，再重新核实、裁决和编译。机器检查通过与最终听看通过继续分开记录。
