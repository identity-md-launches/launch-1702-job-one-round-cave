# Release Gate and wall checks

The focused offline `release-gate` suite passed: 10 tests cover the real
ZTO-first replay, exact binding of all four call fields, unknown member refusal,
expiry, set mismatch/incompleteness, strict request schema, immutability, CLI
exit classes, and a network-disabled demo. The documented demo returned
`ready`, exit 0.

`finish_wall_34.py` confirmed both required PNG paths are identical RGB PNGs at
1254 × 1254, and made `34.jpg` as a 512 × 512 JPEG under 100 KB. It found 9,949
changed pixels inside the composited addition rectangle and zero outside. The
full PNG and JPEG were visually inspected; the inherited five-digit Pepe hand
remains, no hand was added, and no writing was observed. `delivery-checks-34.json`
records the exact dimensions, formats, hashes, byte counts, and inherited visual
limitation.
