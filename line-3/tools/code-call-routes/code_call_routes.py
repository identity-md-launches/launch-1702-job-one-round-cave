#!/usr/bin/env python3
"""Join proof-backed call operands to conservative legacy-EVM routes offline."""
import argparse
import json
from pathlib import Path
import sys

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS / 'code-calls'))
sys.path.insert(0, str(TOOLS / 'code-routes'))
import code_calls as calls
import code_routes as routes

STATUSES = ('direct-model-path', 'dynamic-target-candidate', 'excluded-by-model')


def join(code, call_scan):
    """Counts cover all call instructions; operand details retain the bounded preview."""
    decoded, _, destinations, edges, _, dynamic = routes.graph(code)
    direct, _ = routes.walk(edges, dynamic, destinations, False)
    conservative, expanded = routes.walk(edges, dynamic, destinations, True)

    def status(pc):
        return (STATUSES[0] if pc in direct else
                STATUSES[1] if pc in conservative else STATUSES[2])

    counts = {key: 0 for key in STATUSES}
    metadata_counts = {key: 0 for key in STATUSES}
    metadata = call_scan['recognized_solidity_metadata']
    call_pcs = set()
    for pc, op, _, _ in decoded:
        if op in calls.CALLS:
            call_pcs.add(pc)
            counts[status(pc)] += 1
            if metadata and pc >= metadata['start']:
                metadata_counts[status(pc)] += 1
    calls.lens.require(len(call_pcs) == call_scan['call_instruction_count'],
                       'call and route decoder counts disagree')
    preview = []
    for hit in call_scan['call_preview']:
        calls.lens.require(hit['pc'] in call_pcs, 'call offset is not a decoded call')
        preview.append({**hit, 'route_status': status(hit['pc'])})
    return {'route_model': 'legacy-evm-adjacent-push-v1',
            'call_route_counts': counts, 'metadata_call_route_counts': metadata_counts,
            'dynamic_jump_expansion_used': expanded,
            'call_preview': preview, 'omitted_call_count': call_scan['omitted_call_count'],
            'target_details_complete': call_scan['omitted_call_count'] == 0}


def inspect(bundle, anchor_hash=None):
    # Verification happens before any route/target finding is released.
    result = calls.inspect(bundle, anchor_hash)
    code_by_address = {}
    for node in bundle['observation']['nodes']:
        for item in (node, node.get('beacon')):
            if item is not None:
                address = calls.lens.address(item['address'])
                code = calls.lens.code_bytes(item['code'])
                calls.lens.require(address not in code_by_address or
                                   code_by_address[address] == code,
                                   'conflicting runtime for address')
                code_by_address[address] = code
    for runtime in result['runtimes']:
        runtime.update(join(code_by_address[runtime['address']], runtime))
    result['schema'] = 'code-call-routes-result-v1'
    result['scope'] = (
        'Call operands and conservative structural routes joined on the same verified '
        'historical runtime bytes. Route counts cover every decoded call; target details '
        'cover only the bounded preview. Direct paths may be infeasible; dynamic jumps '
        'admit every decoded JUMPDEST. Excluded-by-model is not a safety verdict. '
        'Metadata remains included and annotated. Locally constant targets are conditional '
        'on successful linear segment execution, not verified dependencies. No stack/gas '
        'feasibility, actual reachability, external code, source equivalence, safety, '
        'consensus, finality, current state or authority to transact is established.')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True)
    parser.add_argument('--anchor-hash')
    args = parser.parse_args()
    try:
        result = inspect(calls.ancestry.read_json(args.bundle), args.anchor_hash)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError, OverflowError, AttributeError,
            IndexError, RecursionError) as error:
        print('Code Call Routes: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
