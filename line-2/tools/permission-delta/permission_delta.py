#!/usr/bin/env python3
"""Turn two verified ERC-20 permission inventories into a compact review digest."""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
CHANGES_DIR = HERE.parent / 'allowance-changes'
sys.path.insert(0, str(CHANGES_DIR))
import allowance_changes as changes


def priority(row):
    """Return a conservative review band; it is not a safety or trust score."""
    change = row['change']
    if change in ('increased', 'became_active'):
        return 'review_now'
    if change == 'newly_observed':
        return 'coverage_review'
    if change in ('decreased', 'became_zero'):
        return 'confirm_change'
    if row.get('balance_delta_raw', '0') != '0':
        return 'balance_context'
    return 'no_permission_change'


def digest(before, after):
    """Validate raw evidence through Allowance Changes and make its triage explicit."""
    report = changes.compare(before, after)
    coverage = report['coverage']
    items = []
    for row in report['pairs']:
        band = priority(row)
        if band == 'no_permission_change':
            continue
        item = {
            'priority': band,
            'owner': row['owner'],
            'spender': row['spender'],
            'change': row['change'],
            'before': row['before'],
            'after': row['after'],
        }
        for key in ('allowance_delta_raw', 'balance_delta_raw', 'spendable_delta_raw'):
            if key in row:
                item[key] = row[key]
        items.append(item)
    order = {'review_now': 0, 'coverage_review': 1, 'confirm_change': 2, 'balance_context': 3}
    items.sort(key=lambda item: (order[item['priority']], item['owner'], item['spender']))
    bands = {name: sum(item['priority'] == name for item in items) for name in order}
    decision = ('coverage_incomplete' if not coverage['all_previous_pairs_rechecked']
                else 'review_permission_change' if bands['review_now'] or bands['coverage_review']
                else 'confirm_reduction' if bands['confirm_change'] else 'no_permission_change_measured')
    return {
        'schema': 'permission-delta-digest-v1',
        'decision': decision,
        'chain_id': report['chain_id'], 'token': report['token'],
        'token_address': report['token_address'], 'decimals': report['decimals'],
        'before_block': report['before_block'], 'after_block': report['after_block'],
        'complete_wallet_audit': False, 'coverage': coverage,
        'permission_change_counts': report['counts'],
        'review_item_counts': bands, 'review_items': items,
        'limitations': [
            'A digest is triage, not authorization, a safety assessment or a transaction plan.',
            'Missing pairs are unknown coverage, never interpreted as revocation or zero allowance.',
            'Newly observed means previously unmeasured, not newly approved.',
            'Balance movement is context only; it does not establish transfer cause or spender behavior.',
            'Only validated, measured standard ERC-20 pairs are covered; Permit2, signatures and unknown spenders are omitted.',
            'Historical RPC evidence is trusted input, not current state, a state proof or future-execution evidence.',
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', help='raw Allowance Lens observation or Changes inventory')
    parser.add_argument('--after', help='later raw observation or Changes inventory')
    args = parser.parse_args(argv)
    try:
        changes.lens.require((args.before is None) == (args.after is None),
                             'provide both --before and --after, or neither for the offline demonstration')
        demonstration = args.before is None
        before = changes.load(args.before or CHANGES_DIR.parent / 'allowance-lens' / 'observation.json')
        after = changes.load(args.after or CHANGES_DIR / 'recheck.json')
        result = digest(before, after)
        result['demonstration'] = demonstration
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError, OverflowError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
