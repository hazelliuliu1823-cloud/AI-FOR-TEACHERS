"""Synthetic source/decision fixtures. No real video understanding is claimed."""
import copy
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / 'scripts'))
from compile_render_manifest import compile_manifest
from check_render_authorization import check
from execution_integrity import (adopted_evidence_digest, constraint_digest, digest,
                                 event_spec, file_digest, read_project, source_signature,
                                 time_mapping_digest)
from timeline_math import canonical_assembly_ranges, output_ranges_from_overlaps
from validate_project import validate
from prepare_execution_authorization import prepare


def write_fixture(root, files):
    for name, data in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if name.endswith('.csv'):
            with path.open('w', encoding='utf-8', newline='') as fh:
                writer = csv.DictWriter(fh, fieldnames=data['headers'])
                writer.writeheader()
                writer.writerows(data['rows'])
        elif name.endswith('.jsonl'):
            path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in data), encoding='utf-8')
        elif name.endswith('.json'):
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        else:
            path.write_text(data, encoding='utf-8')


def recalculate(files):
    timeline = files['timeline.json']
    ranges = canonical_assembly_ranges(timeline['events'], timeline['fps_num'], timeline['fps_den'])
    for event, row in zip(timeline['events'], ranges):
        event['out_in_frame'], event['out_out_frame'] = row['assembly_in_frame'], row['assembly_out_frame']
    overlaps = [0] + [t.get('overlap_frames', 0) for t in files['transitions.json']]
    out, total = output_ranges_from_overlaps(ranges, overlaps)
    timeline['duration_budget'].update(sum_event_frames=sum(r['length_frames'] for r in ranges),
        sum_transition_overlap_frames=sum(overlaps), computed_output_frames=total)
    return total


def seal(root, adjustments=None):
    """Only the test author confirms these synthetic plans. Never stamps evidence."""
    project, sources, units, observations, boundaries, reviews, timeline, transitions = read_project(root)
    transcript = {r['utterance_id']: r for r in [json.loads(x) for x in (root / 'transcript.jsonl').read_text().splitlines() if x.strip()]}
    ids = [e['event_id'] for e in timeline['events']]
    auth = {'schema_version': '1.0', 'authorization_id': 'AUTH-SYNTHETIC', 'version': 1,
        'status': 'confirmed', 'confirmed_by': 'synthetic-test-author', 'project_id': project['project_id'],
        'project_version': project['version'],
        'execution_plan_digest': file_digest(root / project['execution_plan_ref']),
        'narrative_direction_digest': file_digest(root / project['narrative_direction_ref']),
        'selected_events': ids, 'sequence': ids,
        'allowed_units': sorted({e['unit_id'] for e in timeline['events'] if e['kind'] == 'source'}),
        'allowed_boundaries': sorted({e['edit_boundary_ref'] for e in timeline['events'] if e['kind'] == 'source'}),
        'allowed_adjustments': adjustments or {eid: [] for eid in ids},
        'event_specs': {e['event_id']: event_spec(e) for e in timeline['events']},
        'audio_specs': {t['track_id']: t for t in timeline['audio_tracks']},
        'text_specs': timeline['text_tracks'], 'transitions': transitions,
        'output': {k: timeline[k] for k in ('fps_num', 'fps_den', 'width', 'height')},
        'audio_policy': project['audio_policy'],
        'source_bindings': {sid: {'source_signature': source_signature(s),
            'time_mapping_digest': time_mapping_digest(s), 'source_constraint_digest': constraint_digest(project, s)} for sid, s in sources.items()},
        'evidence_digest': adopted_evidence_digest(timeline, units, observations, boundaries, reviews, transitions, transcript)}
    (root / 'execution-authorization.json').write_text(json.dumps(auth, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    project['execution_authorization_digest'] = digest(auth)
    (root / 'project.json').write_text(json.dumps(project, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return auth


def override(rule, a, b, target='E001', ref='R001'):
    return {'override_id': f'OV-{rule}-{a}', 'target_id': target, 'type': 'audio_transition' if rule == 'audio_transition' else 'creative_exception',
        'target_range': {'source_id': 'SRC001', 'start_ms': a, 'end_ms': b},
        'violated_rule': rule, 'evidence_ref': ['review:' + ref],
        'reason': 'Synthetic creative exception for a specified source interval',
        'creative_decision': 'Test director explicitly adopts this treatment', 'approved_by': 'synthetic-test-author'}


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.files = json.loads((PACKAGE / 'tests/fixtures/ready-project.json').read_text(encoding='utf-8'))
        self.save()

    def save(self, reseal=True, adjustments=None):
        write_fixture(self.root, self.files)
        if reseal:
            seal(self.root, adjustments)

    def assertBlocked(self, text=None):
        report = validate(self.root)
        self.assertEqual(report['status'], 'fail', report)
        if text:
            self.assertTrue(any(text in err for err in report['errors']), report['errors'])
        with self.assertRaises(ValueError):
            compile_manifest(self.root)

    def assertReady(self):
        report = validate(self.root)
        self.assertEqual(report['status'], 'pass', report['errors'])
        manifest = compile_manifest(self.root)
        self.assertTrue(manifest['render_allowed'])
        self.assertFalse(manifest['playback_verified'])
        self.assertEqual(check(self.root, manifest)['status'], 'pass')
        return manifest

    def test_valid_ready_and_guard(self):
        self.assertEqual(self.assertReady()['total_frames'], 125)

    def test_preparation_only_creates_a_draft(self):
        draft = prepare(self.root)
        self.assertEqual(draft['status'], 'draft')
        self.assertIsNone(draft['confirmed_by'])
        self.assertEqual(draft['selected_events'], ['E001'])

    def test_missing_machine_authorization_blocks(self):
        (self.root / 'execution-authorization.json').unlink()
        self.assertBlocked('execution authorization')

    def test_unconfirmed_direct1(self):
        self.files['project.json']['narrative_direction_status'] = 'pending'
        self.save(); self.assertBlocked('narrative_direction_status')

    def test_unconfirmed_direct2(self):
        self.files['project.json']['execution_plan_status'] = 'pending'
        self.save(); self.assertBlocked('execution_plan_status')

    def test_missing_render_authorization(self):
        self.files['project.json']['render_authorized'] = False
        self.save(); self.assertBlocked('render_authorized')

    def test_draft_requires_explicit_planning(self):
        self.files['timeline.json']['status'] = 'draft'
        self.files['project.json']['render_authorized'] = False
        self.save()
        with self.assertRaises(ValueError): compile_manifest(self.root)
        manifest = compile_manifest(self.root, planning=True)
        self.assertFalse(manifest['render_allowed'])
        with self.assertRaises(ValueError): check(self.root, manifest)

    def test_detail_without_direct1_is_blocked_even_in_draft(self):
        self.files['timeline.json']['status'] = 'draft'
        self.files['project.json']['narrative_direction_status'] = 'not_provided'
        self.save(); self.assertBlocked('completed Detail Structure requires confirmed Direct 1')

    def test_source_version_stales_adopted_evidence(self):
        self.files['sources.json'][0]['version'] = 'synthetic-v2'
        self.save(); self.assertBlocked('stale or missing source/time-mapping binding')

    def test_mapping_change_stales_adopted_evidence(self):
        self.files['sources.json'][0]['time_mapping'] = {'type': 'offset', 'offset_ms': 100}
        self.save(); self.assertBlocked('stale or missing source/time-mapping binding')

    def test_source_outside_scope(self):
        self.files['project.json']['source_scope'] = ['SRC999']
        self.save(); self.assertBlocked('outside authorized source_scope')

    def test_video_outside_usable_union(self):
        self.files['sources.json'][0]['usable_ranges'] = [{'start_ms': 10000, 'end_ms': 20000, 'reason': 'Synthetic exclusion'}]
        self.save(); self.assertBlocked('outside usable_ranges')

    def test_audio_outside_usable_ranges(self):
        self.files['sources.json'][0]['usable_ranges'] = [{'start_ms': 1000, 'end_ms': 6000, 'reason': 'Only the selected video is usable'}]
        t = self.files['timeline.json']['audio_tracks'][0]
        t['source_in_ms'], t['source_out_ms'] = 0, 5000
        self.save(); self.assertBlocked('A001: selected range falls outside usable_ranges')

    def test_adjacent_usable_ranges_are_a_union(self):
        self.files['sources.json'][0]['usable_ranges'] = [{'start_ms': 0, 'end_ms': 3000, 'reason': 'First'}, {'start_ms': 3000, 'end_ms': 20000, 'reason': 'Second'}]
        self.save(); self.assertReady()

    def test_allowed_scope_enforced(self):
        self.files['sources.json'][0]['allowed_scope'] = [{'start_ms': 2000, 'end_ms': 6000}]
        self.save(); self.assertBlocked('outside allowed_scope')

    def test_excluded_range_enforced(self):
        self.files['sources.json'][0]['downstream_constraints'] = [{'type': 'exclude_range', 'start_ms': 2500, 'end_ms': 2800}]
        self.save(); self.assertBlocked('intersects excluded range')

    def test_source_constraint_ref_required(self):
        del self.files['timeline.json']['events'][0]['source_constraint_ref']
        self.save(); self.assertBlocked('source_constraint_ref')

    def test_failed_review_is_not_coverage(self):
        self.files['reviews.jsonl'][0]['result'] = 'failed'
        self.save(); self.assertBlocked('is unsuccessful')

    def test_review_requires_reviewer_and_locator(self):
        self.files['reviews.jsonl'][0]['evidence_locator'] = 'none'
        self.save(); self.assertBlocked('lacks reviewer/locator')

    def test_stale_review_does_not_pass_by_reconfirming_plan(self):
        self.files['reviews.jsonl'][0]['source_signature'] = 'obsolete'
        self.save(); self.assertBlocked('is unsuccessful, stale')

    def test_wrong_source_deep_observation(self):
        self.files['deep-observations.csv']['rows'][0]['source_id'] = 'SRC999'
        self.save(); self.assertBlocked('source mismatch')

    def test_adopted_pending_evidence(self):
        self.files['deep-observations.csv']['rows'][0]['evidence_status'] = 'pending'
        self.save(); self.assertBlocked('evidence_status must be supported/partial')

    def test_missing_evidence_binding(self):
        self.files['deep-observations.csv']['rows'][0]['source_signature'] = ''
        self.save(); self.assertBlocked('stale or missing source/time-mapping binding')

    def test_unadopted_contradiction_does_not_block(self):
        row = copy.deepcopy(self.files['deep-observations.csv']['rows'][0])
        row.update(observation_id='DO002', evidence_status='contradicted')
        self.files['deep-observations.csv']['rows'].append(row)
        self.save(); self.assertReady()

    def test_direct_unit_selection_controls_timeline(self):
        auth = json.loads((self.root / 'execution-authorization.json').read_text())
        auth['allowed_units'] = ['U999']
        self.update_auth(auth)
        self.assertBlocked('unit is not authorized')

    def test_direct_selected_events_control_timeline(self):
        auth = json.loads((self.root / 'execution-authorization.json').read_text())
        auth['selected_events'] = ['E999']
        self.update_auth(auth)
        self.assertBlocked('events not selected')

    def test_direct_sequence_controls_timeline(self):
        auth = json.loads((self.root / 'execution-authorization.json').read_text())
        auth['sequence'] = ['E999']
        self.update_auth(auth)
        self.assertBlocked('sequence differs')

    def update_auth(self, auth):
        (self.root / 'execution-authorization.json').write_text(json.dumps(auth))
        project = json.loads((self.root / 'project.json').read_text())
        project['execution_authorization_digest'] = digest(auth)
        (self.root / 'project.json').write_text(json.dumps(project))

    def test_changed_plan_requires_reconfirmation(self):
        (self.root / 'execution-plan.md').write_text('# Use a different source and story\n')
        self.assertBlocked('changed since confirmation')

    def test_constraints_changed_after_confirmation(self):
        path = self.root / 'sources.json'
        sources = json.loads(path.read_text())
        sources[0]['usable_ranges'][0]['end_ms'] = 10000
        path.write_text(json.dumps(sources))
        self.assertBlocked('source constraints changed')

    def test_changed_evidence_requires_reconfirmation(self):
        p = self.root / 'units.jsonl'
        unit = json.loads(p.read_text())
        unit['protected_ranges'][0]['reason'] = 'A materially different protection decision'
        p.write_text(json.dumps(unit) + '\n')
        self.assertBlocked('evidence/protection changed')

    def test_unauthorized_event_adjustment(self):
        data = json.loads((self.root / 'timeline.json').read_text())
        data['events'][0]['function'] = 'An unauthorized new narrative function'
        (self.root / 'timeline.json').write_text(json.dumps(data))
        self.assertBlocked('changes exceed Direct 2 allowed adjustments')

    def test_allowed_safe_trim(self):
        self.files['timeline.json']['text_tracks'] = []
        self.save(adjustments={'E001': ['trim_inside_safe_window']})
        data = json.loads((self.root / 'timeline.json').read_text())
        data['events'][0]['source_out_ms'] = 5960
        data['events'][0]['out_out_frame'] = 124
        data['audio_tracks'][0]['source_out_ms'] = 5960
        data['audio_tracks'][0]['local_out_frame'] = 124
        data['duration_budget'].update(sum_event_frames=124, computed_output_frames=124)
        (self.root / 'timeline.json').write_text(json.dumps(data))
        self.assertReady()

    def test_protected_dialogue_cannot_be_music(self):
        self.files['timeline.json']['audio_tracks'][0]['kind'] = 'music'
        self.save(); self.assertBlocked('cannot be replaced')

    def test_source_audio_duration_mismatch(self):
        self.files['timeline.json']['audio_tracks'][0]['source_out_ms'] = 3000
        self.save(); self.assertBlocked('audio duration does not match')

    def test_audio_sync_drift_is_blocked(self):
        t = self.files['timeline.json']['audio_tracks'][0]
        t['source_in_ms'], t['source_out_ms'] = 2000, 7000
        self.save(); self.assertBlocked('out of sync')

    def test_fade_may_not_erase_dialogue_tail(self):
        self.files['timeline.json']['audio_tracks'][0]['fade_out_ms'] = 1500
        self.save(); self.assertBlocked('audio_required_range override')

    def test_muted_dialogue_is_blocked(self):
        self.files['timeline.json']['audio_tracks'][0]['muted'] = True
        self.save(); self.assertBlocked('protected source audio is muted')

    def test_boundary_override_rejects_unrelated_review(self):
        self.creative_cut()
        review = copy.deepcopy(self.files['reviews.jsonl'][0])
        review.update(review_id='R002', start_ms=17000, end_ms=18000, modalities=['frames'], result='failed')
        self.files['reviews.jsonl'].append(review)
        self.files['timeline.json']['events'][0]['overrides'][0]['evidence_ref'] = ['review:R002']
        self.save(); self.assertBlocked('is unsuccessful')

    def test_successful_but_unrelated_review_does_not_release_override(self):
        self.creative_cut()
        review = copy.deepcopy(self.files['reviews.jsonl'][0])
        review.update(review_id='R002', start_ms=17000, end_ms=18000)
        self.files['reviews.jsonl'].append(review)
        self.files['timeline.json']['events'][0]['overrides'][0]['evidence_ref'] = ['review:R002']
        self.save(); self.assertBlocked('reviews do not cover')

    def creative_cut(self):
        event = self.files['timeline.json']['events'][0]
        event.update(source_out_ms=5600, boundary_override=True,
            boundary_override_reason='Synthetic director adopts an abrupt tail ending', boundary_override_review_refs=['R001'],
            overrides=[override('safe_out_window', 5600, 6200), override('boundary_must_keep', 1300, 5800), override('audio_required_range', 1300, 5800)])
        t = self.files['timeline.json']['audio_tracks'][0]
        t.update(source_out_ms=5600, local_out_frame=115)
        self.files['timeline.json']['text_tracks'][0].update(local_out_frame=115, stable_hold_frames=115)
        recalculate(self.files)

    def test_explicit_creative_tail_cut_is_allowed(self):
        self.creative_cut(); self.save(); self.assertReady()

    def test_placeholder_override_is_blocked(self):
        self.creative_cut()
        self.files['timeline.json']['events'][0]['overrides'][0]['creative_decision'] = 'none'
        self.save(); self.assertBlocked('creative_decision must be concrete')

    def test_override_does_not_exempt_unit_meaning(self):
        self.creative_cut()
        self.files['units.jsonl'][0]['protected_ranges'][0]['end_ms'] = 5700
        self.save(); self.assertBlocked('protected meaning range')

    def test_legal_j_cut(self):
        timeline = self.files['timeline.json']
        timeline['events'].insert(0, {'event_id': 'E000', 'kind': 'card', 'duration_ms': 1000, 'out_in_frame': 0, 'out_out_frame': 25, 'card_text': 'Synthetic lead-in'})
        event = timeline['events'][1]
        event.update(sync_mode='J_cut', overrides=[override('audio_transition', 1300, 5800)])
        timeline['audio_tracks'][0].update(source_in_ms=0, local_in_frame=-25, sync_mode='J_cut')
        self.files['transitions.json'] = [{'from_event': 'E000', 'to_event': 'E001', 'relation': 'chapter_change', 'effect': 'hard_cut', 'overlap_frames': 0}]
        recalculate(self.files); self.save(); self.assertReady()

    def test_legal_l_cut(self):
        timeline = self.files['timeline.json']
        timeline['events'].append({'event_id': 'E002', 'kind': 'card', 'duration_ms': 1000, 'out_in_frame': 125, 'out_out_frame': 150, 'card_text': 'Synthetic outro'})
        timeline['events'][0].update(sync_mode='L_cut', overrides=[override('audio_transition', 1300, 5800)])
        timeline['audio_tracks'][0].update(source_out_ms=7000, local_out_frame=150, sync_mode='L_cut')
        self.files['transitions.json'] = [{'from_event': 'E001', 'to_event': 'E002', 'relation': 'chapter_change', 'effect': 'hard_cut', 'overlap_frames': 0}]
        recalculate(self.files); self.save(); self.assertReady()

    def two_source_events(self):
        timeline = self.files['timeline.json']
        event = copy.deepcopy(timeline['events'][0])
        event.update(event_id='E002', audio_source_refs=['A002'])
        timeline['events'].append(event)
        audio = copy.deepcopy(timeline['audio_tracks'][0])
        audio.update(track_id='A002', anchor_event_id='E002', sync_event_id='E002')
        timeline['audio_tracks'].append(audio)
        self.files['transitions.json'] = [{'from_event': 'E001', 'to_event': 'E002', 'relation': 'comparison', 'effect': 'xfade', 'overlap_frames': 25}]
        recalculate(self.files)

    def test_protected_overlap_placeholder_is_blocked(self):
        self.two_source_events()
        self.files['transitions.json'][0]['overlap_protection_review'] = 'none'
        self.save(); self.assertBlocked('protected_overlap override')

    def test_concrete_authorized_protected_overlap_is_allowed(self):
        self.two_source_events()
        self.files['transitions.json'][0]['overrides'] = [override('protected_overlap', 5000, 5800, target='E001->E002'), override('protected_overlap', 1300, 2000, target='E001->E002')]
        self.save(); self.assertReady()

    def test_wrong_modality_overlap_review_is_blocked(self):
        self.two_source_events()
        self.files['reviews.jsonl'].append(dict(self.files['reviews.jsonl'][0], review_id='R002', modalities=['frames']))
        self.files['transitions.json'][0]['overrides'] = [override('protected_overlap', 5000, 5800, target='E001->E002', ref='R002'), override('protected_overlap', 1300, 2000, target='E001->E002')]
        self.save(); self.assertBlocked('successful video reviews do not cover')

    def test_card_duration_is_an_authorized_decision(self):
        timeline = self.files['timeline.json']
        timeline['events'].append({'event_id': 'E002', 'kind': 'card', 'out_in_frame': 125, 'out_out_frame': 150, 'card_text': 'Approved outro'})
        self.files['transitions.json'] = [{'from_event': 'E001', 'to_event': 'E002', 'relation': 'chapter_change', 'effect': 'hard_cut', 'overlap_frames': 0}]
        recalculate(self.files); self.save()
        path = self.root / 'timeline.json'
        changed = json.loads(path.read_text())
        changed['events'][1]['out_out_frame'] = 151
        changed['duration_budget'].update(sum_event_frames=151, computed_output_frames=151)
        path.write_text(json.dumps(changed))
        self.assertBlocked('card_duration_frames')

    def test_render_guard_rejects_changed_inputs(self):
        manifest = self.assertReady()
        (self.root / 'content-map.md').write_text('# New uncompiled content\n')
        with self.assertRaisesRegex(ValueError, 'inputs changed'): check(self.root, manifest)

    def test_render_guard_rejects_tampered_manifest(self):
        manifest = self.assertReady()
        manifest['audio_tracks'][0]['source_in_ms'] = 0
        with self.assertRaisesRegex(ValueError, 'content changed'): check(self.root, manifest)

    def test_text_only_changes_preserve_media_caches(self):
        before = self.assertReady()['cache_keys']
        self.files['timeline.json']['text_tracks'][0]['text'] = 'An explicitly reconfirmed revised caption'
        self.save()
        after = self.assertReady()['cache_keys']
        self.assertEqual(before['clean_video'], after['clean_video'])
        self.assertEqual(before['mix_audio'], after['mix_audio'])
        self.assertNotEqual(before['final'], after['final'])

    def test_fps_invalidates_audio_cache(self):
        before = self.assertReady()['cache_keys']['mix_audio']
        self.files['timeline.json']['fps_num'] = 50
        self.files['project.json']['output']['fps_num'] = 50
        self.files['timeline.json']['audio_tracks'][0]['local_out_frame'] = 250
        self.files['timeline.json']['text_tracks'][0].update(local_out_frame=250, stable_hold_frames=250)
        recalculate(self.files); self.save()
        self.assertNotEqual(before, self.assertReady()['cache_keys']['mix_audio'])

    def test_cumulative_quantization_and_invalid_overlap(self):
        events = [{'event_id': f'E{i}', 'kind': 'source', 'source_in_ms': 0, 'source_out_ms': 41} for i in range(100)]
        ranges = canonical_assembly_ranges(events, 25, 1)
        self.assertEqual(ranges[-1]['assembly_out_frame'], 103)
        with self.assertRaises(ValueError): output_ranges_from_overlaps(ranges[:2], [0, 100])


if __name__ == '__main__':
    unittest.main(verbosity=2)
