---
name: long-video-remix
description: 从三到五小时或多集影视、活动视频中建立可回查的画面与原声索引，先输出正式的文字化 Structured Observation Layer 与 Content Map；由人工或独立 Director 确定 Narrative Direction 后回原素材做定向高密度核验，再由 Director 基于 Detail 证据形成 Editorial Execution Plan，最后落实为可执行剪辑时间轴、渲染清单与成片核查。用于长视频结构化、九宫格分析、逐抽样帧记录、定向精查、同集重组、跨场景主题混剪、剪辑执行稿、分层渲染、成片返工、导出核查及跨模型交接；不把两次创意决策作为默认自动职责。
---

# 长视频结构化与混剪执行

公开仓库版本 v1.0.5 · 2026年10月1日

本 Skill 的核心不是“一句话自动生成成片”，而是先把视频、图像、对白与上下文等高成本多模态信息压缩成有来源、可检索、可回查的**紧凑结构化工作层**，让后续人工、Director 或其他 Skill 尽量基于表格 / 文本继续工作；创意方案确认后，再只把命中的区域压回原素材做高密度核验，并落实成真正可执行的剪辑方案。

整体工作分为三个功能层，但 Direct 在完整工作流里出现两次：

- **Structure**：先用 Broad Structure 把原始多模态素材转换成正式的文字化结构数据；在第一次 Director 已确定叙事主线后，再回原片做第二轮 Directed Deep / Detail Structure。
- **Direct**：第一次回答“这批素材到底讲什么”，形成 Narrative Direction / Narrative Spine；第二次在 Detail Structure 证据补全后回答“最终具体怎么讲”，形成 Editorial Execution Plan。两次都默认由人、独立研究 / 编导环境或 Director 完成。
- **Execute**：只把第二次 Director 已确认的执行方案与已核实素材编译成时间轴、渲染清单、粗剪 / 成片及 QA，不重新发明主线。

标准路径是：

```text
Source
  ↓
Broad Structure
  ↓
Structured Observation Layer
(frame-observations + action-node-candidates + structure-questions + scene/segment observations)
  ↓
Content Map + emotional / relationship cues
  ↓
Direct 1 — Narrative Direction
“到底讲什么？” → Narrative Spine + candidate regions + questions to verify
  ↓
Directed Deep / Detail Structure
“围绕这条主线，把证据看清楚”
  ↺ 证据不足 / 主线不成立时返回 Direct 1 调整
  ↓
Direct 2 — Editorial Execution Plan
“这些证据最终怎么讲？” → confirmed execution plan
  ↓
Execute
  ↓
Render / QA
```

抽帧负责发现，连续音画负责核实，完整片段负责剪辑。允许改变叙述顺序和集中呈现分散线索；保留原话含义、真实指向、必要因果和动作完整性。

## 执行边界

- 按本轮明确要求、已确认方案、指定素材、一般默认值的顺序执行。未经要求，不改原 Handoff、已有成片或已确认的编导主线。
- 先核查可用模型及工具，按能力映射 MCP；本 Skill 中的能力名均为内部抽象名，不是真实工具名。没有调用成功记录，不写成已经完成。
- 默认以角色和剧情为对象。公开活动只描述可见行为和观看感受，不由混剪推断真人私下关系、性取向或心理。
- 不凭抽样帧补出未见动作，不凭转写补出未听台词，不把用户摘要或工具标签改写为亲眼观察。
- **Broad Structure 不因已有 brief 过早缩窄覆盖。** brief 可以帮助标注重点，但第一轮仍要保留整体内容面、coverage 和 unknowns。
- **Structure 有最低信息地板。** `frame-observations.csv`、动作节点候选、结构化问答 / 未验证项，以及进入第二轮后的 `detail-intervals.csv` / `speaker-adjudications.csv` 是基础工作层，不得用 overview、Content Map、最终文案或剪辑结论替代。某字段没有可见信息时也要显式写 `none` / `unknown` / `not_applicable`，不能留空造成“未观察”和“没有发生”混淆。
- **时间标签是全流程的证据主键。** Structure 中一律以 `source_id + source_ms / source_range` 为 canonical 定位；`display_timecode` 只是人读显示，九宫格序号、ASR 自带时间、代理文件时间和成片时间都不能替代源时间。任何抽帧、硬字幕、ASR、原声核听、动作节点、Detail observation、unit 都必须保留或能无歧义映射回同一源时间；Execute 再由 source time 通过 event anchor 编译到 assembly / output frame。源版本或 time mapping 变化时，所有精确下游坐标必须失效重核。
- **未观察到不等于没有发生。** 4fps 是动作候选的局部加密起点，不是“没有发生”的充分证据。否定性结论必须先限定明确 source-time 范围，再按事实类型核验：视觉动作 / 物件缺席需连续视频覆盖完整机会窗口，某句话未说需连续原声覆盖声明区间，或存在能直接排除该事实的可靠反证；否则只记录 `not_observed_in_sample` / `unknown`。
- **证据冲突按事实类型裁决，不设一条机械总排名。** 视觉动作以连续原画为主；实际台词以清晰原声核听与可靠官方硬字幕相互校验；说话人 / 对象结合口型、连续原声、人物关系与字幕信号。ASR 尤其在方言 / 强口音下默认只作 locator，未经回听或硬字幕核对不得升级为台词事实；冲突必须显式保留。
- **先记录基础事实，再做派生判断。** 画面事实、动作、硬字幕、原声要点、与前帧变化、背景、情绪线索、主题判定、confidence / 证据依据、问题与未验证项必须保留；意象标签、情绪解释、叙事功能和剪辑价值只能建立在这些基础记录之上。
- **第一次 Direct 的 Narrative Direction 是创意意图，不等于素材已经证明。** Directed Deep / Detail Structure 必须围绕其 narrative spine、candidate regions 和 verification questions 重新回到相关原片核对。
- 如果第二轮证据与 narrative direction 冲突，报告冲突、替代素材和缺口；默认返回 Direct 1 调整主线，不通过剪辑技巧强行证明原方案。
- **第二次 Direct 必须发生在 Detail Structure 之后。** 它基于已核实的 Deep observations / verified units / protected ranges 形成 Editorial Execution Plan；Execute 默认只落实该计划，不把素材证据层直接等同于最终剪辑方案，也不擅自重写已确认的核心表达。
- 同一集优先；同一事件、对白指向和关系阶段优先级高于服装相似。跨集须有明确主题联系，并让观众辨认时空变化。
- 删段不删句，删重复不删因果。必要问答、否定、条件、迟疑、回应和动作后果共同决定最短保留范围。
- 默认不改写原声、不拼接词语制造新对白、不借用异场反应冒充即时回应。明确要求架空或恶搞时另行约定，不沿用剧情准确混剪的事实标签。
- 不强制每条五至八段或四十五至六十秒。未给时长时先提出由证据支持的时长，再试剪；不为达到配额拆碎互动。
- 不设固定审批关卡。有明确授权就继续；仅在素材缺失、关键意思不确定或需扩大用户明确限定范围时，完成可做部分后提出一个具体问题。

## 开始工作

1. 读取 [工作流程](references/workflow.md) 和 [数据契约](references/data-contracts.md)，建立任务目录与 `project.json`。
2. 读取 [MCP 适配](references/mcp-adapter.md)，发现真实能力、记录映射并完成小范围探测。只使用获授权的素材访问与处理范围。
3. 检查已有产物。按源文件版本和配置恢复进度；不因切换模型重复扫描完整视频。
4. 如果当前任务只要求 Structure，可在 Structured Observation Layer + Content Map 完成后正式交付，不必进入 Direct 或 Execute。
5. 如果要继续混剪，先读取已有 Narrative Direction；没有时，把 Broad Structure 的正式结构化表单、scene / segment observations、Content Map、情绪 / 关系线索和 usable bounds 交给用户或独立研究 / 编导环境，结合外部资料与人工判断形成第一次 Direct 输出。Detail Structure 完成后，再把完整证据包交回 Director 形成第二次 Direct 的 Editorial Execution Plan。
6. 从当前可验证阶段开始，按下面的顺序推进。缺少某种观察能力时降级输出，并明确标签。

## 工作顺序

| 阶段 | 执行动作 | 产物 | 进入下一步的条件 |
|---|---|---|---|
| A 素材登记 | 确认版本、时长、时间基准、字幕匹配、能力与配置 | project、sources、capability-map | 能把后续证据定位回原素材；否则只做准备 |
| B Broad / Board Structure | 全时段粗扫画面和台词；逐张记录已分析抽样帧的完整基础观察；保留帧尾、原声要点、主题判定与 confidence；标记相邻帧变化、意象、动作节点候选，并对候选开 4fps 局部窗口；记录问题回答与未验证项；登记可用素材物理边界并增量落盘 / 更新 coverage | frames、frame-observations、action-node-candidates、structure-questions、transcript、coverage、usable source bounds | 基础观察层完整且可识别覆盖与缺口；源时间映射稳定；人工 / Director 不必重新从九宫格猜内容 |
| C Structured Working Layer + Content Map | 在逐抽样帧表之上形成 scene / segment 观察、source-order overview、情绪 / 关系线索和跨场景 Content Map；这些都是 Broad Structure 的正式文字化结构输出，不是用 Content Map 替代表单 | frame-observations、action-node-candidates、structure-questions、scenes / segment observations、overview、content-map、emotional / relationship cues | 形成足够完整且可下钻回 frame observation 的素材面；若 deliverable=content_map 可在此正式交付 |
| D1 Direct — Narrative Direction | 人 / Director 读取正式结构化表单 + Content Map + 外部研究，抽选“到底讲什么”：核心命题、Narrative Spine、candidate regions、需要 Detail 验证的问题和禁改项 | brief、narrative-direction、external research refs、narrative mapping | 主线已人工确认到足以指导定向深挖；不要求已有精确切点 |
| E Directed Deep / Detail Structure | 带着 Narrative Direction 回到相关原素材，先建立精查区间卡，再提高抽样 / 播放密度；补完整画面、内容、背景、前后状态、原声、说话人裁决、主题判定与 confidence；进一步识别完整可剪单元的音频 / 动作 / 反应边界，给出 preferred in/out、safe in/out windows、must-keep ranges 与 cut risk，再形成 verified units / protected ranges | detail-intervals、deep-observations、speaker-adjudications、edit-boundaries、已核实 units、reviews、protected_ranges、evidence gaps | 每个核心节点有足够音画、内容与语境证据，并有可追溯 edit boundary；主线不成立时退回 D1 调整 |
| D2 Direct — Editorial Execution Plan | Director 读取 Detail Structure 的完整证据包，决定“这些材料最终怎么讲”：最终取舍、顺序、段落功能、声音 / 文字策略、时长分配、允许调整与禁改项 | execution-plan、selected verified units、final narrative mapping | 最终执行方案已确认；关键节点 evidence_status 不为 pending / contradicted |
| F Execute | 只落实已确认 execution plan：先通过阶段 / Direct / evidence / edit-boundary 机械门槛，再用累计时长统一量化事件边界并完成时长预算对账；按反馈类型确定失效范围；标明声音的叙事作用；再编译叠化后的时间轴、分层渲染并生成全接点图表 | timeline（含 duration budget 与 boundary refs）、transitions、render-manifest、edit-plan、rough-cut | 两次 Direct 均 confirmed；每个入选 source event 显式引用实际采用的 Deep observation 与 edit boundary，默认切点落在 safe windows 并覆盖 must-keep ranges；若故意越界必须显式 override 并绑定具体规则、区间、当前有效 review 与已确认创作决定；Direct 2 机器授权、当前 source/time-mapping 证据、许可取段和原声音轨连续性检查均通过；预算守恒；源时间→成片时间映射可追；实测帧数与时长；近静音窗口有记录，再继续音画实看 |
| G QA & Handoff | 逐接点及全片复核，做 EVA，保存问题与缓存版本 | render-audit、接点图表、qa、handoff | 技术检查与人工观看分别记录，不以成功日志代替验收 |

## Structure 的两种密度

### 第一轮：Broad Structure

目标是**扩大可见范围，并把多模态素材压成正式、文字化、可检索、可回查的结构化工作层**，不是提前替某个选题找证明。Broad 的核心出口首先是这些表单和分片段观察数据；Content Map 与情绪 / 关系大意建立在它们之上，不能替代它们。

- 全时段建立基础画面与台词覆盖；
- 对每张**已实际分析的抽样帧**建立一行基础结构化观察：帧号 / 时间 / 帧尾 ms、可见人物、画面事实、动作 / 状态、可观察情绪线索、表情 / 视线、空间关系、环境背景、关键物件、`motif_tags`、硬字幕 / 可见文字、**原声要点及其核听状态**、邻近对白、内容说明、`change_from_previous`、**topic_judgment、confidence、confidence_basis**、interpretations 与 unknowns；
- `change_from_previous` 只写相邻**已分析抽样帧**之间实际可见的变化，不把中间未观察过程补成完整动作；第一张可写 `not_applicable`；
- 出现明显动作变化、视线 / 站位变化、物件交接、进入 / 离开等候选节点时，登记 `action-node-candidates.csv`，同时保留候选起止帧、最小有效单元候选、口型 / 说话线索与关系转折信号，围绕候选点建立默认 **4fps** 的局部高密度窗口；若因源帧率、工具限制或连续播放更合适而偏离 4fps，必须记录 `sampling_exception_reason`；
- 对理解场景或候选价值有实质影响的问题，登记 `structure-questions.csv`：保留问题、回答、回答状态、证据引用、未验证项和下一步核查；未回答的问题保持 `unresolved`，不能被 overview 或最终结论吞掉；
- 同时保留机器可追溯的 `frames.jsonl` 与便于人工 / Director / 其他 Skill 阅读的 `frame-observations.csv`；动作候选与问题分别进入 `action-node-candidates.csv`、`structure-questions.csv`；后续创意阶段优先消费这些结构化表，而不是反复加载原始九宫格；
- 场景、人物、事件、关系变化和无声互动都保留入口；
- 形成 source-order overview 和跨场景 Content Map；
- Broad Structure 的正式交付包称为 **Structured Observation Layer**：`frame-observations.csv` + `action-node-candidates.csv` + `structure-questions.csv` + scene / segment 观察 + `overview.md`；`content-map.md`、情绪 / 关系线索和 usable bounds 是建立在这套文字化结构数据之上的导航层。第一次 Director 必须优先消费这套表单，而不是只读一份总结；
- 明确抽样、字幕 / ASR、连续音画核实三种 coverage 的差别；
- Broad 阶段发现片头卡、黑场、硬切尾、缺帧 / 缺音等物理边界时，在 `sources.json` 中登记 `usable_ranges` / `downstream_constraints`，并在 Content Map / handoff 显式传给 Direct，不能让编导对不存在的可用时长做承诺；
- 高成本长任务采用 **incremental output + resume + coverage accounting**：按已完成区间持续落盘基础表和 coverage；任务中断后从缺口继续，不因 agent / 工具静默结束而重扫已经完成且版本一致的多模态区间；
- 不把未处理区域悄悄排除。

### 第二轮：Directed Deep Structure

目标是**只把已确认方案命中的节点重新压回原片证据**，把高成本观察集中在真正需要的区域。

- 先建立 `detail-intervals.csv`：写清精查区间、为什么进入精查、前情、当前背景、后续、内容摘要、目标问题与主题关联；再根据计划节点提高抽样密度或直接连续播放；
- 先建立 `deep-observations.csv`：完整记录人物与站位、镜头 / 构图、动作链、关键画面变化、可观察情绪线索 / 情绪解释、表情 / 视线、空间关系、场景环境、关键物件与 `motif_tags`；
- 写清这一核心区域**实际发生了什么**，并补充 setting_context、narrative_context、before_state、after_state；
- 从台词命中扩展到完整问答、动作链和必要前后文；保留原声要点、硬字幕 / ASR 冲突和核听状态。说话人或对象不清时进入 `speaker-adjudications.csv`，按事实类型综合帧级口型、可见人物、连续原声与可靠硬字幕裁决 speaker / addressee；ASR 默认只作 locator / 辅助信号，方言或强口音未经核听不得单独定案；
- facts、interpretations、unknowns 分开；每个核心观察保留 `topic_judgment`、`confidence` 与 `confidence_basis`，主题判定必须落到该帧 / 节点承担的具体叙事作用，不能只写抽象标签；检查反证、误读风险和时空关系；
- 在完整理解之后，再把初步 unit 收敛为可剪 unit，并形成 context_ranges、protected_ranges 与 isolated_use_risk；同时必须建立 Edit Boundary / Continuity Layer：区分内容范围、真实音频尾部、动作 / 反应收束，输出 preferred in/out、safe in/out windows、must-keep ranges、handles 与 cut risk。字幕消失、ASR 结束或抽样帧中的动作停止都不能直接当作自然切点；
- 如果 Narrative Direction 不成立，把具体问题返回 Direct 1，而不是直接替用户重写核心创意；如果证据成立，则把完整 Detail evidence package 交回 Direct 2，由 Director 形成最终 Editorial Execution Plan 后才进入 Execute。

## 决策时读取

- 抽帧密度、批次、Content Map、第二轮定向回查和恢复：读取 [工作流程](references/workflow.md)。
- 时间码、记录字段、Structured Observation Layer / Content Map / 两次 Direct 与时间轴关系：读取 [数据契约](references/data-contracts.md)。
- 换模型或 MCP、能力缺失、调用失败：读取 [MCP 适配](references/mcp-adapter.md)。
- 在已确认 Narrative Direction / execution plan 下保住完整对白、连续性与正确重组关系：读取 [重组与剪辑规则](references/montage-rules.md)。
- 首次出片或返工：读取 [渲染与工程检查](references/render-engineering.md)，按文字校准、时间轴编译、分层渲染、解码实测、全接点检查顺序执行。
- 交付前、移交另一模型：读取 [检查与交接](references/qa-handoff.md)。
- 准备 Direct 2 执行记录、进入正式编译或接入渲染器：读取 [执行完整性契约](references/execution-integrity.md)，将采用证据与源版本绑定，明确 adopted_utterance_refs 和源音轨 review_refs；逐源音轨核对白保护及完整取段核听，包括卡片、未关联与异源仅音频。关联视频时另核同步；独立声音按成片放置核完整对白、政策原因及 track 级例外。continuity_type 不关闭保留对白政策；指纹计算不等于实际观察或人工确认。
- 每次改版或重新封装后：读取 [核心能力回归检查](references/regression-checklist.md) 与 [Structure 能力对照矩阵](references/structure-regression-matrix.md)，确认 Board/Broad / Detail / Direct / Execute 主线和基础信息层没有被弱化。
- 需要演示两轮 Structure、外部 Direct 和 Execute 的衔接：读取 [执行示例](references/worked-example.md)。示例均为虚构，不是当前素材。

复制 `assets/project-template.json` 建立配置。Broad Structure 可复制 `assets/frame-observation-template.csv` 建立人可读逐抽样帧观察表，同时用 `assets/action-node-candidate-template.csv` 记录动作节点的 4fps 局部窗口、用 `assets/structure-question-template.csv` 记录问题回答与未验证项；第二轮先复制 `assets/detail-interval-template.csv` 建立精查区间卡，再用 `assets/deep-observation-template.csv` 建立核心区域高密度观察表；说话人 / 对象不清时使用 `assets/speaker-adjudication-template.csv`，即使本轮没有歧义也保留带表头的文件。需要 Direct 时，可复制 `assets/brief-template.md`、`assets/narrative-direction-template.md` 和 `assets/execution-plan-template.md`；`assets/editorial-plan-template.md` 保留为兼容 / 合并式计划模板，也可以直接接入用户已有的编导文档。复制 `assets/timeline-template.json` 建立时间轴。

具备 Python 时运行 `scripts/validate_project.py 项目目录` 检查来源、时间和引用；不具备 Python 时按数据契约逐项核查，并写明为人工或模型静态检查。脚本不判断剧情真伪或观看流畅度。

进入实际渲染时，用 `scripts/compile_render_manifest.py 项目目录` 编译成片坐标与缓存键，再按 [渲染与工程检查](references/render-engineering.md) 使用 `scripts/audit_render.py` 实测导出并生成接点对照表。前者需要 Python；后者需要 Python 和 FFmpeg，拼图额外需要 Pillow。缺少能力就列明未验证项，不填通过。

## 每次工作结束

先交付已完成产物，再用短文字说明：本次处理范围、当前处于 Broad Structure / Direct / Directed Deep Structure / Execute 的哪一层、发现、未验证项和下一步。更新 `handoff.md` 及 `coverage.json`。长任务同时记录已完成区间、未完成区间和可恢复入口。

时间标签必须随交接一起保存：源版本、`time_mapping`、所有关键 `source_id + source_ms / range`、以及已经编译出的 assembly / output frame 对应关系。任何下游工件若失去源时间回查能力，视为不可交接。

同一项目保留稳定 ID；修订增加版本，不能让旧引用悄悄指向不同素材。不要以再次询问已确认事项代替推进。
