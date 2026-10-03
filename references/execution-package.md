# Structure 异常、Detail 交接与 Execution Package

本契约补充现有 B / E / D2 / F / G，不新增阶段。原有 CSV 表头、证据、时间标签、Edit Boundary、对白保护、机器授权和渲染检查继续适用。

## 1. 输出契约与异常继续

First / Broad Structure 与 Detail Structure 的必需文件、字段和类型保持锁定。字段无法取得时，保留字段：CSV 文本使用原契约允许的 `unknown` / `not_applicable`，JSON 的未知数值使用 `null`；枚举保持原有取值。`none` 只表示已核实没有相应内容，不能表示工具失败。不得把所有字段改成 status 对象，也不得为填满字段补造人物、台词、时间、观察或核验。

在 `structure-exceptions.jsonl` 中另行记录无法满足的字段或产物；有异常时必须交付此文件，无异常时可以不创建。每行包含：

| 字段 | 固定要求 |
|---|---|
| exception_id | 稳定、唯一 ID |
| stage | B / C / E；对应原阶段，不新增阶段 |
| artifact | 受影响的项目文件名 |
| record_id | 既有行 ID；整文件异常用 `null` |
| field | 受影响字段；整文件异常用 `*` |
| status | `unavailable` / `uncertain` / `partial` |
| reason | 实际无法取得或无法确认的原因 |
| impact | `low` / `medium` / `high` |
| downstream_handling | 可继续什么、不能据此确认什么、需要怎样补查 |

模板见 `assets/structure-exception-template.json`；仅在实际发生异常后填写，不把模板示例当成观察。

输出异常后继续索引、整理、草案和交接，不因一个非核心字段或关键帧失败停住整个流程。无法观察的记录不得伪装成“已分析帧”；缺失区间仍进入 coverage。若没有实际观察行，保留规定表头，并在异常和 coverage 中报告缺口；不能用虚构行补数量。数值、ID 或源时间无法可靠获得时保留未知状态，不宣称该记录符合精确执行契约。

阶段未实际完成时保留 partial / pending；异常声明不等于将阶段改成 complete，也不豁免静态错误。核心素材不可用、文件损坏或时间轴无法解析时，暂停依赖它的动作并交付已完成部分；其他可独立完成的工作继续。采用证据不足或主线冲突仍按原规则回 D1 / E；进入正式渲染仍须通过全部既有门槛。

## 2. Detail 的真实关键帧

E 阶段固定交付 `keyframe-references.json` 及可取得的原片图片。通常选 1–3 张足以展示重要素材节点的真实画面，不追求配额，不给每个镜头抽一张。它们是事实层的视觉依据；字幕、动效与视觉规则由 D2 决定。

文件为数组，每条保留以下字段：`frame_id`、`source_id`、`timestamp_ms`、`image_ref`、`source_segment`（unit ID）、`narrative_role`、`notes`、`status`、`reason`、`impact`、`downstream_handling`。`timestamp_ms` 是 canonical source time，图片保留原片内容；不得生成或修饰一幅画面充当原片证据。相同关键帧继续使用既有 frame_id，另附对应 source 版本 / time_mapping 与 evidence refs 供回查。

`status` 使用 `available` / `unavailable` / `uncertain` / `partial`。available 必须对应实际可打开的图片和可靠源时间。图片提取失败时 `image_ref=null`，保留已知定位，写原因、影响与下游处理，并同步异常声明；源时间也不可靠时 `timestamp_ms=null`。若没有可定位的候选帧，交付空数组并声明产物级异常，不编造 K1 或图片路径。模板见 `assets/keyframe-reference-template.json`，模板不是已提取图片。

## 3. Detail → 外部 Director 2 的交接

Detail 不替 Director 生成最终方案，但交付必须在没有安装本 Skill 的环境中也能独立阅读。使用 `assets/execution-handoff-template.md` 生成 `execution-handoff.md`，与证据表、关键帧清单、实际图片及必要源素材入口一起交付；这个包是 E 阶段产物，不是额外步骤。

交接至少包含：

1. Narrative Context：已确认主题、内容目标、情绪路径、人物关系、必须保护的原话 / 画面与禁改项，引用既有 Narrative Direction，不新写成事实。
2. Selected Clip Structure：segment / unit ID、source ID / 版本 / 时间映射、源区间、叙事用途、采用证据、context / protected ranges、edit boundary 与未验证项。
3. Keyframe References：清单、可访问图片、源时间、素材节点与用途；无法提供图片的异常随包携带。
4. Next Stage Requirements：**直接写入**下节要求的 Execution Package 组成、完成标准和边界。不能只写“按 Skill 继续”，也不能只给接收者无法读取的安装目录链接。
5. 文件清单与资源可达性：附带什么、还缺什么、源素材如何访问；确认传出的图片 / 证据文件实际包含在交接中。此前日志只作来源，不改写为下一模型的亲眼观察。

外部 Director 优先复用此包，按缺口局部回查；不因换模型重扫全片，不重做已确认的 D1。

## 4. Director 2 的 Execution Package

D2 保留 Editorial Execution Plan，交付升级为 **Execution Package**。最小组成是 `execution-plan.md` + `execution-reference.md` + 采用素材 / Detail 证据与关键帧入口 + 原有 `execution-authorization.json`。允许引用项目中的既有文件，无需复制一套素材库。

| 组成 | 执行前写清的内容 |
|---|---|
| Editorial Execution Plan | 最终取舍、顺序、逐段源 in/out、速度 / 画面处理、保护范围、总长与各段预算；实际文字全文、逐条出现 / 消失锚点与阅读停留；音轨取段 / 放置、转场及允许调整 |
| Visual Treatment Reference | 少量样本及由此确认的全片视觉规则；原片保留 / 裁切 / 缩放、画面占比、文字与人物 / 原字幕关系 |
| Text Treatment Rules | 各类文字的字体 / 可用字体文件或确定替代、尺寸及单位、字重、颜色、描边 / 背景、位置 / 对齐、行数 / 换行、动效与阅读时间；绑定输出分辨率 |
| Audio Treatment Rules | 原声 / 环境音 / BGM / 旁白的采用政策；每条音轨取段、源与成片锚点、增益、速度、淡化及完整对白保护；不默认加 BGM |
| Transition Rules | 具体接点使用 cut / fade / black card 等什么处理及帧数；真正增时的卡片 / hold 计入事件和预算 |
| Reference Application Rules | 用一两个代表性风格参考锁定文字层级、位置、画面关系、情绪强调和视觉密度；按相同规则扩展到全片 |
| Asset / Constraint Mapping | 素材、字体、关键帧、风格参考及必要资源的文件入口；禁改项、可调整项、缺失项及降级处理 |
| QA Criteria | 内容 / 保护范围、实际文字与阅读时间、音轨 / 接点及 Reference Compliance 的判据；未经播放的项不得填通过 |

使用 `assets/execution-plan-template.md` 和 `assets/execution-reference-template.md`。参考文档是执行规格，不只是“简洁 / 有情绪 / 字体大一点”等意图；逐条文字与素材时间放在计划，重复使用的样式放在 reference，二者相互引用。没有某层时写 not_applicable 及原因，不为满足标题额外制作。

保留 event anchor + local frame 的坐标表达；预计成片坐标只能标为计划值，正式 output frame 由现有编译器给出并对账。不能把 source time 当成成片时间。

风格参考与原片关键帧区分：原片关键帧证明“画面有什么”；D2 可以用它制作一两个带文字处理的参考样本，或使用已确认参考。若没有生成图片的能力，明确说明并给出可执行的文字样式参数，不能声称已有视觉预览。此缺口可随包继续，不自动把整个计划判成不可用；依赖项须在制作前落实。

**不要求每个字幕、镜头或主要视觉动作逐项映射一个 reference；reference 不是 storyboard / shot list。** 样本用于提炼 Design Rules 并保持全片一致。Execute 在这些规则和已有 allowed_adjustments 内实施，不能重新决定核心表达、素材取舍或风格。

## 5. 与原工程入口的衔接

新项目的 project 设置 `execution_package_policy="plan_and_reference"`，并保存 `structure_exceptions_ref`、`keyframe_references_ref`、`execution_handoff_ref`、`execution_reference_ref` 和 `execution_reference_asset_refs`（实际采用的风格样本文件，未使用图片则为 []）。沿用原 project / timeline / authorization schema 版本，不改正式 CSV。

新项目在 Detail complete 时须有关键帧清单和独立 handoff；关键帧 unavailable 按上节声明仍可继续。ready_for_render 时还须有非空 reference 文档及已列出的实际参考资源。机器仅检查结构 / 文件 / 指纹，文档是否足够执行、参考图是否实现设计意图仍须按本契约审阅。

准备 draft 时追加 `execution_reference_digest` 和 `execution_reference_asset_digests`。完整执行包中的 reference 文档 / 风格样本改变，会使既有 Direct 2 确认和旧渲染入口失效；按已有授权裁决变化后更新记录。新机制不自动确认草稿，也不改对白保护、源许可、时间轴算法或缓存边界。

旧项目未声明新 package policy 时保持原机械行为；按 v1.0.6 继续制作时补齐上述交接 / reference 并设置 policy，不重写旧观察表。未得到的事实通过异常声明携带，不能靠重新计算指纹变成有效证据。

## 6. Reference Compliance

在现有 G / EVA 中增加 `ReferenceCompliance` 检查：全片是否遵守已确认的文字层级、位置、字号 / 颜色、画面关系、情绪强调、动效 / 转场及禁止事项。对照一两个样本和全片规则，不逐镜头核配对数量。声音另按既有 Audio 检查和本次音轨规范复核。

qa 每项仍用原字段 name、status、method、evidence、finding、action。静态规则检查与实际导出观看分开；没有真实导出或没有实际对照查看时写 not_tested，参考图提取成功和脚本成功都不等于全片风格通过。
