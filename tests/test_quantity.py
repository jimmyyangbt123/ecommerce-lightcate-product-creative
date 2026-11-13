import importlib.util
from pathlib import Path
import unittest

# Run tests against the installed source while developing, the bundled copy after export.
import os
ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('TEMU_SKILL_SOURCE', str(ROOT / 'skills' / 'temu-product-creative')))
spec = importlib.util.spec_from_file_location('check_delivery', SOURCE / 'scripts' / 'check_delivery.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class QuantityContractTests(unittest.TestCase):
    def document(self, counts, title, header):
        return {'listings': [{'id': 'L1', 'pack_counts': counts, 'title': title, 'cover_header': header}]}

    def test_single_and_multiple_actual_options(self):
        for counts, token in [([1], '1pc'), ([2], '2pc'), ([4, 1, 2], '1/2/4pc')]:
            with self.subTest(counts=counts):
                self.assertEqual(module.validate(self.document(counts, token+' Camping Light', token+' HANG & GO')), [])

    def test_quantity_only_at_end_of_title_fails(self):
        errors = module.validate(self.document([1], 'Camping Light, 1pc', '1pc CAMP LIGHT'))
        self.assertTrue(any('title' in error for error in errors))

    def test_single_prefix_cannot_represent_multiple_options(self):
        self.assertTrue(module.validate(self.document([1, 2, 4], '1pc Camping Light', '1/2/4pc CAMP')))

    def test_minimum_option_must_not_be_omitted(self):
        self.assertTrue(module.validate(self.document([1, 2, 4], '2/4pc Light', '2/4pc CAMP')))

    def test_cover_must_use_exact_prefix_not_longhand(self):
        self.assertTrue(module.validate(self.document([1, 2, 4], '1/2/4pc Light', 'CHOOSE 1, 2 OR 4 LAMPS')))

    def test_invalid_counts_rejected(self):
        for counts in [[], [0], [-1], [True], ['1'], [1.5], [1, 1]]:
            with self.subTest(counts=counts):
                self.assertTrue(module.validate(self.document(counts, '1pc Light', '1pc CAMP')))

    def test_missing_fields_and_empty_manifest_rejected(self):
        for doc in [{}, {'listings': []}, {'listings': [{}]}, {'listings': [None]}, []]:
            with self.subTest(doc=doc):
                self.assertTrue(module.validate(doc))

    def test_prefix_needs_word_boundary(self):
        self.assertTrue(module.validate(self.document([1], '1pcLight', '1pc CAMP')))

    def test_each_listing_has_its_own_actual_counts(self):
        doc = self.document([1], '1pc Light', '1pc CAMP')
        doc['listings'].append({'id': 'L2', 'pack_counts': [2, 4], 'title': '2/4pc Lamps', 'cover_header': '2/4pc HOME'})
        self.assertEqual(module.validate(doc), [])
        doc['listings'][1]['title'] = '1/2/4pc Lamps'
        self.assertTrue(module.validate(doc))

    def test_duplicate_listing_ids_rejected(self):
        doc = self.document([1], '1pc Light', '1pc CAMP')
        doc['listings'].append(dict(doc['listings'][0]))
        self.assertTrue(module.validate(doc))


class CommandLineTests(unittest.TestCase):
    def run_document(self, text):
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            path.write_text(text, encoding='utf-8')
            return subprocess.run([__import__('sys').executable, str(SOURCE / 'scripts' / 'check_delivery.py'), str(path)], capture_output=True, text=True)

    def test_valid_input_exit_zero(self):
        result = self.run_document('{"listings":[{"id":"L1","pack_counts":[1],"title":"1pc Light","cover_header":"1pc LIGHT"}]}')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_wrong_prefix_exit_one(self):
        result = self.run_document('{"listings":[{"id":"L1","pack_counts":[1],"title":"Light 1pc","cover_header":"1pc LIGHT"}]}')
        self.assertEqual(result.returncode, 1)
        self.assertIn('title', result.stderr)

    def test_malformed_json_exit_two(self):
        result = self.run_document('{broken json')
        self.assertEqual(result.returncode, 2)

    def test_missing_argument_exit_two(self):
        import subprocess
        result = subprocess.run([__import__('sys').executable, str(SOURCE / 'scripts' / 'check_delivery.py')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)


if __name__ == '__main__':
    unittest.main()
