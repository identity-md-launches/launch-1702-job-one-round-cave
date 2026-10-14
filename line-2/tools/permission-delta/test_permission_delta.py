import copy
import sys
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'allowance-changes'))
import permission_delta as delta
import allowance_changes as changes


def observation(block, allowance='0', balance='10'):
    address = '0x1111111111111111111111111111111111111111'
    spender = '0x2222222222222222222222222222222222222222'
    return {'schema': 'allowance-lens-observation-v1', 'source': 'https://ethereum-rpc.publicnode.com',
            'chain_id': 1, 'token': 'ZTO', 'token_address': changes.lens.TOKENS['ZTO'],
            'block': {'number': hex(block), 'hash': '0x' + f'{block:064x}', 'timestamp': hex(block)},
            'query': {'mode': 'explicit_pairs', 'from_block': block, 'to_block': block,
                      'owner': address, 'spenders': [spender]}, 'logs': [], 'log_headers': {},
            'raw': {'decimals': '0x' + f'{18:064x}',
                    'balances': [{'owner': address, 'data': '0x70a08231' + '0' * 24 + address[2:],
                                  'result': '0x' + f'{int(balance):064x}'}],
                    'allowances': [{'owner': address, 'spender': spender,
                                    'data': '0xdd62ed3e' + '0' * 24 + address[2:] + '0' * 24 + spender[2:],
                                    'result': '0x' + f'{int(allowance):064x}'}]}}


class PermissionDeltaTests(unittest.TestCase):
    def test_increase_is_review_now(self):
        result = delta.digest(observation(1, '0'), observation(2, '7'))
        self.assertEqual(result['decision'], 'review_permission_change')
        self.assertEqual(result['review_items'][0]['priority'], 'review_now')
        self.assertEqual(result['review_items'][0]['change'], 'became_active')

    def test_reduction_is_confirmation_not_silence(self):
        result = delta.digest(observation(1, '9'), observation(2, '4'))
        self.assertEqual(result['decision'], 'confirm_reduction')
        self.assertEqual(result['review_items'][0]['priority'], 'confirm_change')

    def test_balance_change_without_permission_is_context(self):
        result = delta.digest(observation(1, '9', '10'), observation(2, '9', '4'))
        self.assertEqual(result['decision'], 'no_permission_change_measured')
        self.assertEqual(result['review_items'][0]['priority'], 'balance_context')

    def test_missing_after_pair_is_coverage_incomplete(self):
        after = observation(2, '0')
        other = '0x3333333333333333333333333333333333333333'
        owner = after['query']['owner']
        after['query']['spenders'] = [other]
        after['raw']['allowances'][0].update({
            'spender': other,
            'data': '0xdd62ed3e' + '0' * 24 + owner[2:] + '0' * 24 + other[2:],
        })
        result = delta.digest(observation(1, '9'), after)
        self.assertEqual(result['decision'], 'coverage_incomplete')
        self.assertEqual(result['review_items'][0]['priority'], 'coverage_review')

    def test_inputs_not_mutated(self):
        before, after = observation(1, '0'), observation(2, '2')
        old_before, old_after = copy.deepcopy(before), copy.deepcopy(after)
        delta.digest(before, after)
        self.assertEqual(before, old_before)
        self.assertEqual(after, old_after)


if __name__ == '__main__':
    unittest.main()
