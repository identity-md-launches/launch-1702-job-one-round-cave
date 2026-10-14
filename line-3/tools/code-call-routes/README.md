# Code Call Routes

Pair historical, proof-backed external-call operands with Code Routes' conservative route model. This helps a worker review call-site findings without mistaking metadata bytes or an excluded instruction for an established external dependency. All full-runtime bytes remain part of code identity.

Run from the repository root, offline, with Python 3.9+ and only the standard library:

```sh
python3 -B line-3/tools/code-call-routes/demo.py
```

Expected: `demonstration_passed: true`. The command re-verifies real saved ZTO evidence first and IMD second at Ethereum block **26,188,209**, then recomputes target operands and route membership from the same runtime. When tried, ZTO had zero decoded calls. IMD had **eleven dynamic-target candidates** and **one excluded-by-model call**; that excluded CALLCODE overlaps recognized Solidity metadata. Its locally constant STATICCALL target at byte offset 12,834 remains a dynamic-target candidate. No fresh chain capture is claimed. The saved header is unanchored; its inclusion proof establishes consistency relative to that header, not consensus authenticity.

Inspect another workspace-local raw proof bundle:

```sh
python3 -B line-3/tools/code-call-routes/code_call_routes.py --bundle line-3/tools/code-routes/imd-proof.json
```

Optional `--anchor-hash` compares an independently obtained execution block hash; it cannot authenticate a copied bundle hash. Invalid proof, malformed input or mismatched anchor exits 1 with empty stdout. CLI syntax errors exit 2. The tool prints JSON and writes no files.

Route totals cover **all** decoded call instructions. Operand details retain Code Calls' first-64 preview and explicitly report omissions and `target_details_complete`. No call is silently dropped from route totals. Keep committed sibling `code-calls`, `code-routes`, `code-surface`, `code-opcodes`, `code-ancestry`, `code-proof` and `code-lens` tools and their ordinary Python dependencies; no network or installation is needed. The demo additionally needs Code Routes' saved proof JSON files.

Direct model paths can be infeasible. Dynamic jumps conservatively admit every decoded JUMPDEST. An excluded path is a model result, not a safety finding. Target constants apply only if their linear segment executes successfully. This tool does not model stack feasibility, conditions, gas, cross-contract execution or future control-flow formats; 0xef-prefixed runtimes are refused by the inherited scanners. It verifies no external target code, complete dependency graph, source equivalence, reachable execution, current runtime, finality or permission to transact. It reads no environment variables, wallet, key or secret; it never signs, sends, pays, posts or deploys.

Eleven focused tests passed, including real proof joins, corrupted proof/anchor/runtime rejection, direct and dynamic paths, halted suffixes, PUSH-data exclusion, metadata retention, preview truncation and 100 deterministic random byte streams compared with the existing route-query API:

```sh
python3 -B -m unittest discover -s line-3/tools/code-call-routes -p 'test_*.py' -v
```

The mark's meaning: **Pepe checks whether the trail reaches the called stone.**
