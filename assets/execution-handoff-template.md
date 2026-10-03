# Detail Structure → Director 2 Handoff

> E 阶段交付。接收方无需安装原 Skill，即可凭本文件与随附证据形成 Execution Package。本文件不替代 Detail 表，也不提前生成最终剪辑方案。模板空白须填入实际信息；未知项明确标注并带异常原因。

## 当前状态与文件清单

- 项目 / 产物版本：
- 当前已完成范围 / coverage 缺口：
- 实际随附文件与可读取位置（包括图片）：
- 尚未包含的资源与取得方式：
- exceptions 文件及影响 / 下游处理：

## 已确认叙事背景

- Narrative Direction 文件与确认来源：
- 核心主题 / 内容目标：
- 情绪路径 / 人物关系（事实、解读分列）：
- 必须保护的原话、画面、动作与表达重点：
- 已确认禁改项：

## 所选素材与证据

| segment / unit ID | source ID / 版本 / time_mapping | 源区间 ms | 叙事用途及状态 | evidence refs / reviews | context / protected ranges | edit boundary / safe windows | 缺口 / 反证 |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |

原音轨完整核听范围、问答 / 动作的最短完整范围及切点风险：

## 原片关键帧

- keyframe-references.json：
- 真实图片文件与 source timestamp：
- 每张图对应的素材节点 / narrative role：
- 提取失败或定位不确定项（status / reason / impact / downstream_handling）：

## 下游任务：生成完整 Execution Package

Director 2 基于以上已核实素材和 Narrative Direction 决定最终呈现；保留两次 Direct 的职责，不重做已确认主线，不把未核实项当成事实。素材不足只补对应缺口；主线冲突说明证据并返回 Direct 1。

请一次交付以下内容，已明确的规则填具体参数，不将必要判断留到 Execute：

1. **Editorial Execution Plan / execution-plan.md**：最终素材取舍、顺序、逐段 source in/out、速度 / 画面处理、保护范围、时长预算、逐条文字全文与出现 / 消失锚点、原声音轨及接点处理。
2. **Visual / Text Reference / execution-reference.md**：字体及可用资源、字号与单位、字重 / 颜色、位置 / 对齐、换行 / 行数、描边 / 背景、阅读停留、动效；明确输出分辨率、原片裁切 / 缩放和文字与画面的关系。
3. **Audio Specification**：每条原声 / 环境音 / BGM / 旁白的政策、源取段、成片放置、增益、速度、淡化、完整对白保护；没有配乐需求时不默认添加。
4. **Transition Specification**：每个接点采用什么及帧数；黑场 / card / hold 若增时，要计入事件与总长。
5. **Reference Application Rules**：一两个代表性风格样本锁定整体视觉语言，再将规则一致应用到全片；不要求每个镜头或字幕单独映射 reference。原片关键帧是素材依据，不能单独代替文字设计规格。没有出图能力时声明缺口并给出可执行参数。
6. **Asset / Constraints**：可读素材、证据、关键帧、字体和参考资源；允许调整、禁改项、status / reason / impact / downstream_handling。封面等仅在本任务要求时提供，其余记 not_applicable。
7. **QA Criteria**：内容、保护范围、时间、文字可读性、音轨 / 接点与 Reference Compliance；静态检查和真实播放分开，未实看写 not_tested。
8. **原有机器授权**：已有项目继续使用 execution-authorization.json，保存采用范围、顺序、允许调整与证据 / 决策指纹；草稿不自动升为 confirmed。reference 文档 / 实际样本改变后，旧确认失效，须按已有授权裁决并更新。

时间继续以 source_id + source ms 定位，文字 / 音轨放置优先使用 event anchor + local frames；正式成片坐标按现有时间轴编译对账。异常可以随包继续推进可做部分，但不能豁免证据、完整对白、Edit Boundary、源许可或正式渲染条件。

## Execute 接手入口

接收 Source Clips + Detail Structure + execution-plan + execution-reference + Constraints 组成的完整包。按已确认方案和允许调整制作；不重新选择核心主题、取舍或风格。资源 / 参数仍有缺口时先明确处理，不擅自补造确认结果。
