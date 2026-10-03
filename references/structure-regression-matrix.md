# Structure Capability Regression Matrix

本表用于对照早期 Board / Detail Structure 的完整执行要求与当前 schema。发布前必须逐项保持，不得以“简化”“更吸引人”“已有总结”为理由删除。

| 旧版明确要求 | 当前正式产物 / 字段 | 强制控制 |
|---|---|---|
| Board / Broad 全片概览，不能把抽样当连续观看 | `frames.jsonl` + `coverage.json` + `frame-observations.csv` | Broad complete 时逐抽样帧表必须与 frames 一一对应；coverage 区分 sample / transcript / av_review |
| 帧号 / 帧名 / 时间 / 帧尾 ms | `frame_id` / `frame_name` / `timestamp_ms` / `frame_end_ms` | validator 要求 frame_end_ms > timestamp_ms |
| 画面事实 | `visual_facts` | 必填；不能用解释替代 |
| 人物动作 / 状态 | `visible_action_state` | 必填；相邻抽样之间未观察过程不能补写 |
| 情绪 / 表情 / 视线 | `observed_emotional_cues` / `emotional_interpretation` / `expression_gaze` | 观察线索与解释分列 |
| 意象 / 选题标记 | `motif_tags` | 必填；只是导航标签，不自动等于象征意义 |
| 硬字幕 | `visible_text` / Deep 的 `hard_subtitle_notes` | 必填或显式 none |
| 原声要点 | `original_audio_keypoint` / Deep 的 `original_audio_keypoints` + `audio_verification_status` | 未核听必须写 not_verified / not_reviewed；字幕不得冒充原声 |
| 与前帧变化 | `change_from_previous` | 必填；第一帧可 not_applicable |
| 主题判定 | `topic_judgment` | 必填；必须落到该帧 / 节点的具体叙事功能，不能只写抽象标签 |
| confidence / 证据类型 | `confidence` + `confidence_basis` | 两者同时必填 |
| 动作节点候选 | `action-node-candidates.csv` | Broad complete 时文件必须存在 |
| 4fps window | `window_start_ms` / `window_end_ms` / `sampling_fps` | 默认 4fps；偏离必须 `sampling_exception_reason` |
| 0.1–0.5s 颗粒裁决 | action candidate 的高密度窗口 + continuous review | workflow 明确只对切点 / 口型 / 关系转折节点加密 |
| 最小有效单元候选 | `min_effective_unit_*` | action candidate 显式记录，Deep 另有 `min_effective_unit_candidate` |
| 问题回答 | `structure-questions.csv` | question / answer / status / evidence / confidence / unverified / next_check |
| 未验证项 | `unknowns` / `unverified_items` / coverage | 不得被总结吞掉 |
| Detail 区间信息 | `detail-intervals.csv` | Deep complete 时至少一行，前情 / 当前背景 / 后续 / 目标问题必填 |
| 完整 Detail 内容档案 | `deep-observations.csv` | Deep complete 时至少一行；画面、动作链、背景、内容、原声、before/after 等必填 |
| 说话人帧级裁决 | `speaker-adjudications.csv` | Deep complete 时文件必须存在；有歧义则逐条裁决，只有字幕 / 画面不得假装 resolved |
| protected ranges / 最小保留意义 | `units.jsonl.protected_ranges` | Execute / ready_for_render 继续由 validator 检查 |
| 可剪边界 / 连续性 | `edit-boundaries.csv` | Detail 产物；Direct 2 / Execute 必须引用 safe windows / must-keep ranges |
| 否定性事实举证 | negative evidence rule | 稀疏 / 4fps 密集抽样只能给 not_observed / unknown；negative fact 必须限定 scope，并按事实类型使用连续视频 / 连续原声或可直接排除该事实的可靠反证 |
| 字幕 / 原声 / ASR 冲突 | transcript + `speaker-adjudications.csv` | 按事实类型裁决；方言 / 强口音 ASR 默认 locator_only |
| 素材物理可用边界 | `sources.json.usable_ranges/downstream_constraints` | Broad complete 时必须显式记录并传入 Content Map / handoff |
| 时间标签稳定性 | source_id + source ms/range → assembly/output frame | 同 frame/source time 必须一致；代理和输出坐标不得覆盖 source time |
| 长任务恢复 | incremental artifacts + `coverage.json` | 中断后按缺口续跑，不能重扫已完成且版本一致区间 |
| 时长预算 | `timeline.duration_budget` | ready 前按整数帧守恒；覆盖文字不重复加时 |
| 声音叙事作用 | `audio_tracks.narrative_role/treatment_reason` | 先判断功能再做 preserve/remove 等处理 |
| 反馈失效范围 | feedback → invalidation matrix | 文字 / 声音 / 结构 / 创意分别局部重算或回退 |
| Broad 正式文字化交付 | `frame-observations.csv` + action-node + Q&A + scene/segment observations + overview | Content Map / 情绪大意只能建立在这些结构表单之上，不能替代 |
| 第一次 Director | `narrative-direction.md` | 明确 thesis / narrative spine / candidate regions / verification questions；不提前冒充最终 execution plan |
| 第二次 Director | `execution-plan.md` | Detail evidence 完成后再确认最终取舍、顺序、声音 / 文字 / 时长 / 执行边界；Execute 不跳过 |
| 最终执行与 QA | timeline / render-manifest / render audit / junction checks / EVA / handoff | 原 Execute 主线不变 |

## 发布判定

只有当上表所有“当前正式产物 / 字段”仍存在，且 validator 的正向与反向测试通过，才允许声明 Structure 能力未回归。
