# Changelog

## v1.0.5 — Independent Source Audio Dialogue · 2026-10-01

- Fixed F4: derive and validate utterances independently for every adopted source audio track, including card-only speech, unassociated extra tracks and audio-only sources. Full current utterance evidence and audio verification are required before preservation decisions.
- Included audio-only utterances and their dedicated reviews in adopted_evidence_digest. Changes invalidate unchanged confirmation; recompilation must still reject stale evidence.
- Preserved source-event synchronization and existing event-level exceptions. Independent speech permits asynchronous output placement, compatible continuation across cards and valid track-level audio_required_range exceptions; explicit policy changes require a track-level reason.
- Added independent speech regression cases and v1.0.4 migration guidance. Retained all formal CSV templates, original core scripts, two Direct stages, layered caches, render audit and previously declared capability boundaries.

## v1.0.4 — Dialogue Selection & Full Audio Review Coverage · 2026-10-01

- Fixed F1: validate explicitly adopted utterances and known same-source speech intersecting actual video / associated audio selections before checking self-declared protection ranges. Missing, stale or unverified adopted speech cannot be filtered out by an underdeclared audio boundary.
- Fixed F2: dialogue preservation is triggered by adopted speech / speech metadata independently of continuity_type. Scene or action labels cannot allow muted, replaced or misaligned preserved dialogue. Explicit policy changes require a confirmed event-level reason.
- Fixed F3: every source audio track requires independent current audio review_refs covering its complete source range, including J/L-cut extensions. Track-only reviews enter the adopted evidence digest; creative exceptions do not grant review coverage.
- Added explicit adopted_utterance_refs to ready source events, migration instructions, positive and negative regression cases, and a refreshed synthetic-ready example.
- Preserved the six formal Structure CSV templates, two Direct stages, timeline math, layered caches and render audit. Broad coverage, sampling / semantic proof, Deep protection transfer and non-dialogue audio closure remain explicitly bounded.

## v1.0.3 — Structured Representation & Execution Integrity · 2026-10-01

- Added current-source / time-mapping bindings for adopted observations, boundaries, reviews, unit verification, utterances, video events and source audio tracks; stale evidence blocks ready execution.
- Added a machine-readable Direct 2 execution authorization, with selected events / units / boundaries, exact sequence, adopted evidence snapshot, track / transition recipes and explicit permitted adjustments. Decision or evidence changes invalidate its fingerprints.
- Extended existing Edit Boundary protection to source-audio coverage, duration, source/output synchronization and fades; explicit supported J/L-cut and creative tail-cut exceptions remain possible.
- Enforced source_scope, usable_ranges, optional allowed_scope and typed source-range constraints against actual video and audio adoption.
- Required precise override targets, violated rules, current successful review coverage and confirmed creative decisions; placeholder and unrelated overlap/boundary reviews no longer release execution.
- Default compilation now rejects non-ready or unauthorized drafts; --planning carries render_allowed=false. Added a current-input / manifest-integrity guard for renderer adapters.
- Added output fps to mix_audio cache identity while retaining the existing layered cache design, cumulative timeline math and render-audit script.
- Reworked the README first screen around lower repeated multimodal-understanding cost, reusable rich structure and human creative direction. Preserved complete technical content and added installation, migration, release, executable regression and synthetic-ready files.
- Preserved the six formal Structure tables, two Direct stages and original render QA. This release does not claim automatic proof of all coverage, sampling or semantic judgments.

## v1.0.2 — Compact multimodal structure for lower-context reuse

- Added a hard **Edit Boundary / Continuity Layer** between Detailed Structure and Direct 2: `edit-boundaries.csv` records real audio tails, action/reaction settle points, preferred in/out, safe windows, must-keep ranges, handles and cut risk.
- `ready_for_render` now requires every selected source event to reference an explicit edit boundary; default cuts must land inside the safe windows and preserve must-keep ranges. Deliberate boundary violations require an explicit override reason and review references.
- Added boundary-aware validation / compilation so subtitle or ASR endpoints cannot silently become cut points, while preserving all existing Structure, two-Direct, evidence, timeline, cache and render-QA behavior.
- Fixed final-layer cache identity for generated card text: changing `card_text` or card text-render parameters now invalidates only the final composited cache, while clean-video and audio caches remain reusable when otherwise safe.
- Fixed validator preflight when Directed Deep / Detail is incomplete: Deep indexes are initialized safely and evidence-linkage checks are skipped until the stage is complete, so ready-state violations return structured validation/compiler errors instead of crashing.
- Refined Execute evidence linkage from coarse `unit_id` aggregation to explicit event-level `deep_observation_refs`; adopted observations are now checked for source identity, source-time coverage, and current evidence status, while unrelated observations in the same unit do not block execution.
- Added dependency-aware cache reuse reporting: unknown audio source / asset versions disable `mix_audio` and `final` reuse without unnecessarily disabling known video-layer caches; `cache_reusable` remains the backward-compatible final aggregate flag.
- Synced README responsibility wording so evidence verification stays in Directed Deep / Detail Structure, and added `timeline_math.py` to the repository tree.

- Clarified the canonical workflow without changing the confirmed Structure / Execute capabilities: Broad Structure now explicitly exits as a **formal textual Structured Observation Layer** (observation tables + scene/segment roll-ups) before Content Map; Direct is explicitly two-pass — first Narrative Direction, then post-Detail Editorial Execution Plan.
- Added `assets/narrative-direction-template.md` and `assets/execution-plan-template.md`; legacy `editorial-plan-template.md` remains for compatibility. Execute is not allowed to skip the second Director decision and invent the final storytelling plan from evidence alone.

- Tightened negative-evidence rules: sparse or 4fps sampling can establish `not_observed`, not interval-level absence; negative facts require bounded scope plus fact-type-appropriate continuous video/audio review or direct counterevidence.
- Added fact-type-specific evidence conflict handling; dialect / strong-accent ASR defaults to locator-only until verified.
- Hardened `ready_for_render` gates: completed Broad/Content Map/Detail stages, both Direct documents confirmed, selected Deep evidence not pending/contradicted, and explicit render authorization are now mechanically checked.
- Validator and compiler now share cumulative timeline quantization and post-overlap output coordinates; text/audio tracks are checked against final output length, not assembly length.
- `source.time_mapping` is included in precise cache identity, so mapping changes invalidate unit / clean-video / audio / final cache keys.
- Added a canonical time-tag policy from source evidence through assembly/output coordinates, with source/time consistency checks.
- Added source usable-boundary propagation into Direct, long-task incremental checkpoint / resume rules, a frame-based duration budget ledger, feedback-to-invalidation mapping, and explicit audio narrative roles.

- Restored the full Board/Broad → Detail Structure information floor: frame-end timing, original-audio keypoints, topic judgment, confidence + evidence basis, detail interval cards, minimum-effective-unit candidates, and frame-level speaker/addressee adjudication.
- Structure summaries, Content Map, editorial copy, or edit plans are explicitly forbidden from replacing these base observation artifacts.

- Restored the Structure minimum-information floor as a hard requirement: one structured row per analyzed sampled frame, with visible facts, action/state, motif tags, hard text, change-from-previous, content description and unknowns preserved before summaries.
- Added `assets/action-node-candidate-template.csv` for action / gaze / position / object-change candidates with default 4fps local inspection windows.
- Added `assets/structure-question-template.csv` for question → answer → evidence → unresolved-item tracking.
- Expanded Deep Observation with key visual changes, emotional cues / interpretation, motif tags, question refs and unverified items.
- Strengthened validation and QA so Content Map / final copy cannot substitute for the foundational Structure layer.
- Rebalanced the README first screen so the project presents **Structure + Execute** as the two core capabilities, with Human Direct as the creative interface between them.
- Repackaged the README around the core value of Structure: turning expensive multimodal source material into compact, searchable and reusable structured data.
- Added a clear before / after explanation and a concrete content-performance example that joins time-coded user behavior with structured visual / narrative observations.
- Added `examples/content-performance-analysis.md` to show how the same structured layer can support analytics and research beyond editing.
- 强化 Structure 的核心定位：把视频 / 图像 / 对白 / 场景上下文等高成本多模态输入压成 **compact structured representation**，供后续人和模型优先通过表格 / 文本低上下文复用。
- 明确 Direct 可在独立研究 / 编导环境中结合 Structure 输出、行业 / 主题资料、平台语境、参考案例与大量人工判断形成并确认 editorial / script plan。
- 明确计算成本策略：Broad Structure 低密度全局压缩；只有已确认脚本命中的区域才进入 Directed Deep Structure 高密度多模态回查。
- `project.json` 增加可选的 `research_context_refs` 与 `human_decision_refs`，用于保留外部研究和人工决策来源。
- 更新 README、Skill、workflow、data contracts、agent metadata 与时间轴校验 / 编译实现；保持 renderer-neutral 架构、正式 Structure / Direct 表单与 render-audit 脚本不变。

## v1.0.1 — Structure observation layer restored

- Restored a formal human-readable **Frame Observation Index** for Broad Structure instead of leaving downstream users with only contact sheets / raw frame evidence.
- Added `assets/frame-observation-template.csv`.
- Added a formal **Deep Observation Index** for Directed Deep Structure.
- Added `assets/deep-observation-template.csv`.
- Expanded Directed Deep Structure to capture complete visual description, content description, setting context, narrative context, before / after state, dialogue / audio verification, interpretations, unknowns and counterevidence before cut decisions.
- Updated README, workflow, data contracts, worked example, handoff rules and agent metadata accordingly.
- No change to the core Direct boundary, timeline compiler, renderer-neutral architecture or render-audit scripts.

## v1.0.0 — Initial public release

- Broad Structure → Human Direct → Directed Deep Structure → Execute.
- Content Map / Brief / Editorial Plan templates.
- Evidence and timeline contracts.
- Render-manifest compiler and render audit tooling.
- MIT License.
