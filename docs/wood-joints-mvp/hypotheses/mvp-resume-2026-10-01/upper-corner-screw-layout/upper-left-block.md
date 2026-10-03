# Upper-left common-cleat transfer

Updated October 2, 2026. **Parent execution completed all six cases and twelve
host-pair solutions.** This is a finite local mechanics hypothesis, with no
numerical STOP. Parent owns subsequent resistance/splitting integration.
Current capacities, geometry, source frame forces and complete-joint HOLD
remain unchanged.

This finite scenario gives each of the two timber hosts one compatible
rigid pose, with all four bolts acting against one common rigid left cleat.
It uses the actual left-side stations, normals and six simultaneous source
wrenches. It does not transfer a right-corner result or assume symmetric
loads. The cleat's zero motion is a common rigid-motion gauge; timber/cleat
elastic deformation and whole-frame redistribution remain outside this
local model.

## Actual left geometry and ownership

The source has exactly 44 rows incident on `top_outer_left_cleat`: 22 joining
`base_rail_top` and 22 joining `base_side_left`. Each interface has two bolt
lateral planes per bolt, two axial ties and sixteen unchanged face-contact
cells. There is no third interface or omitted cleat connector in this source.

| Interface | Bolt IDs after `top_outer/clip_single_top_left_1/` | Diameter / bore envelope | Host / cleat grip | Existing radial gap in each receiver |
| --- | --- | --- | --- | --- |
| Top rail | `rail_1`, `rail_2` | 6.35 / 7.5 mm | 38.1 / 139.7 mm | 0.575 mm |
| Left side | `side_1`, `side_2` | 7.9375 / 9.0 mm | 88.9 / 88.9 mm | 0.53125 mm |

Both modeled bolt grips total 177.8 mm. Actual delivered smooth shank,
threads, nut seats and tool access are not established by that sum. The
diameters and bore values are the existing analysis inputs, not drilling
instructions. Rail pitch is 33 mm; side pitch is 67.85 mm.

The rail interface midpoint is
`[-1084.85,1449.925650780383,2178.633244419241]` mm. Its host-to-cleat axis
is approximately `[0,-0.642787609929,-0.766044442915]`. The side midpoint
is `[-1130.3,1405.026936228858,2125.125040079900]` mm with axis `[1,0,0]`.
Their finished sampled contact areas are 10552.972706647 and
16594.855497693 mm². The source face normal and compression-only stiffness
remain tied to every actual left row.

One common cleat datum is the mean of its unique saved physical nodes:
`[-1085.85,1405.026936229123,2125.125040079677]` mm. It supplies the common
reference for both host motions and all net cleat forces/moments; it is not
silently replaced by a right-side coordinate or assumed center of mass.

## Source wrenches and gravity

The exact current six nominal-clearance states are A12 rear, A12 forward,
A12 left, K12 right, K12 rear and A1 rear. Source connector wrench on each
host comes from that state's actual interface rows in D and its saved raw
force vector. The negative interface wrench is the local host drive.
Individual source bolt forces are comparison values and numerical seeds;
the compatible local solution may redistribute them.

When shifting a wrench from body datum b to common cleat datum c,
`M_c = M_b + (b-c) cross F`. Rigid host translation is shifted using
`t_c = t_b + theta cross (c-b)`. Source scaled rotational columns use
moments divided by 1000; local beam pose scaling follows the unchanged
177.8 mm grip convention. These scalings must remain distinct.

At the common cleat datum, the saved applied W load is approximately
`[0,0,-10.530841176;-38.512328660,-7.883118764,0]` N/N mm, the same in all
six cases after the recorded dead-load factor. It includes the existing
mapped hardware/gravity contribution and couples. It is not the bare
timber-only weight. The producer retains it once in whole-cleat balance;
gravity is not added again to either host interface drive.

Both source and derived host interface wrenches are reported at the same
cleat datum. The corresponding reaction on the cleat has the opposite
force and moment, including bolt-seat moments and all face reactions.
Those two reactions plus the saved cleat W form the whole-block equilibrium
account. This is equilibrium of a rigid common-cleat scenario, not a wood
stress field, splitting resistance or full-frame compatibility result.

## Reused conditional mechanics

The producer uses two private instances of the frozen shared-host mechanics:
one for the rail pair and one for the side pair. Both share the same fixed
rigid cleat reference. Their axes, face rows, transverse bases and datums
come from the left records; no right-side force or pass is adopted.

One existing middle branch is used: hypothetical bolt E=200000 MPa,
wood bore/washer-seat K=20 MPa/mm and head contact K=10000 MPa/mm. Source
face-contact modulus remains 100 N/mm³. The existing two beam bending
planes, eight elements per receiver, unilateral radial bore contacts,
tilted circular head/washer/wood contact and positive-tension axial
compatibility law are retained. No preload, friction, adhesion or new
material law is introduced.

Rail and side washer envelopes retain the helper's existing declared
dimensions and hypothetical bearing circles. Rigid washer contact moments
do not supply washer bending resistance. Smooth-bolt sectional stress
proxies and any assumed steel reference stay separate from delivered
hardware, thread-root response and actual capacities.

## Completed finite responses

The parent ran the frozen producer at
[rawlocal/upper-left-block/attempt01/checks.json](rawlocal/upper-left-block/attempt01/checks.json).
Its status is `FINITE_SHARED_HOST_POSE_BLOCK_HYPOTHESIS`, with no failure.
The receipt contains all twenty-four bolt states and 192 face-cell states:
four bolts and thirty-two face cells in each of the six source cases. Both
host motions and both source/derived interface wrenches are reported at the
common cleat datum in each case. No right-side state supplies a left demand.

Each entry below is compatible tension T / host-bore lateral resultant V,
in N, rounded to three decimals. Entries within a row belong to the same
case and local state. Rounded zero includes numerical reactions below
0.00002 N; it is not an asserted zero-capacity path.

| Case | `rail_1` T / V | `rail_2` T / V | `side_1` T / V | `side_2` T / V |
| --- | ---: | ---: | ---: | ---: |
| A12 rear | 596.727 / 467.523 | 352.569 / 452.290 | 351.458 / 0.000 | 499.388 / 961.538 |
| A12 forward | 497.425 / 389.874 | 299.663 / 376.021 | 282.056 / 0.000 | 444.382 / 804.734 |
| A12 left | 614.043 / 472.155 | 359.300 / 454.337 | 366.054 / 0.000 | 507.918 / 975.111 |
| K12 right | 72.673 / 28.483 | 72.429 / 33.777 | 45.251 / 0.000 | 76.656 / 89.746 |
| K12 rear | 100.281 / 41.764 | 101.982 / 63.616 | 60.454 / 0.000 | 110.789 / 132.060 |
| A1 rear | 11.031 / 0.000 | 11.073 / 0.000 | 4.587 / 0.000 | 6.043 / 6.776 |

These forces redistribute under the shared host poses. For example, in
A12 left the two original rail tensions were 660.676 and 202.379 N; the
compatible pair returns 614.043 and 359.300 N. The interface resultant is
retained through the simultaneous bolt and face reactions, rather than
through preservation or averaging of the original individual tensions.

| Case | Rail face compression, N | Rail active cells / 16 | Side face compression, N | Side active cells / 16 |
| --- | ---: | ---: | ---: | ---: |
| A12 rear | 675.981 | 4 | 902.413 | 3 |
| A12 forward | 560.169 | 4 | 759.073 | 3 |
| A12 left | 677.903 | 4 | 910.432 | 3 |
| K12 right | 79.196 | 3 | 115.342 | 3 |
| K12 rear | 120.519 | 3 | 150.788 | 2 |
| A1 rear | 13.735 | 4 | 10.630 | 3 |

Active counts use compression greater than 1e-7 N. Maximum sampled face
pressure is 0.495582 MPa. The complete per-cell opening, force, area and
pressure records remain in `checks.json` and `face-cells.csv`.

Maximum absolute whole-cleat balance residuals are 1.8155782e-5 N and
8.2786396e-4 N mm. Source-only balance residuals are 7.7521e-12 N and
7.6713e-10 N mm. Both balances use the exact saved cleat W once, including
its -10.530841176 N vertical force and existing gravity couples. The
derived interface forces do not receive a second cleat-weight load.

All twelve pair solutions meet the unchanged local numerical criteria.
Maximum local gradient is 6.0963475e-5 N; maximum absolute local force and
moment residuals are 1.8155786e-5 N and 3.9027546e-4 N mm. Maximum positive
tension axial-compatibility residual is 4.081e-15 mm. The A1 rail tangent
has nullity seven; the three A12 side tangents and the A1 side tangent each
have nullity one at the declared relative 1e-12 cutoff. Their reported poses
are representative nonunique equilibria. Other local tangents have nullity
zero. The output does not claim uniquely determined unloaded motions.

The maximum smooth-bolt sectional von Mises proxy is 174.810513 MPa at
`side_2` in A12 left, or 0.275588 of the hypothetical 92 ksi comparison.
No local state flags that hypothetical elastic limit as exceeded. Maximum
wood-seat mean pressure over the full washer annulus is 2.874356 MPa; its
ratio to the existing 4.309223 MPa mean-bearing reference is 0.667024.
Maximum sampled wood-seat point pressure is 6.370015 MPa. These diagnostics
do not make the point pressure a mean-bearing failure criterion or prove
washer bending resistance. Actual washer stress, washer capacity, delivered
hardware capacity and coupled-joint resistance remain null in the receipt.
Complete-joint acceptance and physical release remain false.

Parent's [same-state component replay](upper-left-block-components.md)
reports maximum lateral-reference ratio 0.722296, bolt bearing-path ratio
0.142295, mean-seat ratio 0.667024 and smooth-steel diagnostic ratio
0.275588, all in A12 left. Its checks SHA256 is
`25f0bb27a752f68d28ededb97017b1675d47751f44922d95d021d1b91e096420`.
These retain the existing conditional references; they do not establish
oblique-load or splitting acceptance or a complete-joint pass.

## Frozen evidence

Paths below are relative to this folder. The producer also pins the exact
helper dependencies it consumes.

| Source | SHA256 |
| --- | --- |
| `frame-250-attempt02/comparison.json` | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| `frame-250-attempt02/response.npz` | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| `operators-attempt02/operators.npz` | `c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3` |
| `operators-attempt02/model.json` | `b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626` |
| `operators-attempt02/row-identities.json` | `cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27` |
| `operators-attempt02/model-inputs.json` | `e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc` |
| `operators-attempt02/operator-assessment.json` | `1a82cd2adbfece3942bf8c90f593f1e21a150adb65db625135aadd258fd5024a` |
| `bolted-replay-results/corner-attempt01/component-results.json` | `401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6` |
| `upper-right-rail-pair.py` | `4243b53bbb7377753f0b1fdd73fa1aa6c80e1a96c99d428def88e82a899e6f96` |
| `upper-right-side-pair.py` | `ce07e9489d96fb251ee780ecb96cdbb38539b5d204922a74c39066095d9ac0cc` |
| `upper-right-combined-transfer.py` | `fba852724b82ee3cd28b0318bfdf156ac1786f85ac26257698d8d103c26c62b0` |

## Execution handoff

The producer is [upper-left-block.py](upper-left-block.py), SHA256
`7b07b3f575b7c7cac6dc69dfef83b02ec06c8bac5990ebf1a58f74e807498f6f`.
Targeted Ruff passed after restoring the selected source-row index list.
Neither the worker nor its bounded implementation helper ran the producer,
mechanics, native/frame/CAD execution or software tests. There was no staging
or commit by either worker.

The parent used the idle-ledger-locking CLI from the repository root, with
single-thread BLAS and no-sync UV. `build(Path(fresh_output))` remains the
callable API:

```sh
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/upper-left-block.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/upper-left-block/attempt01
```

The output folder must be new. This complete run returns six block states,
twelve host-pair solutions, twenty-four bolt states and 192 face-cell states.
Each case includes both host poses and source/derived interface wrenches at
the common cleat datum, plus whole-cleat balance with the current W included
once. `checks.json` retains full contact and bolt response; the producer also
writes host, bolt, beam, bore, face and cleat-wrench CSV receipts, source pins
and a byte-exact producer snapshot. A numerical STOP retains successful prior
host responses and the failed state's debug data, without a relaxed retry.

All twelve source pins and nine output bindings in `source-pins.json` were
authenticated against their recorded bytes after the parent run. The
executed producer and saved snapshot remain byte-exact at the SHA256 above.
The completed output hashes below are relative to
`rawlocal/upper-left-block/attempt01/`.

| Output | SHA256 |
| --- | --- |
| `checks.json` | `5e8c52e529f58f9276c4c67f554fa0b74a990dd501e347e59434aa244e628ed0` |
| `source-pins.json` | `1d6dc81e530cefe641e12d120c0f64d912eb773ff3b3634b2e55190acaf5d9e8` |
| `states.csv` | `ac40f507c74e74bab9dca6ff5c6671b127bdb87147b5cf50769dc9a60bcd095e` |
| `bolt-states.csv` | `618328da65550f386482b870766d93d47048cd7cb6b6e93afe8aa261bd6aeea3` |
| `beam-fields.csv` | `96980313594928b7f73f3116bdfe71d2b14201a0f46d2a1e00587bfc117f619a` |
| `bore-fields.csv` | `4526c2a8479cd1e33b3e5272d65cb61280b02c202a34cf8514b4c4ec25fdbeaa` |
| `face-cells.csv` | `92a31c43896f41c1af226df1532c26c3dc1aefa2f423eea6bba650b25f5d2693` |
| `cleat-wrenches.csv` | `cacf49516719f0a963f0315075d1311985434ac2c4545b32278a26ec1ba5f3cd` |
| `producer.py.snapshot` | `7b07b3f575b7c7cac6dc69dfef83b02ec06c8bac5990ebf1a58f74e807498f6f` |

No further mechanics run, retry, law sweep or geometry change was performed
by the worker. Parent owns same-state resistance and splitting integration,
shared staging and publication.
