# Gathering report — round 14

On 2026-10-14 I inspected the tools' executable/demo interfaces and I/O paths, ran every line tool's documented unittest discovery check, and tried every line tool using its offline demonstration or saved real-evidence command. **142 commands returned their expected exits; 959 tests passed**, including **52 line suites / 792 tests** and the shared integration suites. Expected refusals were checked as refusals. `check-results.json` records commands, exits, counts and demo-output digests. These are local contributor checks, not independent certification. One new read-only real-chain capture was also tried and then replayed offline.

| Line | Suites | Tests | Works | Broken |
| --- | ---: | ---: | --- | --- |
| 1 | 11 | 128 | Historical ZTO/IMD bounds and minimum-input target search | None reproduced |
| 2 | 14 | 179 | Measured permissions, unsigned drafts and conservative delta triage | None reproduced |
| 3 | 14 | 266 | Proof-relative code identity and bounded call-route analysis | Previous stale demo repaired; no new failure |
| 4 | 13 | 219 | Exact independent calls, complete sets, age policy and request release gate | None reproduced |

## Line 1 — ZTO/IMD swap bounds

**Tried:** all eleven suites, existing archive/band/path/sizes/capacity/refresh/review/handoff/bundle/drift demonstrations, and new **ZTO Target** with `--input ZTO --target 0.0001 --ceiling 10 --slippage-bps 100`. The deliberate incomplete path still exits 2 without releasing a bound.

**Works:** the target search uses real historical pool state at block **26,184,260**, directly checks the selected input and one raw unit less, and returns `target_reached`. The minimum input is **6.605354095186351266 ZTO**, estimated output **0.000101010101010102 IMD**, rounded planning minimum **0.0001 IMD**. One ZTO raw unit less yields **0.000099999999999999 IMD**. The explicit ceiling/tolerance are demonstration controls. Tests also exercise reverse direction and unreachable/out-of-coverage targets. All inherited bounds/handoff checks passed. **Broken:** none reproduced. This is historical planning arithmetic, not current liquidity, settlement, gas, token behavior, MEV or a receipt guarantee. The fixed-state search assumption is documented; no partial path is promoted to an answer.

**Outside use / overlap:** useful to an unfamiliar worker preparing a trade; does not merely serve cave records. It concerns amounts and tick coverage, distinct from permission inventories, code identity and call evidence.

## Line 2 — ERC-20 spending permissions

**Tried:** all fourteen suites and demonstrations, including permission gate denial, allowance changes/union/caps, draft and bundle reviews, age refresh, receipt/spender exposure, and new **Permission Delta Digest**.

**Works:** the new digest validates real ZTO inventories at blocks **26,183,751** and **26,184,324**. All **19** previous pairs were rechecked, measured allowances stayed unchanged, and two balance movements are labeled `balance_context`. The decision is `no_permission_change_measured`, never a complete-wallet safety claim. Tests exercise activation, reduction, missing coverage and input immutability. Existing tools still distinguish latent permissions on empty balances, measured funded exposure and explicitly hypothetical receipt/cap scenarios. **Broken:** none reproduced. Unknown spenders, Permit2 downstream grants, unused signatures, custom authorization, other assets, current state and causes of balance movements remain outside coverage.

**Outside use / overlap:** useful for measured standard ERC-20 authorization review by any worker. Its unsigned drafts are a different function from Line 4's observed call rehearsals; the two can be joined only with matching caller/evidence.

## Line 3 — executable code identity

**Tried:** all fourteen suites and demonstrations: lens/changes/opcodes, proof/ancestry/review/set, delta/surface/constants/routes/metadata/calls, and new **Code Call Routes**. I also compared the rerun Code Calls demo with its saved artifact.

**Works:** the previous gathering's stale `code-calls/demo-result.json` has been repaired: it now equals the current demo output exactly. `gathering/code-calls-demo-14.json` preserves this check. Code Call Routes reverifies real ZTO-first and IMD-second evidence at block **26,188,209**. ZTO has zero decoded call instructions. IMD has twelve: **eleven dynamic-target candidates and one excluded-by-model CALLCODE overlapping recognized metadata**. The locally constant STATICCALL target at byte offset **12,834** remains a dynamic-target candidate. Route totals cover every decoded call, while target detail is explicitly bounded. `gathering/code-call-routes-demo-14.json` records the output. **Broken:** none reproduced; the prior handoff defect is resolved.

**Outside use / overlap:** useful for unfamiliar contract reviewers. Structural route membership is not actual reachability, external-target code identity, complete dependency discovery, source/ABI equivalence, safety, consensus authenticity or current runtime. This remains distinct from Line 4's RPC-observed outcomes.

## Line 4 — contract-call rehearsal

**Tried:** all thirteen suites and demonstrations, including successful/reverted rehearsal replay, changes/witnesses, return/revert expectations, calldata decoding, relay provenance, exact binding, complete sets, expiry, and new **Release Gate**.

**Works:** the new gate checks one explicit request against a complete matching set within its reviewer-declared age window. Its ZTO-first `totalSupply()` demonstration at block **26,188,241** returns `ready`; mutations to every call field, absent members, changed return bytes, expiry and incomplete sets are refused. The demo's PoolManager sender is explicitly a simulation context, not an available transaction origin. All older checks passed. **Broken:** none reproduced. Review time is an input rather than a trusted clock. Independent calls do not share writes; provider identity, ABI meaning, authority, gas, effects, current state and future inclusion remain unproved.

**Outside use / overlap:** useful to any worker assembling a proposed call for human review. It checks observed calls and exact context, rather than code identity or permission policy.

## Shared handoff and glue

Promoted Line 4's **Release Gate**, its ten tests and real request unchanged to `shared/release-gate/`; `provenance.json` records matching source SHA-256 hashes. All sibling dependencies were already ordinary committed shared Python files. New **Proof Context Release** joins it with the existing Line 3/4 proof-backed signature/calldata/return context. Only the exact selected call is released, and only after the whole set matches, is within the explicit age window, and every proof/decoder context aligns. Intermediate diagnostics expose no unsigned call or decoded values of their own. Invalid proofs fail without a handoff; stale or mismatched requests skip the proof join.

The offline demo reuses unmodified real ZTO `balanceOf(PoolManager)` evidence and code proof at block **26,187,032**. At historical age 3,600 seconds it returns `ready` and raw balance **285939607966355541747129965**. At 7,201 seconds it returns `withheld`, exit 2, with null call and decoded result. **24 promoted/integration tests** passed, covering context mutations, missing set members, inclusive expiry, corrupted proof, changed code block/signature, input immutability, strict CLI JSON and network-disabled demos.

I additionally ran `gathering/capture_release.py` through the supplied contributor route. It collected a ZTO code proof, reconstructed its header, and rehearsed `balanceOf(PoolManager)` pinned to that same hash at Ethereum block **26,188,942** (`0x8e5c4251a2bca8eead54f1d13c69da4f0cb687ee3dbc8c69177b45f0073167c5`). Public attribution is **https://ethereum-rpc.publicnode.com**; actual upstream identity/independence were not established. At the recorded review time, 916 seconds after the block, the joined result was `ready`, raw balance **315601872916425009005580689**. `shared/release-gate/live-14/` holds the raw proof/evidence and explicit policy/request/manifest/result; its CLI replay passed offline. The proof is unanchored. Replaying its recorded review time is a historical check, not a current freshness claim. PoolManager balance is not this pool's liquidity.

Line 1 could use this interface for quoter calls and Line 2 for unsigned permission-call review, with their own matching raw evidence/proofs. Neither capability is claimed covered by the balance demonstration. No invented sender, missing requester value or relabeled evidence was used. Nothing was signed, sent, paid, posted or deployed; no environment variable, wallet, key or secret was read.

## Scope for 21 Pepes and coins

All four goals have useful bounded cores, serve workers beyond this cave, and remain different in kind. No goal needs replacement. Keep Line 1 to fixed-pool exact-input arithmetic and reviewed bounds; Line 2 to explicitly measured standard ERC-20 permissions and labeled scenarios; Line 3 to proof-relative identity and bounded legacy-EVM structural models; Line 4 to exact independent historical calls, complete sets and explicit review policies. Universal transaction safety, all-authorization discovery, arbitrary EVM reachability, authentic ABI/source recovery, stateful cross-contract sequences and guaranteed inclusion are too large for 21 short tasks. Narrow any proposed extension to those boundaries and preserve the refusal paths.

`COINS.md` says **none**: ZTO first and IMD second supply the real assets needed here. No line needs another coin or a coin-specific v4 hook, and no Python tool needs deployment. No coin/deploy order was created, checked or posted.

## Wall and delivery

**The Reviewed Gate** adds a red-ochre arch and three chalk pebbles to a visually bare patch left of Pepe. Record 13's ancestor was downloaded and SHA-256 checked. One image-tool edit produced actual gate pigment; its generated rock was discarded because whole-wall generation softened inherited texture. The conservation step transferred only the new pigment. Exactly **4,944 pixels** changed inside `[310,548,413,675]`; **zero pixels** outside it changed. Earlier motifs, central Pepe, cracks, color, lighting, size and framing remain. Both inherited hands have five digits, four fingers plus a thumb. No hand was added. No words, numbers, signature, border or watermark were observed. `VISUAL.md` records review and limitations.

Required `artifacts/gathering/wall-v14.png` is a **1254 × 1254, RGB 8-bit PNG**, 3,920,901 bytes; `wall.png` is its identical requested mirror. Both remain untracked for the uploader. `dist/gathering/14.jpg` is a **512 × 512 baseline JPEG**, 54,700 bytes, visually inspected and structurally validated. No unmet visual requirement was observed.

`dist/gathering/14.json` has the exact requested keys/traits and hash of the final wall bytes. `dist/goals.json` reads the four unchanged GOAL.md files. Self-contained `dist/index.html` includes **all 157 records**, by wall and newest painted round first: **70 paintings**, **87 placeholders** folded below. This is a later gathering; the existing future placeholders and all earlier records remain. Long addresses wrap on small screens. No line folder or line record was changed. `delivery-checks-14.json` records packaging checks.

## Suite inventory

- Line 1: zto-archive, zto-band, zto-bundle, zto-capacity, zto-drift, zto-handoff, zto-path, zto-refresh, zto-review, zto-sizes, zto-target.
- Line 2: allowance-caps, allowance-changes, allowance-lens, allowance-union, approval-draft, bundle-refresh, draft-age, draft-bundle, draft-refresh, draft-witness, permission-delta, permission-gate, receipt-exposure, spender-exposure.
- Line 3: code-ancestry, code-call-routes, code-calls, code-changes, code-constants, code-delta, code-lens, code-metadata, code-opcodes, code-proof, code-review, code-routes, code-set, code-surface.
- Line 4: call-changes, call-expectation, call-rehearsal, call-witness, calldata-lens, rehearsal-binding, rehearsal-expiry, rehearsal-set, relay-rehearsal, release-gate, return-lens, revert-expectation, set-expiry.
