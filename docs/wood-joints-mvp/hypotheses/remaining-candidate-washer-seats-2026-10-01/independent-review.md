# Independent review: remaining candidate washer seats

Reviewed the frozen producer and README on 2026-10-01. Their hashes matched
the requested bytes:

- `check_support.py`: `a3cedb8e6fddf9d4080afd82cf12cf3e5a39658868baa478ad1f14eee7d07967`
- `README.md`: `9d8c9ebd6f7ba60fedf58e73baa3148aa5c34b55ae607a1889ead9262e2ca770`

From the repository root, the self-test passed. The full replay exited 1 as
documented and wrote its JSON only to `/tmp/remaining-washer-seats.json`:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/remaining-candidate-washer-seats-2026-10-01/check_support.py --self-test
.venv/bin/python docs/wood-joints-mvp/hypotheses/remaining-candidate-washer-seats-2026-10-01/check_support.py --check > /tmp/remaining-washer-seats.json
```

The partition is complete and disjoint: 92 candidate axes comprise the six
primary axes excluded by this packet, 32 axes in the two pinned upper cohorts,
and 54 axes analyzed here. The replay emits 108 unique outer seats across 54
bolts and imports 26 finished member STEP solids. It verifies the source input
pins, base and eccentric method hashes, upper-cohort exclusion hashes, each
model/manifest/STEP path and hash, and each imported solid's validity, face
count, and round-trip volume. The only three-receiver axes are
`knee_outer_right_side_1` and `_2`; seat derivation uses the first and last
receiver intervals, with no middle washer.

I confirmed the replay distinguishes 76 seats with 7.5 mm bores from 32 seats
with 7.3 mm bores. Both are separate from the conditional 6.35 mm nominal
smooth-body scenario. Every seat runs the three centered annulus cases and
inward/outward measurements at all depths (0.01, 0.05, and 0.1 mm). The
eccentric envelope uses the seat-specific bore and declared nominal radial
plays; it checks a continuous radial region in the BREP, not just the sampled
directions. Circle-only areas are explicitly marked inapplicable where that
envelope is not contained.

There is exactly one reported geometry exception:
`center_principal_right_2`, nut seat on `base_principal_center_right`. Its
centered support fractions are 90.5046% for CAD, 90.6001% for the plain
minimum-area catalog corner, and 90.0598% for the plain outer-envelope corner.
Its swept containment is 86.7211%, so `hole_only_applicable` is false; the
outward probes remain clear. The other 107 seats meet only the packet's
declared geometry screen. The companion
[`cut-diagnosis-review.md`](cut-diagnosis-review.md) independently traces the
exception to the retained F1–G1 service passage and checks the circular-overlap
area against the affected STEP. The replay status `GEOMETRY_EXCEPTIONS` and
exit 1 are therefore expected. They do not state a strength failure, adopted
criterion result, candidate rejection, or joint acceptance.

The producer and README stay within their claim limits: the body size and
catalog dimensions are conditional geometry scenarios, not delivered bounds;
the source BREP has no semantic cut inventory; no physical inspection,
pressure distribution, washer/wood resistance, native response, six-case
envelope, or joint acceptance is established. The single partial-support seat
remains unresolved for any resistance or load-transfer claim. I found no
material discrepancy between the frozen checker, README, and replay result.
