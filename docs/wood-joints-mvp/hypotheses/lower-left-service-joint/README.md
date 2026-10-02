# Lower-left outer service cleat: conditional working assessment

**Keep the reviewed geometry for the working scenario. This finite assessment
is complete; complete-joint qualification and physical release remain HOLD.
The full 47-criterion authority and eight release flags are unchanged.**

Scope: `left_service_outer_lower_cleat`, duty
`clip_horizontal_lower_left_1`, joining `base_rail_service_lower_left`
and `base_side_left`. The common reviewed cleat is 88.9 × 88.9 × 119.7 mm,
with four quarter-inch bolt axes in two orthogonal pairs at 33 mm pitch.
No member, bore, bolt axis or hardware geometry is changed.

## Decision worksheet

The assessment reuses the authenticated
[upper-service frame helper](../upper-left-service-frame-clearance-2026-10-01/check_frame.py)
and its original 50-body compliance operator. It changes the four selected
axis identities and common datum in a separate Python process, rather than
copying or modifying the source implementation. Lower-cleat lateral rows
are **96–103**, axial rows **1580–1583**. The helper's upper-specific tension
display is replaced by the authenticated lower-axis values and independently
checked against the saved vectors.

There are **84 states**: 21 authenticated saved states for each of three
clearance assumptions, plus 21 states with the lowest previously studied
target lateral stiffness at full clearance. Loads are **2× the recorded
proportional gravity-plus-climber loads**, including doubled gravity.
Peaks in one row need not occur at the same state.

| Relative bolt clearance | Target lateral law | Bolt shear / tension peaks | Local rail-to-side movement | Local rail-to-side rotation |
| --- | --- | ---: | ---: | ---: |
| 0 mm | Source, about 3,087 N/mm | 203 / 142 N | 0.090 mm | 0.178° |
| 0.50 mm | Source | 12 / 16 N | 0.749 mm | 0.093° |
| 1.15 mm | Source | 9 / 16 N | 0.782 mm | 0.091° |
| 1.15 mm | Hypothetical effective timber E = 150 MPa, about 958 N/mm | 9 / 16 N | 0.782 mm | 0.091° |

All 84 states fall below the inherited **provisional 1 mm movement / 0.5°
rotation targets**. These are development decision targets, not adopted
criteria. The zero-clearance force envelope is larger than the earlier
upper-cleat 100 N lateral study box, so that box is not transferred here.

Clearance allows the surrounding connections to take more of the transfer.
This supports retaining the cleat in the conditional frame model; it does not
show that the outer bolts alone carry the frame loads. The source Hillman
panel springs are unqualified, as explained in the
[existing panel-sharing check](../upper-left-service-panel-sharing-2026-10-01/README.md).
Other bolted joints retain zero clearance in this comparison.

## Motion, simultaneous loads and checks

Both interface loads are returned together, with signed global forces and
moments about the same datum. Receiver-datum moments are not assigned to bolt
bending. Both hosts are compared at the source cleat's rigid-body centroid:
`[-1085.85, 595.275244676, 1160.100552769]` mm.

Local movement uses all ten returned projections at each cleat/host interface,
including the elastic `e-H*f` contribution. The local six-coordinate fit's
largest residual is **0.00284 mm** across the grid, and **0.00134 mm** at
1.15 mm clearance. The report also retains the separate global rigid-body
coordinates; they are not interchangeable with this local estimate.

All 84 calculations satisfy the declared source laws and recorded floor
bearing/open signs. Force-bearing rigid-coordinate rank is **300** after
removing zero-force normal contacts and unloaded gap pairs. This prevents
the earlier arbitrary free-rotation/zero-force-contact issue from being
silently inherited. The saved-vector check independently rejoins raw
compatibility, body equilibrium, signed world-port moments and local fits.

The zero-clearance baseline matches all 21 scaled native source states within
**0.001 N / 0.000010 mm**, against the prior practical comparison tolerances
of 0.002 N / 0.0001 mm. Older exact DAT interval refusals remain unchanged.
No native solve or new solid operator is produced.

## Practical component screen

The following are **demand indices under explicit hypotheses**, not adjusted
resistances or joint capacities. Values are the worst over the full 84-state
grid; their governing states may differ.

| Quantity | Worst demand index | Reference or limitation |
| --- | ---: | --- |
| Individual-bolt lateral reference | 0.333 maximum unadjusted ratio | Reused six-mode single-shear method, hypothetical Fyb = 45 ksi / DF-L SG = 0.50 |
| Bolt combined steel scenario | 362 MPa / 634 MPa = 0.57 | Hypothetical steel yield; axial stress on a 0.189 in root, bending on nominal 6.35 mm shank |
| Quarter-annulus seat pressure | 2.67 MPa / 4.31 MPa = 0.62 | Hypothetical timber seat reference; 25% of nominal annulus area |
| Washer radial-strip index | 99 MPa / 250 MPa = 0.40 | Hypothetical steel reference; not a qualified plate/contact solution |
| Nominal projected host bearing average | 0.36 MPa | `V/(diameter × host depth)`; no timber resistance or grain adjustment assigned |

These reuse the earlier working scenario's explicit material hypotheses.
The assumed bending moment is `V × wood grip / 4`; it is **not a proven
upper bound**. Nominal shank bending and root axial stress do not qualify
the actual delivered thread transition or its stress distribution. The
washer strip index omits coupled head/nut contact and nonuniform plate stress.
At 1.15 mm clearance the corresponding steel, seat and washer indices are
approximately 0.027, 0.070 and 0.045, respectively.

The lateral screen reuses the
[existing single-shear reference helper](../remaining-single-shear-reference-2026-10-01/README.md),
with the lower-cleat's exact receiver lengths, proposed grains and each new
signed lateral force vector. Its maximum unadjusted ratio is **0.3323** at
zero clearance and **0.015** at 1.15 mm. It covers 336 bolt/states, with
189 explicit null references where the inherited helper treats the lateral
force as zero and its grain angle undefined. Those nulls are not assigned
zero capacities or invented directions. The two main/side assignments and
independent Mode IV arithmetic agree under the reused helper's checks.

The 45 ksi bending-yield input is a hypothesis distinct from the 634 MPa
axial steel scenario. NDS Table 12A's tabulated diameter range does not qualify
quarter-inch hardware. Contact, detailing, group and adjustment applicability
are not closed; this arithmetic does not establish an adjusted joint capacity.

The [existing grip screen](../../current-grip-screen.md) gives 127 mm wood
grip with 152.4 mm modeled shaft for each rail bolt, and 177.8 mm grip with
203.2 mm modeled shaft for each side bolt. The partially threaded length
comparators remain dimensional hypotheses, not a delivered-bolt inspection.
The [common-pattern geometry map](../../current-joint-family-reuse.md)
permits reusing the cleat/holes as a template; its two host bodies, installed
head-to-nut order and signed loads are checked separately here.

Finished-section strength, loaded/unloaded edge classification, splitting
and simultaneous orthogonal-group applicability remain unqualified. A low
average bearing index cannot close those checks. Recorded access envelopes
also remain distinct from turning/counterhold and an actual assembly sequence.

## Reused geometry and assembly evidence

The existing remaining-washer result contains **eight passing nominal seat
rows** for these four axes: rail heads on cleat, rail nuts on rail, side heads
on side member and side nuts on cleat. Each has full support of its CAD ring
and recorded Type A Wide envelope corners, including the recorded continuous
offset sweep. The source report's overall `GEOMETRY_EXCEPTIONS` status belongs
to a separate center-principal nut seat; it is not represented as a whole
report pass. Nominal support does not establish pressure or washer strength.

The existing exact-component access screen records six clear modeled component
movements per axis, **24 total**, including bolt withdrawal and nut/washer
slides. These are component routes, not a socket/extension corridor or a
qualified simultaneous turning/counterhold operation. The
[current transport hypothesis](../../transport-operations.md) stages block
stacks while frame faces are accessible, before panels and harness; support,
capture, tool use and full forward/reverse sequence remain assumptions.

The [geometry evidence join](results/attempt01/geometry-evidence.json) retains
the exact source paths/hashes and eight seat rows without rerunning CAD or
the primary's washer checker. It distinguishes raw grip dimensions from
partial-thread product comparators and physical inspection.

## Recommended next check and integration

**Next single check:** recompute this lower-cleat response in the main agent's
integrated frame, with the other working joint clearances and all six cases.
The isolated change here leaves the other bolts tight and covers only
A1-rear, A12-rear and K12-rear. Its favorable force sharing cannot establish
the simultaneous-clearance or missing-case result.

This packet remains active input to that integration. The original upper
packets, source checker, geometry and ignored evidence remain preserved.
No socket concept, new fastener, stock enlargement or frame redesign is
proposed. Main-agent worksheet integration should retain the panel stiffness,
floor support and unresolved local failure-mode assumptions.

## Evidence and reproduction

- [Producer](study.py): immutable-helper reuse, explicit lower mapping,
  84-state comparison and intrinsic equation/rank checks.
- [Comparison](results/attempt01/comparison.json): every state, simultaneous
  signed interface loads, common-datum motion and component indices.
- [Vectors](results/attempt01/vectors.npz): all `f`, `q`, `a` for 84 states.
- [Saved-vector check](results/attempt01/validation.json): source pins,
  raw equilibrium/laws, mapping and signed moment/fit joins.
- [Lateral reference comparison](results/attempt01/lateral-reference.json):
  336 bolt/states using the existing helper; [producer](reference.py).
- [Completion receipt](results/attempt01/receipt.json): final pins,
  reproduction comparison and main-agent integration summary.

The outputs are ignored evidence; retain them or the recorded external
archive when integrating. Reproduce into a fresh directory:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/lower-left-service-joint/study.py \
  --outdir /tmp/lower-left-service-joint-replay
```

Existing output directories are refused. No source or authority file, native
readiness flag, commit or push is changed by this assessment.
