# Core Capability Regression Checklist

每次更新 README、定位、schema 或脚本后，都用此表确认已验证能力没有被包装层覆盖或删除。

## 主线不可变

`Broad Structure → Structured Observation Layer → Content Map / emotional cues → Direct 1 Narrative Direction → Directed Deep / Detail Structure → Direct 2 Editorial Execution Plan → Execute → Timeline / Render / QA`

除非版本明确声明 breaking change，否则不得删除、跳过或把任一步默认为由另一层替代。

## 全流程时间标签稳定性

- Structure 的 canonical tag 始终是 `source_id + source_ms / range`；display timecode、抽样号、ASR 时间和代理时间不是主键。
- source 明确 `time_mapping`；代理 / 分轨 / 字幕均能映射回源时间。
- frame observation 与 `frames.jsonl` 同一 frame_id 的 source/time 一致。
- Deep observation 位于对应 Detail interval 内；speaker adjudication 与 utterance 源时间有重叠。
- Execute 使用 assembly / output frame，但保留 source time；track 用 event anchor + local frame 或明确 output coordinate。
- 源版本 / time mapping 变化时精确下游缓存与坐标失效。

## Broad Structure 最低信息地板

- `frames.jsonl` 保留可追溯 sampled-frame 证据。
- `frame-observations.csv` 每个已分析 sampled frame 一行，并与 `frames.jsonl` 的 `frame_id` 集合一致。
- 基础字段显式存在：帧号 / 时间 / 帧尾 ms、画面事实、动作 / 状态、意象标签、硬字幕 / 可见文字、原声要点及核听状态、与前帧变化、内容描述、topic_judgment、confidence / confidence_basis、unknowns。
- 表情 / 视线、空间、背景、情绪线索保留，不把情绪解释写成事实。
- `action-node-candidates.csv` 保留动作 / 视线 / 站位 / 物件变化候选；默认 4fps 局部窗口，偏离需记录原因；同时保留候选起止、最小有效单元候选、口型 / 说话线索与关系转折。
- `structure-questions.csv` 保留问题、回答、状态、证据、未验证项和下一步核查。
- Broad 的正式出口首先是上述文字化结构表单与 scene / segment observations；overview / Content Map / 情绪大意 / 最终文案不得替代以上基础记录。
- negative fact 不由稀疏抽样推出；方言 / 强口音 ASR 未核听只作 locator。
- 每个 source 有 usable ranges / downstream constraints；影响后续时长设计的物理边界已传给 Direct。
- 长任务支持增量落盘、coverage accounting 与断点续跑，不因静默中断重扫已完成区间。

## Directed Deep Structure

- 核心区间重新回原素材，不只复用第一轮摘要。
- `detail-intervals.csv` 先保留进入精查原因、前情、当前背景、后续、目标问题和主题关联。
- `deep-observations.csv` 保留完整画面、构图、动作链、关键变化、情绪线索 / 谨慎解释、空间、场景背景、叙事背景、意象、内容描述、硬字幕、原声及核听状态、字幕 / ASR 冲突、before / after、topic_judgment、confidence / confidence_basis、说话人裁决引用、问题引用、反证和未验证项。
- `speaker-adjudications.csv` 保留说话人 / 对象的帧级裁决；无歧义时也保留表头。
- 先理解完整，再形成 unit / context_ranges / protected_ranges。
- Detail 必须继续形成正式 `edit-boundaries.csv`：真实音频尾部、动作 / 反应收束、preferred in/out、safe windows、must-keep ranges、handles、cut risk；字幕 / ASR 结束不能替代可剪边界。
- 证据冲突时先判断层级：主线级冲突返回 Direct 1；Detail 证据成立后必须交回 Direct 2 形成最终 execution plan，不由 Execute 偷改已确认主线。

## 两次 Direct

- Direct 1 明确输出 Narrative Direction：核心命题 / Narrative Spine / candidate regions / verification questions / constraints；不要求精确切点。
- Directed Deep / Detail Structure 只围绕 Direct 1 已确认主线补证据；计划目标不能倒推 facts。
- Direct 2 在 Detail evidence package 完成后输出 Editorial Execution Plan：selected verified units、顺序、段落功能、保护范围、声音 / 文字 / 时长 / 转场意图、执行边界。
- Execute 不得从 Detailed Structure 直接跳过 Direct 2 自行生成最终讲法。

## Execute

- verified units、context_ranges、protected_ranges 保留。
- duration budget ledger 保留；event frames − transition overlaps 与预计 output frames 一致。
- audio track 保留 narrative_role / treatment_reason。
- 反馈分类 → invalidation / 回退范围规则保留。
- assembly timeline 与 output timeline 双坐标保留。
- transitions、audio_tracks、text_tracks、render-manifest 保留。
- render audit、近静音扫描、全接点图、动态听看与 handoff 保留。

## 发布前机械检查

1. JSON / CSV / YAML 可解析；Python 脚本可编译。
2. README / SKILL / workflow / data-contracts 对同一能力表述一致。
3. `scripts/validate_project.py` 对 Structure 最低信息地板与 Execute 静态引用进行检查。
4. 对照上一正式 Release 做文件级 diff；未列入版本目标的核心脚本 / 规则如有变化，必须单独解释。
5. 不得以“更简洁”“更吸引人”为理由删除已确认的数据字段或执行步骤。

## 实现层机械回归（v1.0.2）

- 4fps 只作为动作候选加密起点；不能单独证明某动作 / 台词 / 物件在整个区间“没有发生”。负面事实必须有明确 scope，并按视觉 / 原声事实类型使用连续 review 或直接反证。
- Broad 标记 complete 时，`frames.jsonl`、`frame-observations.csv`、`scenes.jsonl`、`coverage.json`、`overview.md`、Content Map 必须真实存在且基础表非空；动作候选 / Q&A 可以是带表头空表。
- `ready_for_render` 必须要求两次 Direct 均 `confirmed`、文档存在、Detail 完成、render_authorized=true；每个选中的 source event 必须显式列出本次实际采用的 `deep_observation_refs` 与 `edit_boundary_ref`，引用 observation 的 source / source-time 覆盖正确，且 evidence_status 为 supported / partial；默认切点落在 safe windows 并覆盖 must-keep ranges；同 unit 未采用的 pending / contradicted observation 不得误伤本次执行。
- validator / compiler 共用累计量化与 overlap 后 output 坐标；文字 / 音频轨不得以 assembly 总长冒充 output 上界。
- 改变 `source.time_mapping` 必须改变相关 unit / clean / audio / final cache key；缓存可复用性按实际依赖分层判断，未知音频版本只关闭 mix_audio / final，不应误关已知版本的 clean-video。

## v1.0.3 可运行回归

运行 `python3 -m unittest discover -s tests -v`，检查证据版本、Direct 2 采用范围 / 顺序、源限制、独立对白、合法 J/L-cut / 截尾、无关或占位 override、规划清单与渲染入口。源内容改变不得只重写 source_signature；需要实际重新核实。Broad 覆盖统计、4fps 实际观察证明与说话人语义裁决仍按原规则人工 / 模型完成，本版本不声称全部已经机械实现。

## v1.0.4 对白与音轨核听回归

同一命令包含 tests/test_dialogue_continuity.py：漏报整句 / 第二句、漏保对白的旧版本和假核查、scene / action 下的静音、缺采用 ID 或 speech 元数据、音轨 review 缺失 / 过期 / 错误模态 / 1ms 缺口，均须被静态校验、正式编译及入口阻断。充分核听的 J/L-cut、有效删句例外、明确改变政策的静音及取段外未采用对白须保留合法对照；音轨独有 review 改动须使旧证据确认失效。

## v1.0.5 独立源音轨对白回归

tests/test_independent_audio_dialogue.py 覆盖卡片对白、同源额外音轨、异源仅音频，以及确认后独立 utterance / 专属 review 改动。截句、静音、过期 / 未核实证据、错误标签和无效例外须被静态校验、正式编译及入口阻断；完整声音、异步放置、跨卡片连续接句、有效 track 删句例外和已确认政策变化须保持正向对照。另一成片位置的完整播放不能掩盖本次截句；源音轨全取段核听继续独立要求。纯音乐 / 环境声整体收束沿用人工职责边界。

## v1.0.6 已确认增量

- 原 schema / CSV 表头未变；字段无法取得时 status / reason / impact / downstream_handling 随包输出，可做工作继续，未核实项不冒充事实或渲染完成。
- E 固定提供真实关键帧清单与自包含 handoff；handoff 直接含下游 Execution Package 要求，不依赖同一 Skill 环境。
- D2 同时交付计划与制作 reference，文字 / 声音 / 转场 / 资产 / 约束 / QA 参数足够执行；少量样本锁定全片规则，不逐镜头或字幕映射。
- Execute 接收完整包，Reference Compliance 进入原 QA；声明 reference 改动后旧确认 / 渲染入口失效，旧项目与原对白 / 授权 / 时间轴 / 缓存回归继续通过。
