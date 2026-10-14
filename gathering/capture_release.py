#!/usr/bin/env python3
"""Capture a same-block ZTO code proof and balance rehearsal; read-only RPC only."""
import argparse
import datetime
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'shared/release-gate'))
import release_surface as glue

proof = glue.fresh.surface.surface.context.surface.proof
core = glue.gate.expiry.core
PUBLIC = 'https://ethereum-rpc.publicnode.com'
MANAGER = '0x000000000004444c5dc75cb358380d2e3de08a90'


def capture(relay=None):
    # Both evidence types use one route; this never claims provider independence.
    rpc = proof.ProofRPC(relay or PUBLIC)
    bundle = proof.collect(rpc, core.TOKENS['ZTO'])
    selected = rpc.call('eth_getBlockByNumber', [bundle['observation']['block']['number'], False])
    block = core.header(selected)
    core.require(block['hash'] == bundle['observation']['block']['hash'], 'proof block changed')

    class PinnedRPC(core.RPC):
        def call(self, method, params):
            if method == 'eth_getBlockByNumber' and params == ['finalized', False]:
                return selected
            return super().call(method, params)

    read_rpc = PinnedRPC(PUBLIC, relay=relay)
    tx = {'from': MANAGER, 'to': core.TOKENS['ZTO'],
          'data': '0x70a08231' + MANAGER[2:].rjust(64, '0'), 'value': '0x0'}
    observation = core.capture(read_rpc, tx, 'uint256')
    label = 'zto-manager-balance'
    evidence = {'schema': glue.gate.expiry.sets.EVIDENCE_SCHEMA,
                'observations': [{'id': label, 'observation': observation}]}
    plan = {'schema': glue.gate.expiry.sets.SCHEMA, 'chain_id': 1,
            'block': observation['block'], 'calls': [{'id': label, 'call': observation['call'],
            'expected_return': observation['outcome']['result']}]}
    now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    policy = {'schema': glue.gate.expiry.SCHEMA, 'as_of': hex(now),
              'max_age_seconds': 7200, 'plan': plan}
    request = {'schema': glue.gate.REQUEST_SCHEMA, 'member_id': label, 'call': tx}
    choices = {label: {'signature': 'balanceOf(address)', 'return_types': ['uint256']}}
    report = glue.evaluate(evidence, policy, request, choices, {label: bundle})
    return bundle, evidence, policy, request, report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--relay', help='optional worker-provided Ethereum loopback transport')
    parser.add_argument('--output', required=True, help='new directory within shared/release-gate')
    args = parser.parse_args(argv)
    output = core.workspace_path(args.output)
    core.require(output.is_relative_to(ROOT / 'shared/release-gate') and not output.exists(),
                 'output must be a new shared/release-gate directory')
    values = capture(args.relay)
    names = ('proof.json', 'evidence.json', 'policy.json', 'request.json', 'result.json')
    documents = {name: json.dumps(value, indent=2, allow_nan=False) + '\n'
                 for name, value in zip(names, values)}
    manifest = {'schema': 'set-surface-manifest-v1', 'members': [{
        'id': 'zto-manager-balance', 'signature': 'balanceOf(address)', 'return_types': ['uint256'],
        'proof': (output / 'proof.json').relative_to(ROOT).as_posix()}]}
    documents['manifest.json'] = json.dumps(manifest, indent=2) + '\n'
    core.require(all(len(text.encode()) < 100_000 for text in documents.values()), 'output exceeds 100 KB')
    output.mkdir()
    for name, text in documents.items():
        with (output / name).open('x', encoding='utf-8') as handle:
            handle.write(text)
    print(json.dumps({'verdict': values[-1]['verdict'], 'block': values[1]['observations'][0]
                     ['observation']['block'], 'source': PUBLIC,
                     'transport': 'contributor-relay' if args.relay else 'public-endpoint',
                     'provider_independence_established': False,
                     'unsigned_call_is_simulation_context': True}))
    return 0 if values[-1]['verdict'] == 'ready' else 2


if __name__ == '__main__':
    sys.exit(main())
