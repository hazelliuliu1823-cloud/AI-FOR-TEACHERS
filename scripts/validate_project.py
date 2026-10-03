#!/usr/bin/env python3
"""Validate core references and timing only; never certifies editorial truth."""
import csv
import json
import math
import sys
from pathlib import Path

from timeline_math import canonical_assembly_ranges, output_ranges_from_overlaps
from execution_integrity import validate_integrity


def validate(root):
    errors, warnings, checked, skipped = [], [], [], []

    def require(condition, message):
        if not condition:
            errors.append(message)
        return condition

    def integer(value):
        return type(value) is int

    def positive(value):
        return integer(value) and value > 0

    def load(name, default):
        path = root / name
        if not path.exists():
            skipped.append(name)
            return default
        checked.append(name)
        try:
            if name.endswith('.jsonl'):
                return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
            result = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(result, type(default)):
                raise ValueError('unexpected top-level type')
            return result
        except (ValueError, OSError) as exc:
            errors.append(f'{name}: {exc}')
            return default


    def load_csv(name):
        path = root / name
        if not path.exists():
            skipped.append(name)
            return [], []
        checked.append(name)
        try:
            with path.open('r', encoding='utf-8-sig', newline='') as fh:
                reader = csv.DictReader(fh)
                headers = reader.fieldnames or []
                rows = list(reader)
            return headers, rows
        except (OSError, csv.Error) as exc:
            errors.append(f'{name}: {exc}')
            return [], []

    def nonblank(value):
        return isinstance(value, str) and bool(value.strip())

    def csv_refs(value):
        if not isinstance(value, str):
            return []
        raw = value.strip()
        if raw.lower() in ('', 'none', 'unknown', 'not_applicable'):
            return []
        return [part.strip() for part in raw.split(';') if part.strip()]

    def csv_ms(value, label, allow_na=False):
        raw = (value or '').strip() if isinstance(value, str) else value
        if allow_na and isinstance(raw, str) and raw.lower() in ('none', 'unknown', 'not_applicable'):
            return None
        try:
            result = int(raw)
        except (TypeError, ValueError):
            require(False, f'{label}: must be integer milliseconds' + (' or not_applicable' if allow_na else ''))
            return None
        if result < 0:
            require(False, f'{label}: must be nonnegative milliseconds')
            return None
        return result

    def csv_ranges(value, label):
        raw = (value or '').strip() if isinstance(value, str) else ''
        if raw.lower() in ('', 'none', 'unknown', 'not_applicable'):
            return []
        result = []
        for token in [part.strip() for part in raw.split(';') if part.strip()]:
            pieces = token.split('-', 1)
            if len(pieces) != 2:
                require(False, f'{label}: range must use start-end;start-end source-ms syntax')
                continue
            try:
                a, b = int(pieces[0]), int(pieces[1])
            except ValueError:
                require(False, f'{label}: range endpoints must be integer milliseconds')
                continue
            if not 0 <= a < b:
                require(False, f'{label}: invalid range {token}')
                continue
            result.append((a, b))
        return result

    def index(rows, key):
        result = {}
        for row in rows:
            if not require(isinstance(row, dict), f'{key}: row must be object'):
                continue
            value = row.get(key)
            if not require(isinstance(value, str) and bool(value), f'missing {key}'):
                continue
            require(value not in result, f'duplicate {key}: {value}')
            result[value] = row
        return result

    project = load('project.json', {})
    structure_state = project.get('structure_state', {}) if isinstance(project, dict) else {}
    broad_complete = isinstance(structure_state, dict) and structure_state.get('broad_pass') in ('complete', 'completed', 'done')
    deep_complete = isinstance(structure_state, dict) and structure_state.get('directed_deep_pass') in ('complete', 'completed', 'done')

    if broad_complete or deep_complete:
        time_policy = project.get('time_policy', {}) if isinstance(project, dict) else {}
        require(isinstance(time_policy, dict) and time_policy.get('time_tag_stability') == 'strict',
                'completed Structure requires strict time_policy.time_tag_stability')
        require(time_policy.get('canonical_source_time_key') == 'source_id+source_ms',
                'completed Structure requires canonical source time key source_id+source_ms')
        require(time_policy.get('require_source_time_mapping') is True,
                'completed Structure requires source time mapping')
        structure_policy = project.get('structure_policy', {}) if isinstance(project, dict) else {}
        require(structure_policy.get('negative_claim_policy') == 'not_observed_is_not_absent',
                'completed Structure requires strict negative-claim policy')
        require(structure_policy.get('negative_claim_dense_sampling_is_sufficient') is False,
                'completed Structure requires dense sampling to be non-sufficient for interval-level absence claims')
        require(structure_policy.get('negative_claim_requires_bounded_scope') is True,
                'completed Structure requires bounded scope for negative claims')
        require(structure_policy.get('negative_claim_requires_fact_type_continuous_or_direct_evidence') is True,
                'completed Structure requires fact-type continuous/direct evidence for negative claims')
        require(structure_policy.get('evidence_conflict_policy') == 'resolve_by_fact_type_and_record_conflict',
                'completed Structure requires fact-type evidence conflict policy')
        require(structure_policy.get('dialect_asr_policy') == 'locator_only_until_verified',
                'completed Structure requires dialect ASR locator-only policy')
        require(structure_policy.get('long_task_checkpoint_policy') == 'incremental_output_resume_coverage',
                'completed Structure requires incremental checkpoint/resume policy')

    sources = index(load('sources.json', []), 'source_id')
    if not sources:
        warnings.append('No source records; this is not an executable media project.')
    for sid, source in sources.items():
        require(positive(source.get('duration_ms')), f'{sid}: duration_ms must be positive integer')
        if not source.get('version'):
            warnings.append(f'{sid}: source version unknown; caches that depend on this source are not reusable')

    def interval(sid, start, end, label):
        if not require(sid in sources, f'{label}: unknown source {sid}'):
            return False
        if not require(integer(start) and integer(end), f'{label}: times must be integer milliseconds'):
            return False
        duration = sources[sid].get('duration_ms')
        return require(positive(duration) and 0 <= start < end <= duration, f'{label}: invalid or out-of-source range')

    if broad_complete:
        for sid, source in sources.items():
            require(isinstance(source.get('time_mapping'), dict) and bool(source.get('time_mapping')),
                    f'{sid}: Broad Structure complete requires explicit time_mapping')
            usable = source.get('usable_ranges')
            if require(isinstance(usable, list) and bool(usable), f'{sid}: Broad Structure complete requires usable_ranges'):
                for i, item in enumerate(usable):
                    label = f'{sid}.usable_ranges[{i}]'
                    if require(isinstance(item, dict), f'{label}: must be object'):
                        interval(sid, item.get('start_ms'), item.get('end_ms'), label)
                        require(nonblank(item.get('reason')), f'{label}: reason must be explicit')
            require(isinstance(source.get('downstream_constraints'), list),
                    f'{sid}: Broad Structure complete requires downstream_constraints array')

    frames = index(load('frames.jsonl', []), 'frame_id')
    if broad_complete:
        require(bool(frames), 'Broad Structure complete requires non-empty frames.jsonl')
        require(structure_state.get('content_map') in ('complete', 'completed', 'done'),
                'Broad Structure complete requires structure_state.content_map=complete')
        scenes = index(load('scenes.jsonl', []), 'scene_id')
        require(bool(scenes), 'Broad Structure complete requires non-empty scenes.jsonl')
        coverage = load('coverage.json', [])
        require(isinstance(coverage, list) and bool(coverage), 'Broad Structure complete requires non-empty coverage.json')
        for i, row in enumerate(coverage):
            label = f'coverage.json[{i}]'
            if not require(isinstance(row, dict), f'{label}: must be object'):
                continue
            interval(row.get('source_id'), row.get('start_ms'), row.get('end_ms'), label)
            require(row.get('modality') in ('visual_sample', 'transcript', 'av_review'), f'{label}: invalid modality')
            require(row.get('status') in ('complete', 'partial', 'failed', 'pending', 'excluded'), f'{label}: invalid status')
            require(nonblank(row.get('method')), f'{label}: method must be explicit')
            require(nonblank(row.get('reason')), f'{label}: reason must be explicit')
        for filename, label in [('overview.md', 'overview.md'), (project.get('content_map_ref') or 'content-map.md', 'content map')]:
            path = root / filename
            require(path.exists() and bool(path.read_text(encoding='utf-8').strip()) if path.exists() else False,
                    f'Broad Structure complete requires non-empty {label}')

    for fid, row in frames.items():
        t = row.get('timestamp_ms')
        interval(row.get('source_id'), t, t + 1 if integer(t) else None, fid)

    if broad_complete:
        complete_values = ('complete', 'completed', 'done')
        for key in ('frame_observations', 'action_node_candidates', 'structure_questions', 'minimum_information_floor'):
            require(structure_state.get(key) in complete_values, f'Broad Structure complete requires structure_state.{key}=complete')
        frame_headers, frame_rows = load_csv('frame-observations.csv')
        required_frame_columns = {
            'source_id', 'timestamp_ms', 'frame_end_ms', 'frame_id', 'frame_name', 'characters',
            'visual_facts', 'visible_action_state', 'observed_emotional_cues', 'expression_gaze',
            'spatial_relationship', 'setting_background', 'key_objects', 'motif_tags', 'visible_text',
            'original_audio_keypoint', 'audio_verification_status', 'nearby_dialogue_refs', 'content_description',
            'change_from_previous', 'topic_judgment', 'confidence', 'confidence_basis', 'unknowns'
        }
        require(required_frame_columns.issubset(set(frame_headers)),
                'frame-observations.csv: missing required minimum-information columns')
        require(bool(frame_rows), 'Broad Structure complete requires non-empty frame-observations.csv')
        observed_ids = []
        for number, row in enumerate(frame_rows, start=2):
            fid = (row.get('frame_id') or '').strip()
            require(bool(fid), f'frame-observations.csv row {number}: missing frame_id')
            if fid:
                observed_ids.append(fid)
            for key in required_frame_columns - {'source_id', 'timestamp_ms', 'frame_id'}:
                require(nonblank(row.get(key)), f'frame-observations.csv row {number}: {key} must be explicit, use none/unknown/not_applicable when empty')
            try:
                t0 = int((row.get('timestamp_ms') or '').strip())
                t1 = int((row.get('frame_end_ms') or '').strip())
            except ValueError:
                t0 = t1 = None
            require(t0 is not None and t1 is not None and t1 > t0, f'frame-observations.csv row {number}: frame_end_ms must be integer > timestamp_ms')
            if fid in frames:
                require((row.get('source_id') or '').strip() == frames[fid].get('source_id'),
                        f'frame-observations.csv row {number}: frame/source time tag mismatch')
                require(t0 == frames[fid].get('timestamp_ms'),
                        f'frame-observations.csv row {number}: timestamp_ms must match frames.jsonl for {fid}')
            allowed_audio_status = {'not_reviewed','subtitle_only','asr_only','audio_verified','no_audio','not_applicable','unknown'}
            require((row.get('audio_verification_status') or '').strip() in allowed_audio_status, f'frame-observations.csv row {number}: invalid audio_verification_status')
        require(set(observed_ids) == set(frames),
                'Broad Structure complete requires frame-observations.csv frame_id set to match frames.jsonl')

        action_headers, action_rows = load_csv('action-node-candidates.csv')
        required_action_columns = {
            'candidate_id', 'source_id', 'trigger_frame_id', 'candidate_start_frame_ref', 'candidate_end_frame_ref',
            'center_timestamp_ms', 'window_start_ms', 'window_end_ms', 'sampling_fps', 'trigger_reason',
            'action_description', 'response_description', 'outcome_description',
            'min_effective_unit_start_ms', 'min_effective_unit_end_ms', 'min_effective_unit_status',
            'lip_sync_check', 'relationship_turn_signal', 'question_refs', 'speaker_adjudication_refs',
            'topic_judgment', 'confidence', 'confidence_basis', 'evidence_refs',
            'verification_status', 'unknowns', 'sampling_exception_reason'
        }
        require(required_action_columns.issubset(set(action_headers)),
                'action-node-candidates.csv: missing required columns')
        for number, row in enumerate(action_rows, start=2):
            label = f'action-node-candidates.csv row {number}'
            require(nonblank(row.get('candidate_id')), f'{label}: missing candidate_id')
            require(nonblank(row.get('trigger_reason')), f'{label}: missing trigger_reason')
            for key in ('candidate_start_frame_ref','candidate_end_frame_ref','action_description','response_description','outcome_description',
                        'min_effective_unit_start_ms','min_effective_unit_end_ms','min_effective_unit_status','lip_sync_check',
                        'relationship_turn_signal','question_refs','speaker_adjudication_refs','topic_judgment','confidence',
                        'confidence_basis','evidence_refs','verification_status','unknowns'):
                require(nonblank(row.get(key)), f'{label}: {key} must be explicit, use none/unknown/not_applicable when empty')
            fps_text = (row.get('sampling_fps') or '').strip()
            try:
                fps = float(fps_text)
            except ValueError:
                fps = None
            require(fps is not None and fps > 0, f'{label}: sampling_fps must be positive')
            sid = (row.get('source_id') or '').strip()
            fid = (row.get('trigger_frame_id') or '').strip()
            require(sid in sources, f'{label}: unknown source_id {sid}')
            require(fid in frames, f'{label}: unknown trigger_frame_id {fid}')
            if fid in frames and sid in sources:
                require(frames[fid].get('source_id') == sid, f'{label}: trigger frame/source mismatch')
            try:
                center = int((row.get('center_timestamp_ms') or '').strip())
                wa = int((row.get('window_start_ms') or '').strip())
                wb = int((row.get('window_end_ms') or '').strip())
            except ValueError:
                center = wa = wb = None
            if sid in sources and center is not None and wa is not None and wb is not None:
                require(0 <= wa <= center < wb <= sources[sid].get('duration_ms', -1), f'{label}: invalid 4fps window range')
                if fid in frames and integer(frames[fid].get('timestamp_ms')):
                    require(wa <= frames[fid]['timestamp_ms'] < wb,
                            f'{label}: trigger frame timestamp must fall inside candidate window')
            else:
                require(False, f'{label}: center/window times must be integer milliseconds')
            if fps is not None and abs(fps - 4.0) > 1e-9:
                require(nonblank(row.get('sampling_exception_reason')), f'{label}: non-4fps window requires sampling_exception_reason')

        question_headers, question_rows = load_csv('structure-questions.csv')
        required_question_columns = {
            'question_id', 'stage', 'question', 'answer', 'answer_status', 'evidence_refs',
            'confidence', 'confidence_basis', 'unverified_items', 'next_check'
        }
        require(required_question_columns.issubset(set(question_headers)),
                'structure-questions.csv: missing required columns')
        allowed_status = {'supported', 'partial', 'unresolved', 'contradicted', 'not_applicable'}
        for number, row in enumerate(question_rows, start=2):
            label = f'structure-questions.csv row {number}'
            require(nonblank(row.get('question_id')), f'{label}: missing question_id')
            require(nonblank(row.get('question')), f'{label}: missing question')
            require((row.get('answer_status') or '').strip() in allowed_status, f'{label}: invalid answer_status')
            require(nonblank(row.get('answer')), f'{label}: answer must be explicit, use unresolved when not answered')
            require(nonblank(row.get('confidence')), f'{label}: confidence must be explicit')
            require(nonblank(row.get('confidence_basis')), f'{label}: confidence_basis must be explicit')
            require(nonblank(row.get('evidence_refs')), f'{label}: evidence_refs must be explicit, use none when empty')
            require(nonblank(row.get('unverified_items')), f'{label}: unverified_items must be explicit, use none when empty')
            require(nonblank(row.get('next_check')), f'{label}: next_check must be explicit, use none when no follow-up is needed')

    transcript = index(load('transcript.jsonl', []), 'utterance_id')
    for tid, row in transcript.items():
        interval(row.get('source_id'), row.get('start_ms'), row.get('end_ms'), tid)
        require(isinstance(row.get('audio_verified'), bool), f'{tid}: audio_verified must be boolean')
        if row.get('origin') == 'asr':
            require(row.get('asr_role') in ('locator_only', 'candidate', 'verified_transcript'),
                    f'{tid}: ASR utterance requires explicit asr_role')
            if row.get('asr_role') == 'verified_transcript':
                require(row.get('audio_verified') is True or bool(row.get('review_refs')),
                        f'{tid}: verified_transcript ASR requires audio/review evidence')

    reviews = index(load('reviews.jsonl', []), 'review_id')
    for rid, row in reviews.items():
        interval(row.get('source_id'), row.get('start_ms'), row.get('end_ms'), rid)

    def covered_review(refs, sid, start, end, modality):
        ranges = []
        for ref in refs:
            row = reviews.get(ref, {})
            a, b = row.get('start_ms'), row.get('end_ms')
            if row.get('source_id') == sid and modality in row.get('modalities', []) and integer(a) and integer(b):
                ranges.append((a, b))
        cursor = start
        for a, b in sorted(ranges):
            if a > cursor:
                break
            cursor = max(cursor, b)
        return cursor >= end

    def ranges_cover(ranges, start, end):
        """Return True when half-open integer ranges fully cover [start, end)."""
        cursor = start
        for a, b in sorted(ranges):
            if b <= cursor:
                continue
            if a > cursor:
                break
            cursor = max(cursor, b)
            if cursor >= end:
                return True
        return cursor >= end

    units = index(load('units.jsonl', []), 'unit_id')
    # Always initialize Deep evidence indexes so incomplete stage state produces
    # normal validation errors instead of UnboundLocalError later in preflight.
    deep_index = {}
    boundary_index = {}
    for uid, unit in units.items():
        valid = interval(unit.get('source_id'), unit.get('start_ms'), unit.get('end_ms'), uid)
        protected = unit.get('protected_ranges', [])
        if not require(isinstance(protected, list), f'{uid}: protected_ranges must be array'):
            protected = []
        for p in protected:
            if not require(isinstance(p, dict), f'{uid}: protected range must be object'):
                continue
            a, b = p.get('start_ms'), p.get('end_ms')
            if valid:
                require(integer(a) and integer(b) and unit['start_ms'] <= a < b <= unit['end_ms'], f'{uid}: protected range outside unit')
        tids = unit.get('utterance_ids', [])
        if not require(isinstance(tids, list), f'{uid}: utterance_ids must be array'):
            tids = []
        for tid in tids:
            if require(isinstance(tid, str) and tid in transcript, f'{uid}: unknown utterance {tid}'):
                require(transcript[tid].get('source_id') == unit.get('source_id'), f'{uid}: utterance source mismatch')

    if deep_complete:
        require(project.get('narrative_direction_status') == 'confirmed',
                'completed Detail Structure requires confirmed Direct 1 Narrative Direction')
        direction_ref = project.get('narrative_direction_ref')
        require(nonblank(direction_ref) and (root / direction_ref).is_file(),
                'completed Detail Structure requires Narrative Direction file')
        complete_values = ('complete', 'completed', 'done')
        require(structure_state.get('deep_observations') in complete_values, 'Directed Deep Structure complete requires structure_state.deep_observations=complete')
        require(structure_state.get('detail_intervals') in complete_values, 'Directed Deep Structure complete requires structure_state.detail_intervals=complete')
        require(structure_state.get('speaker_adjudications') in complete_values, 'Directed Deep Structure complete requires structure_state.speaker_adjudications=complete')
        require(structure_state.get('edit_boundaries') in complete_values, 'Directed Deep Structure complete requires structure_state.edit_boundaries=complete')

        detail_headers, detail_rows = load_csv('detail-intervals.csv')
        required_detail_columns = {
            'detail_interval_id','plan_node_id','source_id','start_ms','end_ms','entry_reason','preceding_context',
            'current_background','following_context','content_summary','target_questions','topic_relevance',
            'evidence_refs','unknowns'
        }
        require(required_detail_columns.issubset(set(detail_headers)), 'detail-intervals.csv: missing required detailed-context columns')
        require(bool(detail_rows), 'Directed Deep Structure complete requires at least one detail interval')
        for number, row in enumerate(detail_rows, start=2):
            label=f'detail-intervals.csv row {number}'
            for key in required_detail_columns - {'start_ms','end_ms'}:
                require(nonblank(row.get(key)), f'{label}: {key} must be explicit, use none/unknown/not_applicable when empty')
            sid=(row.get('source_id') or '').strip()
            try:
                a=int((row.get('start_ms') or '').strip()); b=int((row.get('end_ms') or '').strip())
            except ValueError:
                a=b=None
            if a is None or b is None:
                require(False, f'{label}: start_ms/end_ms must be integer milliseconds')
            else:
                interval(sid,a,b,label)

        detail_index = {(r.get('detail_interval_id') or '').strip(): r for r in detail_rows}

        speaker_headers, speaker_rows = load_csv('speaker-adjudications.csv')
        required_speaker_columns = {
            'adjudication_id','stage','source_id','utterance_id','start_ms','end_ms','frame_window_refs',
            'lip_movement_observation','visible_speaker_candidate','addressee_candidate','audio_speaker_candidate',
            'hard_subtitle_signal','asr_signal','asr_role','evidence_resolution_rule','subtitle_audio_conflict',
            'decision','decision_basis','confidence','evidence_refs','unknowns'
        }
        require(required_speaker_columns.issubset(set(speaker_headers)), 'speaker-adjudications.csv: missing required speaker-adjudication columns')
        for number, row in enumerate(speaker_rows, start=2):
            label=f'speaker-adjudications.csv row {number}'
            for key in required_speaker_columns - {'start_ms','end_ms'}:
                require(nonblank(row.get(key)), f'{label}: {key} must be explicit, use none/unknown/not_applicable when empty')
            sid=(row.get('source_id') or '').strip()
            try:
                a=int((row.get('start_ms') or '').strip()); b=int((row.get('end_ms') or '').strip())
            except ValueError:
                a=b=None
            if a is None or b is None:
                require(False, f'{label}: start_ms/end_ms must be integer milliseconds')
            else:
                interval(sid,a,b,label)
            tid = (row.get('utterance_id') or '').strip()
            if require(tid in transcript, f'{label}: unknown utterance_id {tid}'):
                utterance = transcript[tid]
                require(utterance.get('source_id') == sid, f'{label}: utterance/source time tag mismatch')
                ua, ub = utterance.get('start_ms'), utterance.get('end_ms')
                if a is not None and b is not None and integer(ua) and integer(ub):
                    require(max(a, ua) < min(b, ub), f'{label}: adjudication range must overlap utterance range')
            require((row.get('asr_role') or '').strip() in ('locator_only_until_verified','candidate','verified'),
                    f'{label}: invalid asr_role')
            require((row.get('evidence_resolution_rule') or '').strip() == 'resolve_by_fact_type_and_record_conflict',
                    f'{label}: evidence_resolution_rule must preserve fact-type conflict resolution')
            allowed_decisions={'resolved','supported','partial','unresolved','contradicted','not_applicable'}
            require((row.get('decision') or '').strip() in allowed_decisions, f'{label}: invalid decision')

        deep_headers, deep_rows = load_csv('deep-observations.csv')
        required_deep_columns = {
            'observation_id', 'detail_interval_id', 'plan_node_id', 'source_id', 'start_ms', 'end_ms', 'visual_facts',
            'action_chain', 'key_visual_changes', 'observed_emotional_cues', 'emotional_interpretation',
            'setting_context', 'narrative_context', 'motif_tags', 'content_description', 'hard_subtitle_notes',
            'original_audio_keypoints', 'audio_verification_status', 'subtitle_asr_conflicts', 'dialogue_audio',
            'speaker_adjudication_refs', 'before_state', 'after_state', 'question_refs', 'topic_judgment',
            'confidence', 'confidence_basis', 'interpretations', 'unknowns', 'unverified_items',
            'evidence_status', 'counterevidence', 'context_ranges', 'protected_ranges', 'min_effective_unit_candidate'
        }
        require(required_deep_columns.issubset(set(deep_headers)),
                'deep-observations.csv: missing required detailed-structure columns')
        require(bool(deep_rows), 'Directed Deep Structure complete requires at least one deep observation')
        for number, row in enumerate(deep_rows, start=2):
            label = f'deep-observations.csv row {number}'
            observation_id = (row.get('observation_id') or '').strip()
            if require(bool(observation_id), f'{label}: observation_id must be explicit'):
                require(observation_id not in deep_index, f'{label}: duplicate observation_id {observation_id}')
                deep_index[observation_id] = row
            for key in ('observation_id', 'detail_interval_id', 'plan_node_id', 'visual_facts', 'shot_composition',
                        'action_chain', 'key_visual_changes', 'observed_emotional_cues', 'emotional_interpretation',
                        'expression_gaze', 'spatial_relationship', 'setting_context', 'narrative_context', 'motif_tags',
                        'content_description', 'hard_subtitle_notes', 'original_audio_keypoints', 'audio_verification_status',
                        'subtitle_asr_conflicts', 'dialogue_audio', 'speaker_adjudication_refs', 'before_state', 'after_state',
                        'question_refs', 'topic_judgment', 'confidence', 'confidence_basis', 'interpretations',
                        'unknowns', 'unverified_items', 'evidence_status', 'counterevidence', 'context_ranges',
                        'protected_ranges', 'min_effective_unit_candidate', 'isolated_use_risk', 'review_refs',
                        'narrative_function', 'edit_note'):
                require(nonblank(row.get(key)), f'{label}: {key} must be explicit, use none/unknown/not_applicable when empty')
            sid=(row.get('source_id') or '').strip()
            try:
                a=int((row.get('start_ms') or '').strip()); b=int((row.get('end_ms') or '').strip())
            except ValueError:
                a=b=None
            if a is None or b is None:
                require(False, f'{label}: start_ms/end_ms must be integer milliseconds')
            else:
                interval(sid,a,b,label)
            detail_id = (row.get('detail_interval_id') or '').strip()
            if require(detail_id in detail_index, f'{label}: unknown detail_interval_id'):
                detail = detail_index[detail_id]
                require((detail.get('source_id') or '').strip() == sid, f'{label}: detail/source time tag mismatch')
                try:
                    da = int((detail.get('start_ms') or '').strip()); db = int((detail.get('end_ms') or '').strip())
                except ValueError:
                    da = db = None
                if a is not None and b is not None and da is not None and db is not None:
                    require(da <= a < b <= db, f'{label}: deep observation must stay inside its detail interval')
            require((row.get('evidence_status') or '').strip() in ('pending', 'supported', 'contradicted', 'partial'),
                    f'{label}: invalid evidence_status')

        boundary_headers, boundary_rows = load_csv('edit-boundaries.csv')
        required_boundary_columns = {
            'boundary_id','detail_interval_id','plan_node_id','source_id','unit_id','observation_refs','continuity_type',
            'content_start_ms','content_end_ms','audio_start_ms','audio_end_ms','audio_tail_end_ms',
            'action_start_ms','action_end_ms','reaction_or_settle_end_ms','preferred_in_ms','safe_in_start_ms','safe_in_end_ms',
            'preferred_out_ms','safe_out_start_ms','safe_out_end_ms','must_keep_ranges','left_handle_ms','right_handle_ms',
            'boundary_reason','cut_risk','evidence_refs','confidence','boundary_status'
        }
        require(required_boundary_columns.issubset(set(boundary_headers)),
                'edit-boundaries.csv: missing required edit-boundary columns')
        require(bool(boundary_rows), 'Directed Deep Structure complete requires at least one edit boundary')
        for number, row in enumerate(boundary_rows, start=2):
            label = f'edit-boundaries.csv row {number}'
            boundary_id = (row.get('boundary_id') or '').strip()
            if require(bool(boundary_id), f'{label}: boundary_id must be explicit'):
                require(boundary_id not in boundary_index, f'{label}: duplicate boundary_id {boundary_id}')
                boundary_index[boundary_id] = row
            for key in required_boundary_columns - {
                'content_start_ms','content_end_ms','audio_start_ms','audio_end_ms','audio_tail_end_ms',
                'action_start_ms','action_end_ms','reaction_or_settle_end_ms','preferred_in_ms','safe_in_start_ms','safe_in_end_ms',
                'preferred_out_ms','safe_out_start_ms','safe_out_end_ms','left_handle_ms','right_handle_ms'
            }:
                require(nonblank(row.get(key)), f'{label}: {key} must be explicit, use none/not_applicable when empty')
            sid = (row.get('source_id') or '').strip()
            unit_id = (row.get('unit_id') or '').strip()
            detail_id = (row.get('detail_interval_id') or '').strip()
            continuity = (row.get('continuity_type') or '').strip()
            status = (row.get('boundary_status') or '').strip()
            require(continuity in ('dialogue','action','reaction','music','scene','mixed'), f'{label}: invalid continuity_type')
            require(status in ('pending','supported','partial','contradicted'), f'{label}: invalid boundary_status')
            if require(unit_id in units, f'{label}: unknown unit_id {unit_id}'):
                require(units[unit_id].get('source_id') == sid, f'{label}: unit/source mismatch')
            detail = detail_index.get(detail_id)
            if require(detail is not None, f'{label}: unknown detail_interval_id {detail_id}'):
                require((detail.get('source_id') or '').strip() == sid, f'{label}: detail/source mismatch')
                da = csv_ms(detail.get('start_ms'), f'{label}.detail.start_ms')
                db = csv_ms(detail.get('end_ms'), f'{label}.detail.end_ms')
            else:
                da = db = None

            c0 = csv_ms(row.get('content_start_ms'), f'{label}.content_start_ms')
            c1 = csv_ms(row.get('content_end_ms'), f'{label}.content_end_ms')
            pin = csv_ms(row.get('preferred_in_ms'), f'{label}.preferred_in_ms')
            sin0 = csv_ms(row.get('safe_in_start_ms'), f'{label}.safe_in_start_ms')
            sin1 = csv_ms(row.get('safe_in_end_ms'), f'{label}.safe_in_end_ms')
            pout = csv_ms(row.get('preferred_out_ms'), f'{label}.preferred_out_ms')
            sout0 = csv_ms(row.get('safe_out_start_ms'), f'{label}.safe_out_start_ms')
            sout1 = csv_ms(row.get('safe_out_end_ms'), f'{label}.safe_out_end_ms')
            lh = csv_ms(row.get('left_handle_ms'), f'{label}.left_handle_ms')
            rh = csv_ms(row.get('right_handle_ms'), f'{label}.right_handle_ms')
            required_nums = (c0,c1,pin,sin0,sin1,pout,sout0,sout1,lh,rh)
            if all(v is not None for v in required_nums):
                interval(sid, sin0, sout1, f'{label}.boundary envelope')
                require(sin0 <= pin < sin1 <= sout0 <= pout <= sout1,
                        f'{label}: expected safe_in_start <= preferred_in < safe_in_end <= safe_out_start <= preferred_out <= safe_out_end')
                require(pin <= c0 < c1 <= pout, f'{label}: content range must stay inside preferred boundaries')
                if da is not None and db is not None:
                    require(da <= sin0 < sout1 <= db, f'{label}: boundary envelope must stay inside detail interval')
                    require(pin - da >= lh, f'{label}: left_handle_ms exceeds available Detail handle')
                    require(db - pout >= rh, f'{label}: right_handle_ms exceeds available Detail handle')

            audio_vals = [csv_ms(row.get(k), f'{label}.{k}', allow_na=True) for k in ('audio_start_ms','audio_end_ms','audio_tail_end_ms')]
            action_vals = [csv_ms(row.get(k), f'{label}.{k}', allow_na=True) for k in ('action_start_ms','action_end_ms','reaction_or_settle_end_ms')]
            if continuity in ('dialogue','music','mixed'):
                require(all(v is not None for v in audio_vals), f'{label}: {continuity} boundary requires audio start/end/tail times')
                if all(v is not None for v in audio_vals) and sin1 is not None and sout0 is not None:
                    a0,a1,at = audio_vals
                    require(a0 < a1 <= at, f'{label}: audio times must satisfy start < end <= tail_end')
                    require(sin1 <= a0, f'{label}: safe-in window must end before required audio expression starts')
                    require(at <= sout0, f'{label}: safe-out window must start after required audio tail ends')
            if continuity in ('action','reaction','mixed'):
                require(all(v is not None for v in action_vals), f'{label}: {continuity} boundary requires action start/end/reaction-settle times')
                if all(v is not None for v in action_vals) and sin1 is not None and sout0 is not None:
                    a0,a1,settle = action_vals
                    require(a0 < a1 <= settle, f'{label}: action times must satisfy start < end <= settle_end')
                    require(sin1 <= a0, f'{label}: safe-in window must end before required action starts')
                    require(settle <= sout0, f'{label}: safe-out window must start after action/reaction settles')

            keep_ranges = csv_ranges(row.get('must_keep_ranges'), f'{label}.must_keep_ranges')
            require(bool(keep_ranges), f'{label}: must_keep_ranges must contain at least one explicit source-ms range')
            if sin1 is not None and sout0 is not None:
                for a,b in keep_ranges:
                    require(sin1 <= a < b <= sout0,
                            f'{label}: must-keep range {a}-{b} must be preserved by every safe in/out choice')
                    interval(sid, a, b, f'{label}.must_keep_ranges')

            refs = csv_refs(row.get('observation_refs'))
            require(bool(refs), f'{label}: observation_refs must name the Deep observations supporting this boundary')
            support = []
            for ref in refs:
                if not require(ref in deep_index, f'{label}: unknown Deep observation {ref}'):
                    continue
                obs = deep_index[ref]
                require((obs.get('source_id') or '').strip() == sid, f'{label}: Deep observation {ref} source mismatch')
                require((obs.get('detail_interval_id') or '').strip() == detail_id, f'{label}: Deep observation {ref} detail interval mismatch')
                try:
                    oa, ob = int((obs.get('start_ms') or '').strip()), int((obs.get('end_ms') or '').strip())
                except ValueError:
                    oa = ob = None
                if oa is not None and ob is not None and pin is not None and pout is not None:
                    if max(oa,pin) < min(ob,pout):
                        support.append((max(oa,pin), min(ob,pout)))
            if pin is not None and pout is not None:
                require(ranges_cover(support, pin, pout), f'{label}: observation_refs do not fully cover preferred boundary range')

    timeline = load('timeline.json', {})
    events = timeline.get('events', [])
    if not require(isinstance(events, list), 'timeline.events must be array'):
        events = []
    event_index = index(events, 'event_id')
    ready = timeline.get('status') == 'ready_for_render'
    # v1.0.6 keeps the original schemas and render gates. Exception declarations
    # report unknowns; they never remove an error or certify an unobserved fact.
    exception_ref = project.get('structure_exceptions_ref')
    exception_rows = []
    if nonblank(exception_ref) and (root / exception_ref).exists():
        exception_rows = load(exception_ref, [])
        required = {'exception_id', 'stage', 'artifact', 'record_id', 'field',
                    'status', 'reason', 'impact', 'downstream_handling'}
        index(exception_rows, 'exception_id')
        for row in exception_rows:
            if not isinstance(row, dict):
                continue
            label = f'structure exception {row.get("exception_id")}'
            require(required.issubset(row), f'{label}: missing exception fields')
            require(row.get('status') in ('unavailable', 'uncertain', 'partial'),
                    f'{label}: invalid status')
            require(row.get('stage') in ('B', 'C', 'E'), f'{label}: invalid stage')
            require(row.get('impact') in ('low', 'medium', 'high'), f'{label}: invalid impact')
            require(row.get('record_id') is None or nonblank(row.get('record_id')),
                    f'{label}: record_id must be an ID or null')
            for key in ('artifact', 'field', 'reason', 'downstream_handling'):
                require(nonblank(row.get(key)), f'{label}: {key} must be explicit')
            warnings.append(f'{label}: {row.get("status")}; {row.get("reason")}; '
                            f'downstream: {row.get("downstream_handling")}')
    package_policy = project.get('execution_package_policy')
    if package_policy is not None:
        require(package_policy == 'plan_and_reference', 'invalid execution_package_policy')
    if package_policy == 'plan_and_reference':
        if deep_complete:
            for key in ('keyframe_references_ref', 'execution_handoff_ref'):
                ref = project.get(key)
                if require(nonblank(ref), f'completed Detail requires {key}'):
                    require((root / ref).is_file(), f'completed Detail requires file: {ref}')
                    if key == 'execution_handoff_ref' and (root / ref).is_file():
                        require(bool((root / ref).read_text(encoding='utf-8').strip()),
                                'completed Detail requires non-empty execution handoff')
            ref = project.get('keyframe_references_ref')
            if nonblank(ref) and (root / ref).is_file():
                rows = load(ref, [])
                index(rows, 'frame_id')
                required = {'frame_id', 'source_id', 'timestamp_ms', 'image_ref',
                            'source_segment', 'narrative_role', 'notes', 'status',
                            'reason', 'impact', 'downstream_handling'}
                if not rows:
                    require(any(isinstance(x, dict) and x.get('artifact') == ref
                                and x.get('field') == '*' for x in exception_rows),
                            'empty keyframe references require an explicit artifact exception')
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    label = f'keyframe {row.get("frame_id")}'
                    require(required.issubset(row), f'{label}: missing keyframe fields')
                    status = row.get('status')
                    require(status in ('available', 'unavailable', 'uncertain', 'partial'),
                            f'{label}: invalid status')
                    timestamp = row.get('timestamp_ms')
                    sid = row.get('source_id')
                    unit_ref = row.get('source_segment')
                    unit = units.get(unit_ref) if isinstance(unit_ref, str) else None
                    if status == 'available' or nonblank(unit_ref):
                        require(unit is not None, f'{label}: unknown source_segment unit')
                    if unit is not None:
                        if nonblank(sid):
                            require(sid == unit.get('source_id'),
                                    f'{label}: source_segment source mismatch')
                        if integer(timestamp):
                            require(integer(unit.get('start_ms')) and integer(unit.get('end_ms'))
                                    and unit['start_ms'] <= timestamp < unit['end_ms'],
                                    f'{label}: timestamp_ms is outside source_segment')
                    frame_id = row.get('frame_id')
                    frame = frames.get(frame_id) if isinstance(frame_id, str) else None
                    if frame is not None:
                        if nonblank(sid):
                            require(sid == frame.get('source_id'),
                                    f'{label}: source_id must match existing frame')
                        if integer(timestamp):
                            require(timestamp == frame.get('timestamp_ms'),
                                    f'{label}: timestamp_ms must match existing frame')
                    if status == 'available':
                        require(sid in sources, f'{label}: unknown source')
                        require(integer(timestamp) and sid in sources
                                and 0 <= timestamp < sources[sid]['duration_ms'],
                                f'{label}: available image requires reliable source timestamp')
                        image_ref = row.get('image_ref')
                        require(nonblank(image_ref) and (root / image_ref).is_file(),
                                f'{label}: available image file is missing')
                    else:
                        for key in ('reason', 'downstream_handling'):
                            require(nonblank(row.get(key)), f'{label}: {key} must be explicit')
                        require(row.get('impact') in ('low', 'medium', 'high'),
                                f'{label}: invalid impact')
                        require(timestamp is None or integer(timestamp),
                                f'{label}: unknown timestamp must be null')
                        if status == 'unavailable':
                            require(any(isinstance(x, dict) and x.get('stage') == 'E'
                                        and x.get('artifact') == ref and x.get('status') == 'unavailable'
                                        and ((x.get('record_id') == frame_id
                                              and x.get('field') in ('image_ref', '*'))
                                             or (x.get('record_id') is None and x.get('field') == '*'))
                                        for x in exception_rows),
                                    f'{label}: unavailable requires a matching exception declaration')
                        warnings.append(f'{label}: {status}; {row.get("reason")}')
        if ready:
            ref = project.get('execution_reference_ref')
            if require(nonblank(ref), 'ready_for_render requires execution_reference_ref'):
                require((root / ref).is_file() and bool((root / ref).read_text(encoding='utf-8').strip()),
                        'ready_for_render requires a non-empty execution reference document')
            assets = project.get('execution_reference_asset_refs', [])
            if require(isinstance(assets, list), 'execution_reference_asset_refs must be an array'):
                for asset in assets:
                    require(nonblank(asset) and (root / asset).is_file(),
                            'declared execution reference asset is missing')
    if ready:
        require(bool(events), 'ready_for_render has no events')
        require(positive(timeline.get('width')) and positive(timeline.get('height')), 'ready_for_render requires output dimensions')
        complete_values = ('complete', 'completed', 'done')
        require(structure_state.get('broad_pass') in complete_values and structure_state.get('content_map') in complete_values,
                'ready_for_render requires completed Broad Structure + Content Map')
        require(structure_state.get('directed_deep_pass') in complete_values,
                'ready_for_render requires completed Directed Deep / Detail Structure')
        require(project.get('narrative_direction_status') == 'confirmed',
                'ready_for_render requires narrative_direction_status=confirmed')
        require(project.get('execution_plan_status') == 'confirmed',
                'ready_for_render requires execution_plan_status=confirmed')
        for key, label in [('narrative_direction_ref', 'Narrative Direction'), ('execution_plan_ref', 'Editorial Execution Plan')]:
            ref = project.get(key)
            if require(nonblank(ref), f'ready_for_render requires {key}'):
                path = root / ref
                require(path.exists() and bool(path.read_text(encoding='utf-8').strip()) if path.exists() else False,
                        f'ready_for_render requires non-empty {label} file: {ref}')
        require(project.get('render_authorized') is True, 'ready_for_render requires render_authorized=true')
        time_policy = project.get('time_policy', {}) if isinstance(project, dict) else {}
        require(isinstance(time_policy, dict) and time_policy.get('time_tag_stability') == 'strict',
                'ready_for_render requires strict time-tag policy')
        execution_policy = project.get('execution_policy', {}) if isinstance(project, dict) else {}
        require(execution_policy.get('duration_budget_required_before_ready') is True,
                'ready_for_render requires duration budget policy')
        require(execution_policy.get('feedback_invalidation_matrix') == 'strict',
                'ready_for_render requires feedback invalidation policy')
        require(execution_policy.get('audio_narrative_role_required') is True,
                'ready_for_render requires audio narrative-role policy')
        require(execution_policy.get('edit_boundary_required_before_ready') is True,
                'ready_for_render requires edit-boundary policy')
    fps_num, fps_den = timeline.get('fps_num'), timeline.get('fps_den')
    fps_ok = positive(fps_num) and positive(fps_den)
    if events:
        require(fps_ok, 'timeline requires positive integer fps_num/fps_den')
    frame_ms = 1000 * fps_den / fps_num if fps_ok else None
    canonical_ranges = []
    if events and fps_ok:
        try:
            canonical_ranges = canonical_assembly_ranges(events, fps_num, fps_den)
        except ValueError as exc:
            require(False, f'timeline cumulative quantization: {exc}')
            canonical_ranges = []
    canonical_by_id = {}
    for i, event in enumerate(event_index.values()):
        eid = event['event_id']
        a, b = event.get('out_in_frame'), event.get('out_out_frame')
        out_ok = integer(a) and integer(b) and 0 <= a < b
        require(out_ok, f'{eid}: invalid assembly frame range')
        if i < len(canonical_ranges):
            expected = canonical_ranges[i]
            canonical_by_id[eid] = expected
            require(a == expected['assembly_in_frame'] and b == expected['assembly_out_frame'],
                    f'{eid}: assembly range must use cumulative timeline quantization; expected '
                    f"{expected['assembly_in_frame']}-{expected['assembly_out_frame']}")
        kind = event.get('kind')
        require(kind in ('source', 'card'), f'{eid}: unsupported event kind')
        if kind != 'source':
            continue
        sid = event.get('source_id')
        start_ms, end_ms = event.get('source_in_ms'), event.get('source_out_ms')
        valid = interval(sid, start_ms, end_ms, eid)
        speed = event.get('speed', 1)
        speed_ok = type(speed) in (int, float) and math.isfinite(speed) and speed > 0
        require(speed_ok, f'{eid}: invalid speed')
        uid = event.get('unit_id')
        if not require(isinstance(uid, str) and uid in units, f'{eid}: unknown unit {uid}'):
            continue
        unit = units[uid]
        require(unit.get('source_id') == sid, f'{eid}: unit/source mismatch')
        if valid and integer(unit.get('start_ms')) and integer(unit.get('end_ms')):
            require(unit['start_ms'] <= start_ms < end_ms <= unit['end_ms'], f'{eid}: cut outside unit')
            for p in unit.get('protected_ranges', []):
                if isinstance(p, dict) and integer(p.get('start_ms')) and integer(p.get('end_ms')):
                    require(start_ms <= p['start_ms'] < p['end_ms'] <= end_ms, f'{eid}: cut drops protected meaning range')
        if ready:
            require(bool(sources.get(sid, {}).get('version')), f'{eid}: source version must be known')
            require(isinstance(sources.get(sid, {}).get('time_mapping'), dict) and bool(sources.get(sid, {}).get('time_mapping')),
                    f'{eid}: ready source requires explicit time_mapping')
            verification = unit.get('verification', {})
            require(isinstance(verification, dict), f'{uid}: verification must be object')
            if isinstance(verification, dict):
                require(all(verification.get(k) in ('reviewed', 'not_applicable') for k in ('audio', 'visual', 'context')), f'{uid}: source review incomplete')
                refs = verification.get('review_refs', [])
                if not require(isinstance(refs, list) and bool(refs), f'{uid}: missing review references'):
                    refs = []
                valid_refs = [ref for ref in refs if isinstance(ref, str) and ref in reviews]
                require(len(valid_refs) == len(refs), f'{uid}: unknown review reference')
                if valid:
                    for name, modality in [('audio', 'audio'), ('visual', 'video')]:
                        if verification.get(name) == 'reviewed':
                            require(covered_review(valid_refs, sid, start_ms, end_ms, modality), f'{uid}: {modality} review does not cover selected range')
                for name in ('audio', 'visual', 'context'):
                    if verification.get(name) == 'not_applicable':
                        reasons = verification.get('not_applicable_reasons', {})
                        require(isinstance(reasons, dict) and bool(reasons.get(name)), f'{uid}: missing reason for {name} not_applicable')
            require(bool(unit.get('protected_ranges')) or bool(unit.get('protection_note')), f'{uid}: missing protection decision')

    transitions = load('transitions.json', [])
    event_ids = list(event_index)
    pairs = list(zip(event_ids[:-1], event_ids[1:]))
    seen = []
    overlap_by_pair = {}
    relations = {'continuous', 'ellipsis', 'comparison', 'flashback', 'chapter_change'}
    for row in transitions:
        if not require(isinstance(row, dict), 'transition must be object'):
            continue
        pair = (row.get('from_event'), row.get('to_event'))
        require(pair in pairs, f'transition {pair}: not adjacent events')
        require(pair not in seen, f'transition {pair}: duplicate')
        seen.append(pair)
        require(row.get('relation') in relations, f'transition {pair}: invalid relation')
        overlap = row.get('overlap_frames', 0)
        if require(integer(overlap) and overlap >= 0, f'transition {pair}: overlap_frames must be nonnegative integer'):
            effect = row.get('effect', 'hard_cut')
            require(effect in ('hard_cut', 'xfade'), f'transition {pair}: invalid effect')
            require(not (effect == 'hard_cut' and overlap) and not (effect == 'xfade' and overlap == 0),
                    f'transition {pair}: hard_cut requires zero overlap; xfade requires positive overlap')
            overlap_by_pair[pair] = overlap
    if events:
        require(set(seen) == set(pairs), 'every adjacent event pair needs a transition record')

    output_ranges = []
    total_output = 0
    overlaps = [0] + [overlap_by_pair.get(pair, 0) for pair in pairs] if events else []
    if canonical_ranges and len(overlaps) == len(canonical_ranges):
        try:
            output_ranges, total_output = output_ranges_from_overlaps(canonical_ranges, overlaps)
        except ValueError as exc:
            require(False, f'timeline output mapping: {exc}')
            output_ranges, total_output = [], 0
    output_by_id = {eid: output_ranges[i] for i, eid in enumerate(event_ids) if i < len(output_ranges)}

    if ready:
        budget = timeline.get('duration_budget', {})
        if require(isinstance(budget, dict), 'ready_for_render requires timeline.duration_budget object') and canonical_ranges:
            sum_event_frames = sum(r['length_frames'] for r in canonical_ranges)
            sum_overlap_frames = sum(overlaps)
            require(budget.get('sum_event_frames') == sum_event_frames,
                    'duration_budget.sum_event_frames must equal cumulative-quantized event frames')
            require(budget.get('sum_transition_overlap_frames') == sum_overlap_frames,
                    'duration_budget.sum_transition_overlap_frames must equal transition overlaps')
            require(budget.get('computed_output_frames') == total_output,
                    'duration_budget.computed_output_frames must equal compiled output frames')
            target = budget.get('target_max_frames')
            target_ms = project.get('target_duration_ms') if isinstance(project, dict) else None
            if target_ms is not None and fps_ok:
                derived_target = math.floor(target_ms * fps_num / (1000 * fps_den))
                require(target == derived_target, 'duration_budget.target_max_frames must match project target_duration_ms')
            if target is None:
                require(budget.get('status') == 'checked_no_limit',
                        'duration budget without target must use status=checked_no_limit')
            elif require(integer(target) and target > 0, 'duration_budget.target_max_frames must be positive integer or null'):
                require(total_output <= target, 'ready_for_render exceeds target duration budget')
                require(budget.get('status') == 'within_budget',
                        'duration budget with target must use status=within_budget')

        # Each selected source event must explicitly name the Deep observations actually used.
        # Only run evidence-linkage checks after Directed Deep / Detail is complete.
        # If the stage is pending, the ready_for_render stage gate above is the structured
        # error; do not cascade into unknown-evidence errors or crash on an unbuilt index.
        if deep_complete:
            evidence_events = events
        else:
            evidence_events = []
        # Do not gate an event on every observation that happens to share the same unit_id:
        # unused pending/contradicted observations remain valid evidence records but are not blockers.
        for event in evidence_events:
            if event.get('kind') != 'source':
                continue
            eid = event.get('event_id') or 'source event'
            sid = event.get('source_id')
            start_ms, end_ms = event.get('source_in_ms'), event.get('source_out_ms')
            refs = event.get('deep_observation_refs')
            if not require(isinstance(refs, list) and bool(refs),
                           f'{eid}: selected source event requires non-empty deep_observation_refs'):
                continue
            string_refs = [ref for ref in refs if isinstance(ref, str)]
            require(len(string_refs) == len(refs), f'{eid}: deep_observation_refs must contain only strings')
            require(len(string_refs) == len(set(string_refs)), f'{eid}: duplicate deep_observation_refs')
            support_ranges = []
            for ref in string_refs:
                if not require(ref in deep_index, f'{eid}: unknown Deep observation {ref}'):
                    continue
                row = deep_index[ref]
                require((row.get('source_id') or '').strip() == sid,
                        f'{eid}: Deep observation {ref} source mismatch')
                status = (row.get('evidence_status') or '').strip()
                require(status in ('supported', 'partial'),
                        f'{eid}: Deep observation {ref} evidence_status must be supported/partial, got {status or "blank"}')
                try:
                    a = int((row.get('start_ms') or '').strip())
                    b = int((row.get('end_ms') or '').strip())
                except ValueError:
                    a = b = None
                if a is not None and b is not None and integer(start_ms) and integer(end_ms):
                    require(max(a, start_ms) < min(b, end_ms),
                            f'{eid}: Deep observation {ref} does not overlap selected source range')
                    support_ranges.append((max(a, start_ms), min(b, end_ms)))
            if integer(start_ms) and integer(end_ms):
                require(ranges_cover(support_ranges, start_ms, end_ms),
                        f'{eid}: referenced Deep observations do not fully cover selected source range')

            boundary_ref = event.get('edit_boundary_ref')
            if not require(isinstance(boundary_ref, str) and bool(boundary_ref.strip()),
                           f'{eid}: selected source event requires edit_boundary_ref'):
                continue
            boundary = boundary_index.get(boundary_ref)
            if not require(boundary is not None, f'{eid}: unknown edit boundary {boundary_ref}'):
                continue
            boundary_observation_refs = csv_refs(boundary.get('observation_refs'))
            require(set(boundary_observation_refs).issubset(set(string_refs)),
                    f'{eid}: edit boundary evidence observations must be included in deep_observation_refs')
            require((boundary.get('source_id') or '').strip() == sid, f'{eid}: edit boundary source mismatch')
            require((boundary.get('unit_id') or '').strip() == event.get('unit_id'), f'{eid}: edit boundary unit mismatch')
            require((boundary.get('boundary_status') or '').strip() in ('supported','partial'),
                    f'{eid}: edit boundary must be supported/partial')
            sin0 = csv_ms(boundary.get('safe_in_start_ms'), f'{eid}.boundary.safe_in_start_ms')
            sin1 = csv_ms(boundary.get('safe_in_end_ms'), f'{eid}.boundary.safe_in_end_ms')
            sout0 = csv_ms(boundary.get('safe_out_start_ms'), f'{eid}.boundary.safe_out_start_ms')
            sout1 = csv_ms(boundary.get('safe_out_end_ms'), f'{eid}.boundary.safe_out_end_ms')
            keep_ranges = csv_ranges(boundary.get('must_keep_ranges'), f'{eid}.boundary.must_keep_ranges')
            override = event.get('boundary_override') is True
            if not override and integer(start_ms) and integer(end_ms) and None not in (sin0,sin1,sout0,sout1):
                require(sin0 <= start_ms < sin1, f'{eid}: source_in_ms must fall inside edit boundary safe-in window')
                require(sout0 <= end_ms <= sout1, f'{eid}: source_out_ms must fall inside edit boundary safe-out window')
                for a,b in keep_ranges:
                    require(start_ms <= a < b <= end_ms, f'{eid}: cut drops boundary must-keep range {a}-{b}')
            elif override:
                require(nonblank(event.get('boundary_override_reason')), f'{eid}: boundary_override requires reason')
                override_refs = event.get('boundary_override_review_refs')
                if require(isinstance(override_refs, list) and bool(override_refs), f'{eid}: boundary_override requires review refs'):
                    valid_override_refs = [ref for ref in override_refs if isinstance(ref, str) and ref in reviews]
                    require(len(valid_override_refs) == len(override_refs), f'{eid}: boundary_override has unknown review ref')
                    require(any(reviews[ref].get('source_id') == sid for ref in valid_override_refs),
                            f'{eid}: boundary_override review refs must include the same source')
            else:
                require(event.get('boundary_override') in (None, False), f'{eid}: boundary_override must be boolean when provided')

    for key in ('audio_tracks', 'text_tracks'):
        tracks = timeline.get(key, [])
        if not require(isinstance(tracks, list), f'{key}: must be array'):
            continue
        for number, row in enumerate(tracks):
            label = f'{key}[{number}]'
            if not require(isinstance(row, dict), f'{label}: must be object'):
                continue
            a, b = row.get('out_in_frame'), row.get('out_out_frame')
            if row.get('anchor_event_id'):
                anchor_id = row['anchor_event_id']
                anchor = output_by_id.get(anchor_id)
                if require(anchor is not None, f'{label}: unknown event anchor'):
                    la, lb = row.get('local_in_frame'), row.get('local_out_frame')
                    if require(integer(la) and integer(lb) and lb > la, f'{label}: local frames must be increasing integers'):
                        a, b = anchor['out_in_frame'] + la, anchor['out_in_frame'] + lb
            else:
                require(row.get('coordinate_space') == 'output',
                        f'{label}: absolute track timing requires coordinate_space=output')
            require(integer(a) and integer(b) and 0 <= a < b <= total_output, f'{label}: outside compiled output')
            if key == 'audio_tracks':
                if row.get('source_id'):
                    interval(row['source_id'], row.get('source_in_ms'), row.get('source_out_ms'), label)
                if ready:
                    require(row.get('narrative_role') in ('dialogue_information','ambience_continuity','emotional_music','rhythm_cue','intentional_silence','other'),
                            f'{label}: ready audio track requires narrative_role')
                    require(nonblank(row.get('treatment_reason')), f'{label}: ready audio track requires treatment_reason')

    if ready and any(e.get('kind') == 'source' for e in event_index.values()):
        require(bool(timeline.get('audio_tracks')), 'ready_for_render requires explicit audio decisions')
    # v1.0.3 binds the existing Structure/Direct records to the actual execution.
    # Keep draft/Structure-only projects editable without asserting readiness.
    if ready and fps_ok and output_by_id:
        try:
            integrity = validate_integrity(root, project, sources, units, deep_index, boundary_index,
                                           reviews, timeline, transitions, output_by_id, total_output)
            errors.extend(integrity['errors'])
            warnings.extend(integrity['warnings'])
        except (ValueError, TypeError, KeyError, AttributeError, OSError) as exc:
            errors.append(f'execution integrity: malformed input: {exc}')
    return {'status': 'fail' if errors else 'pass', 'scope': 'core static references and timing only', 'checked': checked, 'skipped': skipped, 'errors': errors, 'warnings': warnings}


if __name__ == '__main__':
    if len(sys.argv) != 2 or not Path(sys.argv[1]).is_dir():
        print('Usage: validate_project.py PROJECT_DIRECTORY', file=sys.stderr)
        sys.exit(2)
    report = validate(Path(sys.argv[1]))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(1 if report['errors'] else 0)
