# Revised base v3: bounded geometry and strength applicability audit

The read-only audit is complete. All **112 wood washer seats** have full
nominal support on the frozen revised base: **36 fresh changed-host annulus
queries and 76 reused unchanged-seat proofs**. The 22 moved shafts and ten
moved panel/kicker screws follow the principal's 39.2-mm inward translation.
The twelve starting frame-bolt arrangements, all 100 shaft identities, all
66 screw identities, receiver assignments, grips and hardware recipes remain
preserved. These results establish recorded geometry, not complete joint
strength or a physical build release.

The revised frame has no admitted response in this packet. Its six predecessor
fields remain useful evidence for their original geometry. Supplier heel
dimensions, eight connected bolt-stack resistances and panel restraint
qualification remain unresolved. Existing panel and generic screw-head
exceedances remain visible, and their paused remedies remain paused.

## Scope and frozen inputs

This audit addresses the owner's additional bounded investigations: changed
geometry, supplier information, complete-joint applicability and member
restraint. It uses base **`eoere-midpoint-ready-frame-v3`**, extra grid **OFF**,
from [occupied-adjusted-base-v3.json](../../occupied-adjusted-base-v3.json), SHA256
`5e0f05ea39347edcd89e088ab0cd478976b9a7ae9dabcc78c1b92e24d1f01aa7`.
The seven changed timber solids are the right principal, right center kicker
post, header, top rail and three extended right rails. The principal includes
the eleven retained F-column wire clearances added by the parent in v3/v10.
The parent owns geometry review, readiness and any subsequent response work.

[inputs.json](inputs.json) binds the previous geometry, issued fields through
their authenticated intake, published numerical results, the reviewed
[resistance followup](../resistance-followup-v1/README.md), product drawing and
existing NDS source documents. The merged closure has **1,120 source pins**,
verified before and after the calculations. The original bounded packet and
resistance followup remain byte-identical. External archive-manifest pins
stay external; no source manual, mesh or raw run was duplicated.

All six admitted fields are for **`eoere-bottom-rail-tnut-clearance-v1`**. They
use 500 lbf downward (2,224 N), a separate 300-N horizontal component, the
recorded 100-mm normal hold offset, modeled selfweight and a 25-kg allowance
under the inherited unverified no-slip floor assumption. The six-case packet
reports its original model's response. Moving its forces to new positions
would not create an admitted response for base v3.

## Geometry and washer result

All 22 moved shafts and ten moved screws translate by `[-39.2, 0, 0]` mm.
Six duties move coherently. All attachment points follow their own installed
shaft, and all saved attachment intervals follow the canonical direction
with first nonzero coordinate positive, irrespective of installation
direction. An independent saved-BREP query verifies the twelve right-principal
intervals against its actual X bounds to **0.000000101 mm**.

The 36 changed-host washer checks use the existing thin-annulus method on the
saved v10/base timber BREP, with the largest nominal/catalog OD and smallest
supported opening used by the preceding study. Probe depth is 0.1 mm and
full-support tolerance is 0.0001 mm³. Minimum support fraction is
**0.999999999999734**; none fail. The remaining 76 seats preserve both their
position and finished host and reuse their prior full-support proof. No old
washer force is reissued as a new geometry response. Seating pressure,
physical contact stiffness, preload and delivered washer dimensions remain
outside this geometric result.

Each of the ten moved screw centers lies **32.3875 mm** from the left outline
edge of its actual saved right panel/kicker solid, with recorded receiver-body
fraction **1.0**. The nominal panel left X edge is −1.5875 mm and screw X is
30.8 mm. This establishes backing and an outline distance; it does not
calculate screw head punching, installation tolerance or actual panel edge
capacity. [result.json](result.json) lists every moved axis and screw.

## Supplier information and the heel comparison

The live primary [eoere listing](https://www.amazon.com/dp/B0C7V7VS89), checked
on October 8, 2026 (03:07:52 UTC on October 9), still describes ASIN B0C7V7VS89,
model ZX128-B-T4, Q235B and **“1/4 inch (6 mm)”**. Its 300-lb statement does
not define the load point, direction, mounting substrate, fastener arrangement,
failure limit or safety factor. The provided diagram labels quarter-inch
thickness and bolt-hole dimensions, with no inside bend radius or controlled
tolerances. Exact model/ASIN searches located no supplier engineering drawing
in the public material reviewed. No seller was contacted or part measured.

Reuse the completed [heel study](../../heel-assumptions-v1/README.md), including
its [6.35-mm thickness / 6.35-mm radius scenario](../../heel-assumptions-v1/nominal-scenario.md).
The worst fixed-old-action comparison is **140.479 MPa / 140.719 MPa = 0.998300**,
leaving **0.170%** of that conditional elastic reference. The reference-equal
thickness at fixed radius is about 6.34379 mm, only 0.00621 mm below the nominal
scenario. That sensitivity establishes the value of better product inputs;
it is not an actual receiving limit, full formed-heel stress bound or
manufacturer rating. A nominal quarter-inch statement does not establish
the needed lower bound on the metal at the bend.

The useful supplier questions, ready to send if the owner chooses, are:

1. Minimum base-metal thickness excluding coating, stock tolerance and thinning
   at the bend.
2. Inside/outside bend radii and tolerances, plus hole positions from the actual
   bend tangents.
3. Controlled ZX128-B-T4 drawing/revision and Q235B grade-conformance information.
4. Load point, direction, fasteners, substrate, limiting event and safety factor
   underlying the 300-lb statement.

No further radius sweep answers those missing inputs. If a sample becomes
available, the existing heel packet already contains a bounded opening/closing
and off-center component diagnostic. Its proposed 0, 25, 50, 100, 50, 25, 0-N
sequence produces up to 6.51 Nm at the assumed 65.09-mm arm; the actual arm
must be measured. It compares small-load stiffness, flange rotation and
fixture slip. It cannot qualify ultimate capacity, the complete wood joint
or a climber load. No physical test was performed or newly authorized here.

## Complete joints and NDS applicability

The existing repository helpers supply finite component references. Reusing
them avoids a new global solve or an invented perpendicular-to-grain tensile
allowable. The trimmed-cleat stock-depth/engaged-depth shear sensitivity spans
**1,130.940–1,395.813 N**. Its matching grain-normal section shear reaches
**347.214 N**, a worst component ratio of **0.307013**. Parallel net-section
tension references span **22.112–23.379 kN**. These remain sensitivities with
the old own case forces. NDS 2024 §3.4.4.1 concerns the rectangular bending
member's reduced-depth shear. Y-normal tensile opening, full bending/torsion,
sloping-end qualification and interacting connections remain separate.

The 552 prior single wood/steel bolt component comparisons remain reusable
within their stated scope; the worst unadjusted lateral ratio is **0.699104**.
That value would require `Cg × Cdelta >= 0.699104` at CD = 1 on that component
route. Neither factor is adopted. Under NDS 2024 §11.3.6, the row calculation
has an actual load-aligned-row prerequisite. All **276** issued receiver-pair
records are examined; none already qualifies that prerequisite. An arbitrary
projection of these oblique forces onto a near-zero grain pitch does not
establish a group factor.

Eight shaft stacks have no complete reference:

| Shaft IDs | Ordered material stack | Existing method gap |
| --- | --- | --- |
| 065, 066, 079, 080 | steel 6.35 mm / wood 38.1 mm / steel 6.35 mm | Independently loaded outer angles, unequal own lateral forces, thread intervals and free couples |
| 067, 070, 071, 074 | steel 6.35 mm / wood 88.9 mm / wood 38.1 mm | Different outer materials, different grain/geometry, interacting bearing and bolt bending |

NDS 2024 §12.3.1 supplies single-shear and symmetric-double-shear yield limits,
subject to contact, loading and spacing prerequisites. The unequal-bearing
length provision in §12.3.5.4 does not prove these mixed and independently
loaded stacks symmetric. §12.3.8's four-or-more-member rules do not directly
apply to these three-member stacks. The useful next calculation is a connected
three-member dowel bearing/yield model with each member's own action, material,
geometry and actual thread-bearing intervals, followed by separate axial-seat
and free-couple checks. Adding two isolated single-shear capacities is not
that model.

The raw audit retains all eight shafts' own ports in every original case.
For scale, the four mixed wood/steel cleat shafts have independent maxima of
**1.490 kN** lateral force and **13.538 Nm** free couple. The four two-steel
stacks have up to **43.590 N** difference between their outer lateral force
vectors. These maxima occur on different own records and are not combined
into a synthetic load case. Shafts 079/080 also moved in base v3; all old
action values remain attached to the old geometry.

The [AWC Connection Calculator](https://awc.org/resources/connection-calculator/)
is a useful individual-fastener reference tool. Its published scope does not
turn a single/double-shear calculation into this complete 3D joint assessment.
No new online calculator values are adopted.

## Member restraint and the attachment path

NDS 2024 §§3.6.6 and 3.7.1 tie bracing and effective length to actual restraint;
§3.7.1.4 limits rectangular-column slenderness to 50 in this use. The following
are geometric candidate stations, including unqualified end closures, with
Ke = 1 shown only to describe their possible spacing:

| Member | Full span | Maximum panel-screw station gap | Gap / weak dimension | Peak old candidate screw head reference ratio, CD = 1 |
| --- | ---: | ---: | ---: | ---: |
| Header | 2,435.225 mm | 400.000 mm | 10.499 | 1.557 |
| Top rail | 2,257.425 mm | 870.150 mm | 22.839 | 2.168 |
| Left principal | 2,474.015 mm | 358.383 mm | 9.406 | 0.416 |
| Right principal | 2,474.015 mm | 358.383 mm | 9.406 | 0.129 |

The weak dimension is 38.1 mm, making the 50b domain limit about **1,905 mm**.
The full spans exceed it while the candidate station gaps are shorter. The
weak displacement is Z for the header, along the inclined panel for the top
rail and X for the principals. Every applicable screw axis is perpendicular
to its member's weak displacement: the possible restraint comes through
**screw lateral bearing and panel in-plane stiffness**.

The result traces each member's screws to its panels, other screw axes and
other frame receivers. Thus an identifiable geometric return path exists.
Strength/stiffness of that path and the end restraints remain unqualified;
effective lengths and Cp are not adopted. Full-strength credit also must
address simultaneous actions. Even on the original fields, candidate header
and top-rail brace screws exceed their generic head comparison. Across all
66 original screws/panels, the retained peak generic head ratio is **2.572**,
panel bending **4.613** and panel rolling shear **2.451**. These are recorded
diagnostic exceedances, not product-specific Hillman ratings. Actual Hillman
lateral resistance/stiffness and local panel-head behavior remain missing.

## Disposition, verification and next actions

The useful result is a narrower work list. Washer support and moved-axis
geometry are closed for this frozen nominal base. The remaining strength
inputs are actual/controlled heel dimensions; a connected model for the
eight stacks; and qualified panel/attachment/end-restraint behavior. Current
case actions require compatible geometry-specific fields under the parent's
readiness and execution control. Known failed component screens still stop
the affected operation; they are not waived by this audit. No frame redesign,
member enlargement, new fastener, floor-friction test or physical work follows
from these calculations.

The five permanent files are this summary, `analyze.py`, `inputs.json`,
`result.json` and [verification.json](verification.json). Detailed seat rows,
own case ports, old screw diagnostics and the complete pin map remain in the
ignored output at
`fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/revised-base-audit-v1/attempt06/`.
Known-answer probes distinguish full support, a gap and an edge-clipped ring.
Independent arithmetic checks ring volume and station spacing; an independent
saved-solid query checks the canonical intervals. Ruff and all input hashes
pass. No native solve, response assembly, CAD rebuild or viewer export ran.

Reproduce from the repository root:

```bash
uv run python docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/revised-base-audit-v1/analyze.py --out fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/revised-base-audit-v1/reproduce
```

Base v3's parent geometry, original six fields, both earlier strength packets,
and this audit stay active for their stated uses. Earlier rejected adjusted
geometry and interrupted prototype attempts are history; they remain
recoverable and are not pruned here. The main agent maintains the existing
development summary and ledger and owns shared staging/publication.
