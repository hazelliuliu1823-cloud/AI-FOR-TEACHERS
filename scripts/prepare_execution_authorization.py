#!/usr/bin/env python3
"""Prepare a DRAFT Direct 2 execution record. Never confirms or refreshes evidence."""
import argparse
import json
from pathlib import Path

from execution_integrity import (adopted_evidence_digest, constraint_digest, event_spec,
                                 file_digest, read_project, source_signature, time_mapping_digest)


def prepare(root):
    project, sources, units, observations, boundaries, reviews, timeline, transitions = read_project(root)
    path = root / 'transcript.jsonl'
    transcript = {r['utterance_id']: r for r in [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]} if path.exists() else {}
    selected = timeline.get('events', [])
    source_ids = {e.get('source_id') for e in selected if e.get('kind') == 'source'}
    source_ids.update(t.get('source_id') for t in timeline.get('audio_tracks', []) if t.get('source_id'))
    def decision_digest(ref):
        return file_digest(root / ref) if ref and (root / ref).is_file() else None
    result = {'schema_version': '1.0', 'authorization_id': None, 'version': 1,
        'status': 'draft', 'confirmed_by': None, 'project_id': project.get('project_id'),
        'project_version': project.get('version'),
        'execution_plan_digest': decision_digest(project.get('execution_plan_ref')),
        'narrative_direction_digest': decision_digest(project.get('narrative_direction_ref')),
        'selected_events': [e['event_id'] for e in selected], 'sequence': [e['event_id'] for e in selected],
        'allowed_units': sorted({e['unit_id'] for e in selected if e.get('kind') == 'source'}),
        'allowed_boundaries': sorted({e.get('adopted_boundary_ref') or e.get('edit_boundary_ref') for e in selected if e.get('kind') == 'source'}),
        'allowed_adjustments': {e['event_id']: [] for e in selected},
        'event_specs': {e['event_id']: event_spec(e) for e in selected},
        'audio_specs': {t['track_id']: t for t in timeline.get('audio_tracks', [])},
        'text_specs': timeline.get('text_tracks', []), 'transitions': transitions,
        'output': {k: timeline.get(k) for k in ('fps_num', 'fps_den', 'width', 'height')},
        'audio_policy': project.get('audio_policy'),
        'source_bindings': {sid: {'source_signature': source_signature(sources[sid]),
            'time_mapping_digest': time_mapping_digest(sources[sid]),
            'source_constraint_digest': constraint_digest(project, sources[sid])} for sid in sorted(source_ids) if sid in sources},
        'evidence_digest': adopted_evidence_digest(timeline, units, observations, boundaries, reviews, transitions, transcript)}
    if project.get('execution_reference_ref') or project.get('execution_package_policy') == 'plan_and_reference':
        result['execution_reference_digest'] = decision_digest(project.get('execution_reference_ref'))
    reference_assets = project.get('execution_reference_asset_refs', [])
    if not isinstance(reference_assets, list) or any(not isinstance(x, str) or not x.strip() for x in reference_assets):
        raise ValueError('execution_reference_asset_refs must be an array of paths')
    if reference_assets or project.get('execution_package_policy') == 'plan_and_reference':
        result['execution_reference_asset_digests'] = {ref: decision_digest(ref) for ref in reference_assets}
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project_directory', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        target = args.output or args.project_directory / 'execution-authorization.draft.json'
        if target.exists():
            raise ValueError('Output exists; choose a new draft filename rather than overwrite a decision')
        draft = prepare(args.project_directory)
        target.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'status': 'draft_only', 'file': str(target), 'render_allowed': False}, ensure_ascii=False))
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(json.dumps({'status': 'error', 'error': str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
