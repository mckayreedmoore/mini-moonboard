# Knee bridge washer: one bounded reference

**Parent run complete: sampled elastic proxy 174.478 MPa, index 0.697914 against the existing assumed 250-MPa yield. Proposal remains unadopted.**
This packet runs one fine polar plate/contact envelope for the
receipt-bound proposed knee-spine bridge bolt ties. It does not add a capacity
criterion or change the proposal geometry.

## Frozen demand and support

The load source is
[`knee-spine-reinforcement/attempt01/checks.json`](rawlocal/knee-spine-reinforcement/attempt01/checks.json),
SHA-256
`c9360e7ca4ab167a5cbc505373b2bd1342aa6a830f72a26113da9f7c4a8ad778`, bound
by its parent receipt. The producer checks the receipt-bound outputs and keeps
the original 12 body cases and 984 v-cuts. It takes the already factored
**1.25 uniform-force-margin** tie forces from all 12 cases: 24 bolt loads and
48 washer-end loads, with each bolt's tension repeated at its two ends.

The envelope peak is **T=1060.6566047532085 N**, from `k12-right` on
`knee_outer_right_spine`, proposed bridge bolt 2. This peak already includes
the 1.25 proposal factor. The producer applies no additional factor and sets
**M=0** for every end. Proposal witness and full per-case load mapping stay in
the output.

The frozen proposal records eight fully backed annular lands, four on each
spine: washer OD/ID/thickness `25.4/8.3058/2.5 mm`, proposed bore diameter
`7.5 mm`, and positive edge/neighbor-bore clearances. The producer reuses
those receipt-bound land records and their dimensions/clearances; it performs
no CAD or geometry regeneration. Those records describe proposed geometry,
not inspected stock or hardware.

## One concentric M=0 solve

Reuse `retail-washer.py::load(edge)` and the existing
`upper-right-washer-edge.py` fine model, rigid-mode diagnostic, engineering
coupon and `solve_state`. The frozen baseline is
[`retail-washer-suite/attempt01-fine/checks.json`](rawlocal/retail-washer-suite/attempt01-fine/checks.json),
SHA-256
`3e2dee327dbd81d8584955de3c4918c9acc695b0386fa46abd568ba767c64f74`.
Model must match its family and fine resolution exactly: 4/12 radial elements,
Fourier order 8, 128 angles and 1142 unknowns; E=200,000 MPa, nu=0.30,
Fy=250 MPa comparison, Kwood=20 MPa/mm and Khead=10,000 MPa/mm.

The synthetic saved-rigid-contact state is analytical and concentric. For
`ri=4.1529 mm`, `ro=12.7 mm`, head radius `5 mm`, and peak T, set
`Awood=pi*(ro^2-ri^2)`, `Ahead=pi*(5^2-ri^2)`, contact closures
`T/(Kwood*Awood)` and `T/(Khead*Ahead)`, and both tilts to zero. This state
seeds the existing Newton solve only; the output contact forces and plate
fields come from that solve.

One peak solve envelopes the lower listed tensions only under **positive
homogeneity for this fixed model**: same M=0 geometry, elastic plate/material
hypotheses, zero initial gap, no preload, and fixed Kwood/Khead. It gives no
actual washer capacity. Product yield/resistance, installed contact, 3D edge
stress, bolt-end moment demand, joint compatibility and complete-joint
acceptance remain unestablished.

## Parent execution

Producer API: `run(output)`. Producer SHA-256:
`1cf5476e3787fcf67668cf79a5214526f340f8b2cb27fcc15c77f103b9b4a737`.
From repository root, use a fresh output directory:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-bridge-washer.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-washer/attempt02
```

The ignored output records source pins, input snapshots, `fields.csv`, checks,
receipt and full STOP details including the last accepted state. Parent performed
the serialized plate run. Wood/head contact peaks are **2.6101 / 55.3751 MPa**;
force residuals are below 0.000000001 N. All 72 source pins and receipt outputs
match. Attempt02 corrects only a stale grain-status sentence; its state, coupon
and `fields.csv` are identical to preserved attempt01. No CAD/frame/native solve,
software test or agent review ran.

Saved `rawlocal/knee-bridge-washer/attempt02/checks.json` SHA-256 is **d3ad497f8990bca5f18d691d77cd90646b3d40a09d02331c6adf36aa900a2a9d**; receipt **041067657335395f4b1723a237e11574a0ed0b3efcba4e95f32e25db77d3630f**.

The proposal remains unadopted; the 47-criterion authority stays pending.
[Modified grain comparisons are complete](knee-bridge-grain.md); physical release is false. The separate
conditional bolt-length correction to **6.5 in** stays outside this washer
screen; preliminary 8 in fit wording supplies no numerical or
hardware-acceptance claim here.
