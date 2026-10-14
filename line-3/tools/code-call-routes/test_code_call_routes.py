"""Proof rejection and route joins; synthetic bytecode exists only as test data."""
from pathlib import Path
import random
import subprocess
import sys
import unittest
import code_call_routes as tool

FOLDER = Path(__file__).resolve().parent


def evidence(token='zto'):
    return tool.calls.ancestry.read_json(FOLDER.parent / 'code-routes' / (token + '-proof.json'))


def scan(code):
    return tool.join(code, tool.calls.scan(code))


class JoinTests(unittest.TestCase):
    def test_real_proofs(self):
        for token, count in (('zto', 0), ('imd', 12)):
            result = tool.inspect(evidence(token))
            runtime = result['runtimes'][0]
            self.assertEqual(sum(runtime['call_route_counts'].values()), count)
            self.assertTrue(result['proof']['state_inclusion_verified'])
            self.assertFalse(result['reachability_verified'])
            self.assertFalse(result['external_target_code_verified'])
            self.assertFalse(result['anchor_authenticity_verified'])
            self.assertTrue(runtime['target_details_complete'])
            pcs = [hit['pc'] for hit in runtime['call_preview']]
            reference = tool.routes.scan(tool.calls.lens.code_bytes(
                evidence(token)['observation']['nodes'][0]['code']), pcs)['queried_pcs']
            self.assertEqual([hit['route_status'] for hit in runtime['call_preview']],
                             [hit['route_status'] for hit in reference])

    def test_halt_excludes_suffix_without_removing_calls(self):
        result = scan(bytes.fromhex('5f5afa005f5af1'))
        self.assertEqual(result['call_route_counts'], dict(zip(tool.STATUSES, (1, 0, 1))))

    def test_dynamic_jump_admits_jumpdest(self):
        result = scan(bytes.fromhex('3556005b5f5afa'))
        self.assertEqual(result['call_preview'][0]['route_status'], 'dynamic-target-candidate')
        self.assertTrue(result['dynamic_jump_expansion_used'])

    def test_constant_jump_skips_call(self):
        result = scan(bytes.fromhex('6008565f5af100005b5f5afa'))
        self.assertEqual([h['route_status'] for h in result['call_preview']],
                         ['excluded-by-model', 'direct-model-path'])

    def test_push_data_not_instructions(self):
        self.assertEqual(sum(scan(bytes.fromhex('63f1f2f4fa00'))['call_route_counts'].values()), 0)

    def test_preview_is_honestly_incomplete_counts_are_complete(self):
        result = scan(b'\x5f\x5a\xfa' * 100)
        self.assertEqual(sum(result['call_route_counts'].values()), 100)
        self.assertEqual(len(result['call_preview']), 64)
        self.assertEqual(result['omitted_call_count'], 36)
        self.assertFalse(result['target_details_complete'])

    def test_metadata_annotation_preserved(self):
        result = tool.inspect(evidence('imd'))['runtimes'][0]
        self.assertEqual(sum(result['metadata_call_route_counts'].values()), 1)
        self.assertTrue(result['call_preview'][-1]['overlaps_recognized_metadata'])

    def test_proof_and_anchor_corruption(self):
        bundle = evidence()
        bundle['header_rlp'] = bundle['header_rlp'][:-2] + 'ff'
        with self.assertRaises(ValueError):
            tool.inspect(bundle)
        with self.assertRaises(ValueError):
            tool.inspect(evidence(), '0x' + '11' * 32)

    def test_runtime_forgery_rejected(self):
        bundle = evidence()
        node = bundle['observation']['nodes'][0]
        code = bytes.fromhex('5f5afa')
        node.update(code='0x' + code.hex(), code_bytes=len(code),
                    code_hash=tool.calls.lens.digest(code))
        bundle['observation']['effective_code_hash'] = node['code_hash']
        with self.assertRaises(ValueError):
            tool.inspect(bundle)

    def test_random_join_matches_route_queries(self):
        rng = random.Random(34)
        for _ in range(100):
            code = bytes(rng.randrange(256) for _ in range(200))
            if code[0] == 0xef:
                continue
            result = scan(code)
            pcs = [hit['pc'] for hit in result['call_preview']]
            reference = tool.routes.scan(code, pcs)['queried_pcs']
            self.assertEqual([hit['route_status'] for hit in result['call_preview']],
                             [hit['route_status'] for hit in reference])

    def test_cli_refusal_has_no_stdout(self):
        result = subprocess.run([sys.executable, '-B', str(FOLDER / 'code_call_routes.py'),
                                 '--bundle', 'line-3/GOAL.md'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, '')


if __name__ == '__main__':
    unittest.main()
