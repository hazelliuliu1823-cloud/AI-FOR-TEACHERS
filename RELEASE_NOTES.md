# v1.0.7 — 常用提问示例 / Prompt Examples

2026-10-03

本次更新集中在双语使用说明，帮助使用者按当前任务提出请求，并明确每一阶段应拿到什么。

## 四个常用提问示例

- 还没有选题：先做 Broad Structure，交付结构化观察表、全片概览、Content Map 和覆盖记录。
- Broad 已完成：提出候选创作方向，供人讨论并确认主线。
- 主线已确认：定位需要做 Detail 的区间，交付精查任务单。
- 区间已选好：完成 Detail，交付证据、剪辑边界、真实关键帧与可独立阅读的 handoff。

中英 README 的示例均位于“快速开始”之后。原有首屏、核心价值、流程示意、折叠方法和内容效果分析示例保留。

## 版本与兼容

版本统一为 v1.0.7，安装说明、CHANGELOG 和校验清单同步更新。本次为文档与发布整理，工程脚本、测试、模板、契约、示例、agent 配置及历史 QA 保持原字节。已有项目资料和已确认方案继续复用。

## 实际验证

- Python 3.12.14：153 项回归全部通过。
- 合成示例：静态校验、时间轴编译、渲染授权检查全部通过。
- 文档链接、包内文件校验和与压缩包完整性检查通过。

本次验证不包含真实长视频分析或成片播放；合成示例检查工程链路。

安装与更新见 [INSTALL.md](INSTALL.md)，历史验证记录见 [docs/qa](docs/qa/README.md)。

## English

This documentation release includes four matching Chinese and English prompt examples and their expected deliverables: Broad Structure, creative-direction proposals, targeted Detail intervals, and Detail evidence with a self-contained handoff.

The existing introduction, workflow illustration, core values, folded method, and content-performance example are retained. Engineering scripts, tests, templates, contracts, examples, agent metadata, and historical QA are unchanged.

All 153 regression tests passed under Python 3.12.14. The synthetic example passed validation, timeline compilation, and render-authorization checks. Documentation links, package checksums, and archive integrity were checked. Real-video analysis and playback were not re-tested.

---

# v1.0.6 — Structure Exceptions & Execution Package

本版以 v1.0.5 为底稿，只落实已确认的七项修改：固定字段下明确异常并继续可做部分；Detail 固定交付真实关键帧；Detail 形成独立 handoff 并携带下游完整输出要求；Direct 2 输出完整 Execution Package；少量 reference 锁定全片规则；Execute 接收完整包；原 QA 增加 Reference Compliance。

新增可复用契约与四份模板见 [执行包规范](references/execution-package.md)。通常一两个风格样本即可，不要求每个镜头或字幕对应 reference。关键帧缺失要声明原因 / 影响 / 下游处理，不能用生成图冒充原片，也不能把异常变成渲染豁免。

原有流程、两次 Direct、正式 CSV 表头、证据与时间标签、Edit Boundary、对白保护、授权、渲染算法及分层缓存保留。仅为完整包补充文件 / reference 指纹检查，使制作规则改变时旧确认失效；未声明新 package policy 的旧项目保持原机械行为。机器不证明参考图质量或文档完备性，最终风格按 Reference Compliance 实际对照观看。

安装 / 迁移见 [INSTALL.md](INSTALL.md)，本轮范围与实际验证见 [v1.0.6-QA.md](docs/qa/v1.0.6-QA.md)。

2026年10月2日封版修补（版本仍为 v1.0.6）：核对关键帧与 unit / 已有帧记录的来源和时间一致性；实际关键帧图片纳入输入指纹，图片被覆盖后旧渲染入口须重新编译；unavailable 强制匹配同步异常声明。新增 15 项回归，全部 153 项通过。原工程流程和实现保持不变。

2026年10月2日公开文档整理（版本仍为 v1.0.6）：完整中英 README 保留低成本复用、丰富结构、人工 Direct 与可靠 Execute 的定位；补齐文件树和本地安装命令、英文 description 与素材使用权说明，作者署名统一为 hazelliuliu1823-cloud。历史 QA 归档至 [docs/qa](docs/qa/README.md)，其原始验证记录保留；安装包校验和重新生成。

---

# v1.0.5 — Independent Source Audio Dialogue

长视频先形成可检索、可回查的结构化工作层。后续选题、改稿和多版本剪辑优先复用这层数据，只对命中区域重新进行高密度音画核实，减少重复处理整段多模态素材的开销。人保留两次创意决定，系统根据确认方案完成工程执行。

本版在 v1.0.4 上集中修补 F4：独立源音轨采用的对白没有全面进入整句检查与确认摘要。

- **逐源音轨检查**：卡片上的原声、未列入视频 audio_source_refs 的额外音轨、另一素材仅采用声音，均从实际取段推导已知 utterance。先核对来源、当前版本、audio_verified 和整句核听，再检查保留政策与实际可听覆盖。
- **确认摘要补齐依赖**：音轨独有 utterance 及其专属 review 进入 evidence_digest。确认后改动这些记录会使原确认失效；重新编译也必须检查当前证据资格。
- **合法独立声音继续执行**：完整且已核实的异步对白不强制绑定视频口型；按同源、同 speed 与一致的成片映射，可在多轨 / 卡片间连续保留整句。
- **例外归属明确**：视频原声沿用 event 级同步、保护与例外；独立截句使用 track 级 audio_required_range，明确不保留政策使用 track.dialogue_policy_reason。具体创作决定仍来自已有 Direct 2，不增加创意阶段。

此前 F1—F3 的修补与音轨完整取段核听要求保留。Broad / Detail 分工、六套 Structure 正式表、两次 Direct、Edit Boundary、时间标签、累计量化、分层缓存和 render audit 保留。没有预设成本降幅；抽帧、ASR、定向回看和 GPU 渲染仍需计算资源。

安装 / 迁移见 [INSTALL.md](INSTALL.md)，本轮实际验证见 [v1.0.5-QA.md](docs/qa/v1.0.5-QA.md)。已有 v1.0.4 项目保留全部结构化资料，完成独立对白对账后，按已有创作授权更新 Direct 2 记录并重新编译。

Broad 覆盖、采样与说话人语义证明、Deep 保护转移以及非对白声音的整体收束继续保留原职责边界。合成验证不证明真实长视频理解质量或最终观感；最终听看仍独立记录，外部渲染适配器须接入入口检查。
