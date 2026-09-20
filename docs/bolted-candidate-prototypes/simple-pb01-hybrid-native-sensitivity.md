# PB-01 one-cleat hybrid native sensitivity

Status: **numerical diagnostic only; not V4 same-case demand, G1, or drilling release.**
The frozen source set is PR branch commit `49c733b`; all three runs carry
the same 260-entry native-plus-producer SHA-256 manifest, including the
hybrid adapter, pose generator and pose JSON. The physical panel is
kerf-right and all 66 fixed panel/kicker screw axes remain modeled. One
3/8-in trial four-bolt cleat replaces the lower-right ML24Z station;
**23 other angle/SDS stations remain old-topology proxies**. Bolt springs,
one-point interface contacts, and trial steel-stack mass are provisional.
The separate 1/4-in geometry pose was **not** used in these native runs.

| Unchanged case and search | Cycles | Contact | Global/member/MPC | Maximum panel displacement | Numerical gate |
| --- | ---: | --- | --- | ---: | --- |
| `a12-left`, all-contact update | 14 | converged | pass/pass/pass | 14.6752 mm | pass |
| `a12-forward`, all-contact update | 14 | repeated active set | pass/pass/pass | 13.5548 mm in final nonconverged cycle | fail |
| `a12-forward`, seeded one-at-a-time | 14 | converged | pass/pass/pass | 13.5736 mm | pass |

The forward retry loaded the **same cached source-authenticated model**.
It seeded 118 normal contacts from cycle 13 of the nonconverged all-contact
run, then changed only the contact-search pivot strategy. The seed report's
SHA-256 is `1660199a1c0809fc34124f41670b9b7cbef3d928afe30bdd6d622372b7cb3f91`.
An unseeded one-at-a-time attempt was interrupted after ten partial cycles:
it began with hundreds of contact inconsistencies and was not a useful
bounded search. Its partial forces are not evidence.

The three completed report SHA-256 values, in table order, are:

1. `f223602796ae5667d2fea5f79d42fa6ae53a2ffcc4d96b4e11a1f6fd9dd731ba`
2. `1db2de8117d5502ea0da25e0c48dc588f7f53622c00da992e242e4ccf2db0090`
3. `6ccb7ea126ca68cdf835ba5bc855290d4285f37d274eac84ce3e31cac597def9`

Their retained raw directories are under `/tmp/mini_pb01_hybrid_*_49c733b`
on the working host; `/tmp` is not durable storage. The fresh default runs
can be regenerated with the [source-fingerprinted runner](../../scripts/simple_pb01_hybrid_diagnostic_run.py).
The seeded continuation additionally requires the native runner's cache,
`one_at_a_time` strategy and the recorded seed normal-contact set. Do not size the
cleat, bolts or frame from these proxy-topology forces. Next evidence must
replace **every** old connector duty in one coherent candidate, qualify
the actual product/wood/washer/group and contact inputs, and run all six
unchanged cases on that candidate.

## Later quarter-labelled mass sensitivity

At source commit `55c2f75`, the separate `--variant quarter` hybrid
`a12-left` run converged in 14 cycles and passed global, member and MPC
numerical gates. Its maximum panel displacement was 14.6742 mm. The trial
four-stack mass was 0.33158 kg, versus 0.51951 kg for the earlier 3/8-in
run. Its report SHA-256 is
`151e154575585d5c8749395900ac5afa004142e6686cdf8eca1b19e989169dbd`.

This **is not a bolt-diameter response study**. The 1/4-in and 3/8-in
records have identical bolt centerlines; the nominal bore change does not
alter this mesh, and both use the same arbitrary 1,000-N/mm spring and
single midpoint face contacts. Only the provisional trial stack mass
changes in the native model. The separate CAD screen, not this run, tests
the 1/4-in bore's local fit. The 23 legacy proxies and all resistance
limitations above still apply. The quarter run's raw output is under
`/tmp/mini_pb01_hybrid_quarter_a12_left_55c2f75` on the working host.

## Subsequent contact-model correction (not a historical rerun)

The source after these archived runs replaces each single midpoint face
contact with four interior, compression-only samples on the actual seated
overlap. The earlier source had a row-axis rotational release at each
isolated interface because both bolt points and its contact point were
collinear. The four-point quadrature can transmit a contact couple while
closed and releases each point when it opens. Its total normal stiffness
remains a provisional input, now independent of bolt axial and lateral
stiffness. The historical SHA-256 values and results above describe the
**old** contact idealization and cannot be reused as results of the new one.
No physical seating stiffness, contact-pressure distribution, or V4 demand
bound follows from this correction alone.

One new source-authenticated `a12-left` quarter-labelled run at commit
`4c60e46` used the four samples per face and three separate default
stiffness inputs (each 1,000 N/mm; face value is the **total** per
interface). The all-contact update converged in 14 cycles; global and
member equilibrium passed, and maximum panel displacement was 14.6739 mm.
Its report SHA-256 is
`c10b2b2d1b979fe82ffc5bca31c60e374650610e4c44245e8e56431c7b0c4918`.
The raw directory is
`/tmp/mini_pb01_quarter_contact4_a12left_4c60e46`; it is temporary.
The report retains a 260-entry native-plus-producer source manifest, 23
legacy proxy stations, and explicit diagnostic/no-design/no-drilling scope.
This run is a numerical smoke test of the changed contact idealization,
not a calibrated stiffness study or a V4 same-case demand.
