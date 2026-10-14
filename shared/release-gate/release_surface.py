#!/usr/bin/env python3
"""Release an exact rehearsed call with its matching proof-backed decoder context."""
import argparse
import json
from pathlib import Path
import sys

import release_gate as gate

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'set-expiry'))
import fresh_surface as fresh

SCHEMA = 'proof-context-release-v1'
LIMITS = (
    'Ready is a historical evidence handoff, never permission to transact. The '
    'sender can be a contract and need not be an available transaction origin. '
    'Review time, age policy, signature and return layout are reviewer inputs. '
    'Supplied headers are not consensus-authenticated; call returns are RPC '
    'claims, not proved state effects. Selector matching does not authenticate '
    'an ABI or establish reachability. No current state, authorization, gas, '
    'nonce, fees, atomic sequence or future execution is established. Nothing is sent.'
)


def evaluate(evidence, policy, request, choices, proofs, anchor_hash=None):
    """Withhold both call and decoded values unless every gate succeeds."""
    released = gate.evaluate(evidence, policy, request)
    # There is exactly one release point. An inherited intermediate ready result
    # remains diagnostic and does not expose an unsigned call of its own.
    result = {
        'schema': SCHEMA, 'verdict': 'withheld',
        'reason': 'Exact-call gate is ' + released['verdict'],
        'release_gate': {k: v for k, v in released.items() if k != 'unsigned_call'},
        'proof_context': None, 'unsigned_call': None, 'decoded_call': None,
        'limits': LIMITS,
    }
    if released['verdict'] != 'ready':
        return result
    joined = fresh.evaluate(evidence, policy, choices, proofs, anchor_hash)
    result['proof_context'] = {k: v for k, v in joined.items() if k != 'decoded_calls'}
    if joined['verdict'] != 'aligned':
        result['reason'] = 'Matching rehearsal failed complete code/call alignment'
        return result
    selected = next(item for item in joined['decoded_calls']
                    if item['id'] == released['member_id'])
    result.update(verdict='ready',
                  reason='Exact selected call, fresh complete set and code/decoder context align',
                  unsigned_call=released['unsigned_call'], decoded_call=selected)
    gate.expiry.sets.bounded(result)
    return result


def demo_inputs(expired=False):
    evidence, policy, choices, proofs = fresh.demo_inputs(expired)
    member = policy['plan']['calls'][0]
    request = {'schema': gate.REQUEST_SCHEMA, 'member_id': member['id'],
               'call': dict(member['call'])}
    return evidence, policy, request, choices, proofs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('demo', help='real historical ZTO balance call and same-block proof')
    commands.add_parser('expired-demo', help='withhold the same call beyond its review window')
    check = commands.add_parser('check')
    for name in ('evidence', 'policy', 'request', 'manifest'):
        check.add_argument(name)
    check.add_argument('--anchor-hash')
    args = parser.parse_args(argv)
    try:
        anchor = None
        if args.command in ('demo', 'expired-demo'):
            inputs = demo_inputs(args.command == 'expired-demo')
        else:
            read = gate.expiry.sets.binding.read_json
            choices, proofs = fresh.surface.manifest(read(args.manifest))
            inputs = (read(args.evidence), read(args.policy), read(args.request), choices, proofs)
            anchor = args.anchor_hash
        report = evaluate(*inputs, anchor_hash=anchor)
        print(json.dumps(report, indent=2, allow_nan=False))
        return 0 if report['verdict'] == 'ready' else 2
    except (ValueError, KeyError, TypeError, AttributeError, OSError, OverflowError,
            IndexError, RecursionError, gate.expiry.core.RPCError) as exc:
        print(json.dumps({'schema': SCHEMA, 'verdict': 'invalid', 'error': str(exc)}),
              file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
