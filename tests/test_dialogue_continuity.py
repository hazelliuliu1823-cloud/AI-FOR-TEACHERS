"""Speech selection and full source-audio reviews; synthetic evidence only."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

import test_execution_integrity as helper


PACKAGE = Path(__file__).resolve().parents[1]


class DialogueContinuityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.files = json.loads((PACKAGE / 'tests/fixtures/ready-project.json').read_text())
        self.save()
        self.baseline = helper.compile_manifest(self.root)

    def save(self):
        helper.write_fixture(self.root, self.files)
        helper.seal(self.root)

    def assertBlocked(self, text):
        report = helper.validate(self.root)
        self.assertEqual(report['status'], 'fail', report)
        self.assertTrue(any(text in err for err in report['errors']), report['errors'])
        with self.assertRaises(ValueError):
            helper.compile_manifest(self.root)
        with self.assertRaises(ValueError):
            helper.check(self.root, self.baseline)

    def assertReady(self):
        report = helper.validate(self.root)
        self.assertEqual(report['status'], 'pass', report['errors'])
        manifest = helper.compile_manifest(self.root)
        self.assertTrue(manifest['render_allowed'])
        self.assertFalse(manifest['playback_verified'])
        self.assertEqual(helper.check(self.root, manifest)['status'], 'pass')
        return manifest

    def omit_whole_utterance(self):
        boundary = self.files['edit-boundaries.csv']['rows'][0]
        boundary.update(audio_start_ms='5700', audio_end_ms='5750', audio_tail_end_ms='5800',
                        dialogue_required_range='5700-5800')
        event = self.files['timeline.json']['events'][0]
        event.update(audio_boundary={'required_start_ms': 5700, 'required_end_ms': 5800},
                     dialogue_required_range='5700-5800')
        self.files['timeline.json']['audio_tracks'][0].update(source_in_ms=5700, local_in_frame=117)

    def second_utterance(self, start=5000, end=5500):
        utterance = copy.deepcopy(self.files['transcript.jsonl'][0])
        utterance.update(utterance_id='T002', start_ms=start, end_ms=end, text='Second synthetic expression')
        self.files['transcript.jsonl'].append(utterance)
        self.files['units.jsonl'][0]['utterance_ids'].append('T002')
        return utterance

    def long_l_cut(self):
        timeline = self.files['timeline.json']
        timeline['events'].append({'event_id': 'E002', 'kind': 'card', 'out_in_frame': 125,
                                  'out_out_frame': 400, 'card_text': 'Synthetic long outro'})
        timeline['events'][0].update(sync_mode='L_cut', overrides=[helper.override('audio_transition', 1300, 5800)])
        timeline['audio_tracks'][0].update(source_out_ms=17000, local_out_frame=400, sync_mode='L_cut')
        self.files['transitions.json'] = [{'from_event': 'E001', 'to_event': 'E002',
            'relation': 'chapter_change', 'effect': 'hard_cut', 'overlap_frames': 0}]
        helper.recalculate(self.files)

    def extension_review(self, start=8000, end=17000, **changes):
        review = dict(self.files['reviews.jsonl'][0], review_id='R002', start_ms=start,
                      end_ms=end, modalities=['audio'])
        review.update(changes)
        self.files['reviews.jsonl'].append(review)
        self.files['timeline.json']['audio_tracks'][0]['review_refs'] = ['R001', 'R002']
        return review

    def test_underdeclared_range_cannot_hide_whole_utterance(self):
        self.omit_whole_utterance()
        self.save(); self.assertBlocked('audio_required_range override')

    def test_empty_explicit_selection_cannot_hide_in_range_utterance(self):
        self.omit_whole_utterance()
        self.files['timeline.json']['events'][0]['adopted_utterance_refs'] = []
        self.save(); self.assertBlocked('audio_required_range override')

    def test_omitted_second_utterance_is_checked(self):
        self.files['transcript.jsonl'][0]['end_ms'] = 4000
        self.second_utterance()
        self.files['edit-boundaries.csv']['rows'][0].update(audio_end_ms='4300',
            audio_tail_end_ms='4500', dialogue_required_range='1300-4500')
        self.files['timeline.json']['events'][0].update(audio_boundary={'required_start_ms': 1300,
            'required_end_ms': 4500}, dialogue_required_range='1300-4500')
        self.files['timeline.json']['audio_tracks'][0].update(source_out_ms=4700, local_out_frame=93)
        self.save(); self.assertBlocked('audio_required_range override')

    def test_omitted_utterance_stale_binding_is_still_checked(self):
        self.omit_whole_utterance()
        self.files['transcript.jsonl'][0].update(source_signature='old-source', review_refs=['MISSING'])
        self.save(); self.assertBlocked('utterance.T001: stale')

    def test_omitted_utterance_missing_review_is_still_checked(self):
        self.omit_whole_utterance()
        self.files['transcript.jsonl'][0]['review_refs'] = ['MISSING']
        self.save(); self.assertBlocked('utterance.T001: unknown review')

    def test_omitted_asr_cannot_claim_unheard_transcript(self):
        self.omit_whole_utterance()
        self.files['transcript.jsonl'][0].update(origin='asr', asr_role='verified_transcript',
                                                audio_verified=False, review_refs=['MISSING'])
        self.save(); self.assertBlocked('utterance.T001: adopted utterance must be audio_verified')

    def test_audio_verified_false_is_blocked_even_with_valid_review(self):
        self.files['transcript.jsonl'][0]['audio_verified'] = False
        self.save(); self.assertBlocked('adopted utterance must be audio_verified')

    def test_unknown_explicit_utterance_is_blocked(self):
        self.files['timeline.json']['events'][0]['adopted_utterance_refs'] = ['MISSING']
        self.save(); self.assertBlocked('unknown adopted utterance')

    def test_duplicate_explicit_utterances_are_blocked(self):
        self.files['timeline.json']['events'][0]['adopted_utterance_refs'] = ['T001', 'T001']
        self.save(); self.assertBlocked('explicit unique array')

    def test_wrong_source_explicit_utterance_is_blocked(self):
        self.second_utterance().update(source_id='OTHER')
        self.files['timeline.json']['events'][0]['adopted_utterance_refs'] = ['T001', 'T002']
        self.save(); self.assertBlocked('adopted utterance source mismatch')

    def test_scene_type_cannot_mute_preserved_dialogue(self):
        self.files['edit-boundaries.csv']['rows'][0]['continuity_type'] = 'scene'
        self.files['timeline.json']['audio_tracks'][0]['muted'] = True
        self.save(); self.assertBlocked('protected source audio is muted')

    def test_known_in_range_speech_survives_missing_unit_references(self):
        self.files['units.jsonl'][0]['utterance_ids'] = []
        self.files['timeline.json']['events'][0]['adopted_utterance_refs'] = []
        self.files['edit-boundaries.csv']['rows'][0]['continuity_type'] = 'scene'
        self.files['timeline.json']['audio_tracks'][0]['muted'] = True
        self.save(); self.assertBlocked('protected source audio is muted')

    def test_scene_type_cannot_remove_all_dialogue_tracks(self):
        self.files['edit-boundaries.csv']['rows'][0]['continuity_type'] = 'scene'
        self.files['timeline.json']['events'][0]['audio_source_refs'] = []
        self.save(); self.assertBlocked('audio_source_refs must identify')

    def test_action_type_cannot_mute_preserved_dialogue(self):
        boundary = self.files['edit-boundaries.csv']['rows'][0]
        boundary.update(continuity_type='action', action_start_ms='1500', action_end_ms='5500',
                        reaction_or_settle_end_ms='5800')
        self.files['timeline.json']['audio_tracks'][0]['muted'] = True
        self.save(); self.assertBlocked('protected source audio is muted')

    def test_scene_type_with_preserved_speech_is_legal(self):
        self.files['edit-boundaries.csv']['rows'][0]['continuity_type'] = 'scene'
        self.save(); self.assertReady()

    def test_speech_metadata_triggers_protection_without_transcript_ids(self):
        self.files['units.jsonl'][0].update(utterance_ids=[], audio_state={'speech': True})
        self.files['timeline.json']['events'][0]['adopted_utterance_refs'] = []
        self.files['edit-boundaries.csv']['rows'][0]['continuity_type'] = 'scene'
        self.files['timeline.json']['audio_tracks'][0]['muted'] = True
        self.save(); self.assertBlocked('protected source audio is muted')

    def test_explicit_policy_change_allows_confirmed_intentional_silence(self):
        self.files['project.json']['audio_policy']['preserve_dialogue'] = False
        self.files['project.json']['source_audio_policy'] = 'intentional_silence'
        self.files['timeline.json']['events'][0]['dialogue_policy_reason'] = 'Confirmed synthetic silent montage'
        self.files['timeline.json']['audio_tracks'][0]['muted'] = True
        self.save(); self.assertReady()

    def test_policy_change_without_reason_is_blocked(self):
        self.files['project.json']['audio_policy']['preserve_dialogue'] = False
        self.files['timeline.json']['audio_tracks'][0]['muted'] = True
        self.save(); self.assertBlocked('dialogue_policy_reason')

    def test_unadopted_out_of_selection_utterance_is_not_forced_into_edit(self):
        self.second_utterance(start=6500, end=7000).update(audio_verified=False,
            source_signature='unreviewed-candidate', review_refs=[])
        self.save(); self.assertReady()

    def test_explicit_out_of_selection_adoption_is_checked(self):
        self.second_utterance(start=6500, end=7000).update(source_signature='old-source')
        self.files['timeline.json']['events'][0]['adopted_utterance_refs'].append('T002')
        self.save(); self.assertBlocked('utterance.T002: stale')

    def test_valid_creative_sentence_removal_is_allowed(self):
        self.omit_whole_utterance()
        self.files['timeline.json']['events'][0]['overrides'] = [helper.override('audio_required_range', 1300, 5500)]
        self.save(); self.assertReady()

    def test_sentence_removal_override_cannot_use_unrelated_review(self):
        self.omit_whole_utterance()
        review = dict(self.files['reviews.jsonl'][0], review_id='R002', start_ms=17000, end_ms=18000)
        self.files['reviews.jsonl'].append(review)
        self.files['timeline.json']['events'][0]['overrides'] = [helper.override('audio_required_range', 1300, 5500, ref='R002')]
        self.save(); self.assertBlocked('reviews do not cover')

    def test_l_cut_unreviewed_extension_is_blocked(self):
        self.long_l_cut()
        self.save(); self.assertBlocked('source audio: successful audio reviews do not cover 1000-17000')

    def test_l_cut_reviewed_extension_is_legal(self):
        self.long_l_cut(); self.extension_review()
        self.save(); self.assertReady()

    def test_l_cut_one_ms_review_gap_is_blocked(self):
        self.long_l_cut(); self.extension_review(start=8001)
        self.save(); self.assertBlocked('source audio: successful audio reviews do not cover')

    def test_l_cut_review_overlap_is_legal(self):
        self.long_l_cut(); self.extension_review(start=7900)
        self.save(); self.assertReady()

    def test_l_cut_extension_review_must_have_audio_modality(self):
        self.long_l_cut(); self.extension_review(modalities=['video'])
        self.save(); self.assertBlocked('source audio: successful audio reviews do not cover')

    def test_l_cut_failed_extension_review_is_blocked(self):
        self.long_l_cut(); self.extension_review(result='failed')
        self.save(); self.assertBlocked('source audio: review R002 is unsuccessful')

    def test_l_cut_stale_extension_review_is_blocked(self):
        self.long_l_cut(); self.extension_review(source_signature='old-source')
        self.save(); self.assertBlocked('source audio: review R002 is unsuccessful')

    def test_source_audio_without_explicit_reviews_is_blocked(self):
        self.files['timeline.json']['audio_tracks'][0].pop('review_refs')
        self.save(); self.assertBlocked('source audio requires explicit unique review_refs')

    def test_l_cut_missing_extension_review_id_is_blocked(self):
        self.long_l_cut()
        self.files['timeline.json']['audio_tracks'][0]['review_refs'] = ['R001', 'MISSING']
        self.save(); self.assertBlocked('source audio: unknown review MISSING')

    def test_j_cut_unreviewed_lead_in_is_blocked(self):
        timeline = self.files['timeline.json']
        timeline['events'].insert(0, {'event_id': 'E000', 'kind': 'card', 'out_in_frame': 0,
            'out_out_frame': 25, 'card_text': 'Synthetic lead-in'})
        timeline['events'][1].update(sync_mode='J_cut', overrides=[helper.override('audio_transition', 1300, 5800)])
        timeline['audio_tracks'][0].update(source_in_ms=0, local_in_frame=-25, sync_mode='J_cut')
        self.files['reviews.jsonl'][0]['start_ms'] = 1000
        self.files['transitions.json'] = [{'from_event': 'E000', 'to_event': 'E001',
            'relation': 'chapter_change', 'effect': 'hard_cut', 'overlap_frames': 0}]
        helper.recalculate(self.files)
        self.save(); self.assertBlocked('source audio: successful audio reviews do not cover 0-6000')

    def test_track_only_review_change_invalidates_evidence_confirmation(self):
        self.long_l_cut(); self.extension_review()
        self.save(); self.assertReady()
        path = self.root / 'reviews.jsonl'
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows[1]['evidence_locator'] = 'Different synthetic review record'
        path.write_text(''.join(json.dumps(row) + '\n' for row in rows))
        self.assertBlocked('evidence/protection changed')

    def test_creative_override_cannot_upgrade_unreviewed_source_audio(self):
        self.long_l_cut()
        self.files['timeline.json']['events'][0]['overrides'].append(helper.override('audio_required_range', 1300, 5800))
        self.save(); self.assertBlocked('source audio: successful audio reviews do not cover')


if __name__ == '__main__':
    unittest.main(verbosity=2)
