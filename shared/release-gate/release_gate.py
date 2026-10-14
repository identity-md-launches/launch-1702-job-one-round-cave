#!/usr/bin/env python3
"""Gate one explicit proposed call on a fresh, complete rehearsal set. Offline only."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    'release_gate_expiry', HERE.parent / 'set-expiry' / 'set_expiry.py')
expiry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(expiry)

SCHEMA = 'rehearsal-release-gate-v1'
REQUEST_SCHEMA = 'rehearsal-release-request-v1'
EXIT = {'ready': 0, 'expired': 1, 'mismatch': 1, 'inconclusive': 2}
LIMITS = (
    'Ready means only that one explicit call exactly equals one member of a complete '
    'matching historical rehearsal set within the reviewer-declared age window. It is '
    'not approval, authorization, a signature, or permission to send. The caller may '
    'be a contract and need not be an available transaction origin. No current state, '
    'future inclusion, gas, fees, nonce, effects, ABI authenticity, authority, wallet, '
    'provider identity, or chain authenticity is established. Calls in the set are '
    'independent; no writes are simulated. Nothing is sent.'
)


def request(value):
    """Normalize the exact call requested for release; unknown fields are refused."""
    expiry.sets.bounded(value)
    core = expiry.core
    core.require(isinstance(value, dict) and set(value) == {'schema', 'member_id', 'call'},
                 'request requires exactly schema, member_id and call')
    core.require(value['schema'] == REQUEST_SCHEMA, 'unsupported release request schema')
    member = expiry.sets.identifier(value['member_id'])
    core.require(isinstance(value['call'], dict) and set(value['call']) ==
                 {'from', 'to', 'data', 'value'},
                 'request call requires explicit from, to, data and value only')
    return {'schema': REQUEST_SCHEMA, 'member_id': member,
            'call': core.transaction(value['call'])}


def evaluate(evidence, selected_policy, selected_request):
    """Return ready only for the exact selected member of a fresh, complete set."""
    wanted = request(selected_request)
    chosen = expiry.policy(selected_policy)
    member = next((item for item in chosen['plan']['calls']
                   if item['id'] == wanted['member_id']), None)
    report = {
        'schema': SCHEMA, 'verdict': 'inconclusive', 'reason': '',
        'member_id': wanted['member_id'], 'requested_call': wanted['call'],
        'policy_sha256': expiry.sets.binding.digest(chosen),
        'request_sha256': expiry.sets.binding.digest(wanted), 'limits': LIMITS,
    }
    if member is None:
        report.update(verdict='mismatch', reason='requested member is absent from the reviewed set')
        return report
    differences = [{'field': field, 'expected': member['call'][field],
                    'requested': wanted['call'][field]}
                   for field in ('from', 'to', 'data', 'value')
                   if wanted['call'][field] != member['call'][field]]
    report['reviewed_block'] = chosen['plan']['block']
    report['expected_return'] = member['expected_return']
    report['differences'] = differences
    if differences:
        report.update(verdict='mismatch',
                      reason='requested call differs from its reviewed set member')
        return report
    freshness = expiry.evaluate(evidence, chosen)
    report['set_expiry'] = freshness
    if freshness['verdict'] == 'fresh':
        report.update(verdict='ready',
                      reason='exact requested call is a member of a fresh complete rehearsal set',
                      unsigned_call=wanted['call'])
    elif freshness['verdict'] == 'expired':
        report.update(verdict='expired', reason='matching set is outside its declared age window')
    else:
        report.update(verdict=freshness['verdict'],
                      reason='set expiry check is ' + freshness['verdict'])
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('demo', help='gate one saved real ZTO-first call offline')
    gate = commands.add_parser('gate', help='gate an explicit proposed call against a set')
    gate.add_argument('evidence')
    gate.add_argument('policy')
    gate.add_argument('request')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            evidence = expiry.sets.binding.read_json(HERE.parent / 'rehearsal-set' / 'zto-set-evidence.json')
            selected_policy = expiry.sets.binding.read_json(HERE.parent / 'set-expiry' / 'zto-set-expiry-policy.json')
            selected_request = expiry.sets.binding.read_json(HERE / 'zto-release-request.json')
        else:
            evidence = expiry.sets.binding.read_json(args.evidence)
            selected_policy = expiry.sets.binding.read_json(args.policy)
            selected_request = expiry.sets.binding.read_json(args.request)
        report = evaluate(evidence, selected_policy, selected_request)
        print(json.dumps(report, indent=2, allow_nan=False))
        return EXIT[report['verdict']]
    except (ValueError, KeyError, TypeError, OSError, RecursionError, expiry.core.RPCError) as exc:
        print(json.dumps({'schema': SCHEMA, 'verdict': 'inconclusive', 'error': str(exc)}),
              file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
