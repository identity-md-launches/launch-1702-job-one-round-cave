# ZTO Target

Find the **smallest exact input** whose estimated output, after a worker-chosen planning tolerance, reaches a worker-chosen output target. The search uses one pinned ZTO/IMD Uniswap v4 pool observation and integer raw token units. It first finds the complete path coverage inside the chosen input ceiling, then searches that region and directly checks the chosen input and one raw unit less. A result beyond the ceiling or recorded bitmap coverage releases no input bound.

## One command to see it work

From the repository root, with Python 3.10+ and no installation or network:

```sh
python3 -B line-1/tools/zto-target/zto_target.py --input ZTO --target 0.0001 --ceiling 10 --slippage-bps 100
```

The bundled observation is real historical Ethereum pool state at block **26,184,260**, already captured by ZTO Path. In the tested command the smallest input is **6.605354095186351266 ZTO**. Its estimated output is **0.000101010101010102 IMD**; the rounded planning minimum is exactly **0.0001 IMD**. One ZTO raw unit less gives a minimum of **0.000099999999999999 IMD**. The result required 69 local quote probes; `demo-report.json` is the saved output. Change `--input` to `IMD` to search the reverse direction. `--snapshot` accepts another workspace ZTO Path observation, including one collected by ZTO Refresh or Archive.

## What happened when tried

The command above returned `target_reached` offline. A target above a 1-ZTO ceiling returned `target_unreachable_within_ceiling`. A 10,000-IMD target against a 1-billion-ZTO ceiling returned `target_not_reached_in_coverage`; it did not infer an answer from a partial quote. The focused real-observation suite passed five tests in under a second, including reverse direction, raw-unit rounding and invalid controls:

```sh
python3 -B -m unittest discover -s line-1/tools/zto-target -p 'test_*.py' -v
```

Exit 0 means a directly checked target input; exit 2 means the target was not reached within complete recorded coverage; exit 1 means invalid input or evidence. Output includes the snapshot's canonical SHA-256 and block, plus the chosen threshold pair. The search assumes exact-input output is nondecreasing across the complete range for this fixed pool state; it checks the final adjacent pair, but does not prove a general theorem about arbitrary hooks. This pool's captured hook and fee settings are validated by the sibling decoder.

This is historical planning arithmetic, not a current price, executable transaction or receipt guarantee. Liquidity, settlement, token behavior, gas and MEV can change the actual outcome. All code is Python standard library plus ordinary committed sibling `zto-capacity/`, `zto-path/`, `zto-review/`, `zto-sizes/` and `zto-band/` source. It never reads an environment variable, key or wallet, signs or sends anything, or contacts the network. No new coin is needed: the real ZTO/IMD pool is the subject.
