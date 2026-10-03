# Upper-left service joint MVP closure

**Disposition: HOLD. This joint is not MVP complete or accepted.** The owner
asked this chat to choose one open joint and finish it with practical,
explicit assumptions. The chosen duty is `clip_horizontal_upper_left_1`,
implemented by `left_service_outer_upper_cleat` between
`base_rail_service_upper_left` and `base_side_left`. Primary confirmed this
scope does not overlap the active washer, stress-frame or STI17 work.

Start project continuation at the canonical
[next-agent handoff](../../NEXT-AGENT-HANDOFF-2026-10-01.md). This packet is a
bounded local closure attempt under `compact-floor-flush-wood-joints-development`,
revision `led-clearance-2x6-runner-seated-blocks-v1`; it changes no reviewed
geometry, authority, criterion disposition or physical-release flag.

## Keep the joint simple

Retain the full-section 88.9 × 88.9 × 119.7 mm wood cleat and its four
existing through-bolt axes: two into the service rail and two into the side
member. Each pair has 33 mm pitch. The proposed local bill has one DF-L No. 2
4×4 cleat, two nominal 1/4-20 × 6 in partially threaded bolts, two nominal
1/4-20 × 8 in partially threaded bolts, four compatible Grade 5 regular hex
nuts and eight Type A wide washers. These are conditional requirements and
catalog-length classes, not selected SKUs, delivered parts or an order.
The host rail and side member remain individual transport parts. No member
enlargement or custom steel is proposed; the 66 Hillman screws and twelve
starting frame-bolt arrangements remain separate.

The immediate engineering task is to close **this complete cleat connection**,
including both timber interfaces and their interaction, rather than qualify
one bolt in isolation. Its saved whole-boundary records contain four bolt
lateral planes, four outer-seat axial ties and eight unilateral contact
cells. The checker retains all 16 connection names and both receiver force
and moment resultants at each of the 21 same-state block datums, including
self-weight in the authenticated source balance. Those resultants are not
reassigned uniformly to a cut, washer or pair.

## What the new check establishes

[`check_joint.py`](check_joint.py) hashes 30 distinct direct/raw-source/STEP
inputs, requires the named candidate and reviewed revision, checks exact
four-axis/three-case/seven-increment identity, verifies
all 21 block force and moment residuals against their saved rounding intervals,
validates each boundary's load factor, two receiver identities and all sixteen
port identities, and inventories both washer seats for every bolt. It authenticates existing
diagnostic exports; it does not independently reinterpret their raw RF tokens
or qualify their physical connector laws. Source support queries are reused
without another CAD extraction. [Six runnable tests](test_joint.py) cover
missing/duplicate states, wrong case/factor, the exact force rounding-box
extremum, thread/profile boundaries, whole-boundary mutations, all release
flags, the operational gate set, the exact saved force/moment/datum record
digest and the frozen joint result.

| Calculation | New local result | Meaning |
| --- | ---: | --- |
| Largest saved lateral force including its rounding interval | 33.808167 N | One bolt/state, not a pair sum |
| Largest saved axial tie including its rounding interval | 57.210125 N | A separate bolt/state; not coincident with the lateral maximum |
| Proposed independent per-bolt action box | 100 N lateral and 150 N tension | Covers all saved states; does not bound missing frame responses or moments |
| Largest saved lateral ratio with hypothetical 45 ksi Fyb and only 25% of the single-bolt reference | 0.216756 | Arithmetic sensitivity, not adopted adjusted resistance |
| 100 N action-box lateral ratio under the worst-direction reference and the same 25% budget | 0.704414 | Both receivers assigned 90° to grain for this adverse component reference |
| Largest saved ideal wood-seat ratio using only one quarter of the minimum catalog annulus | 0.248586 | Average Fc-perpendicular compression only |
| 150 N action-box ratio using the same quarter annulus | 0.651770 | Does not qualify washer metal, spreading or local wood pressure |
| Largest nominal same-root steel axial/shear first-yield ratio | 0.006391 | Hypothetical Grade 5, 0.189 in root; excludes bending and thread stripping |
| Nominal head/nut washer seats supported by saved finished CAD | 8 of 8 | Fixed-center catalog-minimum-area annuli; no received-part or tolerance claim |

The force box intentionally allows simultaneous independent extremes. It is
a proposed **local design input**, not a frame reaction, a joint rating or a
substitute for an authenticated six-case envelope. Its bounds provide about
three times the recorded lateral maximum and 2.6 times the tension maximum;
there is no evidence that these multiples dominate the missing cases.

The component calculation specifies dry, normal-temperature DF-L No. 2,
G = 0.50, nominal 0.25 in effective diameter and contacting zero-gap faces.
It reuses the existing six-mode wood/wood helper, retaining the lower result
of both main/side assignments. Fyb = 45 ksi is explicitly hypothetical here,
not inferred from Grade 5 or asserted as a quarter-inch tabulated value.
The 25% budget is a sensitivity; it supplies no proved lower bound on Cg,
C-delta or complete-joint resistance. Zero thread lengths in that helper are
an equivalent nominal-D arithmetic case. The separately declared profiles
below satisfy the quarter-thread geometric condition in both wood receivers.
All material properties are conditional study specifications; no actual
material or installation observation is filled in.

## Resolve the thread geometry by specification

All coordinates are millimetres from the underhead bearing plane. The washer
envelope uses the existing published maximum 2.032 mm head washer. The
following profiles are **declared procurement targets**, not inferred from a
nominal bolt length or an LG gage coordinate:

| Pair | Minimum thread/runout start required by wood | Declared earliest runout | Sufficient external full-form nut coverage required | Declared continuous full-form span | Declared minimum physical tip / required tip |
| --- | ---: | ---: | --- | --- | --- |
| Rail pair, 6 in class | 119.507 | 127.000 | 129.5908–136.8044 | 128.000–148.000 | 149.860 / 140.6144 |
| Side pair, 8 in class | 157.607 | 171.450 | 180.3908–187.6044 | 173.000–196.000 | 198.628 / 191.4144 |

All four targets clear the quarter-thread, sufficient external coverage and
tip screens. This completes a usable **conditional profile specification**
without pretending to have inspected stock. A matched nut still needs
compatible class, active internal threads/chamfers, seat geometry and
functional travel; external coverage alone establishes none of those. A
source-backed item can satisfy this specification without a new frame layout.
See the [hardware scope](../upper-block-strength-2026-10-01/hardware.md) and
[functional gage distinction](../thread-gage-functional-fit-2026-10-01/source-note.md).

## The remaining complete-joint duties

| Duty | Present evidence and disposition | Smallest next operation |
| --- | --- | --- |
| Whole force/moment transfer through both interfaces | 21 equilibrated source states retained; local physical load sharing unresolved | Use these same-state receiver actions and all 16 ports for one joint evaluation |
| Bolt lateral wood bearing and dowel yielding | Six-mode arithmetic has substantial conditional margin | Adopt a supported Fyb/profile/service/group/geometry basis; keep axial transfer separate |
| Bolt tension, shear and bending together | Same-root average tension/shear reference is small; bending and head/nut transfer open | Bound co-located bolt moments from the complete bearing/contact solution |
| Washer metal and actual wood pressure | All eight nominal seats supported; quarter-area compression sensitivity below one | Reuse the parent's qualified output methods for full-seat local stacks, retaining head/nut lands, movement, bending and prying |
| Contact and timber bearing | Signed unilateral contacts retained in whole-body source sums | Resolve finite patch pressure and opening with no friction or preload credit |
| Finished cleat and host net sections, shear/torsion, row tear-out and splitting | Exact source solids available; cleat sampled minimum area 6,569.71 mm² has three regions | Assign force/moment to actual cuts and material regions; evaluate both receivers and shared-cleat interaction |
| Directional ends, edges, pitch and group applicability | 33 mm pairs; cleat rail short end 43.35 mm vs pure-parallel 7D = 44.45 mm | Check finished boundaries and the signed oblique rule; do not adopt an outer-box sensitivity as a pass |
| Joint slip/rotation and frame compatibility | Current source laws are diagnostic | Bound clearance/slip and rotational stiffness; establish that the frame demand contract remains compatible |
| Installed envelope, tools and reverse removal | Current-revision per-axis access sources exist; operations remain unresolved | Screen only these four selected-profile stacks, two-sided tools and cleat extraction, including tolerances and support/capture |
| Shop sequence, transport and local cost | Local quantities fixed; no selected SKUs or validated operation | Cost one cleat/four bolts/four nuts/eight washers and verify the local reversible sequence |
| Complete design envelope | Three rear histories only | Authenticate the missing cases or explicitly adopt and prove a suitable local load envelope |

For conditional access analysis, start with panels/lights in a documented
removed service state, the rail and side supported independently, and captured
nut/washer parts. Model turning and counterhold on both sides before bolt
withdrawal; release the four metal-thread stacks and then remove the cleat.
Check the reverse order and the restored panel/LED/wire scene. This is a
sequence to validate, not a physical assembly instruction or an access pass.
The [current fit/transport register](../evaluation-resume-2026-09-24/current-fit-transport-closeout-attempt02/README.md)
provides the existing operation identities and unresolved boundaries.

The practical recommendation is to keep this geometry and close its full-seat
bolt/washer/contact path and timber failure paths under the declared local
contract. The favorable scalar references do not justify another member size
or further frame-force diagnostic. Conversely, they cannot justify accepting
the joint while its coupled failure modes remain unknown. A failed adopted
criterion, incompatible sourced part or missing transfer path stops that
operation. The primary's known TERM-only timeout defect also stops a new
native run until corrected; no native solve is launched here.

## Reproduce and continue

From the repository root, using the existing local raw evidence:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/upper-left-service-joint-mvp-2026-10-01/check_joint.py > /tmp/mini-moonboard-upper-left-service-joint-mvp-2026-10-01.json
.venv/bin/python -m unittest discover -s docs/wood-joints-mvp/hypotheses/upper-left-service-joint-mvp-2026-10-01 -p 'test_*.py' -v
.venv/bin/ruff check docs/wood-joints-mvp/hypotheses/upper-left-service-joint-mvp-2026-10-01
```

The generated report has `local_joint_mvp_complete=false` and
`complete_joint_accepted=false`. The full 47-criterion authority and every
physical release flag remain unchanged. No passed reference, specified profile
or future independent software review may turn this HOLD into joint acceptance
without the named complete-joint evidence. Check current included usage before
further model work; stop on unknown/exhausted allowance and use no paid fallback.
