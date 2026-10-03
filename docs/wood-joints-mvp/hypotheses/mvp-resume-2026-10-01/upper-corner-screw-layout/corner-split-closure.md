# Corner splitting: necessary normal-transfer census

## Objective

The owner reopened the cross-grain splitting gap after completion of the
[conditional four-corner assessment](corner-group-finish.md). Preserve that
packet and its loads, geometry, material references and results. Address the
gap by first identifying actual tensile normal-transfer requirements in the
saved model, then evaluating a supported resistance path where needed.

The former 0.169987975 MPa maximum is the positive edge stress of one affine
normal field. Its cut has a compressive normal resultant. That diagnostic does
not establish that every possible normal-traction distribution needs tension.
The first calculation below answers that narrower question over **all four
blocks, six cases and 51,312 transverse cut limits**. It does not assign a
splitting capacity or qualify a complete joint.

## Frozen input and geometry

| Input | SHA-256 |
| --- | --- |
| Four-corner attempt03 checks | `2ae3a84f273823dc6ca751e6fdddab8e0d70425ee7b34e1e38ebc79d5b672f23` |
| Complete signed cut inventory | `a60131eaeff3e5bb46579156d31fbfe3423de2848ac2bbb202901013697a5627` |
| Original receipt | `f1d8ad0f204be457f5b8eba2e8185828456251ae7fb67aa945bb7477bacd2f62` |

Top blocks retain 88.9 × 139.7 mm sections; bottom blocks retain approximately
88.9 × 88.9 mm sections. Grain length is approximately 119.7 mm for all four.
The saved geometry is the rectangular blank minus four disjoint transverse
through bores, with positive grain-end bore clearance.

For either transverse plane, all four outer rectangle corners lie at the
grain ends and remain material. The circles or through strips removed by
the interior bores do not remove those corners. Consequently the **convex
hull of the exact retained section is its outer rectangle**. This is checked
from the saved bore stations/radii, not assumed for arbitrary future geometry.

Side bolts run along local `u` and cross `u`-normal grain-parallel planes. Rail
bolts run along local `v` and cross `v`-normal planes. Each current bolt has one
outer washer on the cleat and one on the host; the opposing host/cleat contact
is part of its load path. Geometric crossing alone is not an independent
two-washer tie inside the cleat or an added reinforcement capacity.

## One finite normal-equilibrium method

Read each original full signed cut `[N, Vp, Vq, T, Mp, Mq]`. The normal
traction must recover `[N, P, Q] = [N, -Mq, Mp]`, where `P` and `Q` are its
first moments on the plane. Let the retained support hull have center
`(pc,qc)` and half widths `(hp,hq)`. Define, in newtons:

```text
mp = (P - pc*N)/hp
mq = (Q - qc*N)/hq
S = max(abs(N), abs(mp), abs(mq))
minimum tensile normal resultant = (S + N)/2
compression at that minimum = (S - N)/2
```

For any signed normal-force distribution, tensile force plus compressive
force must be at least `abs(N)`, `abs(mp)` and `abs(mq)`. The bound is attainable
by nonnegative tensile/compressive point weights at the four retained corners:
bilinear weights represent normalized coordinates `(mp/S,mq/S)` for tension
and their opposites for compression. The producer reconstructs all three
normal resultants from those weights.

This is an **exact resultant lower bound under unbounded point pressure**.
A zero bound establishes unconstrained compression-only normal equilibrium.
A positive bound establishes that the saved normal wrench needs tensile
transfer. It supplies neither finite wood pressure nor an actual tie allocation;
real ties at restricted locations may require larger loads. The original
`Vp`, `Vq` and `T` remain recorded and require their own resistance path.

The original nonzero equilibrium residuals are retained. Very small positive
bounds may reflect those source residuals. Both strict positive counts and
an informational above-1-N census are recorded; 1 N is not an acceptance
threshold or a changed source tolerance.

Parent executes five analytical known answers with the census: centered
compression, eccentric compression inside the hull, eccentric compression
outside the hull, a pure normal bending couple and centered tension. Each
retains nonzero shear/shear/torque as unresolved components. No software tests,
frame/CAD solve, native solve or general pre-split model is added.

## Resistance route and applicability

[NDS 2024 §3.8.2](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf)
provides mechanical reinforcement as a route when perpendicular tension cannot
be avoided. [NDS 2024 §§11.1.2–11.1.3](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf)
require applicable member/local connection mechanics and a procedure or tests
for the actual eccentric load path.

The [official 2018 commentary, C3.8.2 and C11.1.3](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf)
identifies stitch bolts/plates as mechanical reinforcement. This is historical
mechanism guidance, not a claimed 2024 commentary capacity. It does not provide
a universal stitch-bolt resistance for these cleats.

Any needed bolt bridge must cross the actual plane and transfer load through
its actual host/contact/head/nut/washer route. Its tension must be evaluated
with the existing simultaneous shear and bending, washer metal behavior and
supported wood bearing/anchorage. Current inward washer reactions are already
counted; no extra tension, friction or preload is credited by this census.
Embedded-screw withdrawal or glued-rod reinforcement rules are not capacities
for the current smooth clearance-hole through-bolts.

The next decision is driven by the named necessary-transfer witnesses. A
supported existing-bolt route would be assessed first. A required local
geometry/hardware change would be reported before altering the model. No
sawn-lumber `Ft_perp`, generic EC5 beam capacity or crossed-group capacity is
invented to close the gap.

## Parent execution

Prepared producer SHA-256:
`896679a90618276471f7610a258734ed0a7032e45d1e6284dfdb37eb2e08ca63`.
Formatting and lint passed. Three direct source hashes and the original
53 source hashes were authenticated without executing the arithmetic.

From the repository root, the parent executes the one frozen census:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/corner-split-closure.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/corner-split-closure/normal-census-attempt01
```

API: `build(output)`. Output must be a fresh owned child. The producer writes
a snapshot, result and source/output receipt. Its snapshot is the immutable
source binding for this phase; the live producer is checked unchanged during
execution. External frozen inputs retain absolute paths. Every original cut
and all six components remain available through the pinned compressed source;
new output stores the deciding same-state witnesses and 48 block/case/plane
census rows. No duplicate complete cut export is created.

## Result and next action

The parent completed `normal-census-attempt01`. The five normal-equilibrium
known answers were satisfied. Independent read-back authenticated all 57
source entries (56 prior inputs and the executed snapshot) and three output
entries. A concurrent attempted invocation stopped at the fresh-output guard
before writing anything; there is one result, produced by the parent.

| Census result | Value |
| --- | ---: |
| Four-block, six-case, two-orientation rows | 48 |
| Transverse cut limits | 51,312 |
| Compression-only normal hull feasible | 51,130 |
| Positive necessary tensile normal lower bound | 182 |
| Lower bound above 1 N, informational only | 0 |
| Positive affine edge stress with compression-only hull feasibility | 22,152 |
| Largest necessary tensile normal lower bound | 0.165250430 N |

The 182 positive bounds occur in only two block/case/orientation rows:

- Bottom outer left, `k12-rear`, `u`-normal: 32 cuts; peak 0.007744996 N
  at 0.587624855 mm, before the station.
- Bottom outer right, `a12-rear`, `u`-normal: 150 cuts; peak 0.165250430 N
  at 1 mm, before the station.

The deciding bottom-right full signed wrench is, in N and Nmm:

```text
[-2.633329550278461, -0.8854731804049458, 2.165231540761144,
 2.0737140936393126, -121.14791291840694, 131.74226173708774]
```

Its minimum normal tensile/compressive pair is 0.165250430 / 2.798579980 N.
The tensile point witnesses lie at the negative `v` edge; they are theoretical
hull points, not the positions of the actual side bolts. This lower bound
therefore is not a qualified bolt demand or a splitting resistance comparison.
It exceeds that cut's retained equilibrium disagreement and is not discarded
as a source tolerance.

The former 0.169987975 MPa affine peak, top outer right / `k12-right` /
`v`-normal / -69.8499 mm before, has a **zero** tensile normal lower bound.
Its normal resultant is -743.552400717 N. Compression at finite pressure,
the original shear/shear/torque and local anchorage still need their applicable
checks; hull feasibility alone is not complete-joint acceptance.

| Output | SHA-256 |
| --- | --- |
| `normal-census-attempt01/checks.json` | `49f7c143d5a7cda5ff0f3ac8e9ef8d1d8fdf8d8090db4a31f6090c346cf7e75f` |
| `normal-census-attempt01/receipt.json` | `aec19f2255d7be94f29d7f4b0d77efae1345063bf39357cb1ddc19b1477b830d` |
| Executed producer snapshot | `896679a90618276471f7610a258734ed0a7032e45d1e6284dfdb37eb2e08ca63` |

Next, use these saved witnesses to assess finite compression pressure and the
actual existing side-bolt/host route for the two positive rows. Existing bolt
actions remain counted once. No extra tension, preload or new hardware/material
capacity is inferred from the small lower bound. Splitting resistance,
complete-joint acceptance and physical/fabrication release remain unclaimed.

## Finite pressure and existing bolt route: completed follow-up

The first census used point forces with unbounded pressure. This follow-up
constructs finite, constant compressive pressures on two rectangles entirely
inside the bore-free grain-end bands. For a compressive normal resultant,
the required pressure centroid is `[-Mq/N, Mp/N]`. A transverse strip centered
at that centroid has width twice its minimum distance to either transverse
edge. Both grain-end bands have height no greater than the smallest grain-end
bore clearance or twice the centroid's distance to a grain end. Their force
fractions place the combined centroid at the required grain coordinate.

Every constructed patch therefore retains material, has finite area and
recovers the original `N`, `Mp` and `Mq`. Maximum pressure is compared with
the existing conditional DF-L No. 2 base `Fc_perpendicular = 625 psi`, without
a bearing-area factor. This is a sufficient construction, not an optimization.
A patch construction above that reference or with no finite area does not
prove that every other pressure distribution fails. Pressure redistribution
is not claimed to be an elastic compatibility solution or a complete local
stress field. Original shear/shear/torque remain explicitly recorded.

Four analytical checks cover centered compression, eccentric compression,
zero normal force with nonzero tangential components and a boundary centroid
that has no finite rectangle witness. There are no new software tests.

For the two rows with positive tensile lower bounds, the producer records the
two actual side-bolt positions, current simultaneous bolt stress witnesses,
both outer washer members/roles and current end moments/wood pressures. These
bolts cross the `u`-normal cuts and terminate on the cleat and its host. Their
existing inward washer loads are already present in the timber-only cut.
Consequently their existing shaft tensions cannot be counted again as spare
reinforcement forces. Under those fixed actions, compression-only equilibrium
still fails at the named positive-bound cuts. A justified reaction
redistribution or reinforcement mechanism is still needed; no added axial
force, preload, friction, washer capacity or anchorage capacity is assigned.

Prepared follow-up producer SHA-256:
`e090270a3bea195800ed3b04b806fe4ea0c5e221ae57faf01f602c8dba769d5e`.
The original executed census snapshot remains unchanged and is its replay
source. The live producer now also exposes this follow-up:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/corner-split-closure.py --finite-pressure --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/corner-split-closure/finite-pressure-attempt01
```

API: `build_finite_pressure(output)`. The parent executes this arithmetic.
The parent completed `finite-pressure-attempt01`, exit 0. Independent read-back
authenticated 59 source entries and three output entries; all four analytical
known answers were satisfied.

All **51,130 compression-hull-feasible cuts also have finite, bore-free band
pressure witnesses below the existing conditional compression reference**.
There are no zero-area witnesses or above-reference constructions. The 182
positive tensile bounds remain unchanged and are not included in that pressure
claim.

| Deciding normal-pressure witness | Result |
| --- | --- |
| Maximum construction | Bottom outer left / `k12-rear` / `u`-normal / 0.305997877 mm before |
| Maximum constant pressure | 1.711917153 MPa |
| Existing conditional `Fc_perpendicular` reference | 4.309223308 MPa |
| Pressure/reference | 0.397268146 |
| Former top-right affine opening peak | 0.460913817 MPa compression; reference ratio 0.106959836 |

The maximum-pressure construction concentrates two small forces on narrow
end bands (each 1.014105541 mm²). This is an explicit finite equilibrium
witness; it is not a claim that such a narrow field occurs in actual wood.
The former top-right affine peak instead has a broad 1,613.213521 mm²
compression patch carrying 743.552400717 N. Neither result supplies elastic
compatibility, wood fracture resistance or an opened-crack shear path.

The two positive-bound rows each have two actual side bolts crossing the
named plane. The saved bottom-right `a12-rear` tensions are 3.418451131 and
0.494036973 N; the bottom-left `k12-rear` values are 3.205190919 and
0.463216259 N. Their local `v` stations are approximately -16.45 / +16.55 mm,
with grain stations approximately 59.85 mm. Each has its head washer on the
side host and nut washer on the cleat. The recorded simultaneous shank stress
and both washer/wood reactions describe the existing load path only. These
already-counted forces do **not** close the positive timber-only lower bound
by being compared to it a second time. The fixed-action obstacle is retained;
no added clamp force or anti-split resistance is qualified.

| Output | SHA-256 |
| --- | --- |
| `finite-pressure-attempt01/checks.json` | `5676849306531c7b506990a5f82e82558f371afadcf7c2dc90bbe24d15c1655c` |
| `finite-pressure-attempt01/receipt.json` | `a8188869edbf53fb683b7d733ceb57ab5bf1f02dbbc23e8a0e8e98ff12815aec` |
| Executed producer snapshot | `e090270a3bea195800ed3b04b806fe4ea0c5e221ae57faf01f602c8dba769d5e` |

This finite normal-pressure/bolt-route assessment is complete. Current
four-corner splitting resistance and complete-joint acceptance remain open:
the two positive rows need a justified redistribution or reinforcement
mechanism with normal force, shear and torque retained. There is no evidence
here of a large necessary tensile transfer, and no assigned splitting capacity.
No software tests, native/CAD/frame execution or geometry changes were made.

## Remaining cleat scope

The owner requested the same assessment for all remaining corner blocks and
cleats after this four-corner work. The parent identified 20 additional bodies
in the existing header (six), knee-spine (two) and remaining-cleat (twelve)
leaf inventories. Preserve their own geometry, grain, holes, forces and source
receipts. Reuse completed nominal checks and apply only missing splitting/load
path checks. The four-corner pressure or resistance results are not capacities
or passes for those different bodies. Inventory coverage alone is not
complete-cleat qualification.
