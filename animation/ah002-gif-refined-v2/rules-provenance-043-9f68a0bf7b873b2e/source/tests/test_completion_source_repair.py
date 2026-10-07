"""An art revision must retain exact replay data, including sort measurements."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from repair_completion_source_043 import verify_art_only_change


class ArtOnlyRepairTests(unittest.TestCase):
    def setUp(self):
        self.before = {
            'levelId': 43, 'image': 'old.png', 'artRevision': 'old',
            'paintedAnimation': {'parts': [{'rect': [0.7, 0.1, 0.1, 0.2]}]},
            'pieces': [{'detail': 0.00676139405475061, 'vertices': [[0, 0], [1, 0], [0, 1]]}],
            'geometry': {'revision': 3, 'detailSource': {'resource': 'historical.png'}},
            'timerSeconds': 180,
        }

    def test_art_relocation_and_master_change_preserve_rules(self):
        after = copy.deepcopy(self.before)
        after['image'] = 'repaired.png'
        after['artRevision'] = 'repair'
        after['paintedAnimation']['parts'][0]['rect'][0] -= 0.01
        self.assertEqual(verify_art_only_change(self.before, after),
                         verify_art_only_change(self.before, self.before))

    def test_same_order_detail_change_is_still_rejected(self):
        after = copy.deepcopy(self.before)
        after['pieces'][0]['detail'] = 0.00766968158886347
        with self.assertRaisesRegex(ValueError, 'immutable rules'):
            verify_art_only_change(self.before, after)

    def test_current_image_must_not_replace_historical_detail_provenance(self):
        after = copy.deepcopy(self.before)
        after['geometry']['detailSource']['resource'] = 'repaired.png'
        with self.assertRaisesRegex(ValueError, 'immutable rules'):
            verify_art_only_change(self.before, after)

    def test_unrelated_gameplay_change_is_rejected(self):
        after = copy.deepcopy(self.before)
        after['timerSeconds'] = 181
        with self.assertRaisesRegex(ValueError, 'immutable rules'):
            verify_art_only_change(self.before, after)


if __name__ == '__main__':
    unittest.main()
