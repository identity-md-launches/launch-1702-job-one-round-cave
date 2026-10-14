#!/usr/bin/env python3
"""Find the least exact input whose rounded planning minimum reaches a target."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'zto-capacity'))
import zto_capacity as capacity
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'zto-review'))
import zto_review as review

path = capacity.path
DEFAULT_SNAPSHOT = capacity.DEFAULT_SNAPSHOT
SCHEMA = 'zto-target-report-v1'


def find_target(observation, token, target_output, ceiling_input, slippage_bps):
    """Search only the complete-coverage prefix of one fixed pool observation.

    The core v4 exact-input estimate and its recorded bitmap coverage are
    inherited from ZTO Path. Success checks the chosen raw unit and its direct
    predecessor, rather than trusting only binary-search bookkeeping.
    """
    require = path.z.require
    require(token in ('ZTO', 'IMD'), 'input must be ZTO or IMD')
    require(type(slippage_bps) is int and 0 <= slippage_bps < 10000,
            'slippage bps must be an integer in 0..9999')
    require(type(target_output) is str and len(target_output) <= 120,
            'target output must be a short plain decimal string')
    require(type(ceiling_input) is str and len(ceiling_input) <= 120,
            'ceiling input must be a short plain decimal string')
    state, bitmap, _ = path.decode(observation)
    din = state['decimals'][1 if token == 'ZTO' else 0]
    dout = state['decimals'][0 if token == 'ZTO' else 1]
    target = path.z.parse_amount(target_output, dout)
    ceiling = path.z.parse_amount(ceiling_input, din)
    require(ceiling < 1 << 127, 'ceiling must fit positive int128 pool delta')
    coverage = capacity.find_bound(observation, token, ceiling_input, slippage_bps)
    probes = coverage['quote_probes']

    def check(raw):
        nonlocal probes
        probes += 1
        quote = path.quote(observation, token, path.z.units(raw, din))
        require(quote['status'] == 'estimated',
                'coverage changed during target search')
        output = int(quote['estimate']['output_raw'])
        minimum = output * (10000 - slippage_bps) // 10000
        return output, minimum

    result = {
        'schema': SCHEMA, 'chain_id': 1, 'pool_id': path.z.POOL,
        'snapshot_sha256': review.digest(observation),
        'block': observation['base']['block'], 'source': observation['base']['source'],
        'input_token': token, 'output_token': 'IMD' if token == 'ZTO' else 'ZTO',
        'target_output_raw': str(target), 'target_output': path.z.units(target, dout),
        'ceiling_input_raw': str(ceiling), 'ceiling_input': path.z.units(ceiling, din),
        'slippage_bps': slippage_bps,
        'minimum_rule': 'floor(estimated_output_raw * (10000 - slippage_bps) / 10000)',
        'bitmap_words': sorted(bitmap),
        'coverage_status': coverage['status'],
        'scope': 'Smallest exact input reaching a caller target within this historical snapshot and recorded tick coverage.',
        'limitations': [
            'Historical RPC evidence is not a current quote or state proof.',
            'The target, tolerance and input ceiling are caller choices, not recommendations.',
            'Coverage boundary is not total pool capacity; no output is inferred beyond it.',
            'Minimum is a planning number, not an enforced receipt.',
            'No router settlement, transfer behavior, gas or MEV simulation.'
        ]
    }
    if coverage['status'] == 'no_complete_input':
        result.update(status='no_complete_input', quote_probes=probes)
        return result

    high = int(coverage['maximum_complete_input_raw'])
    result['maximum_complete_input_raw'] = str(high)
    result['maximum_complete_input'] = path.z.units(high, din)
    high_output, high_minimum = check(high)
    if high_minimum < target:
        result.update(status=('target_unreachable_within_ceiling'
                              if coverage['status'] == 'ceiling_reached'
                              else 'target_not_reached_in_coverage'),
                      maximum_complete_estimated_output_raw=str(high_output),
                      maximum_complete_minimum_output_raw=str(high_minimum),
                      quote_probes=probes)
        return result

    low = 0  # Zero is a mathematical lower bound, never a quoted input.
    while high - low > 1:
        middle = (low + high) // 2
        _, minimum = check(middle)
        if minimum >= target:
            high = middle
        else:
            low = middle
    output, minimum = check(high)
    require(minimum >= target, 'chosen input fails target recheck')
    previous_output = previous_minimum = None
    if high > 1:
        previous_output, previous_minimum = check(high - 1)
        require(previous_minimum < target, 'previous input already meets target')
    result.update(
        status='target_reached', minimum_input_raw=str(high),
        minimum_input=path.z.units(high, din),
        estimated_output_raw=str(output), estimated_output=path.z.units(output, dout),
        planning_minimum_output_raw=str(minimum),
        planning_minimum_output=path.z.units(minimum, dout),
        previous_input_raw=str(high - 1) if high > 1 else None,
        previous_estimated_output_raw=(str(previous_output) if high > 1 else None),
        previous_minimum_output_raw=(str(previous_minimum) if high > 1 else None),
        quote_probes=probes)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', default=str(DEFAULT_SNAPSHOT),
                        help='workspace ZTO Path observation; default is bundled real historical data')
    parser.add_argument('--input', choices=('ZTO', 'IMD'), default='ZTO')
    parser.add_argument('--target', required=True, help='desired output token amount')
    parser.add_argument('--ceiling', required=True, help='maximum input token amount to search')
    parser.add_argument('--slippage-bps', required=True, type=int,
                        help='explicit planning tolerance, integer 0..9999')
    args = parser.parse_args(argv)
    try:
        result = find_target(review.read_json(args.snapshot), args.input, args.target,
                             args.ceiling, args.slippage_bps)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0 if result['status'] == 'target_reached' else 2
    except (ValueError, KeyError, TypeError, AttributeError, OSError, OverflowError,
            RecursionError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
