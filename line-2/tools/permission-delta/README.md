# Permission Delta Digest

Turn two validated ERC-20 permission inventories into a compact, conservative reviewer queue. It reuses Line 2's strict raw-evidence validation from Allowance Changes, then separates allowance increases, newly observed coverage, reductions, and balance-only context. ZTO is the bundled demonstration token; real IMD evidence is also accepted by the inherited validator. Python 3.10+ and the standard library only; no network or installation is needed.

From the repository root, one command shows it working:

```sh
python3 -B line-2/tools/permission-delta/permission_delta.py
```

## What happened when tried

On 2026-10-14, the included historical real ZTO evidence compared blocks 26,183,751 and 26,184,324. All 19 previously measured pairs were rechecked and all allowances were unchanged. Two balances changed, but no measured spendable upper bound changed; the digest therefore reported `no_permission_change_measured` with two `balance_context` items. These saved provider observations are historical evidence, not a current-chain claim.

To digest your own two raw Allowance Lens observations or Allowance Changes inventories:

```sh
python3 -B line-2/tools/permission-delta/permission_delta.py --before line-2/tools/allowance-lens/observation.json --after line-2/tools/allowance-changes/recheck.json
```

Both paths must be inside the workspace, use strict raw evidence and remain below the inherited 96 KiB limit. The tool writes nothing. Exit 0 means its offline arithmetic completed; exit 1 means evidence was malformed or inconsistent.

`review_now` covers an allowance increase or activation; `coverage_review` means a pair is newly observed, not newly approved; `confirm_change` covers a decrease or clearance; and `balance_context` flags a changed measured balance without asserting who moved tokens. If any old pair was not rechecked, the top-level decision is `coverage_incomplete`; missing data is never called a revocation.

Five focused tests passed, including activation, reduction, balance-only context, missing coverage and input immutability:

```sh
python3 -B -m unittest discover -s line-2/tools/permission-delta -p 'test_*.py' -v
```

This is triage only: it does not authorize, compose, simulate, sign or send a transaction; handle wallets, keys, secrets, environment variables, payment, posting and deployment; or contact a network. It covers only explicitly measured standard ERC-20 pairs at historical blocks. Unknown spenders, Permit2, signatures, custom authorization mechanisms, other assets, current state and future execution remain outside coverage. A changed balance does not establish cause or spender behavior, and priority labels are not trust or safety scores.
