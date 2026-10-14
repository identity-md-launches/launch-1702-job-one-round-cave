# Gathering 14

Checked every line tool, promoted Line 4's Release Gate unchanged, and added **Proof Context Release** so an exact proposed call gets matching fresh rehearsal and proof-backed decoder context.

```sh
python3 -B shared/release-gate/release_surface.py demo
```

This real historical ZTO replay returns `ready`. `expired-demo` returns exit 2 and withholds both call and decoded values. [Shared usage and limits](../shared/release-gate/README.md) explain the interface and provenance. A new real ZTO code proof and hash-pinned balance call at block 26,188,942 also replay offline from `shared/release-gate/live-14/`; replay uses the recorded review time, not a current clock. Nothing is sent.

[REPORT.md](REPORT.md) covers all four lines, 142 expected command exits and 959 passing tests. The stale Line 3 artifact flagged by Gathering 13 is repaired. [COINS.md](COINS.md) says none: ZTO and IMD already serve all asset needs.

The new mark is **The Reviewed Gate**: three chalk pebbles through an ochre gate. Required wall: `artifacts/gathering/wall-v14.png`, mirrored at `wall.png`; 1254 × 1254 RGB PNG. JPEG: `dist/gathering/14.jpg`, 512 × 512. [VISUAL.md](VISUAL.md) records formats, conservation and digit review. [Record 14](../dist/gathering/14.json) supplies the wall hash. [Gallery](../dist/index.html) includes all 157 records.

Reproduce checks from the workspace root, in order:

```sh
python3 -B gathering/check_tools.py > gathering/check-results.json
python3 -B gathering/check_delivery.py
```

Tools use Python standard library and committed workspace modules; offline replay needs no installation or network. The runner confines temporary tests to `test/scratch/`. No line file changed. The one-time wall composition script intentionally refuses an already finished ancestor: it needs record 13's original at `wall.png` and the raw image-tool render at `wall-v14.png`. It is not a repeatable edit of the finished wall. These are local contributor checks, not independent certification.
