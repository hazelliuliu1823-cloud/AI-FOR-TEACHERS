# Execution Reference

> 与 execution-plan.md 一起构成 Direct 2 的 Execution Package。填写实际确定参数；任务未使用的层写 not_applicable 及原因。参考样本通常一两个，全片复用同一套规则。

## 版本、规格与确认

- 项目 / reference 版本：
- execution-plan.md / Narrative Direction：
- 输出 width × height / fps：
- reference 状态与已有确认来源：
- 原片关键帧清单 / 图片入口：
- 实际风格样本文件（project.execution_reference_asset_refs；没有图片写 [] 并说明）：

## 少量参考锁定的规则

| reference ID / 实际文件或已确认来源 | 锁定的文字层级、画面关系与强调方式 | 全片应用规则 | 未提供项与原因 |
|---|---|---|---|
|  |  |  |  |

无需每个镜头、字幕或视觉动作单独映射 reference。原片关键帧只提供画面依据；样本或具体参数才能定义文字和视觉处理。

## 画面规则

- 原片保留方式 / crop / scale / 位置（精确参数）：
- 人物、动作、硬字幕需避让的范围 / 安全边距：
- 色彩与效果处理：
- 情绪强化方式及允许使用的范围：
- 禁止的处理：

## 文字样式

| style ID / 文字用途 | 字体文件或可用字体名 / 确定替代 | 字号 / 单位 / 字重 | 颜色 / 描边 / 阴影 / 背景 | 位置 / 坐标基准 / 对齐 / 边距 | 行数 / 换行 / 字距 / 行距 | 进入 / 退出动效及 ms 或帧数 | 阅读停留规则 |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |

实际文字全文、断行及逐条出现 / 消失事件锚点放在 execution-plan.md，并引用 style ID。不要只交“字幕大一些”或“适当停留”。字重是否可用、字号采用 px / pt / 相对高度必须明确；参数绑定本版输出规格。

## 声音与转场

- 原声 / 环境音 / BGM / 旁白政策和禁止项：
- 每条音轨的源 / 取段 / 放置 / 增益 / 速度 / fade / review refs：见 execution-plan.md 的明确记录。
- 每个接点的类型 / overlap 或 card 帧数：见 execution-plan.md 的接点表。
- 重要停顿、动作 / 回应、对白尾部的保护规则：

## 素材与允许调整

| asset ID / 文件 | 用途 / 来源与版本 | available / unavailable / partial / uncertain | reason / impact / downstream_handling |
|---|---|---|---|
|  |  |  |  |

- 字体和参考图片在执行环境的实际入口：
- 可调整项（与原机器授权的 allowed_adjustments 一致）：
- 不得调整项：
- 封面规格 / 全文 / 源图 / 排版（仅本任务要求时）：

## QA 判据

- 全片文字层级、位置、字号 / 颜色、画面占比是否符合上述规则：
- 正常速度阅读时间、遮挡 / 裁切和手机检查：
- 情绪强调、动效 / 转场与 reference 是否一致：
- 原声、保护范围与音轨参数是否实现：
- 实际导出 / reference 对照尚未完成的项：

在原 qa.json checks 中登记 ReferenceCompliance；没有实际观看记 not_tested。具体参数变更同步计划、机器授权与受影响时间轴 / 缓存，不在 Execute 中另行定义风格。
