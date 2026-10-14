"""Real saved pool evidence and boundary checks for ZTO Target."""
import importlib.util
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('zto_target', HERE / 'zto_target.py')
target = importlib.util.module_from_spec(spec)
spec.loader.exec_module(target)


class TargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.observation = target.review.read_json(target.DEFAULT_SNAPSHOT)

    def test_exact_minimal_raw_unit_on_real_pool(self):
        result = target.find_target(self.observation, 'ZTO', '0.0001', '10', 100)
        self.assertEqual(result['status'], 'target_reached')
        self.assertEqual(result['minimum_input_raw'], '6605354095186351266')
        self.assertEqual(result['planning_minimum_output_raw'], result['target_output_raw'])
        self.assertEqual(int(result['previous_minimum_output_raw']),
                         int(result['target_output_raw']) - 1)
        self.assertEqual(result['coverage_status'], 'ceiling_reached')

    def test_target_above_chosen_ceiling(self):
        result = target.find_target(self.observation, 'ZTO', '0.0001', '1', 100)
        self.assertEqual(result['status'], 'target_unreachable_within_ceiling')
        self.assertNotIn('minimum_input_raw', result)

    def test_target_beyond_recorded_coverage(self):
        result = target.find_target(self.observation, 'ZTO', '10000', '1000000000', 100)
        self.assertEqual(result['status'], 'target_not_reached_in_coverage')
        self.assertEqual(result['coverage_status'], 'bounded')
        self.assertNotIn('minimum_input_raw', result)

    def test_first_nonzero_output_unit(self):
        result = target.find_target(self.observation, 'ZTO',
                                    '0.000000000000000001', '1', 0)
        self.assertEqual(result['minimum_input_raw'], '65394')
        self.assertEqual(result['previous_input_raw'], '65393')
        self.assertEqual(result['previous_minimum_output_raw'], '0')

    def test_reverse_direction_and_invalid_controls(self):
        result = target.find_target(self.observation, 'IMD', '1', '100', 50)
        self.assertEqual(result['status'], 'target_reached')
        self.assertEqual(result['output_token'], 'ZTO')
        for bad in (-1, 10000, True):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                target.find_target(self.observation, 'ZTO', '1', '10', bad)
        with self.assertRaises(ValueError):
            target.find_target(self.observation, 'ZTO', '0', '10', 100)
        with self.assertRaises(ValueError):
            target.find_target(self.observation, 'ZTO', '1', '0x10', 100)


if __name__ == '__main__':
    unittest.main()
