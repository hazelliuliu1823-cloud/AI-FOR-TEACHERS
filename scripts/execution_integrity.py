#!/usr/bin/env python3
"""Version-bound evidence, confirmed execution scope and source-audio continuity.

Checks declared records; does not authenticate a reviewer or understand the video.
Run with PROJECT_DIRECTORY to print fingerprints, never to confirm a plan.
"""
import csv
import hashlib
import json
import math
from pathlib import Path


EMPTY = {'', 'none', 'unknown', 'not_applicable', 'null', 'pending', 'todo', 'tbd'}
SUCCESS = {'reviewed', 'pass', 'passed'}
RULES = {'safe_in_window', 'safe_out_window', 'boundary_must_keep',
         'audio_required_range', 'audio_transition', 'protected_overlap'}
DERIVED_EVENT_FIELDS = {'out_in_frame', 'out_out_frame', 'assembly_in_frame', 'assembly_out_frame'}


def digest(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_signature(source):
    return digest({k: source.get(k) for k in ('source_id', 'version', 'duration_ms')})


def time_mapping_digest(source):
    return digest(source.get('time_mapping'))


def constraint_digest(project, source):
    return digest({'source_scope': project.get('source_scope'),
                   'source_id': source.get('source_id'),
                   'usable_ranges': source.get('usable_ranges'),
                   'allowed_scope': source.get('allowed_scope'),
                   'downstream_constraints': source.get('downstream_constraints')})


def event_spec(event):
    result = {k: v for k, v in event.items() if k not in DERIVED_EVENT_FIELDS}
    if event.get('kind') == 'card':
        a, b = event.get('out_in_frame'), event.get('out_out_frame')
        result['card_duration_frames'] = b - a if type(a) is int and type(b) is int else None
    return result


def explicit(value):
    return isinstance(value, str) and value.strip().lower() not in EMPTY


def int_ms(value):
    if type(value) is int:
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def refs(value):
    if isinstance(value, list):
        return [v for v in value if explicit(v)]
    if not explicit(value):
        return []
    return [v.strip() for v in value.split(';') if explicit(v)]


def source_ranges(value):
    if isinstance(value, list):
        result = []
        for row in value:
            if not isinstance(row, dict):
                raise ValueError('range must be an object')
            a, b = int_ms(row.get('start_ms')), int_ms(row.get('end_ms'))
            if a is None or b is None or not 0 <= a < b:
                raise ValueError('range must have increasing nonnegative integer ms')
            result.append((a, b))
        return result
    if not explicit(value):
        return []
    result = []
    for token in refs(value):
        a, b = token.split('-', 1)
        a, b = int_ms(a), int_ms(b)
        if a is None or b is None or not 0 <= a < b:
            raise ValueError('invalid source-ms range')
        result.append((a, b))
    return result


def covers(ranges, start, end):
    cursor = start
    for a, b in sorted(ranges):
        if a > cursor:
            break
        cursor = max(cursor, b)
        if cursor >= end:
            return True
    return cursor >= end


def binding_matches(row, source):
    return (isinstance(row, dict) and source is not None and bool(source.get('version'))
            and row.get('source_signature') == source_signature(source)
            and row.get('time_mapping_digest') == time_mapping_digest(source))


def successful_review(row, source):
    return (binding_matches(row, source) and explicit(row.get('reviewer'))
            and explicit(row.get('evidence_locator')) and row.get('result') in SUCCESS
            and isinstance(row.get('modalities'), list) and bool(row['modalities'])
            and set(row['modalities']).issubset({'video', 'audio', 'frames', 'text'})
            and type(row.get('start_ms')) is int and type(row.get('end_ms')) is int
            and 0 <= row['start_ms'] < row['end_ms'] <= source['duration_ms'])


def source_utterance_ids(sid, ranges, transcript, declared=()):
    """Derive known speech from source selections, independent of video linkage."""
    selected = set(declared)
    ranges = [(a, b) for a, b in ranges if type(a) is int and type(b) is int and a < b]
    for tid, row in transcript.items():
        if row.get('source_id') != sid:
            continue
        a, b = row.get('start_ms'), row.get('end_ms')
        if type(a) is int and type(b) is int and any(max(a, x) < min(b, y) for x, y in ranges):
            selected.add(tid)
    return sorted(selected)


def track_utterance_ids(track, transcript):
    return source_utterance_ids(track.get('source_id'),
        [(track.get('source_in_ms'), track.get('source_out_ms'))], transcript,
        refs(track.get('adopted_utterance_refs')))


def adopted_utterance_ids(event, unit, transcript, tracks):
    """Derive speech from actual selections, never from a claimed protection range."""
    selected = set(refs(event.get('adopted_utterance_refs')))
    selected.update(tid for tid in refs(unit.get('utterance_ids')) if tid not in transcript)
    ranges = [(event.get('source_in_ms'), event.get('source_out_ms'))]
    audio_ids = refs(event.get('audio_source_refs'))
    for track in tracks:
        associated = track.get('track_id') in audio_ids or track.get('sync_event_id') == event.get('event_id')
        if associated and track.get('source_id') == event.get('source_id'):
            ranges.append((track.get('source_in_ms'), track.get('source_out_ms')))
            selected.update(refs(track.get('adopted_utterance_refs')))
    return source_utterance_ids(event.get('source_id'), ranges, transcript, selected)


def adopted_evidence_digest(timeline, units, observations, boundaries, reviews, transitions, transcript=None):
    """Ignore unadopted observations, but include all adopted protection/review data."""
    selected_units, selected_obs, selected_boundaries, review_ids = {}, {}, {}, set()
    selected_utterances = {}
    transcript = transcript or {}
    for event in timeline.get('events', []):
        if event.get('kind') != 'source':
            continue
        uid = event.get('unit_id')
        if uid in units:
            selected_units[uid] = units[uid]
            review_ids.update(refs(units[uid].get('verification', {}).get('review_refs')))
        for tid in adopted_utterance_ids(event, units.get(uid, {}), transcript, timeline.get('audio_tracks', [])):
            selected_utterances[tid] = transcript.get(tid)
            review_ids.update(refs((transcript.get(tid) or {}).get('review_refs')))
        for oid in refs(event.get('adopted_observation_refs')):
            if oid in observations:
                selected_obs[oid] = observations[oid]
                review_ids.update(refs(observations[oid].get('review_refs')))
        bid = event.get('adopted_boundary_ref')
        if bid in boundaries:
            selected_boundaries[bid] = boundaries[bid]
            for ref in refs(boundaries[bid].get('evidence_refs')):
                if ref.startswith('review:'):
                    review_ids.add(ref[7:])
    for container in [*timeline.get('events', []), *timeline.get('audio_tracks', []), *transitions]:
        if container.get('source_id') and container.get('track_id'):
            review_ids.update(refs(container.get('review_refs')))
            for tid in track_utterance_ids(container, transcript):
                selected_utterances[tid] = transcript.get(tid)
                review_ids.update(refs((transcript.get(tid) or {}).get('review_refs')))
        for override in container.get('overrides', []) or []:
            if isinstance(override, dict):
                for ref in refs(override.get('evidence_ref')):
                    if ref.startswith('review:'):
                        review_ids.add(ref[7:])
    return digest({'units': selected_units, 'observations': selected_obs,
                   'boundaries': selected_boundaries, 'utterances': selected_utterances,
                   'reviews': {rid: reviews.get(rid) for rid in sorted(review_ids)}})


def project_inputs_digest(root):
    """All source/decision inputs, excluding generated manifests, audit and caches."""
    project = json.loads((root / 'project.json').read_text(encoding='utf-8'))
    names = {'project.json', 'sources.json', 'units.jsonl', 'frames.jsonl', 'scenes.jsonl',
             'transcript.jsonl', 'reviews.jsonl', 'coverage.json', 'timeline.json', 'transitions.json',
             'frame-observations.csv', 'action-node-candidates.csv', 'structure-questions.csv',
             'detail-intervals.csv', 'deep-observations.csv', 'speaker-adjudications.csv',
             'edit-boundaries.csv'}
    for key in ('narrative_direction_ref', 'execution_plan_ref', 'execution_authorization_ref', 'content_map_ref',
                'execution_reference_ref', 'execution_handoff_ref', 'keyframe_references_ref', 'structure_exceptions_ref'):
        if explicit(project.get(key)):
            names.add(project[key])
    names.update(ref for ref in project.get('execution_reference_asset_refs', []) if explicit(ref))
    keyframe_ref = project.get('keyframe_references_ref')
    if explicit(keyframe_ref) and (root / keyframe_ref).is_file():
        keyframes = json.loads((root / keyframe_ref).read_text(encoding='utf-8'))
        if isinstance(keyframes, list):
            names.update(row['image_ref'] for row in keyframes
                         if isinstance(row, dict) and explicit(row.get('image_ref')))
    return digest({name: file_digest(root / name) if (root / name).is_file() else None
                   for name in sorted(names)})


def read_project(root):
    def read(name, default):
        path = root / name
        if not path.exists():
            return default
        if name.endswith('.jsonl'):
            return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
        return json.loads(path.read_text(encoding='utf-8'))
    def csv_index(name, key):
        path = root / name
        if not path.exists():
            return {}
        with path.open(encoding='utf-8-sig', newline='') as fh:
            return {row[key]: row for row in csv.DictReader(fh)}
    return (read('project.json', {}), {s['source_id']: s for s in read('sources.json', [])},
            {u['unit_id']: u for u in read('units.jsonl', [])},
            csv_index('deep-observations.csv', 'observation_id'),
            csv_index('edit-boundaries.csv', 'boundary_id'),
            {r['review_id']: r for r in read('reviews.jsonl', [])},
            read('timeline.json', {}), read('transitions.json', []))


def validate_integrity(root, project, sources, units, observations, boundaries,
                       reviews, timeline, transitions, output_by_id, total_output):
    errors, warnings = [], []
    transcript_path = root / 'transcript.jsonl'
    transcript = {r['utterance_id']: r for r in
                  [json.loads(line) for line in transcript_path.read_text(encoding='utf-8').splitlines() if line.strip()]} if transcript_path.exists() else {}
    def need(condition, message):
        if not condition:
            errors.append(message)
        return condition
    def bound(row, sid, label):
        return need(binding_matches(row, sources.get(sid)), f'{label}: stale or missing source/time-mapping binding')
    def parse(value, label):
        try:
            return source_ranges(value)
        except (ValueError, TypeError):
            need(False, f'{label}: malformed source ranges')
            return []
    def review_coverage(review_refs, sid, start, end, modalities, label):
        valid_rows = []
        for rid in review_refs:
            if not need(rid in reviews, f'{label}: unknown review {rid}'):
                continue
            row = reviews[rid]
            if need(row.get('source_id') == sid and successful_review(row, sources.get(sid)),
                    f'{label}: review {rid} is unsuccessful, stale or lacks reviewer/locator'):
                valid_rows.append(row)
        for modality in modalities:
            ranges = [(r['start_ms'], r['end_ms']) for r in valid_rows if modality in r['modalities']]
            need(covers(ranges, start, end), f'{label}: successful {modality} reviews do not cover {start}-{end}')
    def scope(row, sid, a, b, label):
        if sid not in sources or type(a) is not int or type(b) is not int or b <= a:
            return
        source = sources[sid]
        need(row.get('source_constraint_ref') == 'source:' + sid,
             f'{label}: source_constraint_ref must identify the adopted source')
        need(isinstance(project.get('source_scope'), list) and sid in project['source_scope'],
             f'{label}: source is outside authorized source_scope')
        usable = parse(source.get('usable_ranges', []), f'{sid}.usable_ranges')
        need(covers(usable, a, b), f'{label}: selected range falls outside usable_ranges')
        if source.get('allowed_scope') is not None:
            allowed = parse(source['allowed_scope'], f'{sid}.allowed_scope')
            need(covers(allowed, a, b), f'{label}: selected range falls outside allowed_scope')
        for constraint in source.get('downstream_constraints', []):
            # Prose constraints remain human decisions; typed range constraints are enforced.
            if not isinstance(constraint, dict):
                continue
            kind = constraint.get('type')
            if not need(kind in ('exclude_range', 'allowed_range'), f'{sid}: unsupported typed downstream constraint {kind}'):
                continue
            ranges = parse(constraint.get('ranges', [constraint]), f'{sid}.downstream_constraints')
            if kind == 'exclude_range':
                need(all(max(a, x) >= min(b, y) for x, y in ranges), f'{label}: selected range intersects excluded range')
            else:
                need(covers(ranges, a, b), f'{label}: selected range exceeds downstream allowed range')

    auth_ref = project.get('execution_authorization_ref')
    auth = {}
    if need(explicit(auth_ref), 'ready_for_render requires execution_authorization_ref'):
        try:
            auth = json.loads((root / auth_ref).read_text(encoding='utf-8'))
            if not isinstance(auth, dict):
                raise ValueError('authorization must be an object')
        except (OSError, ValueError) as exc:
            need(False, f'execution authorization: {exc}')
            auth = {}
    need(auth.get('status') == 'confirmed' and explicit(auth.get('confirmed_by')),
         'execution authorization must be confirmed by an identified director/user')
    need(explicit(auth.get('authorization_id')), 'execution authorization requires authorization_id')
    need(type(auth.get('version')) is int and auth['version'] > 0, 'execution authorization requires positive version')
    need(auth.get('project_id') == project.get('project_id') and explicit(auth.get('project_id')),
         'execution authorization project_id mismatch')
    need(auth.get('project_version') == project.get('version'), 'execution authorization project version is stale')
    need(project.get('execution_authorization_digest') == digest(auth), 'execution authorization digest changed or is missing')
    decision_files = [('execution_plan_digest', 'execution_plan_ref'),
                      ('narrative_direction_digest', 'narrative_direction_ref')]
    if explicit(project.get('execution_reference_ref')) or project.get('execution_package_policy') == 'plan_and_reference':
        decision_files.append(('execution_reference_digest', 'execution_reference_ref'))
    for key, target in decision_files:
        try:
            need(auth.get(key) == file_digest(root / project[target]), f'execution authorization: {target} changed since confirmation')
        except (OSError, KeyError, TypeError):
            need(False, f'execution authorization: missing {target}')
    reference_assets = project.get('execution_reference_asset_refs', [])
    if need(isinstance(reference_assets, list) and all(explicit(x) for x in reference_assets),
            'execution reference assets must be an array of paths'):
        need(len(reference_assets) == len(set(reference_assets)), 'duplicate execution reference asset')
        if reference_assets or 'execution_reference_asset_digests' in auth:
            try:
                need(auth.get('execution_reference_asset_digests') ==
                     {ref: file_digest(root / ref) for ref in reference_assets},
                     'execution authorization: reference assets changed since confirmation')
            except OSError:
                need(False, 'execution authorization: missing reference asset')
    need(auth.get('output') == {k: timeline.get(k) for k in ('fps_num', 'fps_den', 'width', 'height')},
         'execution authorization output specification changed')
    need(auth.get('audio_policy') == project.get('audio_policy'), 'execution authorization audio policy changed')
    event_ids = [e.get('event_id') for e in timeline.get('events', [])]
    need(auth.get('selected_events') == event_ids, 'timeline uses events not selected by Direct 2')
    need(auth.get('sequence') == event_ids, 'timeline sequence differs from Direct 2')
    for key in ('allowed_units', 'allowed_boundaries'):
        values = auth.get(key)
        need(isinstance(values, list) and all(explicit(v) for v in values) and len(values) == len(set(values)),
             f'authorization.{key} must be a unique list of concrete IDs')
    event_specs = auth.get('event_specs', {})
    if not need(isinstance(event_specs, dict), 'authorization.event_specs must be an object'):
        event_specs = {}
    adjustments = auth.get('allowed_adjustments', {})
    if not need(isinstance(adjustments, dict), 'authorization.allowed_adjustments must be an event-keyed object'):
        adjustments = {}
    source_bindings = auth.get('source_bindings', {})
    if not need(isinstance(source_bindings, dict), 'authorization.source_bindings must be an object'):
        source_bindings = {}
    adopted_sources = {e.get('source_id') for e in timeline.get('events', []) if e.get('kind') == 'source'}
    adopted_sources.update(t.get('source_id') for t in timeline.get('audio_tracks', []) if t.get('source_id'))
    for sid in adopted_sources:
        source = sources.get(sid)
        binding = source_bindings.get(sid, {})
        if bound(binding, sid, f'Direct 2 source {sid}') and source is not None:
            need(binding.get('source_constraint_digest') == constraint_digest(project, source),
                 f'Direct 2 source {sid}: source constraints changed since confirmation')
    evidence_digest = adopted_evidence_digest(timeline, units, observations, boundaries, reviews, transitions, transcript)
    need(auth.get('evidence_digest') == evidence_digest, 'adopted evidence/protection changed since Direct 2 confirmation')

    def override_ok(container, target_id, sid, rule, a, b, modalities):
        candidates = container.get('overrides', [])
        if not isinstance(candidates, list):
            need(False, f'{target_id}: overrides must be an array')
            return False
        for ov in candidates:
            if not isinstance(ov, dict) or ov.get('violated_rule') != rule:
                continue
            target = ov.get('target_range', {})
            if not isinstance(target, dict) or target.get('source_id') != sid:
                continue
            oa, ob = target.get('start_ms'), target.get('end_ms')
            if not (type(oa) is int and type(ob) is int and 0 <= oa <= a < b <= ob):
                continue
            label = f'{target_id}.override.{rule}'
            before = len(errors)
            need(ov.get('target_id') == target_id, f'{label}: target_id does not match event/track/transition')
            for key in ('override_id', 'reason', 'creative_decision', 'approved_by'):
                need(explicit(ov.get(key)), f'{label}: {key} must be concrete')
            need(ov.get('approved_by') == auth.get('confirmed_by'), f'{label}: approver differs from confirmed Direct 2 record')
            evidence_refs = refs(ov.get('evidence_ref'))
            need(bool(evidence_refs) and all(r.startswith('review:') for r in evidence_refs),
                 f'{label}: evidence_ref must use review:<id> references')
            review_coverage([r[7:] for r in evidence_refs if r.startswith('review:')],
                            sid, oa, ob, modalities, label)
            if len(errors) == before:
                return True
        need(False, f'{target_id}: missing valid authorized {rule} override for {sid} {a}-{b}')
        return False

    def checked_utterance_ranges(utterance_ids, sid, owner):
        ranges = []
        for utterance_id in utterance_ids:
            label = f'{owner}.utterance.{utterance_id}'
            utterance = transcript.get(utterance_id)
            if not need(utterance is not None, f'{label}: unknown adopted utterance'):
                continue
            need(utterance.get('source_id') == sid, f'{label}: adopted utterance source mismatch')
            bound(utterance, sid, label)
            ua, ub = utterance.get('start_ms'), utterance.get('end_ms')
            if not need(type(ua) is int and type(ub) is int and 0 <= ua < ub <= sources.get(sid, {}).get('duration_ms', 0),
                        f'{label}: invalid adopted utterance range'):
                continue
            need(utterance.get('audio_verified') is True, f'{label}: adopted utterance must be audio_verified')
            review_coverage(refs(utterance.get('review_refs')), sid, ua, ub, ['audio'], label)
            ranges.append((ua, ub))
        return ranges

    event_map = {e['event_id']: e for e in timeline.get('events', [])}
    for event in timeline.get('events', []):
        eid = event['event_id']
        specification = event_specs.get(eid)
        if not need(isinstance(specification, dict), f'{eid}: missing Direct 2 event specification'):
            specification = {}
        allowed = adjustments.get(eid, [])
        need(isinstance(allowed, list) and set(allowed).issubset({'trim_inside_safe_window', 'add_transition_handle'}),
             f'{eid}: unsupported allowed_adjustments')
        changed = {k for k in set(event_spec(event)) | set(specification)
                   if event_spec(event).get(k) != specification.get(k)}
        if changed:
            adjustable = {'source_in_ms', 'source_out_ms'} if allowed else set()
            need(changed.issubset(adjustable), f'{eid}: changes exceed Direct 2 allowed adjustments: {sorted(changed - adjustable)}')
            old_a, old_b = specification.get('source_in_ms'), specification.get('source_out_ms')
            a, b = event.get('source_in_ms'), event.get('source_out_ms')
            if all(type(v) is int for v in (old_a, old_b, a, b)) and 'add_transition_handle' not in allowed:
                need(old_a <= a < b <= old_b, f'{eid}: authorized trim may not extend the selected range')
        if event.get('kind') != 'source':
            continue
        sid, uid = event.get('source_id'), event.get('unit_id')
        a, b = event.get('source_in_ms'), event.get('source_out_ms')
        if not all(type(v) is int for v in (a, b)) or a >= b:
            continue
        scope(event, sid, a, b, eid)
        bound(event, sid, eid)
        need(uid in auth.get('allowed_units', []), f'{eid}: unit is not authorized by Direct 2')
        adopted = event.get('adopted_observation_refs')
        need(isinstance(adopted, list) and bool(adopted) and adopted == event.get('deep_observation_refs'),
             f'{eid}: adopted_observation_refs must match explicit Deep references')
        bid = event.get('adopted_boundary_ref')
        need(bid == event.get('edit_boundary_ref') and bid in auth.get('allowed_boundaries', []),
             f'{eid}: adopted boundary is inconsistent or unauthorized')
        need(event.get('evidence_status') in ('supported', 'partial'), f'{eid}: adopted evidence must be supported/partial')
        for oid in refs(adopted):
            obs = observations.get(oid, {})
            bound(obs, sid, f'{eid}.observation.{oid}')
            review_coverage(refs(obs.get('review_refs')), sid, max(a, int_ms(obs.get('start_ms')) or a),
                            min(b, int_ms(obs.get('end_ms')) or b),
                            ['video', 'audio'] if obs.get('audio_verification_status') == 'audio_verified' else ['video'],
                            f'{eid}.observation.{oid}')
        verification = units.get(uid, {}).get('verification', {})
        bound(verification, sid, f'{eid}.unit verification')
        review_coverage(refs(verification.get('review_refs')), sid, a, b,
                        [m for k, m in [('visual', 'video'), ('audio', 'audio')] if verification.get(k) == 'reviewed'],
                        f'{eid}.unit verification')
        boundary = boundaries.get(bid, {})
        bound(boundary, sid, f'{eid}.boundary.{bid}')
        continuity = boundary.get('continuity_type')
        modalities = ['audio'] if continuity in ('dialogue', 'music') else ['video']
        if continuity == 'mixed':
            modalities = ['video', 'audio']
        brefs = refs(boundary.get('evidence_refs'))
        need(bool(brefs) and all(x.startswith('review:') for x in brefs), f'{eid}: boundary needs concrete review evidence')
        ba, bb = int_ms(boundary.get('preferred_in_ms')), int_ms(boundary.get('preferred_out_ms'))
        if ba is not None and bb is not None:
            review_coverage([x[7:] for x in brefs if x.startswith('review:')], sid, ba, bb, modalities, f'{eid}.boundary')
        si0, si1 = int_ms(boundary.get('safe_in_start_ms')), int_ms(boundary.get('safe_in_end_ms'))
        so0, so1 = int_ms(boundary.get('safe_out_start_ms')), int_ms(boundary.get('safe_out_end_ms'))
        violations = []
        if None not in (si0, si1, so0, so1):
            if not si0 <= a < si1:
                violations.append(('safe_in_window', min(a, si0), max(a + 1, si1)))
            if not so0 <= b <= so1:
                violations.append(('safe_out_window', min(b, so0), max(b + 1, so1)))
        for ka, kb in parse(boundary.get('must_keep_ranges'), f'{eid}.must_keep_ranges'):
            if not a <= ka < kb <= b:
                violations.append(('boundary_must_keep', ka, kb))
        if violations:
            need(event.get('boundary_override') is True, f'{eid}: boundary violations require explicit boundary_override')
            for rule, va, vb in violations:
                override_ok(event, eid, sid, rule, va, vb, modalities)
        # Unit protected meaning ranges are deliberately never exempted here.
        for ov in event.get('overrides', []) or []:
            if isinstance(ov, dict):
                need(ov.get('violated_rule') in RULES, f'{eid}: unrecognized override rule')

    frame_ms = 1000 * timeline['fps_den'] / timeline['fps_num']
    tracks, audio_positions = timeline.get('audio_tracks', []), {}
    track_map = {}
    need(len({t.get('track_id') for t in tracks}) == len(tracks), 'audio track_id must be unique')
    audio_specs = auth.get('audio_specs', {})
    if not need(isinstance(audio_specs, dict), 'authorization.audio_specs must be an object'):
        audio_specs = {}
    need(set(audio_specs) == {t.get('track_id') for t in tracks}, 'audio tracks differ from Direct 2 selection')
    for track in tracks:
        tid = track.get('track_id')
        if not need(explicit(tid), 'audio track requires track_id'):
            continue
        track_map[tid] = track
        specification = audio_specs.get(tid, {})
        if track != specification:
            # A locked original track may follow an explicitly allowed safe trim.
            eid = track.get('sync_event_id')
            event = event_map.get(eid, {})
            allowed = adjustments.get(eid, [])
            flexible = {'source_in_ms', 'source_out_ms', 'local_in_frame', 'local_out_frame'}
            unchanged = {k: v for k, v in track.items() if k not in flexible} == {k: v for k, v in specification.items() if k not in flexible}
            safe_follow = bool(allowed) and track.get('kind') == 'original' and track.get('sync_mode') == 'locked'
            safe_follow = safe_follow and track.get('source_in_ms') == event.get('source_in_ms') and track.get('source_out_ms') == event.get('source_out_ms')
            need(unchanged and safe_follow, f'{tid}: audio processing differs from authorized Direct 2 plan')
        anchor = output_by_id.get(track.get('anchor_event_id'))
        if anchor:
            la, lb = track.get('local_in_frame'), track.get('local_out_frame')
            if type(la) is not int or type(lb) is not int:
                continue
            ta, tb = anchor['out_in_frame'] + la, anchor['out_in_frame'] + lb
        else:
            ta, tb = track.get('out_in_frame'), track.get('out_out_frame')
        if not all(type(v) is int for v in (ta, tb)) or not 0 <= ta < tb <= total_output:
            continue
        audio_positions[tid] = (ta, tb)
        sid = track.get('source_id')
        if not sid:
            continue
        a, b = track.get('source_in_ms'), track.get('source_out_ms')
        if not all(type(v) is int for v in (a, b)) or a >= b:
            continue
        scope(track, sid, a, b, tid)
        bound(track, sid, tid)
        audio_reviews = track.get('review_refs')
        need(isinstance(audio_reviews, list) and bool(audio_reviews)
             and all(explicit(r) for r in audio_reviews) and len(set(audio_reviews)) == len(audio_reviews),
             f'{tid}: source audio requires explicit unique review_refs')
        review_coverage(refs(audio_reviews), sid, a, b, ['audio'], f'{tid}.source audio')
        speed = track.get('speed', 1)
        if not need(type(speed) in (int, float) and math.isfinite(speed) and speed > 0, f'{tid}: invalid audio speed'):
            continue
        need(abs((b - a) / speed - (tb - ta) * frame_ms) <= frame_ms + 1e-7,
             f'{tid}: source audio duration does not match output duration/speed')
        if project.get('audio_policy', {}).get('allow_original_music') is False:
            need(track.get('kind') != 'music', f'{tid}: original source music is prohibited by audio_policy')

    def audible_track_range(track):
        """Conservative source coverage after fades; final listening stays separate."""
        a, b, speed = track.get('source_in_ms'), track.get('source_out_ms'), track.get('speed', 1)
        gain = track.get('gain_db')
        fi, fo = track.get('fade_in_ms', 0), track.get('fade_out_ms', 0)
        if (track.get('track_id') not in audio_positions or track.get('kind') != 'original'
                or track.get('narrative_role') != 'dialogue_information'
                or track.get('treatment', 'preserve') not in ('preserve', 'isolate')
                or track.get('muted', False) is not False
                or type(gain) not in (int, float) or not math.isfinite(gain) or gain <= -80
                or not all(type(v) is int for v in (a, b)) or a >= b
                or type(speed) not in (int, float) or not math.isfinite(speed) or speed <= 0
                or not all(type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in (fi, fo))
                or fi + fo >= (b - a) / speed):
            return None
        return a + fi * speed, b - fo * speed

    # Every source audio track contributes speech evidence, including cards,
    # extra tracks and sources that have no selected video event.
    for track in tracks:
        tid, sid = track.get('track_id'), track.get('source_id')
        if not sid:
            continue
        if 'adopted_utterance_refs' in track:
            declared = track['adopted_utterance_refs']
            need(isinstance(declared, list) and all(explicit(r) for r in declared)
                 and len(set(declared)) == len(declared),
                 f'{tid}: adopted_utterance_refs must be an explicit unique array')
        utterance_ranges = checked_utterance_ranges(track_utterance_ids(track, transcript), sid, tid)
        if not utterance_ranges:
            continue
        # The existing source-event path owns its linked dialogue boundaries,
        # synchronization, coverage and creative exceptions. Do not require a
        # second copy of an already confirmed event-level decision.
        linked = any(e.get('kind') == 'source' and e.get('source_id') == sid
                     and tid in refs(e.get('audio_source_refs')) for e in timeline.get('events', []))
        if linked:
            continue
        if project.get('audio_policy', {}).get('preserve_dialogue') is False:
            need(explicit(track.get('dialogue_policy_reason')),
                 f'{tid}: disabling dialogue preservation requires a confirmed dialogue_policy_reason')
            continue
        need(track.get('kind') == 'original' and track.get('narrative_role') == 'dialogue_information',
             f'{tid}: independent protected speech must retain original dialogue role')
        need(track.get('treatment', 'preserve') in ('preserve', 'isolate'),
             f'{tid}: protected speech treatment removes/replaces source audio')
        gain = track.get('gain_db')
        need(type(gain) in (int, float) and math.isfinite(gain) and gain > -80 and track.get('muted', False) is False,
             f'{tid}: protected source audio is muted, effectively silent or gain unknown')
        fades = (track.get('fade_in_ms', 0), track.get('fade_out_ms', 0))
        need(all(type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in fades),
             f'{tid}: explicit finite audio fades required')
        audible = []
        a, speed = track.get('source_in_ms'), track.get('speed', 1)
        if tid in audio_positions and type(a) is int and type(speed) in (int, float) and math.isfinite(speed) and speed > 0:
            ta = audio_positions[tid][0]
            for other in tracks:
                coverage = audible_track_range(other)
                if coverage is None or other.get('source_id') != sid or other.get('speed', 1) != speed:
                    continue
                mapped_start = audio_positions[other['track_id']][0] + (a - other['source_in_ms']) / speed / frame_ms
                # Complementary tracks may preserve one sentence across cards;
                # another occurrence at a different output time cannot rescue a cut.
                if abs(mapped_start - ta) <= 1.000001:
                    audible.append(coverage)
        for ua, ub in utterance_ranges:
            if not covers(audible, ua, ub):
                override_ok(track, tid, sid, 'audio_required_range', ua, ub, ['audio'])

    for event in timeline.get('events', []):
        if event.get('kind') != 'source':
            continue
        eid, sid = event['event_id'], event['source_id']
        boundary = boundaries.get(event.get('adopted_boundary_ref'), {})
        unit = units.get(event.get('unit_id'), {})
        declared_utterances = event.get('adopted_utterance_refs')
        need(isinstance(declared_utterances, list) and all(explicit(r) for r in declared_utterances)
             and len(set(declared_utterances)) == len(declared_utterances),
             f'{eid}: adopted_utterance_refs must be an explicit unique array')
        utterance_ranges = checked_utterance_ranges(adopted_utterance_ids(event, unit, transcript, tracks), sid, eid)
        speech = bool(utterance_ranges) or unit.get('audio_state', {}).get('speech') is True
        speech = speech or boundary.get('continuity_type') in ('dialogue', 'mixed')
        if not speech:
            continue
        if project.get('audio_policy', {}).get('preserve_dialogue') is False:
            need(explicit(event.get('dialogue_policy_reason')),
                 f'{eid}: disabling dialogue preservation requires a confirmed dialogue_policy_reason')
            continue
        ra, rb = int_ms(boundary.get('audio_start_ms')), int_ms(boundary.get('audio_tail_end_ms'))
        required = parse(boundary.get('dialogue_required_range'), f'{eid}.dialogue_required_range')
        for ua, ub in utterance_ranges:
            if not covers(required, ua, ub):
                override_ok(event, eid, sid, 'audio_required_range', ua, ub, ['audio'])
        if not need(ra is not None and rb is not None and 0 <= ra < rb and bool(required), f'{eid}: missing explicit dialogue/audio protection'):
            continue
        need(covers(required, ra, rb), f'{eid}: dialogue_required_range omits audio start/tail')
        need(event.get('audio_boundary') == {'required_start_ms': ra, 'required_end_ms': rb},
             f'{eid}: event audio_boundary differs from adopted boundary')
        need(event.get('dialogue_required_range') == boundary.get('dialogue_required_range'),
             f'{eid}: event dialogue range differs from adopted boundary')
        if not need(event.get('sync_mode') in ('locked', 'J_cut', 'L_cut'), f'{eid}: explicit sync_mode required'):
            continue
        selected = event.get('audio_source_refs')
        if not need(isinstance(selected, list) and bool(selected) and len(set(selected)) == len(selected),
                    f'{eid}: audio_source_refs must identify adopted audio tracks'):
            continue
        audible = []
        event_out = output_by_id.get(eid)
        if not event_out:
            continue
        for tid in selected:
            track = track_map.get(tid, {})
            if not need(tid in audio_positions and track.get('kind') == 'original' and track.get('source_id') == sid,
                        f'{eid}: protected dialogue cannot be replaced by another source/music'):
                continue
            before_track = len(errors)
            need(track.get('sync_event_id') == eid and track.get('sync_mode') == event['sync_mode'], f'{tid}: audio event/sync declaration mismatch')
            need(track.get('narrative_role') == 'dialogue_information', f'{tid}: protected speech must retain dialogue role')
            treatment = track.get('treatment', 'preserve')
            need(treatment in ('preserve', 'isolate'), f'{tid}: protected speech treatment removes/replaces source audio')
            gain = track.get('gain_db')
            need(type(gain) in (int, float) and math.isfinite(gain) and gain > -80 and track.get('muted', False) is False,
                 f'{tid}: protected source audio is muted, effectively silent or gain unknown')
            fade_in, fade_out = track.get('fade_in_ms', 0), track.get('fade_out_ms', 0)
            if not need(all(type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in (fade_in, fade_out)), f'{tid}: explicit finite audio fades required'):
                continue
            a, b, speed = track.get('source_in_ms'), track.get('source_out_ms'), track.get('speed', 1)
            if not all(type(v) is int for v in (a, b)) or type(speed) not in (int, float) or speed <= 0:
                continue
            ta, tb = audio_positions[tid]
            mapped_start = ta + (event['source_in_ms'] - a) / speed / frame_ms
            need(abs(mapped_start - event_out['out_in_frame']) <= 1.000001 and speed == event.get('speed', 1),
                 f'{tid}: protected audio source/output mapping is out of sync')
            if event['sync_mode'] == 'locked':
                need(event_out['out_in_frame'] <= ta < tb <= event_out['out_out_frame'], f'{tid}: locked audio may not cross event boundaries')
            else:
                if event['sync_mode'] == 'J_cut':
                    need(ta < event_out['out_in_frame'], f'{tid}: J_cut must start before the video event')
                else:
                    need(tb > event_out['out_out_frame'], f'{tid}: L_cut must continue after the video event')
                override_ok(event, eid, sid, 'audio_transition', ra, rb, ['audio', 'video'])
            if len(errors) == before_track and fade_in + fade_out < (b - a) / speed:
                audible.append((a + fade_in * speed, b - fade_out * speed))
        for a, b in sorted(set(required + utterance_ranges)):
            if not covers(audible, a, b):
                override_ok(event, eid, sid, 'audio_required_range', a, b, ['audio'])

    need(auth.get('text_specs') == timeline.get('text_tracks', []), 'text tracks differ from confirmed Direct 2 plan')
    need(auth.get('transitions') == transitions, 'transitions differ from confirmed Direct 2 plan')
    for transition in transitions:
        overlap = transition.get('overlap_frames', 0)
        pair_id = f"{transition.get('from_event')}->{transition.get('to_event')}"
        target = output_by_id.get(transition.get('to_event'))
        if type(overlap) is not int or overlap <= 0 or not target:
            continue
        ja, jb = target['out_in_frame'], target['out_in_frame'] + overlap
        for eid in (transition.get('from_event'), transition.get('to_event')):
            event = event_map.get(eid, {})
            out = output_by_id.get(eid)
            if event.get('kind') != 'source' or not out:
                continue
            ranges = parse(units.get(event.get('unit_id'), {}).get('protected_ranges', []), f'{eid}.protected_ranges')
            boundary = boundaries.get(event.get('adopted_boundary_ref'), {})
            ranges += parse(boundary.get('must_keep_ranges'), f'{eid}.must_keep_ranges')
            for a, b in ranges:
                pa = out['out_in_frame'] + (a - event['source_in_ms']) / event.get('speed', 1) / frame_ms
                pb = out['out_in_frame'] + (b - event['source_in_ms']) / event.get('speed', 1) / frame_ms
                if max(pa, ja) < min(pb, jb):
                    ca = max(a, math.floor(event['source_in_ms'] + (ja - out['out_in_frame']) * frame_ms * event.get('speed', 1)))
                    cb = min(b, math.ceil(event['source_in_ms'] + (jb - out['out_in_frame']) * frame_ms * event.get('speed', 1)))
                    if ca < cb:
                        mods = ['video', 'audio'] if boundary.get('continuity_type') in ('dialogue', 'mixed') else ['video']
                        override_ok(transition, pair_id, event['source_id'], 'protected_overlap', ca, cb, mods)
    return {'errors': errors, 'warnings': warnings, 'authorization_id': auth.get('authorization_id'),
            'authorization_digest': digest(auth), 'evidence_digest': evidence_digest}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project_directory', type=Path)
    args = parser.parse_args()
    project, sources, units, obs, boundaries, reviews, timeline, transitions = read_project(args.project_directory)
    transcript_path = args.project_directory / 'transcript.jsonl'
    transcript = {r['utterance_id']: r for r in [json.loads(x) for x in transcript_path.read_text(encoding='utf-8').splitlines() if x.strip()]} if transcript_path.exists() else {}
    auth_ref = project.get('execution_authorization_ref')
    auth_path = args.project_directory / auth_ref if explicit(auth_ref) else None
    auth_digest = digest(json.loads(auth_path.read_text(encoding='utf-8'))) if auth_path and auth_path.is_file() else None
    print(json.dumps({'source_bindings': {sid: {'source_signature': source_signature(s),
        'time_mapping_digest': time_mapping_digest(s), 'source_constraint_digest': constraint_digest(project, s)}
        for sid, s in sources.items()},
        'evidence_digest': adopted_evidence_digest(timeline, units, obs, boundaries, reviews, transitions, transcript),
        'execution_authorization_digest': auth_digest,
        'note': 'Fingerprints only. These do not confirm a review or authorize execution.'}, ensure_ascii=False, indent=2))
