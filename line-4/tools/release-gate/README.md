# Release Gate

Gate one explicit proposed Ethereum call on a complete, matching, and still
fresh rehearsal set. It turns a verified member into an unambiguous
`unsigned_call` only when the proposed `from`, `to`, calldata and native value
exactly match that member. It is an offline standard-library Python tool: it
does not read environment variables, wallets, keys, or files outside the
workspace, and never signs, broadcasts, pays, posts, or deploys.

Run from the repository root:

```sh
python3 -B line-4/tools/release-gate/release_gate.py demo
```

Tried on 2026-10-14: the demo returned `ready` (exit 0). It replays the saved
ZTO-first `totalSupply()` query at finalised Ethereum block `0x18f99d1`, using
the existing three-call ZTO/IMD set and its explicitly historical review time.
The returned `unsigned_call` is a simulation call from the real PoolManager;
it does not assert that the PoolManager is a transaction origin or that anyone
is authorized to send it. It makes no network request and does not claim
anything about current state.

For reviewed files of your own:

```sh
python3 -B line-4/tools/release-gate/release_gate.py gate evidence.json policy.json request.json
```

`policy.json` is the sibling Set Expiry `rehearsal-set-expiry-v1` policy and
`evidence.json` is the sibling Rehearsal Set evidence. `request.json` contains
exactly `schema: rehearsal-release-request-v1`, `member_id`, and an explicit
call with only `from`, `to`, `data`, and `value`. Unknown fields and malformed,
oversized, duplicate-key, non-finite, or outside-workspace inputs are refused.

| Verdict | Exit | Meaning |
| --- | ---: | --- |
| `ready` | 0 | Exact selected call is in a fresh, complete matching set. |
| `expired` | 1 | Exact call matched, but the declared review window has passed. |
| `mismatch` | 1 | Member ID, proposed context, return, evidence, or plan differs. |
| `inconclusive` | 2 | Evidence is incomplete/invalid or cannot bind every set member. |

`ready` is deliberately narrow: it is not approval to transact and does not
establish authorization, a usable sender, signatures, fees, nonce, gas, ABI
meaning, provider or chain authenticity, state effects, current state, future
inclusion, or a simulated sequence of writes. The Set Expiry policy's review
time is an input, not a trusted clock. The tool depends on the adjacent
`set-expiry/`, `rehearsal-set/`, `rehearsal-binding/`, and `call-rehearsal/`
folders, all ordinary committed standard-library Python code.

Focused offline tests were run successfully:

```sh
python3 -B -m unittest discover -s line-4/tools/release-gate -p 'test_*.py' -v
```
