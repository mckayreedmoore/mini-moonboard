# Bottom outer corner first-order transfer

[The producer](bottom-corner-transfer.py) provides the parent's finite six-case
connection calculation for both existing bottom outer cleats. It keeps the
original 100 mm frame load source and current geometry. Timber is rigid,
washers are concentric and rigid, and forces act at reference geometry.
Circular clearance, K20 bore/wood-seat contacts, bolt bending, direct axial
stretch and the original compression-only face laws are retained. Geometric
shortening and prestress stiffness are zero throughout.

The parent completed `first-order-attempt01` with exit 0 and status
`COMPLETE_FIRST_ORDER_LOCAL_FORCES`: **12 block states, 24 host states and
48 bolt states**. The existing source preparation extracted 24 full host
wrenches, 48 original simultaneous bolt witnesses and both cleats' nodal loads.
The largest source whole-cleat residual component is `3.079e-10` in N or N mm;
nodal loads reproduce mapped W within `8.35e-14`. Each cleat's mapped weight
is counted once; neither host drive receives added weight. These are source
bookkeeping results; the completed local calculation establishes first-order
force compatibility under the declared assumptions, not joint acceptance.

| Maximum independent absolute component residual | Left | Right |
| --- | ---: | ---: |
| Host force, N | 5.128729e-7 | 9.719772e-5 |
| Host moment, N mm | 2.628747e-5 | 9.913583e-4 |
| Whole-cleat force, N | 5.129874e-7 | 1.402330e-6 |
| Whole-cleat moment, N mm | 1.964688e-5 | 6.837206e-5 |

Two same-state witnesses, each from its own side's `side_1` bolt:

| Side / case | Axial tie, N | Simultaneous bore lateral, N | Smooth elastic steel proxy, MPa |
| --- | ---: | ---: | ---: |
| Left / A1-rear | 203.597774 | 243.434807 | 71.254430 |
| Right / K12-rear | 5.283067 | 4.842288 | 1.205204 |

The parent also completed all four cantilever/centered-seat coupons; maximum
cantilever relative error is `2.628e-12`. These are method checks, not wood,
washer or delivered-hardware qualification.

The parent completed the [bottom component replay](bottom-corner-components.md)
once on these same **48 bolt states**, with status
`COMPLETE_SAME_STATE_COMPONENT_REFERENCES`. Its maxima are 0.3978064027
(45 ksi lateral), 0.2782172875 (92 ksi lateral), 0.2804753033 (steel reserve),
0.0365524248 (finished parallel path), 0.2293396147 (mean supported seat)
and 0.1123324054 (smooth elastic bolt stress / 92 ksi). Each maximum belongs
to its own simultaneous state. The existing model, current geometry, original
100 mm load source and simple hypotheses remain the MVP basis; all acceptance
and release flags remain false.

## Geometry bindings

| Interface, on each side | Host / cleat grip | Bolt / bore | Physical outer order |
| --- | --- | --- | --- |
| Bottom rail | 38.1 / 88.9 mm | 6.35 / 7.5 mm | Cleat head, host nut |
| Side | 88.9 / 88.9 mm | 6.35 / 7.5 mm | Host head, cleat nut |

Each host retains its own two bolts and **four** original face cells. All
eight bolts use their own quarter-inch washer family, ID/OD
8.3058/18.4658 mm, and the declared 10 mm flat bearing land. Existing bottom
seat support, changed-side-host support rechecks, finished opening intervals,
grain and STEP identities are included in preparation. No top geometry or
top force field is reused.

The adapter binds the helper's span and DOF scale to 127 mm for the rail and
177.8 mm for the side. Its equations and numerical constants remain frozen.
The computational axis runs from host to cleat; returned labels preserve the
actual reversed rail head/nut order. Source ties lie at outer wood seats;
their full D-row moments are retained. The rail face normal differs from its
bore axis by `2.423e-10` per component; the adapter uses the original face
normal in both opening and force recovery. No tolerance is enlarged.

## Parent API and completed run

- `prepare()` returns `(prepared, pins)` using saved arrays and geometry only.
- `known_answers(prepared)` runs the existing 10 N cantilever coupon on each
  actual span and a centered 100 N series-seat closure coupon. The parent
  completed these in the recorded run.
- `run(output)` runs those coupons, then six cases for both cleats: 12 block
  states, 24 host states and 48 bolt states. The recorded run is complete. It writes
  `checks.json`, a producer snapshot and a source/output receipt in a fresh
  owned child. The parent owns serialization.

The run independently sums each host's bore, own wood-seat pressure and face
actions, then the four-bolt whole cleat plus its nodal weight once. Pressure
centroids carry their moments once. Host tolerances remain 0.001 N / 0.2 N mm;
whole-cleat tolerances remain 0.002 N / 0.4 N mm. A STOP preserves completed
states and current diagnostics without claiming physical incompatibility.

The existing output below is complete and preserved; no rerun is requested.

```sh
packet=docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python "$packet/bottom-corner-transfer.py" --parent-run \
  --output "$packet/rawlocal/bottom-corner-transfer/first-order-attempt01"
```

Without `--parent-run`, the command only prepares sources. The available
[readiness packet](rawlocal/bottom-corner-transfer/preparation-attempt02/readiness.json)
and [receipt](rawlocal/bottom-corner-transfer/preparation-attempt02/source-pins.json)
record **all 26 exact consumed paths and hashes**, including the six current
finished STEP identities. The earlier preparation snapshot remains preserved.

| Artifact, relative to this folder | SHA256 |
| --- | --- |
| `bottom-corner-transfer.py` | `2b05f8a789ed1098d66a0b482c3c4531379a3b5c5bb538ef80f46adfc5356d77` |
| `rawlocal/bottom-corner-transfer/preparation-attempt02/readiness.json` | `e8ca5bbcb38747bb2641928da5927ab9698cf079574ced37dc391903a4b8ec25` |
| `rawlocal/bottom-corner-transfer/preparation-attempt02/source-pins.json` | `cde4ba038b58eb58acb534d5a6a944af0a7ea6e494bcc3e6b99711913f513628` |
| `rawlocal/bottom-corner-transfer/first-order-attempt01/checks.json` | `4d255ba5ebd8f1f93fb41ef90511eb3da49906f4729f33f5f63766e0a0bd78ed` |
| `rawlocal/bottom-corner-transfer/first-order-attempt01/source-pins.json` | `5fdeb9927a759644f5c25d462b532fcd2bb9d2f389f69b462b716f33857fcb51` |
| `rawlocal/bottom-corner-components/attempt01/checks.json` | `39e698d7ffec6646e2295f5ce96be0764ea8fbe6654ed3b0e881040b410bcc95` |
| `rawlocal/bottom-corner-components/attempt01/receipt.json` | `7a241d0e035167c2d920277d9c9f33ac12a919531d2b37c74c6819a0fd58e2ff` |

The completed [result](rawlocal/bottom-corner-transfer/first-order-attempt01/checks.json)
and [receipt](rawlocal/bottom-corner-transfer/first-order-attempt01/source-pins.json)
bind the unchanged producer at `2b05…`; its executed snapshot has the same
full producer hash listed above. Parent now owns that producer. This
annotation reads existing results only; it performs no rerun, test, CAD or
new study. Both bottom producer/note pairs are frozen for parent handoff;
final note hashes are supplied separately to avoid self-hashes.

The original assessment/model/rows/operators/comparison/response bindings
remain `1a82… / b5f9… / cdf2… / c948… / bea6… / 0625…`. Exact hashes are in
the receipt and producer. The reused first-order producer is
`6e3f899ac99d6eef629ac12570b6ea31ea5c3914467c1c7399b7bcdd8d320563`;
its top method receipt is
`b15b57d3879fdca2dac607d11a2ad127acd1008f6c2a6f546333a1b26c754cfe`.
The pressure/action helper is
`2834a9a9fd25083da16034b498b3356197a4a6b2b53ffb35663077c5f93f7764`.

Ruff passed. No mechanics, coupon, CAD, native, frame, heavy run, test or
review loop was executed by this implementation task. The parent's completed
local calculation supplies reference-geometry load transfer only. Finished ligament/group
resistance, radial bore-wall fields, washer metal and actual hardware
qualification remain outside this packet; no Ft-perpendicular or group
capacity is invented. Formal acceptance, complete-joint acceptance,
fabrication and physical release flags remain false. Counterpart claim gates
and other owners' files are preserved. This producer, this note and its
ignored raw preparation remain active; nothing is archived, pruned, staged
or committed.
