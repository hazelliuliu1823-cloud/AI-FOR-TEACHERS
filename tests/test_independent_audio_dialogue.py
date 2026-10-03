"""Independent adopted source speech; all evidence and decisions are synthetic."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

import test_execution_integrity as h

PACKAGE = Path(__file__).resolve().parents[1]


class IndependentAudioDialogueTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.files = json.loads((PACKAGE / 'tests/fixtures/ready-project.json').read_text())
        self.save()
        self.baseline = h.compile_manifest(self.root)

    def save(self):
        h.write_fixture(self.root, self.files)
        return h.seal(self.root)

    def assertBlocked(self, text):
        report = h.validate(self.root)
        self.assertEqual(report['status'], 'fail', report)
        self.assertTrue(any(text in e for e in report['errors']), report['errors'])
        with self.assertRaises(ValueError):
            h.compile_manifest(self.root)
        with self.assertRaises(ValueError):
            h.check(self.root, self.baseline)

    def assertReady(self):
        report = h.validate(self.root)
        self.assertEqual(report['status'], 'pass', report['errors'])
        manifest = h.compile_manifest(self.root)
        self.assertTrue(manifest['render_allowed'])
        self.assertFalse(manifest['playback_verified'])
        self.assertEqual(h.check(self.root, manifest)['status'], 'pass')
        return manifest

    def card_speech(self, full=True):
        timeline = self.files['timeline.json']
        timeline['events'] = [{'event_id': 'C001', 'kind': 'card', 'out_in_frame': 0,
            'out_out_frame': 125, 'background': 'black', 'card_text': 'Synthetic quote'}]
        timeline['text_tracks'] = []
        track = timeline['audio_tracks'][0]
        track.update(source_in_ms=1300, source_out_ms=5500 if full else 3300,
                     anchor_event_id='C001', local_in_frame=0, local_out_frame=105 if full else 50)
        track.pop('sync_event_id', None)
        track.pop('sync_mode', None)
        self.files['transitions.json'] = []
        h.recalculate(self.files)
        return track

    def extra_speech(self, foreign=False, full=True):
        source = self.files['sources.json'][0]
        sid, a, b = 'SRC001', 17000, 19000
        if foreign:
            source = dict(source, source_id='SRC002', locator='synthetic-other.mp4')
            self.files['sources.json'].append(source)
            self.files['project.json']['source_scope'].append('SRC002')
            sid, a, b = 'SRC002', 1000, 4000
        sig, mapping = h.source_signature(source), h.time_mapping_digest(source)
        utterance = dict(self.files['transcript.jsonl'][0], utterance_id='T002', source_id=sid,
            start_ms=a, end_ms=b, text='Synthetic independent speech', source_signature=sig,
            time_mapping_digest=mapping, review_refs=['R002'])
        review = dict(self.files['reviews.jsonl'][0], review_id='R002', source_id=sid,
            start_ms=a, end_ms=b, modalities=['audio'], source_signature=sig, time_mapping_digest=mapping)
        self.files['transcript.jsonl'].append(utterance)
        self.files['reviews.jsonl'].append(review)
        x, y = (a, b) if full else (a + 500, a + 1500)
        track = dict(self.files['timeline.json']['audio_tracks'][0], track_id='A002', source_id=sid,
            source_in_ms=x, source_out_ms=y, local_in_frame=0, local_out_frame=(y-x)//40,
            source_signature=sig, time_mapping_digest=mapping, source_constraint_ref='source:'+sid,
            review_refs=['R002'], treatment_reason='Independent verified speech over the current picture')
        track.pop('sync_event_id', None)
        track.pop('sync_mode', None)
        self.files['timeline.json']['audio_tracks'].append(track)
        return track, utterance, review

    def test_card_complete_speech_is_allowed_without_video_sync(self):
        self.card_speech(); self.save(); self.assertReady()

    def test_card_half_sentence_is_blocked(self):
        self.card_speech(full=False); self.save(); self.assertBlocked('audio_required_range override')

    def test_card_muted_speech_is_blocked(self):
        self.card_speech()['muted'] = True
        self.save(); self.assertBlocked('muted, effectively silent')

    def test_card_silent_gain_is_blocked(self):
        self.card_speech()['gain_db'] = -80
        self.save(); self.assertBlocked('muted, effectively silent')

    def test_card_unknown_gain_is_blocked(self):
        self.card_speech()['gain_db'] = None
        self.save(); self.assertBlocked('gain unknown')

    def test_card_replaced_speech_is_blocked(self):
        self.card_speech()['treatment'] = 'replace'
        self.save(); self.assertBlocked('treatment removes/replaces')

    def test_card_music_label_cannot_hide_speech(self):
        self.card_speech().update(kind='music', narrative_role='emotional_music')
        self.save(); self.assertBlocked('original dialogue role')

    def test_card_fade_cannot_erase_sentence_tail(self):
        self.card_speech()['fade_out_ms'] = 40
        self.save(); self.assertBlocked('audio_required_range override')

    def test_card_invalid_fade_is_blocked(self):
        self.card_speech()['fade_in_ms'] = None
        self.save(); self.assertBlocked('finite audio fades required')

    def test_card_stale_utterance_binding_is_blocked_after_reconfirmation(self):
        self.card_speech()
        self.files['transcript.jsonl'][0]['source_signature'] = 'old-source'
        self.save(); self.assertBlocked('A001.utterance.T001: stale')

    def test_card_stale_mapping_is_blocked_after_reconfirmation(self):
        self.card_speech()
        self.files['transcript.jsonl'][0]['time_mapping_digest'] = 'old-mapping'
        self.save(); self.assertBlocked('A001.utterance.T001: stale')

    def test_card_utterance_unknown_review_is_blocked(self):
        self.card_speech()
        self.files['transcript.jsonl'][0]['review_refs'] = ['MISSING']
        self.save(); self.assertBlocked('utterance.T001: unknown review MISSING')

    def test_card_unverified_asr_is_blocked(self):
        self.card_speech()
        self.files['transcript.jsonl'][0].update(origin='asr', audio_verified=False)
        self.save(); self.assertBlocked('must be audio_verified')

    def test_full_track_review_does_not_replace_full_sentence_review(self):
        track = self.card_speech(full=False)
        self.files['reviews.jsonl'][0]['end_ms'] = 3300
        track['overrides'] = [h.override('audio_required_range', 1300, 5500, target='A001')]
        self.save(); self.assertBlocked('utterance.T001: successful audio reviews do not cover 1300-5500')

    def test_same_source_extra_half_sentence_is_blocked(self):
        self.extra_speech(full=False); self.save(); self.assertBlocked('A002: missing valid authorized')

    def test_same_source_extra_complete_speech_is_allowed(self):
        self.extra_speech(); self.save(); self.assertReady()

    def test_same_source_extra_stale_speech_is_blocked(self):
        _, utterance, _ = self.extra_speech()
        utterance['source_signature'] = 'old-source'
        self.save(); self.assertBlocked('A002.utterance.T002: stale')

    def test_other_source_audio_half_sentence_is_blocked(self):
        self.extra_speech(foreign=True, full=False)
        self.save(); self.assertBlocked('A002: missing valid authorized')

    def test_other_source_audio_complete_speech_is_allowed(self):
        self.extra_speech(foreign=True); self.save(); self.assertReady()

    def test_other_source_audio_stale_speech_is_blocked(self):
        _, utterance, _ = self.extra_speech(foreign=True)
        utterance['time_mapping_digest'] = 'old-mapping'
        self.save(); self.assertBlocked('A002.utterance.T002: stale')

    def test_other_source_audio_may_play_asynchronously(self):
        track, _, _ = self.extra_speech(foreign=True)
        track.update(local_in_frame=25, local_out_frame=100)
        self.save(); self.assertReady()

    def test_independent_speech_speed_may_differ_from_picture(self):
        self.card_speech().update(speed=2, local_out_frame=53)
        self.save(); self.assertReady()

    def test_explicit_empty_track_ids_cannot_hide_selected_speech(self):
        self.card_speech(full=False)['adopted_utterance_refs'] = []
        self.save(); self.assertBlocked('audio_required_range override')

    def test_unknown_explicit_track_utterance_is_blocked(self):
        self.card_speech()['adopted_utterance_refs'] = ['MISSING']
        self.save(); self.assertBlocked('unknown adopted utterance')

    def test_explicit_wrong_source_track_utterance_is_blocked(self):
        track, _, _ = self.extra_speech(foreign=True)
        track['adopted_utterance_refs'] = ['T001']
        self.save(); self.assertBlocked('adopted utterance source mismatch')

    def test_duplicate_explicit_track_utterances_are_blocked(self):
        self.card_speech()['adopted_utterance_refs'] = ['T001', 'T001']
        self.save(); self.assertBlocked('explicit unique array')

    def test_valid_track_sentence_cut_override_is_allowed(self):
        self.card_speech(full=False)['overrides'] = [h.override('audio_required_range', 1300, 5500, target='A001')]
        self.save(); self.assertReady()

    def test_track_cut_override_requires_matching_target(self):
        self.card_speech(full=False)['overrides'] = [h.override('audio_required_range', 1300, 5500, target='C001')]
        self.save(); self.assertBlocked('target_id does not match')

    def test_track_cut_override_requires_current_full_review(self):
        track = self.card_speech(full=False)
        self.files['reviews.jsonl'].append(dict(self.files['reviews.jsonl'][0], review_id='R002', end_ms=3300))
        track['overrides'] = [h.override('audio_required_range', 1300, 5500, target='A001', ref='R002')]
        self.save(); self.assertBlocked('override.audio_required_range: successful audio reviews do not cover')

    def test_track_cut_override_does_not_upgrade_stale_utterance(self):
        self.card_speech(full=False)['overrides'] = [h.override('audio_required_range', 1300, 5500, target='A001')]
        self.files['transcript.jsonl'][0]['source_signature'] = 'old-source'
        self.save(); self.assertBlocked('utterance.T001: stale')

    def test_independent_silence_with_confirmed_policy_reason_is_allowed(self):
        self.card_speech().update(muted=True, dialogue_policy_reason='Test director intentionally adopts a silent quote card')
        self.files['project.json']['audio_policy']['preserve_dialogue'] = False
        self.save(); self.assertReady()

    def test_independent_policy_change_requires_track_reason(self):
        self.card_speech()['muted'] = True
        self.files['project.json']['audio_policy']['preserve_dialogue'] = False
        self.save(); self.assertBlocked('confirmed dialogue_policy_reason')

    def test_policy_change_does_not_upgrade_stale_speech(self):
        self.card_speech().update(muted=True, dialogue_policy_reason='Synthetic confirmed silence')
        self.files['project.json']['audio_policy']['preserve_dialogue'] = False
        self.files['transcript.jsonl'][0]['source_signature'] = 'old-source'
        self.save(); self.assertBlocked('utterance.T001: stale')

    def test_card_utterance_change_invalidates_unchanged_confirmation(self):
        self.card_speech(); auth = self.save(); self.baseline = self.assertReady()
        self.files['transcript.jsonl'][0].update(source_signature='old-source', time_mapping_digest='old-mapping', review_refs=['MISSING'])
        h.write_fixture(self.root, {'transcript.jsonl': self.files['transcript.jsonl']})
        self.assertEqual(json.loads((self.root/'execution-authorization.json').read_text()), auth)
        self.assertBlocked('evidence/protection changed')

    def test_audio_only_utterance_review_change_invalidates_confirmation(self):
        self.card_speech()
        self.files['reviews.jsonl'].append(dict(self.files['reviews.jsonl'][0], review_id='R002'))
        self.files['transcript.jsonl'][0]['review_refs'] = ['R002']
        self.save(); self.baseline = self.assertReady()
        self.files['reviews.jsonl'][1]['evidence_locator'] = 'Changed audio-only utterance review'
        h.write_fixture(self.root, {'reviews.jsonl': self.files['reviews.jsonl']})
        self.assertBlocked('evidence/protection changed')

    def test_other_source_utterance_change_invalidates_confirmation(self):
        _, utterance, _ = self.extra_speech(foreign=True)
        self.save(); self.baseline = self.assertReady()
        utterance['text'] = 'Changed adopted synthetic transcript'
        h.write_fixture(self.root, {'transcript.jsonl': self.files['transcript.jsonl']})
        self.assertBlocked('evidence/protection changed')

    def test_compatible_tracks_preserve_one_sentence_across_cards(self):
        first = self.card_speech(full=False)
        timeline = self.files['timeline.json']
        timeline['events'][0]['out_out_frame'] = 50
        timeline['events'].append({'event_id': 'C002', 'kind': 'card', 'out_in_frame': 50,
            'out_out_frame': 125, 'card_text': 'Synthetic continuation'})
        timeline['audio_tracks'].append(dict(first, track_id='A002', source_in_ms=3300,
            source_out_ms=5500, anchor_event_id='C002', local_in_frame=0, local_out_frame=55))
        self.files['transitions.json'] = [{'from_event': 'C001', 'to_event': 'C002',
            'relation': 'chapter_change', 'effect': 'hard_cut', 'overlap_frames': 0}]
        h.recalculate(self.files)
        self.save(); self.assertReady()

    def test_different_output_occurrence_cannot_rescue_half_sentence(self):
        first = self.card_speech(full=False)
        self.files['timeline.json']['audio_tracks'].append(dict(first, track_id='A002',
            source_in_ms=1300, source_out_ms=5500, local_in_frame=20, local_out_frame=125))
        self.save(); self.assertBlocked('A001: missing valid authorized')

    def test_independent_source_audio_full_review_still_required(self):
        self.card_speech().update(source_in_ms=1000, source_out_ms=6000, local_out_frame=125)
        self.files['reviews.jsonl'][0].update(start_ms=1300, end_ms=5500)
        self.save(); self.assertBlocked('A001.source audio: successful audio reviews do not cover 1000-6000')

    def test_pure_non_dialogue_sound_retains_manual_continuity_boundary(self):
        self.card_speech(full=False).update(kind='music', narrative_role='emotional_music')
        self.files['transcript.jsonl'] = []
        self.files['units.jsonl'][0].update(utterance_ids=[], audio_state={'speech': False})
        self.save(); self.assertReady()


if __name__ == '__main__':
    unittest.main(verbosity=2)
