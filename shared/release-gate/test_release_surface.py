"""Historical real-evidence integration, complete-set refusal and strict CLI tests."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import release_surface as tool


class ReleaseSurfaceTests(unittest.TestCase):
    def setUp(self):
        self.evidence, self.policy, self.request, self.choices, self.proofs = tool.demo_inputs()
        self.label = self.request['member_id']
        self.block_time = int(self.policy['plan']['block']['timestamp'], 16)

    def check(self):
        return tool.evaluate(self.evidence, self.policy, self.request, self.choices, self.proofs)

    def withheld(self, result):
        self.assertEqual(result['verdict'], 'withheld')
        self.assertIsNone(result['unsigned_call'])
        self.assertIsNone(result['decoded_call'])
        self.assertNotIn('unsigned_call', result['release_gate'])

    def test_real_proof_and_call_release(self):
        result = self.check()
        self.assertEqual(result['verdict'], 'ready')
        self.assertEqual(result['unsigned_call'], self.request['call'])
        self.assertEqual(result['decoded_call']['returns'][0]['value'],
                         '285939607966355541747129965')
        self.assertEqual(result['decoded_call']['arguments'][0]['value'],
                         '0x000000000004444c5dc75cb358380d2e3de08a90')
        self.assertNotIn('unsigned_call', result['release_gate'])
        self.assertNotIn('decoded_calls', result['proof_context'])
        self.assertTrue(result['proof_context']['surface_context']['code_checks'][0]
                        ['state_inclusion_verified'])

    def test_each_request_field_bound_and_skips_proofs(self):
        original = copy.deepcopy(self.request)
        for field, value in (('from', '0xd782bdea4ef02a0bd391eb9089470c8080f0a68e'),
                             ('to', '0xd34a99bc0f67ae1bbd63c660e6d0b0dd03e263b7'),
                             ('data', '0x18160ddd'), ('value', '0x1')):
            self.request = copy.deepcopy(original)
            self.request['call'][field] = value
            with patch.object(tool.fresh, 'evaluate', side_effect=AssertionError('skip proof')):
                self.withheld(self.check())

    def test_unknown_member(self):
        self.request['member_id'] = 'unknown'
        self.withheld(self.check())

    def test_expiry_inclusive_then_withheld(self):
        self.policy['as_of'] = hex(self.block_time + self.policy['max_age_seconds'])
        self.assertEqual(self.check()['verdict'], 'ready')
        self.policy['as_of'] = hex(self.block_time + self.policy['max_age_seconds'] + 1)
        with patch.object(tool.fresh, 'evaluate', side_effect=AssertionError('skip proof')):
            result = self.check()
        self.withheld(result)
        self.assertEqual(result['release_gate']['verdict'], 'expired')

    def test_before_block(self):
        self.policy['as_of'] = hex(self.block_time - 1)
        self.withheld(self.check())

    def test_changed_return(self):
        self.policy['plan']['calls'][0]['expected_return'] = '0x'
        self.withheld(self.check())

    def test_complete_set_required(self):
        read = tool.gate.expiry.sets.binding.read_json
        self.evidence = read(tool.HERE.parent / 'rehearsal-set/zto-set-evidence.json')
        self.policy = read(tool.HERE.parent / 'set-expiry/zto-set-expiry-policy.json')
        self.request = read(tool.HERE / 'zto-release-request.json')
        # Missing any other member must withhold even a present selected call.
        self.evidence['observations'].pop()
        self.withheld(self.check())

    def test_same_block_required_for_code(self):
        number = hex(int(self.policy['plan']['block']['number'], 16) + 1)
        self.policy['plan']['block']['number'] = number
        self.evidence['observations'][0]['observation']['block']['number'] = number
        result = self.check()
        self.assertEqual(result['release_gate']['verdict'], 'ready')
        self.withheld(result)
        self.assertIn('same_block_number', result['proof_context']['surface_context']
                      ['code_checks'][0]['failed_checks'])

    def test_signature_mismatch(self):
        self.choices[self.label]['signature'] = 'totalSupply()'
        self.withheld(self.check())

    def test_proof_corruption(self):
        self.proofs[self.label]['header_rlp'] = '0x00'
        with self.assertRaises(ValueError):
            self.check()

    def test_all_decoder_and_proof_members_required(self):
        for choices, proofs in (({}, self.proofs), (self.choices, {})):
            with self.assertRaises(ValueError):
                tool.evaluate(self.evidence, self.policy, self.request, choices, proofs)

    def test_inputs_unchanged(self):
        inputs = (self.evidence, self.policy, self.request, self.choices, self.proofs)
        before = copy.deepcopy(inputs)
        self.check()
        self.assertEqual(inputs, before)

    def test_demo_network_disabled(self):
        with patch('socket.socket', side_effect=AssertionError('network forbidden')):
            for command, expected in (('demo', 0), ('expired-demo', 2)):
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(tool.main([command]), expected)
                report = json.loads(output.getvalue())
                if expected:
                    self.withheld(report)

    def test_explicit_cli_and_duplicate_path_rejection(self):
        scratch = Path('test/scratch'); scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            folder = Path(folder)
            manifest = {'schema': 'set-surface-manifest-v1', 'members': [{
                'id': self.label, 'signature': 'balanceOf(address)', 'return_types': ['uint256'],
                'proof': 'shared/surface-return/zto-proof.json'}]}
            paths = []
            for name, value in (('e', self.evidence), ('p', self.policy),
                                ('r', self.request), ('m', manifest)):
                path = folder / (name + '.json'); path.write_text(json.dumps(value)); paths.append(str(path))
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(tool.main(['check'] + paths), 0)
            self.assertEqual(json.loads(output.getvalue())['verdict'], 'ready')
            (folder / 'r.json').write_text('{"schema":"x","schema":"x"}')
            with contextlib.redirect_stdout(io.StringIO()) as output, contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(tool.main(['check'] + paths), 1)
            self.assertEqual(output.getvalue(), '')
        with contextlib.redirect_stdout(io.StringIO()) as output, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(tool.main(['check', '../outside.json', 'missing', 'missing', 'missing']), 1)
        self.assertEqual(output.getvalue(), '')


if __name__ == '__main__':
    unittest.main()
