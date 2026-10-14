# Proof Context Release

Line 4's **Release Gate** is promoted unchanged, alongside its ten tests and real
ZTO request. `provenance.json` gives source paths and SHA-256 hashes. It uses
the already promoted `set-expiry`, `rehearsal-set` and `rehearsal-binding`
folders. Everything is ordinary committed Python; no installation is needed.

The new `release_surface.py` joins that exact-call gate to the shared
Line 3/4 proof-backed signature, calldata and return decoder. It releases one
explicit call and its decoded arguments/return only if the whole rehearsal set
matches, is within the declared age window, and every member's proof context
aligns. An intermediate gate result never exposes its own unsigned call.
Unknown members, changed caller/target/data/value, missing evidence, expiry,
different proof blocks and selector mismatches withhold the final handoff.
Invalid proof or malformed input is an error with no handoff.

From the workspace root, Python 3.10+ and standard library only:

```sh
python3 -B shared/release-gate/release_surface.py demo
```

Tried successfully: this rechecks real ZTO `balanceOf(PoolManager)` evidence and
its same-block code proof at block **26,187,032**. At the explicit historical
review time 3,600 seconds after the block, it returns `ready` with raw balance
`285939607966355541747129965`. `expired-demo` returns exit 2 and null call/decoder
fields at age 7,201 seconds. The review window is an example policy, not advice.

## A fresh real-chain capture

Gathering 14 also collected and locally verified a new ZTO code proof and a
hash-pinned PoolManager balance call at block **26,188,942**, using the
contributor's read-only route, publicly attributed to
`https://ethereum-rpc.publicnode.com`. `live-14/` holds the untouched raw proof
and call evidence, explicit policy/request/decoder manifest, and result.
The proof was unanchored; provider identity and independence were not established.
Replay it without network:

```sh
python3 -B shared/release-gate/release_surface.py check shared/release-gate/live-14/evidence.json shared/release-gate/live-14/policy.json shared/release-gate/live-14/request.json shared/release-gate/live-14/manifest.json
```

The replay retains the recorded review time, so it checks a historical handoff,
not freshness at the time you run it. For a new review, supply a policy with your
own `as_of` and age window. Explicit mode takes workspace-local, bounded,
duplicate-key-free JSON. The manifest is `set-surface-manifest-v1`, with exactly
one member per planned id, each giving `id`, `signature`, `return_types`, `proof`.
Evidence, policy and request retain the inherited schemas described in
[`release_gate.py`](release_gate.py) and the sibling READMEs.

```sh
python3 -B gathering/run_suite.py discover -s shared/release-gate -p 'test_*.py' -v
```

Twenty-four promoted/integration tests passed. They exercise each context field,
complete-set requirements, inclusive expiry, proof corruption, block and selector
mismatch, immutable inputs, strict CLI JSON and network-disabled demos.

Line 1 can use the interface for explicit quoter rehearsals; Line 2 can use it
for unsigned permission-call review. Both must supply their own matching evidence
and proofs. This demonstration does not cover their calls or authorize them.

`ready` is an evidence handoff, **never permission to transact**. The PoolManager
sender is a simulated contract caller, not an available transaction origin.
PoolManager token balances are not this pool's liquidity. Supplied headers are
not consensus-authenticated; returns are RPC claims. Signatures/layouts are
reviewer choices, not authenticated ABI. No current state, gas, nonce, fees,
authority, effects, atomic sequence or future execution is established. The tools
read no environment variables, wallets, keys or secrets and never sign, send,
pay, post or deploy. Offline replay reads only workspace files.

Optional fresh collection is in `gathering/capture_release.py`; read it first.
It requires an explicit new output directory under this folder and supports an
explicit contributor relay. It never writes partial evidence before validation.
