# Example：把用户行为数据接到视频内容结构上

这个例子展示 Structure 为什么不只服务于剪辑。

## 场景

假设已经发布了数百条短视频，并能拿到每条视频的时间轴级行为数据，例如：

- 每秒留存；
- 跳出；
- 重播；
- 点赞 / 评论 / 收藏发生时间；
- 其他平台可提供的时间点行为。

如果视频仍然只是一个 MP4 文件，那么这些行为数据只能告诉你“哪一秒发生了变化”，却不能直接告诉你“用户当时看见了什么”。

## Structure 之后

Broad Structure 先把已分析的抽样帧、场景、对白和内容说明压成统一结构。例如：

| video_id | time | visible_people | visual_action | dialogue | setting | content_description | narrative_function |
|---|---:|---|---|---|---|---|---|
| V001 | 00:08 | A,B | A转身离开 | “那我走了” | 室内门口 | 争执后A结束交流并离场 | conflict / action change |
| V001 | 00:12 | B | B看向门口，无对白 | — | 室内门口 | A离开后B停留并看向门口 | reaction |
| V001 | 00:19 | B | 静态近景 | 长段解释 | 室内 | B解释前一事件原因 | exposition |

再把用户行为按 `video_id + time` 接进来：

| video_id | time | content_description | narrative_function | retention_delta | replay_delta |
|---|---:|---|---|---:|---:|
| V001 | 00:08 | 争执后A离场 | conflict / action change | +7% | +1% |
| V001 | 00:12 | B无对白反应 | reaction | +3% | +8% |
| V001 | 00:19 | 长段解释 | exposition | -11% | 0% |

## 现在可以分析什么

分析单元从“整条视频”进一步下降到“内容节点”：

- 对比所有 `reaction` 节点的平均留存与重播；
- 找出流失前 3 秒最常出现的内容类型；
- 比较同一种动作在不同人物、场景、视频中的表现；
- 从所有留存突然上升的时间点反查共同的画面、对白和叙事功能；
- 把效果好的内容节点重新检索出来，作为下一轮选题和剪辑参考。

## 为什么这比反复分析视频更有效

原视频仍然是最终证据，但不再是每一次分析都必须重新加载的工作界面。

Structure 生成的是一个可复用的中间表示：

**Multimodal source → compact structured representation → analytics / research / Direct / Execute**

大部分跨视频分析可以先在表格化数据上完成；只有真正需要确认的时间点，再回到原视频做高密度观察。

这样同一批素材的理解成本可以在更多任务之间复用，而不是每换一个问题就重新“看一遍视频”。
