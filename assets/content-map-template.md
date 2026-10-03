# Content Map

> Broad Structure 的正式交付之一。目标是把长素材变成可浏览、可检索、可回查的内容面，不提前替 Director 决定最终主题。

## 1. 素材与覆盖

- Source：
- 已完成 visual_sample：
- 已完成 transcript / subtitle：
- 已完成连续 AV review：
- 低可信 / 未覆盖区域：

## 2. 结构化观察入口

- `frames.jsonl`：机器可追溯的逐抽样帧证据；
- `frame-observations.csv`：供人工 / Director / 其他 Skill 阅读的逐抽样帧基础观察表；
- `action-node-candidates.csv`：动作 / 视线 / 站位 / 物件变化候选及默认 4fps 局部窗口；
- `structure-questions.csv`：会影响理解的问题、回答、证据与未验证项；
- 重要 Content Map 条目应能下钻到 `scene_id`，再继续下钻到 frame / utterance / review。

## 3. Source-order Overview

按原片顺序列出主要 `scene_id`、事件和状态变化。详细内容可引用 `overview.md`。

## 4. 人物 / 关系地图

| 人物 / 关系 | 可确认状态 | 变化节点 | scene_refs | unknowns |
|---|---|---|---|---|

## 5. 事件与行为索引

| 主题 / 行为 | 发生位置 | 可见 / 可听事实 | scene_refs | 值得回查的原因 |
|---|---|---|---|---|

## 6. 对白索引

| 关键词 / 语义 | 原声位置 | 简要内容 | audio_verified | evidence_refs |
|---|---|---|---|---|

## 7. 无声互动 / 动作 / 物件 / 空间线索

| 类型 | 位置 | 可见事实 | motif / change tags | action_candidate_refs | scene_refs | unknowns |
|---|---|---|---|---|---|---|

## 8. 可能存在的前后呼应或对照

> 这里只写“值得进一步回查”的导航性关系，不写成已经成立的编导结论。

-

## 9. Coverage Gaps / Unknowns / Open Questions

- unresolved question refs：
- 未验证项：
- coverage gaps：

## 10. 给 Direct 的使用提示

- 哪些区域内容丰富、适合 brainstorming：
- 哪些关联目前只有抽样证据：
- 哪些区域如果被选入 rough plan，需要第二轮 Directed Deep Structure：

## 进入 Detail / Directed Deep Structure 时继续生成

- `detail-intervals.csv`：核心精查区间卡；进入原因、前情、当前背景、后续、目标问题、主题关联；
- `deep-observations.csv`：核心区间完整高密度内容档案；
- `speaker-adjudications.csv`：说话人 / 对象不清时的帧级口型 / 原声 / 字幕 / ASR 裁决；无歧义时保留表头。

以上文件是 Structure 基础层，不得被脚本、Content Map 摘要或 edit plan 替代。
