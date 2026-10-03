# Execution Package · Editorial Execution Plan

> 第二次 Direct 的输出之一。输入是 Detail 的 evidence package、真实关键帧和独立 handoff；与 execution-reference.md、素材 / 约束和原机器授权一起构成完整 Execution Package。Execute 只落实确认后的包。

## 最终主线

- thesis / narrative spine：
- 与第一次 Narrative Direction 的变化（如有）：
- 变化依据：

## 最终素材取舍

### Segment 1
- selected verified unit(s)：
- adopted utterance IDs / adopted_utterance_refs：
- selected Deep observation(s) / observation_id：
- adopted source range(s)：
- selected edit boundary / boundary_id：
- chosen in / out：
- safe in / out windows：
- must-keep range(s)：
- boundary override：no / yes
- boundary override reason（仅 yes 时）：
- boundary override review refs（仅 yes 时）：
- narrative function：
- 必须保留的 context / protected ranges：
- 原声 / BGM / ambience 策略：
- 每条源音轨完整取段及 audio review_refs（含 J/L-cut 扩展）：
- 独立声音的完整 utterance、成片放置、track 级截句例外 / 政策原因（如有）：
- 文字意图（如有）：
- 预计时长：
- transition / time cue：

### Segment 2
- selected verified unit(s)：
- adopted utterance IDs / adopted_utterance_refs：
- selected Deep observation(s) / observation_id：
- adopted source range(s)：
- selected edit boundary / boundary_id：
- chosen in / out：
- safe in / out windows：
- must-keep range(s)：
- boundary override：no / yes
- boundary override reason（仅 yes 时）：
- boundary override review refs（仅 yes 时）：
- narrative function：
- 必须保留的 context / protected ranges：
- 原声 / BGM / ambience 策略：
- 每条源音轨完整取段及 audio review_refs（含 J/L-cut 扩展）：
- 独立声音的完整 utterance、成片放置、track 级截句例外 / 政策原因（如有）：
- 文字意图（如有）：
- 预计时长：
- transition / time cue：

> 按需要继续增加。

## 逐段执行坐标与画面处理

| event ID / 顺序 | unit / source ID | source in/out ms | speed / crop / scale / 画面位置 | assembly 预计帧 / event anchor | 本段文字 / 声音 / 转场引用 |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## 逐条文字事件

| text ID / 用途 | 逐字全文 / 明确断行 | anchor event ID | local in/out frames | style ID（reference） | 进入 / 退出动效与帧数 | 实际阅读停留 / 保护的重点 |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

## 音轨与接点

| track ID / narrative role | source / asset ID | source in/out ms | event anchor / local frames 或显式 output 坐标 | gain dB / speed / fade ms | review refs / 同步 / 完整对白保护 |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

| 前后 event ID | cut / fade / card 等 | overlap 或独立 card 帧数 | 接续理由 / 保护范围 |
|---|---|---|---|
|  |  |  |  |

## 时长与节奏分配

- 总时长目标：
- 各段预算：
- 必须保留的完整动作 / 对白：

## 执行边界

- 可替换素材：
- 可调整顺序 / 时长：
- Execute 不得改变：

## Evidence check

- pending / contradicted 节点：
- counterevidence 已处理：
- 可进入 Execute：yes / no

## 同包制作参考与 QA

- execution_reference_ref：execution-reference.md
- execution_reference_asset_refs：实际采用的一两个风格样本文件；未使用图片时写 [] 并说明。
- 具体文字 / 画面 / 声音 / 转场规则及资产入口：见同包 reference。
- Reference Application Rules：样本提炼为全片规则，不要求每个字幕 / 镜头单独配对。
- QA：原内容 / 技术 / 听看项 + ReferenceCompliance，未实看保持 not_tested。
- exceptions 与下游处理：

## 机器可读执行授权（v1.0.6）

- execution_authorization_ref：execution-authorization.json
- authorization_id / version：
- confirmed_by：
- selected_events / sequence：
- allowed_units / allowed_boundaries：
- allowed_adjustments（逐 event）：
- event_specs / audio_specs / text_specs / transitions：
- source_bindings / evidence_digest / Direct 文档指纹：
- execution_reference_digest / execution_reference_asset_digests：
- preserve_dialogue / 删句例外 / dialogue_policy_reason（明确改变政策时）：

先用 prepare_execution_authorization.py 生成 draft，再根据本轮已确认决定核对并记录；草稿不能自动升为 confirmed。发生实际证据变化须回查，发生方案变化须按已有用户授权重新裁决，不能仅重算指纹掩盖变化。详见 references/execution-integrity.md。
