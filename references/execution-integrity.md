# 执行完整性契约 · v1.0.6

目录：证据绑定、Direct 2 机器授权、声音连续性、源范围、创作例外、正式编译、迁移。

保留 Broad → Structured Observation Layer / Content Map → Direct 1 → Detail → Direct 2 → Execute → QA。这里只把现有证据与已确认决定接入实际执行，不新增创意阶段。

## 1. 证据绑定

实际审阅或观察时保存两个 SHA-256 指纹，算法见 `scripts/execution_integrity.py`：

- `source_signature`：canonical JSON 的 source_id、version、duration_ms；locator 移动不改变素材身份。
- `time_mapping_digest`：canonical JSON 的完整 source.time_mapping。

进入 ready_for_render 时，这两个字段必须存在于实际采用的 Deep observation、edit boundary、review、unit.verification、utterance、source event 和源音轨。Deep 与 boundary 的 CSV 只追加上述字段；原有列和职责保留。尚未采用的 pending / contradicted observations 不会因同属一个 unit 而阻断当前事件。

每个 source event 增加：

```json
{
  "event_id": "E001",
  "source_id": "SRC001",
  "source_signature": "<本次实际核实版本的指纹>",
  "time_mapping_digest": "<本次实际核实映射的指纹>",
  "deep_observation_refs": ["DO001"],
  "adopted_observation_refs": ["DO001"],
  "edit_boundary_ref": "EB001",
  "adopted_boundary_ref": "EB001",
  "evidence_status": "supported",
  "source_constraint_ref": "source:SRC001"
}
```

新旧引用字段须一致。观察区间覆盖实际取段；status 为 supported / partial。review 仅在 result 为 reviewed / pass / passed，reviewer 与 evidence_locator 具体非空、模态与区间覆盖适配且指纹一致时计入成功核查。

`python3 scripts/execution_integrity.py PROJECT` 只计算源、映射、约束、采用证据与授权记录指纹。它不观察视频、不签署确认，也不更新任何旧记录。源版本或映射变化后先重核采用证据；仅把旧行的指纹改成新值不构成重新核实。

## 2. Direct 2 机器授权

`execution-plan.md` 保留编导表达；v1.0.6 的完整执行包同时包含 `execution-reference.md` 与实际采用的少量风格样本。`execution-authorization.json` 保存同一已确认包的可检查范围。Project 增加 `execution_authorization_ref` 和 `execution_authorization_digest`。后者是完整授权对象 canonical JSON 的 SHA-256。

| 字段 | 作用 |
|---|---|
| authorization_id、version、project_id、project_version | 稳定确认记录与对应项目版本 |
| status=confirmed、confirmed_by | 当前用户 / Director 已确认决定的记录；draft 不允许正式编译 |
| execution_plan_digest、narrative_direction_digest | 两份 Direct 文件的原始字节 SHA-256；改动使旧确认失效 |
| execution_reference_digest、execution_reference_asset_digests | 已声明 reference 文档与实际样本的字节指纹；改动使旧确认失效，未声明的新字段不改变旧项目授权 |
| selected_events、sequence | 所有 event ID 的有序列表，包括 card；与 timeline 必须一致 |
| allowed_units、allowed_boundaries | 可采用的明确 unit / boundary ID 列表 |
| event_specs | 逐 event 已确认字段快照；assembly/output 坐标由编译推导，card 时长另存 card_duration_frames |
| allowed_adjustments | 逐 event 的列表：默认 []，可明确允许 trim_inside_safe_window / add_transition_handle |
| audio_specs、text_specs、transitions | 已确认的音轨、文字和接续；Execute 不得自行替换 |
| output、audio_policy | 已确认输出规格、声音要求 |
| source_bindings | 采用源的 source_signature、time_mapping_digest、source_constraint_digest |
| evidence_digest | 采用 observation / boundary / unit / utterance / review 的 canonical 快照指纹，含每条源音轨独有的 utterance 及其 review |

使用 `prepare_execution_authorization.py PROJECT` 从当前方案准备 draft。脚本不会确认，也不会刷新 evidence；已有同名 draft 不会被覆盖。人工 / Director 对照已确认方案核对取舍、顺序、处理和例外，在授权范围内补 authorization_id、confirmed_by、status 并保存正式文件；不要把 draft 自动升为 confirmed。随后计算授权指纹并写入 project。

`allowed_adjustments` 不允许变更 source、unit、boundary、采用证据、速度、叙事功能或其他字段。safe trim 只能缩短既定范围，add_transition_handle 可在已核实 safe windows 内扩展；两者均不能越过源许可或保护区间。原声 locked 轨可以随已允许的安全裁剪调整源端点和 local frame，其余处理仍须一致。文字 / 接续变化按既有授权重新裁决并更新对应确认记录。改变取段后须按累计量化更新 locked 音轨、文字显示范围和 duration_budget；编译器不会自动替方案改写这些依赖字段。

机器记录将用户已有授权具体化，不增加固定确认关卡。名字、状态和指纹可以检查一致性，不能证明填表者身份或自然语言意图真实；实际决定来自本轮用户 / Director 指令。

## 3. 声音连续性

对白约束由实际采用的 utterance、unit.audio_state.speech=true 或 dialogue / mixed boundary 触发，continuity_type 只说明主要连续性，不能关闭保留对白政策。每个 ready source event 明确写 `adopted_utterance_refs`；检查对象还包括同源 transcript 中与实际视频取段或任一采用源音轨相交的对白，不由待验证的 audio_start_ms—audio_tail_end_ms 筛掉。逐源音轨推导不依赖 audio_source_refs 或 sync_event_id，卡片声音、未关联音轨及异源仅音频同样检查。取段外且未明确采用的对白不强行加入成片。

每条应检查的 utterance 先核对引用、来源、当前版本、audio_verified=true 及覆盖整句的有效 audio review，再核对保护范围与可听音轨。缩小自报保护范围、漏列第二句、清空采用列表均不能跳过这些检查。

使用现有 CSV 的 `dialogue_required_range`，按 `start-end;start-end` 源毫秒格式覆盖 audio_start_ms 至 audio_tail_end_ms 及采用的完整 utterance。event 增加：

```json
{
  "adopted_utterance_refs": ["T001"],
  "audio_boundary": {"required_start_ms": 1300, "required_end_ms": 5800},
  "dialogue_required_range": "1300-5800",
  "sync_mode": "locked",
  "audio_source_refs": ["A001"]
}
```

每个采用的源音轨保留 source_signature、time_mapping_digest、source_constraint_ref，并确定 speed（默认 1）、gain_db、fade_in_ms、fade_out_ms、treatment，以及独立的 `review_refs`（reviews.jsonl 中的 review ID 数组，如 ["R001", "R002"]）。与视频同步时另明确 sync_event_id、sync_mode。成功的同源、当前版本 audio reviews 按半开区间并集合并，必须覆盖完整 source_in_ms—source_out_ms；相邻覆盖可合并，1ms 缺口也不放行。音轨采用的 utterance、其专属 review 及音轨全范围 review 同时进入 evidence_digest，改动后原确认失效，重新编译仍须检查当前证据资格。外部 asset_ref 音轨沿用原契约，本补丁只加强 source_id 音轨。

对白采用 kind=original、narrative_role=dialogue_information，treatment=preserve / isolate。保护某源对白时，不能用另一源或 music 冒充；另一源完整且核实的对白可作为独立音轨采用。muted 或 gain_db≤−80 会被当作实际静音阻断。无效处理或错位的轨道不计入保护范围的可听覆盖。具体可听性仍由最终核听判断。

源音频时长 / speed 与最终 output frame 时长的差最多一输出帧；音画映射在对应源时间处允许最多一帧量化误差。淡音区间不能覆盖保护对白；被采用轨的淡音后源区间并集须覆盖完整 required range。

- locked：源音轨位于对应 event 的 output 区间内，并保持源时间同步。
- J_cut：音轨开始早于对应视频 event，保持源时间映射；需要明确 audio_transition override。
- L_cut：音轨继续到对应视频 event 之后，同样需要 audio_transition override。

J/L-cut 可跨 card / 邻接 event，但不能跨出最终成片总范围。audio_transition 说明已审阅的接续决定，不能替代新增源音频区间的完整核听。创作删句或截尾必须针对被改变的整句 / 保护区间提供有效 audio_required_range override，分别检查声明范围与实际可听范围；普通 boundary override 不自动豁免音轨，也不能把未核听区间升级为已核实。unit.protected_ranges 的意义保护仍不可被该 override 自动取消。

独立源对白按以下适用关系处理，不需要新增视频事件或正式表：

| 音轨关系 | 保留及例外归属 | 同步要求 |
|---|---|---|
| 出现在同源 source event 的 audio_source_refs | 沿用该 event 的完整对白 / boundary 覆盖、原因和例外；逐轨仍检查 utterance 证据 | 保留既有 sync_event_id、locked / J_cut / L_cut 与源时间映射检查 |
| 卡片声音、未列入同源 event 的音轨、异源仅音频 | track 负责完整 utterance 的可听覆盖、政策原因及 audio_required_range 例外 | 按源取段、speed 与最终 output 位置对账，允许异步；anchor_event_id 只锚定位置，不证明口型同步 |

独立轨可选写 adopted_utterance_refs（唯一 ID 数组），明确采用取段外对白时也接受完整检查；实际取段内已知对白自动加入，漏列或 [] 不能免检。每句须由同源、同 speed 且源时间到成片时间映射一致（最多一帧量化差）的有效保留轨覆盖；可跨卡片接续同一句，不能拿另一成片位置的一次完整播放来掩盖本次截句。淡音后的源区间并集用于覆盖计算。独立截句例外放在 track.overrides，target_id 为 track_id，audio_required_range 的 target_range 覆盖受影响整句，核听与确认要求同第5节。已关联 event 的创作决定不要求再复制一份 track 例外。

若本轮明确改为 `audio_policy.preserve_dialogue=false`，对应 event 或独立对白 track 必须有具体 `dialogue_policy_reason` 并进入 Direct 2 快照；此时允许已确认的无对白处理。已采用对白的证据和源音轨完整核听仍须有效。没有对白时使用已核实的无语音元数据及适配 review，不凭改标签宣布不适用。

## 4. 实际源范围

Project.source_scope 是明确允许采用的 source ID 列表。每个 source 的 usable_ranges 必须覆盖最终视频和源音轨采用范围，按半开区间并集合并；存在 allowed_scope 时也须落在其并集内。context 回查不因此扩大成片范围。

可机器处理的 downstream_constraints 对象支持 `type=exclude_range` / `allowed_range`，使用 start_ms / end_ms 或 ranges 数组。未知 typed 规则拒绝正式执行；自由文字约束仍由用户 / Director 核对。

source_constraint_digest 覆盖 source_scope、usable_ranges、allowed_scope 和 downstream_constraints。确认后修改约束，使原 Direct 2 源绑定失效。

## 5. 具体创作例外

event / track / transition 的 `overrides` 必须是对象数组。字段如下：

```json
{
  "override_id": "OV001",
  "target_id": "E001",
  "type": "creative_exception",
  "target_range": {"source_id": "SRC001", "start_ms": 5600, "end_ms": 6200},
  "violated_rule": "safe_out_window",
  "evidence_ref": ["review:R001"],
  "reason": "尾部采用突然结束的处理",
  "creative_decision": "本轮 Direct 2 明确采用该截尾",
  "approved_by": "<对应 confirmed_by 的实际决策者>"
}
```

规则限 safe_in_window、safe_out_window、boundary_must_keep、audio_required_range、audio_transition、protected_overlap。target_id 对 event 为 event ID，对独立音轨为 track ID（audio_required_range），对 transition 为 `E001->E002`；target_range 必须覆盖实际受影响的源区间。evidence_ref 必须解析到同源、当前版本、成功且覆盖相应区间 / 模态的 review。approved_by 与 Direct 2 确认记录一致，override 内容须在其快照中。none / unknown / 空依据及无关 review 均不能放行。

普通越界仍保留原 boundary_override、boundary_override_reason、boundary_override_review_refs，新增具体 overrides 提供真正放行依据。叠化覆盖保护画面时，用 transition.overrides 的 protected_overlap，不能只填 overlap_protection_review 自由字符串。

## 6. 正式编译与入口检查

```sh
python3 scripts/validate_project.py PROJECT
python3 scripts/compile_render_manifest.py PROJECT
python3 scripts/check_render_authorization.py PROJECT PROJECT/render-manifest.json
```

正式清单包含 render_allowed=true、eligibility=validated_for_render、timeline_status、render_authorized、authorization digest、input_digest、manifest_digest。渲染适配器应在实际消费前调用最后一步，防止编译后 evidence / plan 改动或清单被改写。外部渲染器须接入此入口；不能声称已经控制绕过入口的任意第三方渲染器。

规划草稿用 `compile_render_manifest.py PROJECT --planning`，清单携带 render_allowed=false / eligibility=planning_only。规划编译不授权渲染。所有模式的 playback_verified 保持 false；原 render audit、全部接点检查与最终听看继续执行。

## 7. 迁移与本版范围

旧 Structure 文件和六套正式表保留；v1.0.5 不修改任何正式 CSV 模板。旧项目可在 draft / Structure 阶段继续记录；精确执行时补 source event 的 adopted_utterance_refs、每条源音轨的 review_refs、真实当前核听与对应 Direct 2 授权。v1.0.4 中仅由独立音轨采用的对白需要按本节对账，且采用摘要已增加这些依赖；按已有创作授权更新 Direct 2 记录后重新编译，不能只改指纹来掩盖旧证据或截句。

Broad coverage 的实际计算、逐帧行唯一性、4fps 真实执行证明、说话人证据语义及完整 time_mapping 类型规范仍是后续工作；本版不会把原有文字规约说成全部自动校验。执行脚本负责可机械判断的引用、版本、授权、范围和时间关系，无法替代连续音画观察及创作判断。

Deep 的 protected_ranges 仍须由 Direct 2 逐项转移或裁决到 unit / boundary，程序不自动把自由字段变成有效保护要求。音乐 / 环境声的整体收束仍需 Direct 2 和最终核听；本补丁不宣称所有声音类型都已有完整连续性保护。哈希与核查标签也不证明真实听看或审阅者身份。
