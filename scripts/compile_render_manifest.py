#!/usr/bin/env python3
"""Compile an assembly plan to output frames. Does not render media."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

from timeline_math import canonical_assembly_ranges, output_ranges_from_overlaps
from validate_project import validate
from execution_integrity import project_inputs_digest


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def read(path, default=None):
    if not path.exists():
        if default is not None:
            return default
        raise ValueError(f'Missing input: {path.name}')
    if path.suffix == '.jsonl':
        return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    return json.loads(path.read_text(encoding='utf-8'))


def integer(value, label, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f'{label} must be integer >= {minimum}')
    return value


def read_csv_index(path, key):
    if not path.exists():
        return {}
    with path.open('r', encoding='utf-8-sig', newline='') as fh:
        rows = list(csv.DictReader(fh))
    result = {}
    for row in rows:
        value = (row.get(key) or '').strip()
        if value:
            if value in result:
                raise ValueError(f'Duplicate {key}: {value}')
            result[value] = row
    return result


def parse_ranges(value):
    raw = (value or '').strip()
    if raw.lower() in ('', 'none', 'unknown', 'not_applicable'):
        return []
    result = []
    for token in [part.strip() for part in raw.split(';') if part.strip()]:
        a, b = token.split('-', 1)
        result.append({'start_ms': int(a), 'end_ms': int(b)})
    return result


def compile_manifest(root, planning=False):
    # Compiler and static validator intentionally share the same preflight gate.
    # This prevents a timeline from compiling after the validator would reject its
    # stage state, evidence state, source-time mapping, or output coordinates.
    timeline = read(root / 'timeline.json')
    project = read(root / 'project.json', {})
    if not planning and (timeline.get('status') != 'ready_for_render' or project.get('render_authorized') is not True):
        raise ValueError('Render compilation requires ready_for_render and render_authorized=true; use --planning for a non-renderable draft')
    report = validate(root)
    if report['errors']:
        preview = '; '.join(report['errors'][:8])
        more = f' (+{len(report["errors"]) - 8} more)' if len(report['errors']) > 8 else ''
        raise ValueError(f'Static validation failed: {preview}{more}')

    if timeline.get('coordinate_space') != 'assembly':
        raise ValueError('Input must explicitly use coordinate_space=assembly; do not compile output twice')
    project = read(root / 'project.json', {})
    source_rows = read(root / 'sources.json', [])
    sources = {s['source_id']: s for s in source_rows}
    if len(sources) != len(source_rows):
        raise ValueError('Duplicate source_id')
    units = {u['unit_id']: u for u in read(root / 'units.jsonl', [])}
    boundaries = read_csv_index(root / 'edit-boundaries.csv', 'boundary_id')
    transition_rows = read(root / 'transitions.json', [])
    transitions = {(x['from_event'], x['to_event']): x for x in transition_rows}
    if len(transitions) != len(transition_rows):
        raise ValueError('Duplicate transition')

    n = integer(timeline.get('fps_num'), 'fps_num', 1)
    d = integer(timeline.get('fps_den'), 'fps_den', 1)
    width = integer(timeline.get('width'), 'width', 1)
    height = integer(timeline.get('height'), 'height', 1)
    frame_ms = 1000 * d / n
    original_events = timeline.get('events', [])
    if not original_events:
        raise ValueError('No video events')
    ids = [e['event_id'] for e in original_events]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate event_id')
    adjacent_pairs = list(zip(ids[:-1], ids[1:]))
    if set(transitions) != set(adjacent_pairs):
        raise ValueError('Exactly one transition is required for every adjacent pair')

    assembly_ranges = canonical_assembly_ranges(original_events, n, d)
    for e, expected in zip(original_events, assembly_ranges):
        if e.get('out_in_frame') != expected['assembly_in_frame'] or e.get('out_out_frame') != expected['assembly_out_frame']:
            raise ValueError(
                f'{e.get("event_id")}: assembly range must use cumulative timeline quantization; '
                f'expected {expected["assembly_in_frame"]}-{expected["assembly_out_frame"]}'
            )

    overlaps = [0]
    for i, pair in enumerate(adjacent_pairs, start=1):
        transition = transitions[pair]
        effect = transition.get('effect', 'hard_cut')
        overlap = integer(transition.get('overlap_frames', 0), 'overlap_frames')
        if effect not in ('hard_cut', 'xfade') or (effect == 'hard_cut' and overlap) or (effect == 'xfade' and overlap == 0):
            raise ValueError('Use hard_cut with zero overlap or xfade with positive overlap')
        overlaps.append(overlap)
    output_ranges, total = output_ranges_from_overlaps(assembly_ranges, overlaps)

    events, joins, warnings = [], [], []
    for i, original in enumerate(original_events):
        e = dict(original)
        assembly = assembly_ranges[i]
        output = output_ranges[i]
        e.update(
            assembly_in_frame=assembly['assembly_in_frame'],
            assembly_out_frame=assembly['assembly_out_frame'],
            out_in_frame=output['out_in_frame'],
            out_out_frame=output['out_out_frame'],
        )
        if e.get('kind') == 'source':
            sid = e.get('source_id')
            if sid not in sources or not sources[sid].get('version'):
                raise ValueError(f'{sid}: known source version required')
            source = sources[sid]
            if not isinstance(source.get('time_mapping'), dict) or not source.get('time_mapping'):
                raise ValueError(f'{sid}: explicit source time_mapping required')
            sin = integer(e.get('source_in_ms'), 'source_in_ms')
            sout = integer(e.get('source_out_ms'), 'source_out_ms', 1)
            duration = integer(source.get('duration_ms'), 'source duration', 1)
            if not sin < sout <= duration:
                raise ValueError(f'{e["event_id"]}: source range outside source')
            if e.get('unit_id') not in units:
                raise ValueError(f'{e["event_id"]}: missing unit')
            unit = units[e['unit_id']]
            if unit.get('source_id') != sid or not unit['start_ms'] <= sin < sout <= unit['end_ms']:
                raise ValueError(f'{e["event_id"]}: cut outside unit')
            for protected in unit.get('protected_ranges', []):
                if not sin <= protected['start_ms'] < protected['end_ms'] <= sout:
                    raise ValueError(f'{e["event_id"]}: cut drops protected range')
            boundary_ref = e.get('edit_boundary_ref')
            if boundary_ref:
                boundary = boundaries.get(boundary_ref)
                if boundary is None:
                    raise ValueError(f'{e["event_id"]}: unknown edit boundary {boundary_ref}')
                e['edit_boundary'] = {
                    'boundary_id': boundary_ref,
                    'continuity_type': boundary.get('continuity_type'),
                    'preferred_in_ms': int(boundary['preferred_in_ms']),
                    'preferred_out_ms': int(boundary['preferred_out_ms']),
                    'safe_in_start_ms': int(boundary['safe_in_start_ms']),
                    'safe_in_end_ms': int(boundary['safe_in_end_ms']),
                    'safe_out_start_ms': int(boundary['safe_out_start_ms']),
                    'safe_out_end_ms': int(boundary['safe_out_end_ms']),
                    'must_keep_ranges': parse_ranges(boundary.get('must_keep_ranges')),
                    'cut_risk': boundary.get('cut_risk'),
                }
            e['source_version'] = source['version']
            e['source_time_mapping'] = source['time_mapping']
        elif e.get('kind') != 'card':
            raise ValueError('Video event must be source or card')
        events.append(e)
        if i:
            transition = transitions[(ids[i - 1], ids[i])]
            overlap = overlaps[i]
            joins.append({
                'join_id': f'J{i:03d}',
                'from_event': ids[i - 1],
                'to_event': ids[i],
                'effect': transition.get('effect', 'hard_cut'),
                'relation': transition.get('relation'),
                'start_frame': output['out_in_frame'],
                'end_frame': output['out_in_frame'] + overlap,
                'overlap_frames': overlap,
            })

    budget = timeline.get('duration_budget')
    if timeline.get('status') == 'ready_for_render':
        if not isinstance(budget, dict):
            raise ValueError('ready_for_render requires duration_budget')
        sum_event_frames = sum(r['length_frames'] for r in assembly_ranges)
        sum_overlap_frames = sum(overlaps)
        if budget.get('sum_event_frames') != sum_event_frames:
            raise ValueError('duration_budget.sum_event_frames does not match cumulative-quantized events')
        if budget.get('sum_transition_overlap_frames') != sum_overlap_frames:
            raise ValueError('duration_budget.sum_transition_overlap_frames does not match transitions')
        if budget.get('computed_output_frames') != total:
            raise ValueError('duration_budget.computed_output_frames does not match compiled output')
        target = budget.get('target_max_frames')
        if target is None:
            if budget.get('status') != 'checked_no_limit':
                raise ValueError('duration budget without target must be checked_no_limit')
        else:
            if type(target) is not int or target <= 0 or total > target or budget.get('status') != 'within_budget':
                raise ValueError('duration budget is not within target')

    event_map = {e['event_id']: e for e in events}
    for i, join in enumerate(joins):
        if not join['overlap_frames']:
            continue
        trans = transitions[(join['from_event'], join['to_event'])]
        affected = []
        for e in (events[i], events[i + 1]):
            if e['kind'] != 'source':
                continue
            protected_ranges = list(units[e['unit_id']].get('protected_ranges', []))
            if isinstance(e.get('edit_boundary'), dict):
                protected_ranges.extend(e['edit_boundary'].get('must_keep_ranges', []))
            for p in protected_ranges:
                pa = e['out_in_frame'] + (p['start_ms'] - e['source_in_ms']) / e.get('speed', 1) / frame_ms
                pb = e['out_in_frame'] + (p['end_ms'] - e['source_in_ms']) / e.get('speed', 1) / frame_ms
                if max(pa, join['start_frame']) < min(pb, join['end_frame']):
                    affected.append(e['event_id'])
        if affected and not trans.get('overrides'):
            raise ValueError(f'{join["join_id"]}: overlap covers protected meaning in {affected}')
        if affected:
            warnings.append(f'{join["join_id"]}: explicitly authorized protected-overlap exception; playback review remains required')

    compiled_tracks = {}
    for key in ('audio_tracks', 'text_tracks'):
        result = []
        for row in timeline.get(key, []):
            item = dict(row)
            if item.get('anchor_event_id'):
                if item['anchor_event_id'] not in event_map:
                    raise ValueError('Unknown track anchor_event_id')
                e = event_map[item['anchor_event_id']]
                local_a, local_b = item.get('local_in_frame'), item.get('local_out_frame')
                if type(local_a) is not int or type(local_b) is not int or local_b <= local_a:
                    raise ValueError('Track local range must use increasing integer frames')
                # J/L-cuts may extend beyond one event, but never outside the compiled output.
                a, b = e['out_in_frame'] + local_a, e['out_in_frame'] + local_b
            elif item.get('coordinate_space') == 'output':
                a, b = item.get('out_in_frame'), item.get('out_out_frame')
                warnings.append(f'{key}: absolute output position must be rechecked after structural edits')
            else:
                raise ValueError(f'{key}: supply an event anchor or explicit output coordinates')
            if type(a) is not int or type(b) is not int or not 0 <= a < b <= total:
                raise ValueError(f'{key}: track falls outside compiled output')
            item.update(out_in_frame=a, out_out_frame=b, coordinate_space='output')
            if key == 'text_tracks':
                timing = [item.get(k, 0) for k in ('fade_in_frames', 'stable_hold_frames', 'fade_out_frames')]
                if any(type(v) is not int or v < 0 for v in timing) or sum(timing) > b - a:
                    raise ValueError('Text fade and hold exceed display range')
            result.append(item)
        compiled_tracks[key] = result

    render_options = project.get('render_options', {})
    tools = project.get('tool_versions', {})
    tools_known = isinstance(tools, dict) and bool(tools)
    unit_keys = {}
    unit_cache_reusable = {}
    for e in events:
        fields = ['kind', 'source_id', 'source_version', 'source_in_ms', 'source_out_ms', 'speed', 'crop', 'scale', 'card_asset', 'background']
        recipe = {k: e.get(k) for k in fields}
        reusable = tools_known
        if e.get('kind') == 'source':
            # Exact source-time mapping is part of the media identity for precise cuts.
            recipe['source_time_mapping'] = e.get('source_time_mapping')
            reusable = reusable and bool(e.get('source_version')) and bool(e.get('source_time_mapping'))
        elif e.get('card_asset'):
            # External card assets need an explicit asset_version to be safely reusable.
            recipe['asset_version'] = e.get('asset_version')
            reusable = reusable and bool(e.get('asset_version'))
        recipe.update(
            frames=e['out_out_frame'] - e['out_in_frame'],
            width=width,
            height=height,
            fps=[n, d],
            options=render_options.get('video', {}),
            tools=tools,
        )
        unit_keys[e['event_id']] = digest(recipe)
        unit_cache_reusable[e['event_id']] = bool(reusable)
    layout = [{k: e[k] for k in ('event_id', 'out_in_frame', 'out_out_frame')} for e in events]
    clean_key = digest([unit_keys, layout, joins, render_options.get('video', {})])
    clean_reusable = tools_known and all(unit_cache_reusable.values())

    audio_dependencies = []
    audio_reusable = tools_known
    for track in compiled_tracks['audio_tracks']:
        if track.get('source_id'):
            sid = track['source_id']
            source = sources.get(sid, {})
            dependency = {'source_id': sid, 'version': source.get('version'), 'time_mapping': source.get('time_mapping')}
            audio_dependencies.append(dependency)
            if not source.get('version') or not isinstance(source.get('time_mapping'), dict) or not source.get('time_mapping'):
                audio_reusable = False
                warnings.append(f'audio source {sid} has unknown version/time_mapping: mix_audio and final cache reuse disabled')
        elif track.get('asset_ref'):
            dependency = {'asset_ref': track.get('asset_ref'), 'asset_version': track.get('asset_version')}
            audio_dependencies.append(dependency)
            if not track.get('asset_version'):
                audio_reusable = False
                warnings.append(f'audio asset {track.get("asset_ref")} has unknown asset_version: mix_audio and final cache reuse disabled')
        else:
            audio_dependencies.append({'generated_or_silent_track': track.get('track_id')})
    audio_key = digest([
        compiled_tracks['audio_tracks'], layout, joins, audio_dependencies,
        project.get('audio_policy'), render_options.get('audio', {}), tools, [n, d],
    ])

    # Card text is a final text-layer concern. Keep clean-video/audio caches reusable
    # when only card wording or card text rendering changes, but force the final
    # composited cache to change. Include explicit card_* render fields plus common
    # text-render fields so future renderer adapters do not silently reuse stale text.
    card_text_render_fields = {
        'font', 'font_file', 'font_family', 'font_size_px', 'font_size_value', 'font_unit',
        'color', 'text_color', 'position', 'align', 'alignment', 'line_spacing',
        'margin', 'motion', 'fade_in_frames', 'stable_hold_frames', 'fade_out_frames',
        'stroke', 'stroke_width', 'shadow', 'text_box', 'card_render', 'text_render',
    }
    card_text_layer = []
    for event in events:
        if event.get('kind') != 'card' or event.get('card_text') is None:
            continue
        card_item = {
            'event_id': event.get('event_id'),
            'card_text': event.get('card_text'),
        }
        for key, value in event.items():
            if key.startswith('card_') and key not in ('card_asset', 'card_text'):
                card_item[key] = value
            elif key in card_text_render_fields:
                card_item[key] = value
        card_text_layer.append(card_item)

    final_key = digest([
        clean_key, audio_key, compiled_tracks['text_tracks'], card_text_layer,
        render_options.get('final', {}), tools,
    ])
    final_reusable = bool(clean_reusable and audio_reusable and tools_known)
    if not tools_known:
        warnings.append('tool_versions empty: keys are planning identifiers; all cache reuse is disabled')

    quiet_ranges = project.get('expected_quiet_ranges', [])
    for q in quiet_ranges:
        a, b = q.get('start_frame'), q.get('end_frame')
        if type(a) is not int or type(b) is not int or not 0 <= a < b <= total or not q.get('reason'):
            raise ValueError('Expected quiet range needs valid output bounds and a reason')
    if quiet_ranges:
        warnings.append('Expected quiet ranges use absolute output positions; recheck after structural edits')

    compiled_budget = dict(budget) if isinstance(budget, dict) else {}
    compiled_budget.update(
        sum_event_frames=sum(r['length_frames'] for r in assembly_ranges),
        sum_transition_overlap_frames=sum(overlaps),
        computed_output_frames=total,
    )
    result = {
        'schema_version': '1.4',
        'timeline_status': timeline.get('status'),
        'render_authorized': project.get('render_authorized') is True,
        'render_allowed': not planning,
        'compilation_mode': 'planning' if planning else 'render',
        'eligibility': 'planning_only' if planning else 'validated_for_render',
        'execution_authorization_ref': project.get('execution_authorization_ref'),
        'execution_authorization_digest': project.get('execution_authorization_digest'),
        'playback_verified': False,
        'project_id': timeline.get('project_id'),
        'coordinate_space': 'output',
        'fps_num': n,
        'fps_den': d,
        'width': width,
        'height': height,
        'total_frames': total,
        'duration_budget': compiled_budget,
        'duration_seconds': total * d / n,
        'events': events,
        'joins': joins,
        **compiled_tracks,
        'audio_required': project.get('audio_required', True),
        'expected_quiet_ranges': quiet_ranges,
        'cache_keys': {'units': unit_keys, 'clean_video': clean_key, 'mix_audio': audio_key, 'final': final_key},
        'cache_reusable_by_layer': {
            'units': unit_cache_reusable,
            'clean_video': bool(clean_reusable),
            'mix_audio': bool(audio_reusable),
            'final': bool(final_reusable),
        },
        # Backward-compatible aggregate flag: whether the final output cache is safely reusable.
        'cache_reusable': bool(final_reusable),
        'warnings': warnings,
        'input_digest': project_inputs_digest(root),
    }
    result['manifest_digest'] = digest(result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project_directory', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--planning', action='store_true', help='Compile a planning-only manifest with render_allowed=false')
    args = parser.parse_args()
    try:
        manifest = compile_manifest(args.project_directory, planning=args.planning)
        destination = args.output or args.project_directory / 'render-manifest.json'
        destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'status': 'planning_only' if args.planning else 'compiled_not_rendered', 'render_allowed': manifest['render_allowed'], 'file': str(destination), 'frames': manifest['total_frames'], 'warnings': manifest['warnings']}, ensure_ascii=False))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({'status': 'error', 'error': str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
