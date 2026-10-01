# 安装与更新 · v1.0.5

解压后得到 `long-video-remix/` 完整目录。SKILL.md、references、assets、scripts 和 agents 必须一起保留；只复制 SKILL.md 会丢失契约和检查能力。

## 安装

把完整 `long-video-remix` 文件夹放入目标工具支持的 Skill 目录；原位置已有同名版本时先备份，再替换完整文件夹。项目素材和工作数据放在独立项目目录，不放进安装目录。

这是 Skill 与配套脚本安装包。画面读取、ASR、实际渲染通过当前环境的模型、视频 MCP 或渲染器连接，按 references/mcp-adapter.md 发现并验证能力。

## 运行环境

- 静态校验、授权记录、编译与回归：Python 3.9+，只用标准库。
- 导出审计：FFmpeg / ffprobe；生成接点拼图时额外需要 Pillow。
- 模型、视频 MCP、渲染器的依赖按实际适配器配置，不在包内下载大模型或素材。

## 验证安装包

进入解压后的目录运行：

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate_project.py examples/synthetic-ready
python3 scripts/compile_render_manifest.py examples/synthetic-ready
python3 scripts/check_render_authorization.py examples/synthetic-ready examples/synthetic-ready/render-manifest.json
```

示例全部是合成记录，只验证数据链与工程入口；没有真实视频，不用它证明长视频理解或观看效果。

## 从 v1.0.4 更新

保留 Structure 文件与全部正式表单。程序现在逐条 source_id 音轨推导实际取段内已知对白，卡片对白、未关联音轨和另一素材仅采用声音均接受整句证据与保留政策检查，不要求为独立声音补造视频 event 或 Edit Boundary。

独立对白轨使用 kind=original、narrative_role=dialogue_information、treatment=preserve / isolate，并确定 gain、fades、speed 和成片位置。anchor_event_id 只决定放置位置；它不声明口型同步。需要同步的视频原声仍填写对应 source event 的 audio_source_refs 和 sync_event_id / sync_mode。

每条源音轨可选写 adopted_utterance_refs，写时须是唯一 ID 数组；实际取段内已知对白始终自动加入检查，[] 不会免检。保留政策下的独立删句 / 截尾，使用 track.overrides 的 audio_required_range，target_id 为 track_id，范围覆盖受影响整句且有当前有效整句核听。明确改为 preserve_dialogue=false 时，独立对白轨填写具体 dialogue_policy_reason；已关联视频对白沿用 event 级原因及例外，不要求重复填写。

独立音轨采用的 utterance 和专属 review 现在进入 evidence_digest。完成实际证据与已有创作决定对账后，用准备 draft 的既有流程更新 Direct 2 授权和 project 指纹，再重新校验、编译；不能直接把旧摘要当作当前确认。完整对白合法方案继续适用，详见 [执行完整性契约](references/execution-integrity.md)。

## 从 v1.0.3 更新

保留已有结构化数据和正式表单，只补执行记录：source event 增加 `adopted_utterance_refs`（明确采用的 utterance ID；没有时写 []），每条源音轨增加独立 `review_refs`。核听记录须覆盖音轨完整的 source_in_ms—source_out_ms，包括 J/L-cut 扩展部分，且来源、版本与音频模态有效。仅核听过视频取段，不能代替扩展音轨的核听。

程序还会从实际选用的视频及全部源音轨推导应保护的已知对白；缩小 dialogue_required_range 或清空采用列表不能让取段内对白消失。scene / action 等标签仍须遵守保留对白政策。若本轮已明确改变为不保留对白，更新 audio_policy，并在对应 event 或独立音轨写入具体 `dialogue_policy_reason`；保留政策下的删句 / 截尾使用具体的 audio_required_range 创作例外。

补齐真实核查与已确认决定后，再更新 Direct 2 机器授权和 project 中的授权指纹，重新校验、编译。不要只改指纹来替代核听。详见 [执行完整性契约](references/execution-integrity.md)。

## 从 v1.0.2 或更早版本更新

保留已有项目，不重做 Broad。采用 Deep / boundary / review / unit.verification / utterance 需要保存实际核实时的源版本与映射指纹；补 source event 和源音轨的绑定、源许可与声音映射。按 Direct 2 已确认方案准备 execution-authorization.json，并把其指纹记入 project。完整规则见 [执行完整性契约](references/execution-integrity.md)。

旧项目进入正式执行前须完成这些字段，并按上节补充对白采用与完整音轨核听记录；缺少时会被阻断。指纹工具不会替旧资料伪造重新审阅，也不会自动确认草稿。
