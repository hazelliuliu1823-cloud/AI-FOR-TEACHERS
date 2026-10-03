# 数据契约

目录：文件清单、共同约定、证据记录、场景与片段、Content Map 与外部 Direct、计划映射、剪辑时间轴、静态校验。

## 文件清单

按阶段创建需要的文件。还没到某阶段时允许文件不存在，不用空文件冒充已处理。每个项目放在独立目录。

| 文件 | 格式与用途 |
|---|---|
| project.json | 对象；任务范围、约束、参数、交付目标、版本 |
| capability-map.json | 数组；内部能力和真实工具的映射 |
| sources.json | 数组；源文件、版本、时长、时间映射 |
| frames.jsonl | 每行一个抽样帧证据记录；包含图片定位和机器可追溯 facts / unknowns |
| frame-observations.csv | Broad Structure 的人可读逐抽样帧基础观察表；供人工 / Director / 其他 Skill 浏览 |
| action-node-candidates.csv | Broad / Deep Structure 的动作变化候选；记录 4fps 局部窗口、触发原因与核验状态 |
| structure-questions.csv | Structure 阶段的问题—回答—证据—confidence—未验证项工作表 |
| detail-intervals.csv | Directed Deep / Detail Structure 的精查区间卡；保留进入原因、前情、当前背景、后续、目标问题 |
| speaker-adjudications.csv | 说话人 / 对象的帧级裁决记录；口型、画面、硬字幕、ASR、原声与 confidence 分列 |
| transcript.jsonl | 每行一条字幕或转写；保留核听状态 |
| scenes.jsonl | 每行一个事件或场景；链接多个源区间 |
| units.jsonl | 每行一个可用的连续片段及其保护范围 |
| reviews.jsonl | 每行一次实际观察的区间、模态、结果与审阅者 |
| deep-observations.csv | Directed Deep Structure 的核心区域高密度观察表；包含完整画面、内容、背景、前后状态、原声、反证及 plan 关系 |
| edit-boundaries.csv | Detail Structure 的可剪边界 / 连续性表；把内容范围、真实音频尾部、动作 / 反应收束与 safe in/out windows 分开记录，并为 Direct 2 / Execute 提供强约束切点 |
| structure-exceptions.jsonl | 无法满足的 Structure 字段 / 产物声明；status、reason、impact、downstream_handling 与原字段分开保存 |
| keyframe-references.json | Detail 的真实关键帧清单与可读图片入口；source time、素材节点、用途和异常 |
| execution-handoff.md | E 阶段独立交接；主题、证据、保护范围、关键帧及下游完整 Execution Package 要求 |
| execution-reference.md | D2 的制作参考；具体样式、声音 / 转场规则、少量 reference 的应用规则、资源与 QA |
| coverage.json | 数组；按素材、区间、模态记录覆盖状态 |
| overview.md | 带 scene_id 的 source-order 全片导航，不替代证据 |
| content-map.md | 第一轮 Structure 的横向内容地图；链接 scene / evidence / coverage，供人或 Director 做创意判断 |
| brief.md | 可选输入；主题、核心表达、范围、重点和禁改项，可来自用户或外部 Direct |
| narrative-direction.md | 第一次 Direct 的 Narrative Direction；记录核心命题、Narrative Spine、candidate regions、verification questions 与禁改项 |
| execution-authorization.json | Direct 2 的机器授权、采用范围、顺序、处理、证据与决策指纹；draft 不能授权渲染 |
| execution-plan.md | 第二次 Direct 的 Editorial Execution Plan；基于 Detail 证据确认最终取舍、顺序、声音 / 文字策略、时长与执行边界 |
| editorial-plan.md | 兼容旧项目的合并式 / legacy Direct 计划；新项目优先拆分为 narrative-direction + execution-plan |
| candidates.json | 兼容性结构；记录 editorial plan 的映射分支、证据、片段顺序、反例和状态，不要求由本 Skill 自动生成 |
| timeline.json | 对象；主视频轨、音轨、文字轨、输出参数 |
| transitions.json | 数组；每个相邻主视频段落的接续关系 |
| render-manifest.json | 对象；编译后的成片帧轴、接点、轨道坐标、分层缓存键 |
| render-audit.json | 对象；真实导出文件的完整解码计数、时长、近静音及接点图表记录 |
| edit-plan.md | 人可读执行稿，与时间轴保持一致 |
| qa.json | 对象；每项检查、证据、问题及待验证事项 |
| handoff.md | 下一模型从哪里接手、读哪些文件、还差什么 |
| jobs.jsonl | 工具调用、缓存键、状态、产物与可重试错误 |

## 共同约定

- 各类文件的 schema 分开管理：`project.json` 当前使用 `schema_version=1.6`；`timeline.json` 使用 `schema_version=1.4`；`render-manifest.json` 使用 `schema_version=1.4`；`execution-authorization.json` 使用 `schema_version=1.0`。证据 JSONL / CSV 按本文件字段契约管理，不把 project / timeline / manifest 的版本号混用。原有 1.0 / 1.1 证据记录保留，不为升级重写内容。UTF-8；JSONL 每行独立合法 JSON；未知值用 null，不用猜测值占位。
- source_id、frame_id、utterance_id、scene_id、unit_id、candidate_id、event_id、review_id 各自全项目唯一；一旦被引用不重新编号。
- 所有源区间使用整数 start_ms、end_ms，左闭右开，即包含开始、不包含结束。必须满足 0 ≤ start_ms < end_ms ≤ source.duration_ms。单帧用 timestamp_ms，必须小于 duration_ms。
- **`source_id + source ms/range` 是全流程证据层的 canonical time tag。** `display_timecode`、九宫格位置、抽样序号、字幕 / ASR 文件时间和代理时间只是派生信息；若使用代理、分轨或外部字幕，必须通过 `source.time_mapping` 映射回 canonical source time。进入 Execute 后新增 assembly / output frame，但不得覆盖源时间。任何引用如果只有“第几秒”却没有 source_id 或坐标空间，不视为稳定定位。
- 原始文件发生内容变化时建立新 source_id；原版本 ID 保留。只移动位置可更新 locator，保持 source_id 不变。
- evidence_refs 使用带类型的引用，例如 frame:F001、utterance:T001、review:R001。外部前情使用 context_refs，记录来源与核实状态，不伪造本项目证据 ID。
- facts、interpretations、unknowns 分开。facts 中也保留证据来源，区分模型实际观察、用户提供和上游工具输出。
- 第一轮 Broad Structure 与第二轮 Directed Deep Structure 使用同一套稳定 source / scene / unit / evidence ID；第二轮补密时优先更新 verification、context_ranges、protected_ranges 和 review_refs，不复制一个看似全新的平行素材库。
- `frame-observations.csv`、`action-node-candidates.csv`、`structure-questions.csv`、`deep-observations.csv`、`content-map.md`、`brief.md`、`editorial-plan.md` 都是人可读工作层，不替代 JSON / JSONL 原始证据。任何创意判断进入 Execute 前仍须链接回 frame / utterance / scene / unit / review / source range。
- 不把取样帧序号当成源视频帧号。display_timecode 只用于阅读，机器使用毫秒或输出帧号。


## 输出异常、关键帧与执行包补充

原 CSV 表头与类型锁定；字段无法取得时使用原契约允许的未知表示，并在 `structure-exceptions.jsonl` 保存异常，继续可做的索引 / 草案 / 交接，不虚构、删字段或把未完成阶段标成 complete。E 固定提供 keyframe 清单和自包含 handoff；D2 提供 execution-plan + execution-reference。详见 [异常与执行包契约](execution-package.md) 及其可复制模板。

project 增加可选 `structure_exceptions_ref`、`keyframe_references_ref`、`execution_handoff_ref`、`execution_reference_ref`、`execution_reference_asset_refs` 与 `execution_package_policy`。新模板使用 `plan_and_reference`；旧项目未声明时保持既有行为。新 policy 下 Detail complete 须有清单 / handoff，正式 ready 须有 reference 文档和已列出的资源；关键帧缺失有明确异常仍可继续。采用未核实证据的原门槛不变。

完整执行包确认追加 reference 文档 / 实际样本指纹，变更使旧确认失效。只有结构 / 文件 / 指纹经过机器检查，内容完备性与风格一致性仍按契约人工 / 模型审阅；不要据此声称视觉通过。

## 结构化工作层与上下文成本

Structure 的目标之一，是把视频 / 图像 / 原声等高成本多模态输入转换成 **compact structured representation**。`frames.jsonl`、`frame-observations.csv`、`action-node-candidates.csv`、`structure-questions.csv`、scene / segment observations 与 overview 共同构成第一轮正式的 **Structured Observation Layer**；`content-map.md` 与情绪 / 关系线索建立在这层文字化结构数据之上。第一次 Direct 优先消费这些表单和文本，而不是反复重新加载原始视频或九宫格。

这是一种有损压缩式的工作表示，但不是证据替代：所有关键记录必须保留时间码和 evidence refs，确保需要时可以重新下钻到原素材。第二轮 Directed Deep Structure 只对 editorial / script plan 命中的区域恢复更高密度多模态上下文。这样可以减少重复上下文和不必要的高密度观察，但不承诺固定比例的 token 或算力节省。

## 素材和证据记录

sources 每条必填 `source_id`、`locator`、`version`、`duration_ms`、`time_mapping`。version 可以是可核查版本标识或哈希；未知为 null，并阻止复用旧缓存到精确剪辑。`time_mapping` 即使为原文件直读也写 `{"type":"identity"}`，代理 / 合集切分 / 非线性转换则保存可复核映射。其他字段包括 episode、width、height、fps_num、fps_den、frame_rate_mode、audio_streams、subtitle_source。

Broad Structure 完成时，每个 source 还应有 `usable_ranges`（可用源时间区间；完整可用也显式写全长区间）与 `downstream_constraints`。片头 / 片尾卡、黑场、缺音、代理缺段等会限制后续设计的边界必须写入这里，并由 Content Map / handoff 传给 Direct；不能只留在某次分析文字里。

frame 必填 frame_id、source_id、timestamp_ms、image_ref、facts、unknowns。建议补充 sheet_id、cell_index、visible_text、observation_origin。cell_index 为一至九，不参与时间计算。frame 只描述该时点看见的状态。

`frame-observations.csv` 是同一批抽样帧的**人可读基础结构化层**，不是另起一套证据 ID。每行必须对应一个已实际分析的 sampled frame；Broad Structure 标记 complete 时，其 frame_id 集合应与 `frames.jsonl` 一致。字段至少包括：`source_id`、`episode`、`timestamp_ms`、`display_timecode`、`frame_id`、`sheet_id`、`cell_index`、`scene_id`、`characters`、`visual_facts`、`visible_action_state`、`observed_emotional_cues`、`emotional_interpretation`、`expression_gaze`、`spatial_relationship`、`setting_background`、`key_objects`、`motif_tags`、`visible_text`、`nearby_dialogue_refs`、`content_description`、`change_from_previous`、`action_node_candidate_ids`、`interpretations`、`unknowns`、`evidence_ref`、`image_ref`、`coverage_status`。

其中 `visual_facts` / `content_description` 不得把相邻抽样帧之间未实际观察到的动作补齐；**稀疏抽样中的“没看到”不能写成“没有发生”，4fps 或更密抽样本身也不能证明整个区间内没有发生。**否定性事实必须先声明明确的 source-time 观察范围，再按事实类型核验：视觉动作 / 物件缺席需连续视频 review 覆盖完整机会窗口，语音缺席需连续原声 review 覆盖声明区间，或存在能直接排除该事实的可靠反证；否则写 `not_observed_in_sample` / `unknown`。`change_from_previous` 只能描述相邻已分析抽样帧的可见差异；`motif_tags` 是导航标签而非已确认象征；`observed_emotional_cues` 只写可观察线索，`emotional_interpretation` 与事实分列。`visual_facts`、`visible_action_state`、`motif_tags`、`visible_text`、`original_audio_keypoint`、`audio_verification_status`、`change_from_previous`、`content_description`、`topic_judgment`、`confidence`、`confidence_basis`、`unknowns` 不允许空白；没有内容时显式写 `none` / `unknown` / `not_applicable`。这里的“逐帧”始终指逐**已分析抽样帧**。

`action-node-candidates.csv` 每行一个动作 / 视线 / 站位 / 物件状态等变化候选，至少包含 `candidate_id`、`stage`、`source_id`、`scene_id`、`trigger_frame_id`、`center_timestamp_ms`、`trigger_reason`、`change_signal`、`window_start_ms`、`window_end_ms`、`sampling_fps`、`evidence_refs`、`verification_status`、`unknowns`、`review_refs`。默认 `sampling_fps=4`；偏离时必须填写 `sampling_exception_reason`。候选窗口只是局部加密观察机制，不等于动作已经被连续音画验证。

`structure-questions.csv` 用于保留 Structure 中真正影响理解的问题，不允许只把未确定内容散落在总结里。至少包含 `question_id`、`stage`、`source_id`、`scene_id`、`frame_refs`、`plan_node_id`、`question`、`answer`、`answer_status`、`evidence_refs`、`unverified_items`、`next_check`、`review_refs`。`answer_status` 只用 `supported`、`partial`、`unresolved`、`contradicted`、`not_applicable`。未解决问题必须继续可见。

utterance 必填 utterance_id、source_id、start_ms、end_ms、text、origin、audio_verified。origin 为 subtitle、asr、manual 或 user；audio_verified 默认为 false。其他字段包括 speaker、addressee、language、translation、unclear_words、review_refs、`asr_role`。未知说话人保持 null，不能按画面中出现的人直接指定。

ASR 默认是定位 / 候选证据，不天然等于台词事实。方言、强口音或已知高误识率段落应标 `asr_role=locator_only`；要把台词写进 facts，需要可回查的原声核听或可靠硬字幕支持。硬字幕与原声冲突时不机械规定“字幕永远赢”或“原声永远赢”，而是记录 conflict，并按要裁决的事实类型与源可靠性回原片处理。

review 必填 review_id、source_id、start_ms、end_ms、modalities、reviewer、result、evidence_locator。modalities 是实际处理的 video、audio、frames 或 text 列表；reviewer 说明来自模型、工具或用户。保留能复核的工具输出、人工确认记录或音画位置。只有提取音轨的日志不算 audio 审阅。

coverage 每条包含 source_id、start_ms、end_ms、modality、method、status、evidence_file、reason。modality 为 visual_sample、transcript 或 av_review；status 为 complete、partial、failed、pending、excluded。complete 只指该模态在该区间按所列方法处理完成。excluded 必须有理由。覆盖率按区间并集计算，不把批次重叠重复计入；不能把 visual_sample 的完成率叫作完整观看率。

## 场景和片段

scene 包含 scene_id、source_ranges、characters、location、story_time、facts、interpretations、unknowns、before_state、after_state、evidence_refs、context_refs。source_ranges 是若干 source_id/start_ms/end_ms 对象，允许交叉叙事。story_time 不确定时写 null。

unit 包含以下字段。一个 unit 只能对应一个源文件中的连续区间。

```json
{
  "unit_id": "U001",
  "scene_id": "S001",
  "source_id": "SRC001",
  "start_ms": 120000,
  "end_ms": 145000,
  "context_ranges": [{"source_id":"SRC001","start_ms":100000,"end_ms":170000}],
  "protected_ranges": [{"start_ms":122000,"end_ms":142000,"reason":"完整问答与动作回应"}],
  "summary": "示例占位，须据实际素材填写",
  "utterance_ids": ["T001"],
  "evidence_refs": ["utterance:T001"],
  "visual_state": {"costume":null,"props":null,"position":null,"lighting":null},
  "relationship_stage": null,
  "audio_state": {"speech":true,"music":null,"ambience":null},
  "isolated_use_risk": "缺少前一问时指代不清",
  "verification": {"audio":"pending","visual":"pending","context":"pending","review_refs":[]},
  "unknowns": ["尚未回看连续音画"]
}
```

verification 的 audio、visual、context 使用 pending、reviewed、not_applicable。not_applicable 在 not_applicable_reasons 对象中按对应字段说明原因，例如已确认源文件完全没有音轨。仅仅没有对白不等于音频不需检查。reviewed 必须有 review_refs，值为 reviews.jsonl 中真实存在的 review_id；不能仅靠摘要设置。连续画面核查使用 video 模态，仅有 frames 不能标记 visual=reviewed。核查区间合计应覆盖实际选用的片段。protected_ranges 可以在探索期暂为空，精查后入选执行稿时必须有明确保护范围，或在 protection_note 写明为何整段无可保护的对白、动作且经复核。

## Edit Boundary / Continuity Layer

Detail Structure 在“理解完整”之后还必须回答一个独立问题：**如果这段最终被采用，从哪里进、到哪里出才不会无意截断声音、动作、反应或情绪收束？** `edit-boundaries.csv` 是正式基础产物，不得由 execution plan 里的自由文字代替。字幕结束、ASR end、某个抽样帧不再见到动作，都不等于自然切点。

每行至少包含：`boundary_id`、`detail_interval_id`、`plan_node_id`、`source_id`、`unit_id`、`observation_refs`、`continuity_type`、`content_start_ms/end_ms`、`audio_start_ms/end_ms/tail_end_ms`、`action_start_ms/end_ms/reaction_or_settle_end_ms`、`preferred_in_ms/out_ms`、`safe_in_start_ms/end_ms`、`safe_out_start_ms/end_ms`、`must_keep_ranges`、`left_handle_ms/right_handle_ms`、`boundary_reason`、`cut_risk`、`evidence_refs`、`confidence`、`boundary_status`。没有某类连续性时显式写 `not_applicable`，不能留空。

`continuity_type` 使用 `dialogue`、`action`、`reaction`、`music`、`scene`、`mixed`。对于 dialogue / music / mixed，safe-in 窗口必须结束在需完整保留的音频表达开始之前，safe-out 窗口必须开始在真实音频尾部 / 衰减结束之后；对于 action / reaction / mixed，safe-in 必须在动作链开始之前，safe-out 必须在动作或反应 settle 完成之后。`must_keep_ranges` 使用 `start-end;start-end` 的 source-ms 表达，必须位于任一安全切法都会完整覆盖的位置。

Direct 2 选择素材时必须引用 `boundary_id`，而不是自行从字幕时间或内容摘要猜切点。`timeline.json` 中每个 ready source event 必须有 `edit_boundary_ref`。默认要求 `source_in_ms` 落在 safe-in window、`source_out_ms` 落在 safe-out window，并覆盖 boundary 的全部 must-keep ranges。若创作上故意做戛然而止、抢断对白或动作等非自然切法，可以设置 `boundary_override=true`，但必须保留 `boundary_override_reason` 与 `boundary_override_review_refs`，并按 v1.0.3 [执行完整性契约](execution-integrity.md) 提供与具体违规范围、规则、成功审阅和 Direct 2 授权绑定的 `overrides`；这是一项显式创作决定，不能用来掩盖未核准的切点。unit 的 `protected_ranges` 仍是更高层的不可随意丢失约束，override 不自动绕过它。

## Directed Deep Structure 的结构化观察

`deep-observations.csv` 用于第二轮定向高密度 Structure。它不是剪辑表的替代品，也不能只记录“可用 / 不可用”。当某个区域已经被 Narrative Direction（或 legacy rough plan）选为核心回查对象时，应先把它做成更完整的内容档案，再收敛为 unit 和切点。

推荐每行对应一个高密度观察时点或连续观察区间，字段至少包括：

- 定位：`observation_id`、`detail_interval_id`、`plan_node_id`、`source_id`、`episode`、`start_ms`、`end_ms`、`display_range`、`scene_id`、`unit_id`、`representative_frame_refs`、`frame_observation_refs`；
- 画面：`visual_facts`、`shot_composition`、`action_chain`、`key_visual_changes`、`observed_emotional_cues`、`emotional_interpretation`、`expression_gaze`、`spatial_relationship`、`motif_tags`；
- 背景：`setting_context`、`narrative_context`；
- 内容：`content_description`、`hard_subtitle_notes`、`original_audio_keypoints`、`audio_verification_status`、`subtitle_asr_conflicts`、`dialogue_audio`、`speaker_adjudication_refs`、`before_state`、`after_state`；
- 判断：`question_refs`、`topic_judgment`、`confidence`、`confidence_basis`、`interpretations`、`unknowns`、`unverified_items`、`evidence_status`、`counterevidence`；
- 执行衔接：`context_ranges`、`protected_ranges`、`min_effective_unit_candidate`、`isolated_use_risk`、`review_refs`、`narrative_function`、`edit_note`。

字段含义：

- `detail_interval_id` 必须能回到 `detail-intervals.csv`，确保高密度观察不会脱离进入精查时的前情 / 当前背景 / 后续和目标问题；
- `original_audio_keypoints` 只写已真实核听或明确标为未核听的原声要点；`hard_subtitle_notes` / ASR 不得冒充原声；字幕、ASR 与原声不一致时写入 `subtitle_asr_conflicts`；
- `topic_judgment` 写该帧 / 节点在当前候选主题中的具体叙事作用；`confidence` 和 `confidence_basis` 必须同时存在，说明判断来自帧证、连续画面、已核听原声、字幕 / ASR 或组合证据；
- `visual_facts` 写这一时段实际看到的画面；人物、站位 / 朝向、动作、表情 / 视线、人物间距离、物件、景别 / 构图与明显画面变化尽量具体；
- `key_visual_changes` 记录核心区间内已经观察到的动作 / 视线 / 站位 / 物件变化；必要时链接 `action-node-candidates.csv` 的 4fps 局部窗口；
- `observed_emotional_cues` 只写可观察的表情、视线、语气、停顿、身体状态；`emotional_interpretation` 才写谨慎情绪解释，不推断隐藏心理；
- `content_description` 回答“这一小段实际发生了什么”，不只抄对白；
- `setting_context` 写地点、时间、环境、空间状态等场景背景；
- `narrative_context` 写它在完整事件中的位置、前一事件和后续关系；
- `dialogue_audio` 写已核听的原声信息，并明确 speaker / addressee / tone / pause / ambience / music / audio_verified；
- `before_state` / `after_state` 用于保住动作与因果，不等同心理推断；
- `plan_node_id` / `narrative_function` 只说明为什么要回查这一段，不得用计划目标倒推事实；
- `evidence_status` 可用 pending、supported、contradicted、partial；关键节点若为 contradicted 或仍 pending，不进入 ready_for_render。

第二轮可以在第一轮相同 frame_id / scene_id 上补充更密的新 frame / review，也可以对连续区间形成新的 observation_id；不要为了“更细”而复制一套与第一轮断开的素材库。

## Detail 区间卡与说话人裁决

`detail-intervals.csv` 每行对应一个进入 Directed Deep / Detail Structure 的核心区间。至少包含：`detail_interval_id`、`plan_node_id`、`source_id`、`start_ms`、`end_ms`、`entry_reason`、`preceding_context`、`current_background`、`following_context`、`content_summary`、`target_questions`、`topic_relevance`、`evidence_refs`、`unknowns`。前情 / 背景 / 后续不清时写 `unknown`，不能省略。

`speaker-adjudications.csv` 用于说话人 / 对象歧义的帧级裁决。至少包含：`adjudication_id`、`stage`、`source_id`、`utterance_id`、区间、`frame_window_refs`、`lip_movement_observation`、`visible_speaker_candidate`、`addressee_candidate`、`audio_speaker_candidate`、`hard_subtitle_signal`、`asr_signal`、`asr_role`、`evidence_resolution_rule`、`subtitle_audio_conflict`、`decision`、`decision_basis`、`confidence`、`evidence_refs`、`unknowns`。只有字幕或只有画面时不得假装完成裁决；ASR 在方言 / 强口音场景默认 `locator_only_until_verified`。

## Content Map 与两次外部 Direct

`overview.md` 和 `content-map.md` 作用不同：

- `overview.md` 按源时间顺序帮助恢复“原片发生了什么”；
- `content-map.md` 横向组织人物、关系变化、重复行为、对白主题、无声互动、物件 / 空间线索、潜在前后呼应与 unknowns，帮助人或 Director 看见“素材里都有什么可以继续想”。

它们都建立在正式的 Structured Observation Layer 之上，不能反向替代 `frame-observations.csv`、动作节点、Q&A 或 scene / segment 观察。Content Map 中每个可操作条目应尽量带 `scene_id`，必要时补 source range / evidence refs / coverage 状态；情绪大意只作为 `observed cues / trajectory` 的导航性汇总，与心理解释分开。

### Direct 1：Narrative Direction

`narrative-direction.md` 是第一次 Director 的输出，说明“到底讲什么”，至少覆盖：`thesis` / 核心命题、`narrative_spine`、candidate regions / scene refs、各节点功能、verification questions、human decisions、external research refs、constraints / do-not-change。它不要求精确到帧，也不因写得详细就自动升级为素材事实。

Directed Deep Structure 把 Narrative Direction 的每个核心节点映射回已有 Content Map 与原片。建议维护 narrative mapping，至少包含：`plan_node_id`、`function`、`scene_refs`、`unit_refs`、`evidence_refs`、`evidence_status`、`gaps`、`counterevidence`、`allowed_adjustment`。

### Direct 2：Execution Package（含 Editorial Execution Plan）

`execution-plan.md` 在 Detailed Structure 完成后生成，说明“这些已核实材料最终怎么讲”。至少引用 selected verified units / protected ranges，并明确 final order、narrative function、required context、audio treatment、text intent、duration allocation、transition intent、allowed substitutions、execution boundaries 和 do-not-change。

若 evidence_status 仍为 pending / contradicted，不得把对应节点当成可确认执行事实；主线级冲突退回 Direct 1，执行取舍问题留在 Direct 2。Execute 接收 Source Clips、Detail、execution-plan、execution-reference 和 Constraints；只把确认后的包落实为 timeline / render manifest，不在技术层自行补定叙事或风格。reference 用一两个样本锁定全片规则，不逐项映射所有视觉动作。

`brief.md` 可作为两次 Direct 的共同背景输入。`editorial-plan.md` 保留为旧项目或需要合并式文档时的兼容格式，新项目优先使用 `narrative-direction.md` + `execution-plan.md`，第二次 Direct 同时交付 `execution-reference.md`。

## 计划映射与 candidates 兼容结构

`candidates.json` 保留用于兼容既有项目和多分支 Narrative Direction / legacy rough plan。candidate 不再意味着“必须由本 Skill 自动想出的创意主线”；它可以是用户 / Director 提供的 editorial plan 分支，也可以是明确授权 brainstorming 时产生的草案。

candidate 建议包含 candidate_id、origin、thesis、experience、mode、unit_order、roles、claims、counterevidence、unknowns、status。`origin` 可使用 user、director、brainstorming、legacy_auto 等值。mode 为 contrast、payoff、behavior_change 或 perspective；必要时可用自定义值并解释。

claims 每条至少含 text、evidence_refs、status。status 为 supported、interpretation 或 pending；有证据并不自动等于某种心理动机得到证明。counterevidence 记录可能改变主线的上下文；尚未查找时写 pending，不留空后声称不存在。

candidate.status 为 provisional、ready_for_plan 或 rejected。ready_for_plan 表示 Narrative Direction / legacy rough plan 对应的核心素材已经完成 Directed Deep Structure、语境和反证已经检查，不表示粗剪通过。补充 estimated_duration_ms、scope_changes、reorder_reason 和 selected 字段方便执行。

## Execute 前的时长预算

`timeline.duration_budget` 用帧而不是浮点秒做对账，至少含 `sum_event_frames`、`sum_transition_overlap_frames`、`computed_output_frames`、`target_max_frames`、`status`、`adjustment_note`。计算规则：`computed_output_frames = Σ event frames − Σ transition overlap frames`。黑场卡、freeze / hold 等真正增加播放时间的内容必须成为 event 后再计入；覆盖在既有画面上的 text track 不单独加时。若文字阅读时间放不进当前视觉窗口，先修改 event / card / hold 或内容长度，再重新对账。

有明确总时长上限时，ready_for_render 前必须 `computed_output_frames ≤ target_max_frames`；超出时先按既定压缩规则裁决并在 `adjustment_note` 记录调整，不能一边执行一边让预算漂移。无明确上限也要完成对账，可用 `status=checked_no_limit`。

## 剪辑时间轴

### 时间轴量化与 ready_for_render 机械门槛

`timeline.json` 的输入坐标空间是 `assembly`，但 source event 的 assembly 边界不得由每一段独立四舍五入得到。先按 source duration / speed 计算精确帧时长，再对**累计边界**统一量化；card 使用明确整数帧时长。相邻 transition overlap 再从这套累计量化结果映射到 output 坐标。静态校验与编译器必须调用同一套计算规则，因此 text / audio 轨也按最终 output 总帧数检查，不能只拿未扣 overlap 的 assembly 末帧做上界。

当 `timeline.status=ready_for_render` 时，除了时间轴本身合法，还必须满足：Broad Structure + Content Map 完成、Directed Deep / Detail Structure 完成、`narrative_direction_status=confirmed`、`execution_plan_status=confirmed`、两份 Direct 文档存在且非空、`render_authorized=true`。每个被选中的 source event 必须显式给出 `deep_observation_refs`，引用本次实际采用的 `observation_id`；这些 observation 必须与 event 的 `source_id` 一致、其 source-time 区间合并后完整覆盖本次实际采用的 source range，且 `evidence_status` 只能是 `supported / partial`。同一 unit 中未被本次 event 引用的 pending / contradicted observation 继续保留为证据记录，但不阻断本次执行。这些检查不替代原片真伪核验，只阻止“阶段没完成或采用证据映射不清却进入 Execute”。

`source.time_mapping` 是精确时间定位的一部分，不只是输入摘要。任何 source 的 `version` 或 `time_mapping` 改变，所有依赖该 source 的 unit / clean-video / audio / final cache key 都必须变化；旧精确切点缓存不得继续标记为可复用。


timeline 顶层包括 schema_version、project_id、candidate_id、status、coordinate_space、fps_num、fps_den、width、height、events、audio_tracks、text_tracks。status 为 draft 或 ready_for_render。未确定输出规格时保持 draft，未知数字为 null。`timeline.json` 1.4 使用 `coordinate_space=assembly` 保存未扣除叠化的编排计划；实际成片坐标由 `render-manifest.json` 1.4 提供。无叠化时两者可能重合，仍应在出片前完成编译，避免下游混用。

主视频 events 按 out_in_frame 排序，左闭右开，从零开始无缺口、无重叠。每条包含 event_id、kind、out_in_frame、out_out_frame、function。kind=source 时还需 source_id、unit_id、source_in_ms、source_out_ms、speed；进入 `ready_for_render` 时还必须有非空 `deep_observation_refs`，以及明确的 `edit_boundary_ref`。默认切点必须落在该 boundary 的 safe-in / safe-out windows 并覆盖 must-keep ranges；只有显式 `boundary_override=true`、原 reason/review refs 和 v1.0.3 具体 `overrides` 全部有效才允许故意越界。默认 speed=1。kind=card 时记录 card_text 或 card_asset，不借用伪造的 source_id。

每段源素材的精确播放时长先进入同一条累计时间轴，再统一量化到目标 fps；输入 `assembly` 边界必须与这套累计量化结果一致，不能把每段各自四舍五入后的帧长直接相加。单段量化误差可以存在，但只能由累计边界分配，不能逐段累积。精剪仍需按真实解码结果核对。源可变帧率不影响输出采用确定帧率，但必须记录源到输出的映射。

audio_tracks 每条含 track_id、kind、source_id 或 asset_ref、source_in_ms、source_out_ms、out_in_frame、out_out_frame、gain_db、fade_in_ms、fade_out_ms、sync_event_id、reason，并补 `narrative_role` 与 `treatment_reason`。kind 区分 original、music、voiceover、ambience；`narrative_role` 可用 `dialogue_information`、`ambience_continuity`、`emotional_music`、`rhythm_cue`、`intentional_silence`、`other`。先说明声音在叙事中承担什么，再决定 preserve / isolate / attenuate / replace / remove，不能把“信息”窄化成对白。明确是否保留原声；异步 J/L-cut 要说明语义与同步范围，不能把音轨默认等同主视频切点。未知增益和淡化写 null，核听后确定。编译输入优先使用 anchor_event_id、local_in_frame、local_out_frame，编译器据实际段起点生成 out_in_frame/out_out_frame；对确实跨段的绝对定位须显式 coordinate_space=output，并在结构变动后重核。

text_tracks 每条含 text_id、kind、text、out_in_frame、out_out_frame、position、font、font_size_px、color、motion、evidence_refs。kind 区分原声字幕、解释、场景提示。解释不得伪装原话。像素规格未定时使用相对坐标并标记待定。

文字轨也使用 anchor_event_id/local_in_frame/local_out_frame 编译。补充 stable_hold_frames、fade_in_frames、fade_out_frames、glyph_height_px、font_unit、font_size_value、anchor_reference，记录阅读时间和字号校准。fade_in+stable_hold+fade_out 不得超过显示范围；章节卡延长会修改事件长度，不能只修改文字轨。原音不许含音乐等要求写入 project.audio_policy，音频修复必须遵守。

转场使用 transitions 中独立记录；timeline 中各段保持未扣叠化的顺序区间。transition 新增 effect=hard_cut/xfade 与 overlap_frames；硬切为0，叠化为正整数。编译后各段在 render-manifest 中允许按明确的 overlap_frames 相邻重叠，并生成每个接点的成片开始、结束帧。须核查源边界和 protected_ranges；不能把两个片段的完整长度相加后又偷偷扣除叠化时间。双时间轴、量化方法及所有下游坐标更新规则见“渲染与工程检查”。

transition 必填 from_event、to_event、relation、reason、omitted_context、audio_method、time_cue、risk、review_status。relation 使用重组规则规定的五个值。review_status 为 pending 或 reviewed；有几个接点就检查几个，不能只抽查一个代表全部。

render-manifest 顶层记录 coordinate_space=output、fps_num/fps_den、total_frames、duration_seconds、events、joins、audio_tracks、text_tracks、cache_keys、warnings、input_digest。event 同时保留源取段与最终输出帧号；joins 包含 start_frame/end_frame，硬切两者相同。封面从成片选取时引用此坐标；从源片选取时仍记录 source_id 与源时间，不混称同一坐标。

cache_keys 分开标识视频单元、无字合成、音频混音和文字成片层。`cache_reusable_by_layer` 必须按各层真实依赖判断：视频 source 的版本 / time_mapping 未知只影响依赖它的视频层；音频 source 的版本 / time_mapping 或外部 `asset_version` 未知时，`mix_audio` 与 `final` 不得标为可复用，但已知版本且不依赖该音频的视频单元 / clean-video 仍可保持可复用。章节卡的 `card_text` 及其文字渲染参数属于 final 文字合成依赖：仅修改卡片文案、字号、字体、颜色、位置、动效等时必须改变 final cache key，但不应无故使 clean-video 或 audio cache 失效。顶层 `cache_reusable` 为向后兼容的 final 聚合标志。render-audit 记录 file_sha256 与 manifest_sha256，以确认审查的是同一个版本。expected_quiet_ranges 使用成片 start_frame/end_frame 与 reason，供人工解释有意静默；未提供理由不能自动豁免。

人可读执行稿表头统一为：成片时间及帧号｜原素材及时间码｜画面与动作｜原声及音轨｜屏幕文字｜字号位置｜接续与注意事项。另附素材取舍表、完整文字清单、封面选帧和 EVA。

## v1.0.3—v1.0.5 执行绑定补充

Project 1.6、timeline / render-manifest 1.4 增加采用证据版本、Direct 2 机器授权、许可取段与独立原声连续性。详见 [执行完整性契约](execution-integrity.md)，该补充是 ready_for_render 的必需条件；原六套 Structure 表和两次 Direct 的职责保持。旧项目可继续做 Structure / draft，但进入正式执行须补真实绑定与确认，不能将旧 evidence 自动盖成当前版本。

v1.0.4 要求每个 source event 显式列出 adopted_utterance_refs，每条 source_id 音轨独立列出 review_refs。实际取段内已知对白和明确采用的对白均先验证来源、版本与完整音频核查；continuity_type 不能关闭 preserve_dialogue。源音轨全范围（含 J/L-cut 扩展）须由当前有效 audio reviews 的区间并集覆盖，并纳入采用证据指纹。已确认的不保留对白政策须附 event.dialogue_policy_reason；具体删句 / 截尾仍使用有效创作例外。完整规则和未实现边界见执行完整性契约。

v1.0.5 逐 source_id 音轨推导已知对白，视频关联不决定检查资格。卡片、未关联和异源仅音频均核对整句当前证据、核听、保留政策与可听覆盖；音轨独有 utterance 及其 review 进入 evidence_digest。独立轨可选 adopted_utterance_refs；不保留政策的具体原因写 track.dialogue_policy_reason，截句例外写 track.overrides，target_id 为 track_id。视频原声仍沿用 event 级同步与例外。没有新增正式 CSV 列、创意阶段或 schema 版本；完整适用关系见执行完整性契约第3节。

## 静态校验

随附脚本检查 sources、frames、transcript、reviews、units、timeline 的核心 ID、源范围、保护区间、帧时长，以及 transitions 的相邻引用。ready_for_render 还检查核查记录的存在及音视频区间覆盖。它不会证明核查记录所写事实真实、说话人正确、剧情因果成立、实际音画流畅或字幕准确。JSON 合法也不等于数据契约所有语义要求得到满足。

运行 `python3 scripts/validate_project.py 项目目录`；缺失后续阶段文件列为 skipped，不得把输出 status=pass 解释为项目已完成。进入 ready_for_render 前仍须按检查与交接规范人工或模型复核全部相关字段。
