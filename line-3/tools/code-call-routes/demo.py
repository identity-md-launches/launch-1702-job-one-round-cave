"""Replay real ZTO-first and IMD-second historical evidence without network."""
import json
from pathlib import Path
import code_call_routes as tool


def main():
    results = []
    for token in ('zto', 'imd'):
        bundle = tool.calls.ancestry.read_json(
            Path(__file__).resolve().parents[1] / 'code-routes' / (token + '-proof.json'))
        report = tool.inspect(bundle)
        runtime = report['runtimes'][0]
        results.append({'token': token.upper(), 'target': report['target'],
                        'code_block': report['code_block'], 'proof': report['proof'],
                        'call_instruction_count': runtime['call_instruction_count'],
                        'call_route_counts': runtime['call_route_counts'],
                        'metadata_call_route_counts': runtime['metadata_call_route_counts'],
                        'calls': runtime['call_preview']})
    passed = (results[0]['call_instruction_count'] == 0
              and results[1]['call_instruction_count'] == 12
              and sum(results[1]['call_route_counts'].values()) == 12
              and all(r['proof']['state_inclusion_verified'] for r in results))
    return {'demonstration_passed': passed, 'results': results,
            'scope': 'Real historical proof replay; routes are structural model findings.'}


if __name__ == '__main__':
    result = main()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['demonstration_passed'] else 1)
