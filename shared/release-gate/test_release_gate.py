"""Offline replay and refusal tests for Release Gate; no network use."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import release_gate as tool


class ReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.evidence = tool.expiry.sets.binding.read_json(
            tool.HERE.parent / 'rehearsal-set' / 'zto-set-evidence.json')
        self.policy = tool.expiry.sets.binding.read_json(
            tool.HERE.parent / 'set-expiry' / 'zto-set-expiry-policy.json')
        self.request = tool.expiry.sets.binding.read_json(tool.HERE / 'zto-release-request.json')

    def run_gate(self):
        return tool.evaluate(self.evidence, self.policy, self.request)

    def test_real_zto_request_is_ready(self):
        result = self.run_gate()
        self.assertEqual(result['verdict'], 'ready')
        self.assertEqual(result['member_id'], 'zto-supply')
        self.assertEqual(result['unsigned_call'], self.request['call'])
        self.assertEqual(result['set_expiry']['verdict'], 'fresh')

    def test_all_call_fields_are_bound(self):
        for field, value in (('to', '0xd34a99bc0f67ae1bbd63c660e6d0b0dd03e263b7'),
                             ('from', '0xd782bdea4ef02a0bd391eb9089470c8080f0a68e'),
                             ('data', '0x'), ('value', '0x1')):
            with self.subTest(field=field):
                altered = copy.deepcopy(self.request)
                altered['call'][field] = value
                result = tool.evaluate(self.evidence, self.policy, altered)
                self.assertEqual(result['verdict'], 'mismatch')
                self.assertEqual(result['differences'][0]['field'], field)

    def test_unknown_member_refuses_even_if_call_matches_another(self):
        self.request['member_id'] = 'not-reviewed'
        self.assertEqual(self.run_gate()['verdict'], 'mismatch')

    def test_expired_matching_set_is_not_ready(self):
        timestamp = int(self.policy['plan']['block']['timestamp'], 16)
        self.policy['as_of'] = hex(timestamp + self.policy['max_age_seconds'] + 1)
        self.assertEqual(self.run_gate()['verdict'], 'expired')

    def test_set_mismatch_propagates(self):
        self.evidence['observations'][0]['observation']['outcome']['result'] = '0x' + '00' * 32
        self.assertEqual(self.run_gate()['verdict'], 'mismatch')

    def test_incomplete_set_is_inconclusive(self):
        self.evidence['observations'].pop()
        self.assertEqual(self.run_gate()['verdict'], 'inconclusive')

    def test_request_schema_is_strict(self):
        for changed in ({'schema': tool.REQUEST_SCHEMA, 'member_id': 'zto-supply'},
                        {'schema': 'bad', 'member_id': 'zto-supply', 'call': self.request['call']},
                        {'schema': tool.REQUEST_SCHEMA, 'member_id': 'ZTO', 'call': self.request['call']},
                        {'schema': tool.REQUEST_SCHEMA, 'member_id': 'zto-supply',
                         'call': {'to': self.request['call']['to']}}):
            with self.subTest(changed=changed):
                with self.assertRaises(ValueError):
                    tool.request(changed)

    def test_inputs_are_not_changed(self):
        before = copy.deepcopy((self.evidence, self.policy, self.request))
        self.run_gate()
        self.assertEqual((self.evidence, self.policy, self.request), before)

    def test_demo_never_uses_network(self):
        with patch.object(tool.expiry.core.RPC, 'call', side_effect=AssertionError('network forbidden')):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(tool.main(['demo']), 0)
        self.assertEqual(json.loads(output.getvalue())['verdict'], 'ready')

    def test_cli_check_and_bad_request_exit(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temp:
            directory = Path(temp)
            evidence, policy, request = (directory / 'e.json', directory / 'p.json', directory / 'r.json')
            evidence.write_text(json.dumps(self.evidence))
            policy.write_text(json.dumps(self.policy))
            request.write_text(json.dumps(self.request))
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(tool.main(['gate', str(evidence), str(policy), str(request)]), 0)
            self.assertEqual(json.loads(output.getvalue())['verdict'], 'ready')
            request.write_text('{"schema":"bad"}')
            with contextlib.redirect_stderr(io.StringIO()) as errors:
                self.assertEqual(tool.main(['gate', str(evidence), str(policy), str(request)]), 2)
            self.assertEqual(json.loads(errors.getvalue())['verdict'], 'inconclusive')


if __name__ == '__main__':
    unittest.main()
