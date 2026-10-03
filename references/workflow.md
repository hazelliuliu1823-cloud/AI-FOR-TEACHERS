# 工作流程

## 总体路径

本流程不是单向的“结构化 → 自动选题 → 剪辑”。标准路径是：

```text
A 素材登记
  ↓
B Broad Structure：全量粗覆盖
  ↓
C Structured Working Layer + Content Map
  ↓
D1 Direct：Narrative Direction（人 / Director 确定叙事主线）
  ↓
E Directed Deep / Detail Structure：围绕主线回原片做高密度补查
  ↺ 证据不足 / 主线不成立时返回 D1
  ↓
D2 Direct：Editorial Execution Plan（基于核实证据形成最终执行方案）
  ↓
F Execute：时间轴与渲染
  ↓
G QA & Handoff
```

第一次 Structure 追求**广度 + 紧凑表示**：正式产出逐抽样帧 / 分片段观察表、动作节点、Q&A、scene / overview 等文字化结构数据，并在其上形成 Content Map；第一次 Direct 只负责确定 Narrative Direction。第二次 Structure 追求**与已确认 Narrative Direction 相关的证据深度**；Detail 完成后必须再次回到 Director 形成 Editorial Execution Plan，之后才进入 Execute。不要在第一轮为某个主题过早押题，也不要把第二轮证据直接当成最终剪辑方案。

Structure 字段无法取得时，保留原 schema 并明确异常后继续可做部分；E 随证据交付关键帧和独立 handoff，D2 输出完整 Execution Package。具体字段与样式参考规则见 [异常与执行包契约](execution-package.md)，不增加阶段。

## 任务与默认值

接收视频文件或授权地址、已有九宫格、字幕、转写和分析文档。优先复用已完成工作，但先核对它们对应的源视频版本与时间轴。用户只提供九宫格时可以建画面索引，不能据此交付已核实的对白剪辑。

配置必须写明：素材范围、目标人物（如有）、已知目标或开放 Structure、是否限同集、成片比例和时长、原声与配乐要求、已有底稿、交付目标、可用工具。未知项写 null；对不影响前期建档的缺项先继续工作。无指定时，以同集为优先、保留原声、只用必要解释文字；时长和比例不擅自写成用户已确认要求。

`deliverable=content_map` 时，默认目标是完成 A—C，并正式交付 Structured Observation Layer + Content Map，而不是只交一份摘要。`deliverable=detailed_plan` 或更后续产物时，进入 E 前必须取得第一次 Direct 的 Narrative Direction；E 完成后，进入 F 前必须取得第二次 Direct 的 Editorial Execution Plan。两者都可以来自用户或独立研究 / 编导环境。

已有 brief 可以在 Broad Structure 阶段作为重点标记，但不得让第一轮覆盖只剩关键词检索。Structure 的价值之一就是扩大人的可见范围，并把昂贵的多模态上下文压成可反复复用的表格 / 文本层，让后续 Direct 不被最初假设锁死，也不必在每次创意讨论时重复读取原视频。

默认不主动渲染。只有明确要求或任务已包含试剪时才调用渲染；下载、上传、付费和访问私有资源均受当前环境授权约束。不得发布、发给他人或覆盖源视频。

## A 素材登记

为每个源文件建立 source_id，记录文件位置、可取得的版本标识或哈希、时长、流起点、分辨率、帧率信息、是否可变帧率、音轨和字幕。拿不到元数据时标记未知，不从文件名推断集数或版本。

项目时间基准采用原文件从首个展示时刻起算的非负毫秒；保留容器原始 PTS 与项目时间的映射。合集切出单集、代理文件、音轨分块都记录原片偏移。若转换并非线性偏移，保存完整映射，不能直接套加法。

### 时间标签稳定性（全流程硬约束）

`source_id + source timestamp/range` 是 Structure 的 canonical time tag。九宫格格号、抽样序号、ASR 自带时间、代理文件时间、字幕文件时间和 `display_timecode` 都只是派生定位，不得成为新的事实主键。画面、硬字幕、ASR、原声核听、动作节点、问题、Detail observation、unit 必须能无歧义回到同一源时间。

进入 Execute 后才新增 assembly / output frame 坐标，并通过 `anchor_event_id + local_*_frame` 或明确 output 坐标与源时间建立映射；不得反过来用成片时间覆盖源证据时间。源版本、代理偏移或 `time_mapping` 改变时，所有依赖精确时间的字幕、音轨、切点、缓存和 QA 锚点必须失效重核。

字幕先抽查开头、中段、末段与原声的对应。不同版本可能出现片头长度差、删减或累计漂移；只有验证为恒定偏移时才能整体平移。候选段字幕必须局部复核。无法听音时只能记“未核对”。

## B Broad Structure：全片概览

画面和台词分别扫描，再按同一时间轴合并。不要只按台词关键词找候选，否则会漏掉等待、递东西、回望等无声互动。

下表是第一轮可调试的参数，不是质量保证或平台限制。

| 参数 | 起始建议 | 调整条件 |
|---|---|---|
| 分析批次 | 以场景为主，必要时每五至十分钟分批 | 依据图片数、分辨率、上下文和服务时长限制缩小 |
| 批次边缘 | 先取前后各十五至三十秒辅助语境 | 一轮对话仍跨界时继续扩展到事件边界 |
| 概览抽帧 | 镜头代表帧加长镜头约五至十秒补帧 | 快动作、遮挡、无声互动或不确定处增加 |
| 第二轮精查抽帧 | 候选相关段可从每秒一至两张开始 | 动作起止用连续播放或更密抽帧核实 |
| 动作节点局部窗口 | 默认 4fps | 用于 Broad / Deep 中发现的动作、视线、站位、物件交接等变化节点；偏离 4fps 必须记录原因 |

九宫格是展示方式，不等于分析时间单位。每格保留 frame_id、source_id、真实取帧时间；从左至右、从上至下按时间排序。跨场景清楚标记。保留原分辨率单帧；文字或表情看不清就读取单帧或放大，不能凭缩略图补写。

**否定性事实的举证门槛：**稀疏抽样只证明“这一张没有看到”，不证明“整个机会窗口没有发生”；**4fps 也只是局部加密观察的起点，不是区间级否定结论的充分证据。**任何 `没有开门 / 没有说这句话 / 没有出现该物件` 等 negative claim 必须先限定明确的 source-time 观察范围，再按事实类型完成核验：视觉动作 / 物件是否出现，需连续视频 review 覆盖整个机会窗口或有能直接排除该事实的可靠反证；某句话是否说过，需连续原声 review 覆盖所声明区间或有直接、可回查的反证。密集抽帧可以触发进一步核验、缩小窗口或支持“该采样点未观察到”，但不能单独证明整个区间内没有发生。条件不足时只写 `not_observed_in_sample` / `unknown`，不能进入 facts。

每张已分析抽样帧都要留下两层记录：

1. `frames.jsonl`：机器可追溯证据，保留 frame_id、真实时间、image_ref、facts、unknowns；
2. `frame-observations.csv`：面向人工 / Director / 其他 Skill 的**基础结构化观察表**。每个已分析 sampled frame 一行。除定位外，至少覆盖 frame_id / frame_name、timestamp_ms / frame_end_ms、characters、visual_facts、visible_action_state、observed_emotional_cues、expression_gaze、spatial_relationship、setting_background、key_objects、motif_tags、visible_text、**original_audio_keypoint / audio_verification_status**、nearby_dialogue_refs、content_description、change_from_previous、**topic_judgment、confidence、confidence_basis**、action_node_candidate_ids、speaker_adjudication_refs、interpretations、unknowns。可复制 `assets/frame-observation-template.csv`。

这张表不是九宫格的重复说明，而是把“每一张已看过的抽样帧里真正有什么”变成人可浏览的基础层。**基础层不得被 overview、Content Map、最终文案或剪辑建议替代。** `visual_facts`、`visible_action_state`、`motif_tags`、`visible_text`、`original_audio_keypoint`、`audio_verification_status`、`change_from_previous`、`content_description`、`topic_judgment`、`confidence`、`confidence_basis`、`unknowns` 必须有显式值；没有内容时写 `none` / `unknown` / `not_applicable`，不能留空。相邻帧间的动作只能作为待核实假设。请求“逐帧文档”时说明这里是逐抽样帧记录，并列抽样规则，不声称看过每个视频帧。

`frame_end_ms` 用于保留该观察帧 / 观察切片的尾边界；能取得真实帧时按真实帧时长记录，只有静态抽样点时按提取工具给出的观察边界记录并在 coverage 说明。`original_audio_keypoint` 记录该帧附近真正可归属的原声要点；没有核听就写 `not_verified`，不能把字幕文本冒充原声。`topic_judgment` 必须落到该帧 / 节点为什么值得后续检索或承担什么叙事功能，不能只写“甜”“虐”“高光”等空标签；`confidence` 必须和 `confidence_basis` 同时写，例如 `high(frame_evidence)` / `medium(subtitle_only)`。

`change_from_previous` 只比较相邻**已分析抽样帧**：人物进入 / 离开、视线变化、站位变化、物件状态变化、字幕变化、镜头 / 光线明显变化等都可记录，但不能据此补写中间动作过程。`motif_tags` 用于低成本导航重复意象 / 行为 / 空间线索，例如“门 / 离开”“回望”“等待”“共同物件”；它只是索引标签，不等于已经确认象征意义。

### 动作节点候选与 4fps 局部窗口

Broad Structure 或 Directed Deep Structure 发现明显动作变化候选时，写入 `action-node-candidates.csv`（可复制 `assets/action-node-candidate-template.csv`）。每个候选至少记录 trigger_frame_id、候选起止帧、center_timestamp_ms、trigger_reason、change_signal、window_start_ms / window_end_ms、sampling_fps、最小有效单元候选、口型 / 说话线索、关系转折信号、topic_judgment、confidence / confidence_basis、evidence_refs、verification_status 与 unknowns。

默认在候选节点附近使用 **4fps** 局部窗口（0.25 秒采样间隔）观察动作起点、过程、回应与结束；对真正影响切点、口型或关系转折的节点，允许进一步细化到约 **0.1–0.5 秒颗粒**，但必须由连续画面或更密采样支持；窗口长度按事件完整性决定，不强制固定秒数。源帧率不足、工具限制或连续播放更适合时可以偏离 4fps，但必须写 `sampling_exception_reason`。动作候选是“值得加密观察”的导航，不自动升级为已验证动作链。

### 结构化问题回答与未验证项

凡是会影响场景理解、Content Map、Narrative Direction（或 legacy rough plan）或剪辑意义的问题，都写入 `structure-questions.csv`（可复制 `assets/structure-question-template.csv`），至少保留 question、answer、answer_status、evidence_refs、unverified_items、next_check。answer_status 使用 `supported / partial / unresolved / contradicted / not_applicable`。没有证据时保持 unresolved，不允许用最终总结把问题吞掉。

机器检测的镜头切换先作为技术边界。同一轮正反打通常仍属于一个场景；闪白、运镜和灯光变化可能需要人工复核。保留检测原结果及调整结果，不用算法切点直接决定叙事单元。

coverage 分别记录画面抽样、字幕或转写、连续音画复核的时间区间与状态。全时段完成抽样不等于全时段实看。任何未处理、失败或低清区域都保持可见；特别记录片头片尾是否有正片内容。

Broad Structure 的完成条件不是“已经知道该剪什么”，而是：素材主要时间范围已经建立基础索引，场景和对白可以回查，coverage 与 unknowns 清楚；`frame-observations.csv` 与 `frames.jsonl` 一一对应；动作节点候选文件与结构化问题表已生成（没有候选 / 问题时也保留带表头的空表）；基础字段没有被摘要或 Content Map 替代。基础层实际完成后才记 complete；字段 / 产物无法取得时保留结构、报告异常与 coverage 缺口，再继续可做的整理、草案和交接，不能为完成状态补造观察。

### 可用素材边界与长任务 checkpoint

Broad 扫描发现片头 / 片尾卡、黑场、硬切尾、缺失音轨、代理缺段或其他物理边界时，不只在 overview 里提一句：在对应 `sources.json` 条目登记 `usable_ranges` 与 `downstream_constraints`，明确哪些源时间真正可用于后续设计。Content Map 和 handoff 必须把会限制下游分段时长、结论段、J/L-cut 或音频处理的边界传给 Direct。

长时间抽帧、分析、转写和并行任务采用 checkpoint 纪律：基础产物增量落盘，`coverage.json` 同步记录已完成 / 未完成区间；任务中断后按版本、区间和输出完整性从缺口续跑。子任务或 agent 静默结束后先核对落盘数量与 coverage，不因为“没有最终回复”就重做已经可靠完成的部分。具体每多少项落盘、使用什么脚本语言由环境决定，不写死。

## C Structured Working Layer + Content Map：正式文字化结构输出

C 阶段不是把 B 阶段表格“总结掉”，而是把 Broad Structure 的文字化结构数据整理成 Director 可以直接工作的正式交付包：逐抽样帧观察表、动作节点候选、结构化 Q&A、scene / segment 级观察、source-order overview，以及在其上形成的 Content Map、情绪 / 关系线索和 usable bounds。

先写场景事实：人物、地点、可确认的剧情时间、进入时的状态、动作与对白、离开时的状态。再写解读与候选价值。场景可以覆盖多个不连续镜头；交叉叙事需记录多个源区间，不假装它们是一个连续事件。

将跨批次同一对话合并。用 source_id、区间和证据 ID 去重；不要因重叠读取把同一个动作算成发生两次。

`overview.md` 保留 source-order 导航：事件顺序、关系变化、重复线索、未确认事项，每一项链接 scene_id。它不能替代台词原文、`frames.jsonl`、`frame-observations.csv` 和场景卡。Content Map 中的重要线索应能继续下钻回 scene，再下钻到具体 frame / utterance / review，而不是只剩摘要。

同时生成 `content-map.md`。它面向后续人工 / Director，不按源时间顺序机械罗列，而是在不丢证据链接的前提下提供可横向浏览的素材面，例如：

- 人物 / 关系及其变化节点；
- 重要事件和重复出现的行为；
- 可检索对白主题和原声位置；
- 无声互动、物件、空间和动作线索；
- 前后呼应、潜在对照、尚未确认的关联；
- 每项对应 scene_id / source range / evidence refs；
- coverage 缺口和 unknowns。

Content Map 可以提示“这里可能值得继续看”，但不把这种提示写成已经确认的编导结论。

建立初步 unit。每个 unit 必须是同一源文件中的连续区间；若跨源或不连续，拆成多个 unit 并用 scene_id 或后续 plan_id 关联。第一轮 unit 可以较粗，记录可取范围和回查语境范围；`protected_ranges` 可以等待第二轮核验后补齐。unit 没有固定秒数。

如果 `deliverable=content_map`，A—C 完成后就是合法终点。交付时明确哪些内容来自抽样、字幕 / ASR 或连续音画实看，不为了进入后续流程强行生成创意主线。

## D1 Direct：Narrative Direction — 先决定“到底讲什么”

第一次 Direct 是创意层的第一次决策，默认在仓库之外的独立研究 / 编导工作区完成。它消费的是 **Structured Observation Layer + Content Map**：正式表格、scene / segment observations、overview、情绪 / 关系线索、usable bounds，并可叠加行业 / 主题研究、平台语境、参考案例与人工经验。

第一次 Direct 的输出重点不是精确剪法，而是：

- 核心命题 / 观看关系；
- Narrative Spine；
- candidate regions / scenes；
- 每个 spine node 的大致功能；
- 需要 Directed Deep Structure 回原片裁决的问题；
- 已确认的人工判断、禁改项和允许调整范围。

可使用 `assets/narrative-direction-template.md`。已有 rough editorial plan 也可作为兼容输入，但进入 E 前要明确哪些内容属于 Narrative Direction，哪些只是尚未被素材证明的假设。第一次 Direct 不要求精确时间码；已有时间码只作 locator。

把 Narrative Direction 映射到 Content Map：每个 narrative node 链接已有 scene / unit / evidence；没有对应项的节点登记为 evidence gap。不要为了让主线看起来完整而把弱证据升级为事实。

如果用户明确授权本 Skill 辅助 brainstorming，可以给出基于 Content Map 的建议，但要与外部研究、人工判断和后续执行记录分开。默认情况下，不自行替代人的主线判断。

## E Directed Deep / Detail Structure：带着 Narrative Direction 回原片

这是第二轮 Structure。它只对 Narrative Direction 命中的区域重新消费高密度多模态信息，目标是把第一次 Director 的主线问题变成完整、可回查的证据包；它本身还不是最终执行方案。

### Detail 区间卡：先把精查对象说清楚

在任何高密度抽帧或连续播放前，先生成 `detail-intervals.csv`（可复制 `assets/detail-interval-template.csv`）。每个核心区间必须写清：为什么进入精查、前情、当前场景 / 关系背景、后续、这段实际内容的粗摘要、要回答的问题、与当前主题 / plan node 的关系、证据与 unknowns。

**区间卡不是脚本文案。** 它的作用是让后续 Detail Structure 知道“从哪里看、为什么看、要裁决什么”，避免直接拿 Narrative Direction / legacy rough plan 的目标倒推原片。前情 / 背景 / 后续不清时写 `unknown`，不能省略。

对 Narrative Direction 中每个节点重新回到原素材，不仅复用第一轮摘要。先读取对应 scene / unit / transcript / frames / frame-observations，再提高信息密度。第二轮的顺序是**先重新把核心区域看完整，再决定怎么剪**：

- 相关片段从前后各十五至三十秒开始扩查；指代、条件、人物动机或动作因果仍不清楚时继续扩到完整事件，必要时追溯前后场景或前集；
- 候选段可从每秒一至两张抽帧开始，但动作起止、反应链、停顿和声音关系必须用连续播放或等价能力确认；
- 建立 `deep-observations.csv`（可复制 `assets/deep-observation-template.csv`），每个核心观察区间至少补齐：
  - **visual_facts**：人物、站位 / 朝向、动作、表情 / 视线、人物距离、关键物件、景别 / 构图、画面变化；
  - **key_visual_changes / motif_tags**：核心区域内部可确认的视觉变化及可复用意象标签；
  - **setting_context**：地点、可确认时间、环境与空间状态；
  - **narrative_context**：前一个事件是什么、为什么来到这一刻、它与前后事件怎样连接；
  - **observed_emotional_cues / emotional_interpretation**：前者只写可观察的语气、停顿、表情、视线和身体状态，后者才允许谨慎解释情绪；不写无法观察的心理动机；
  - **content_description**：这一小段实际发生了什么，不能只复制字幕关键词；
  - **hard_subtitle_notes / original_audio_keypoints / audio_verification_status / subtitle_asr_conflicts / dialogue_audio**：硬字幕、真正核听到的原声要点、核听状态、字幕 / ASR 冲突、说话人、对象、语气、停顿、环境声 / 音乐分别记录，不能互相替代；
  - **speaker_adjudication_refs**：说话人 / 对象有歧义时链接帧级裁决表；
  - **before_state / after_state**：进入和离开这一段时人物 / 事件状态；
  - **topic_judgment / confidence / confidence_basis**：主题判定落到该观察节点的具体叙事功能，并写证据等级 / 类型；
  - **question_refs / interpretations / unknowns / unverified_items / counterevidence**：把问题、事实、解读和不确定性分开；未验证事项不能因为进入第二轮就被自动清空；
  - **plan_node_id / narrative_function**：这一段为什么被回查、准备承担什么功能，但该字段不能反过来污染事实描述。
- 字幕 / ASR 命中必须回到原声核听；逐一核对说话人、被说话人、否定词、条件、重要停顿、动作发起与回应、动作后果；
- **证据冲突不使用机械总排名。** 视觉动作优先连续原画；“实际说了什么”由清晰原声核听与可靠官方硬字幕相互校验；speaker / addressee 结合口型、连续原声、可见人物关系与字幕信号。ASR 是定位和候选证据，方言 / 强口音默认 `locator_only`，未经核听或硬字幕核对不得写进台词 facts。任何冲突保留在 `subtitle_asr_conflicts` / `speaker-adjudications.csv`，不能选择一个方便 plan 的版本后删除冲突；
- 第二轮同样遵守 negative evidence rule：没有在抽样里出现的动作只能算 `not_observed`；4fps 或更密抽样仍不能单独证明区间级“没有发生”。视觉否定结论要覆盖完整机会窗口的连续视频，语音否定结论要覆盖声明区间的连续原声，或存在可直接排除该事实的可靠反证。
- 检查 Narrative Direction 可能忽略的反证、玩笑语境、时间差、关系阶段和异场反应；
- 在上述内容理解完成后，再把第一轮粗 unit 收敛为可剪 unit，确认 context_ranges、protected_ranges、isolated_use_risk 和 verification；
- **建立 Edit Boundary / Continuity Layer**：对每个可能交给 Direct 2 的核心连续素材，分别核定内容范围、真实音频起止与尾部、动作链起止、反应 / settle 结束；给出 preferred in/out、safe in/out windows、must-keep ranges、handles、cut risk 与 evidence refs。字幕 / ASR 时间只作线索，不能直接当切点；
- 为接续关系准备连续性、比较、倒叙、章节变化等依据。

记录审阅者身份或能力来源、时间范围和结果。只有文件实际被读取不等于被看懂；音频抽取成功也不等于原声已核听。不能处理音频或连续视频时，请有能力的工具或用户核查；同时继续可做的索引和草案。

### E 的关键帧与跨模型 handoff

随 Detail 固定交付 `keyframe-references.json`（通常 1–3 张真实原片代表帧）与 `execution-handoff.md`，参见 [执行包契约](execution-package.md)。图片只提供素材视觉依据；提取失败或没有可定位的帧时保留清单 / 字段并声明异常，继续可做部分。handoff 携带已确认主题、所选源区间与证据 / 保护范围、图片与文件入口、异常，以及下游完整 Execution Package 的输出要求；接收模型即使没有安装此 Skill 也能直接继续。此处不替 D2 作视觉 / 制作决定。

### 何时返回 Direct 1

以下情况不要直接进入 Execute：

- Narrative Direction 的关键节点在原片中没有足够证据；
- 原台词含有被计划忽略的否定、条件或玩笑语境；
- 计划把不同事件误当成同一问答或即时反应；
- 某个段落功能需要的素材不存在，只能靠强解释文案弥补；
- 新发现的前后文会改变核心表达。

此时输出具体 evidence gap、冲突证据和可替代素材，返回 D 调整。允许多次 D ↔ E 循环。不要因为已经投入精查成本就强行保留原计划。

## D2 Direct：Execution Package — 再决定“最终怎么讲”

E 阶段完成后，不直接进入 Execute。以独立 handoff 把 `detail-intervals.csv`、`deep-observations.csv`、speaker adjudications、verified units、context / protected ranges、counterevidence、evidence gaps、source-time refs 和真实关键帧交回 Director；直接附上后续执行包的必需组成，不能依赖同一环境的 Skill 上下文。

第二次 Direct 基于**已经核实的材料能力**形成完整 Execution Package，其中 Editorial Execution Plan 至少明确：

- 最终选择 / 排除的 verified units；
- 段落顺序与每段 narrative function；
- 必须完整保留的对白、动作、反应与 protected ranges；
- 原声 / BGM / ambience / 文字的处理策略；
- 总时长与各段分配；
- 转场 / 时空提示等执行意图；
- 可替换范围、允许执行层调整的边界、不得改变的核心表达。

同时填写 `assets/execution-reference-template.md`，冻结具体文字规格、画面关系、声音 / 转场、少量风格样本的应用规则、资源入口与 QA 判据；逐条文字全文及出现 / 消失锚点在计划中给出。通常一两个样本即可，不要求每个字幕或镜头对应 reference。完整要求见 [执行包契约](execution-package.md)。可使用 `assets/execution-plan-template.md`。如果 Detailed Structure 暴露出主线级冲突，先退回 D1；如果只是素材取舍 / 排序 / 执行策略问题，在 D2 内解决。只有计划及 reference 组成的执行包被确认，且关键 evidence_status 不为 pending / contradicted，并且每个入选 source segment 已引用可用 edit boundary，才进入 F Execute。`ready_for_render` 是机械状态，不是文字口径：项目必须同时满足 Broad / Content Map / Detail 完成、两次 Direct 状态均为 `confirmed`、对应文档真实存在，以及 `render_authorized=true`。每个入选 source event 还必须显式列出本次真正采用的 `deep_observation_refs` 与 `edit_boundary_ref`；这些 observation 的 source 必须与 event 一致，source-time 覆盖本次采用区间，状态为 `supported / partial`。默认 source_in/out 必须落在 boundary 的 safe windows 并覆盖 must-keep ranges；有意越界只能通过显式 override + 创作理由 + review refs。同一 unit 中未采用的 pending / contradicted observation 不阻断本次执行。静态校验或编译器任一项不通过都不得进入渲染。

## F Execute：执行与粗剪

输入为 Source Clips + Detail Structure + execution-plan + execution-reference + Constraints；Execute 只在既有规则与允许调整内制作，不补定核心风格。实际出片前读取“渲染与工程检查”。先完成 **duration budget ledger**：源片段按目标 fps 使用**累计时长统一量化**确定 assembly 边界，不允许每段各自四舍五入后再相加；validator 与 compiler 必须共用同一套累计量化与 overlap 计算。再以累计量化后的事件帧数求和，减去相邻 transition overlap，得到预计成片帧数；黑场卡 / freeze / hold 等真正新增时间必须作为事件计入，普通覆盖式文字停留不单独加时。若文字阅读时间放不进现有画面，必须在结构层显式延长事件、加 card / hold、减字或调整别处预算，不能把文字时长重复加到总长。预算未对平不得标记 ready_for_render。

随后按反馈类型先判断失效范围，再动文件：纯文字层反馈只重烧文字层；声音策略改变失效音频 + final；切点 / 段长 / 转场改变重新编译 timeline 并使所有依赖坐标的下游失效；核心主线 / 段落功能变化退回 Direct，并只重做受影响的 Directed Deep Structure。

音频处理前先标记它在该段的 **narrative_role**（例如 dialogue_information / ambience_continuity / emotional_music / rhythm_cue / intentional_silence），再决定 preserve / isolate / attenuate / replace / remove；不能把“信息”只理解成对白。

再用锚点和对照帧校准文字，按实际叠化帧数编译 render-manifest；所有成片文字、音轨放置、封面定位和接点核查使用此版本成片坐标。分开保存视频单元、无字底片、混音和文字烧录产物，便于局部返工。

先生成 edit-plan，再编译 timeline。详细稿包含成片参数、主线、源素材取舍、逐段画面、原声、创作者文字、字号位置、转场、封面、禁止项和待验证项。画面、声音、文字按 D2 执行包的各层规格落实，同一主句可跨原片正反打保留；若执行稿还缺必要参数，指出缺口并回 D2 补定，不擅自补写风格或表达。

粗剪先保留必要原声及最少的场景提示，验证结构，再按执行包中已确认的策略处理配乐和包装。按照转场逐个观看接点，再正常速度看全片。原片音乐无法干净衔接时优先换切点、加长段落或接受明确场景切换；不假设淡化即可解决所有音乐断裂。

用户只要执行稿时，交付 detailed_plan；未生成粗剪则 rough_cut_verified=false。用户要成片而当前没有渲染能力时，交付能够直接执行的计划与明确缺口，不谎称已剪好。

每次导出先完整解码实测帧数和展示时长，再做全片低电平扫描，并从该成片自动生成全部接点对照图。技术错误先修复；近静音和接点图进入实际核听、播放，不能用截图代替动态检查。

## G QA、保存与恢复

在原 EVA 中增加 Reference Compliance：对照少量已确认样本与全片规则，检查文字层级、位置、画面关系、强调方式和风格漂移；不检查逐镜头配对数量。静态规则检查和真实导出观看分开记录，未实看保持 not_tested。

每批成功后保存结果和 coverage；长任务把“已完成区间 / 未完成区间 / 最近可靠 checkpoint / 可恢复入口”一起保存；每阶段结束保存 handoff。缓存键由源文件版本、处理区间、参数、工具及模型版本组成。换源版本或 time mapping 时重新核对时间标签并失效精确下游坐标；调整 Broad Structure 抽样密度只重做受影响区间；Direct 调整通常复用第一轮 Content Map 与已验证证据，不重扫全片。

如果 Narrative Direction 改动只影响局部节点，优先只重做对应的 Directed Deep Structure 区域。只有新的方向依赖此前完全未覆盖或低可信区域，才扩展相应 Structure 范围。

切点或片段长度变化，强制失效对应片段及下游缓存；不能只看同名文件是否存在。将片段 manifest、渲染参数及实际时长纳入缓存判定。纯文字改动可复用无字底片和已确认音轨；卡片或转场时长变化则须重新编译并更新所有下游位置。

下一模型先读 handoff、project、capability-map、sources、coverage、Structured Observation Layer、content-map、Narrative Direction 与 Editorial Execution Plan，再按需读取相关 scene / unit / review / evidence。不得仅凭前一模型的 overview、Narrative Direction 或 execution plan 把未看部分写成已验证。

## v1.0.3 执行完整性接入

沿用 A—G 与两次 Direct。Detail 的实际观察记录与 edit boundary 追加源版本、时间映射指纹；单位 verification 与采用 reviews / utterances 保留同样绑定。完成 Direct 2 时，将已经确认的取舍保存为 execution-authorization.json：采用事件、顺序、unit / boundary、音轨、文字、转场与允许调整。Execute 读取这些记录并检查实际采用范围、原声对白和例外依据，再编译。

授权不增加固定审批关卡：当前用户已经确认且包含执行时，据该授权继续工作；缺证据时补实际观察，机器记录不能代替观察。按 [执行完整性契约](execution-integrity.md) 创建字段，并在外部渲染前运行 check_render_authorization.py。
