# Current candidate: review packet

**Recommendation:** retain the `top-joint-development` candidate for the next
human design review. Keep the 2×8 backing and independent plywood leg plies;
do not buy deeper framing to compensate for an unidentified joint or stability
problem. This is an inspectable design proposal, **not build/use approval**.
The packet is still a draft: the complete per-member edge/ligament audit and
remaining product-fit dispositions below are not finished.

## Start here

- [Interactive candidate](https://mckayreedmoore.github.io/mini-moonboard/?model=top-joint-development)
- [Current changes, STEP and metric/imperial schedules](top-joint-development.md)
- [Purchased face stock and selected lumber](purchased-materials.md)
- [Remaining plywood, hold, insert and wiring selections](remaining-material-hardware-closure.md)
- [Selected bolts/nuts/washers](selected-bolt-hardware.md) and [wood screws](selected-wood-fasteners.md)

The face uses purchased Roseburg 23/32 CAT plywood as a nominal 18.25625 mm
assumption. The legs/splices use separately selected plywood: two nominal
19.05 mm plies, without adhesive or friction credit in the assessment. The
selected DF-L backing lumber is distinct from either plywood. Preserve sheet
strength-axis identification; do not infer it from a curved leg's outline.

## What the evidence says

| Question | Current answer |
| --- | --- |
| Do modeled parts and hardware fit without unintended solid intersections? | The top-candidate nominal screen passes, with exactly 24 documented tool-access obstructions requiring installation order. It does not verify actual tools or manufacturing tolerances. |
| Do the displayed holes and schedules match CAD? | All seven development variants passed export regressions; the current viewer includes 365 entries and all 278 connection bore paths were checked. |
| Did the revised top bolts improve end distance? | Nominal minimum timber end distance is 70.4 mm. The extended steel leaf still needs bending/prying/fabrication review. |
| Do screw tips remain inside the modeled final receivers? | The axial diagnostic finds all 164 nominal tips inside, with minimum axial cover 5.55625 mm. This excludes measured stock variation and is not a three-dimensional minimum cover. |
| Is there material along the threaded tail? | Minimum nominal point-included axial overlap is 25.4 mm. Point geometry and full-circumference support are not verified, so effective threaded embedment remains unresolved. |
| Do bolt ends project beyond nuts? | Minimum catalog-stack tip projection is 4.2362 mm, using nominal grips. Actual stock variation and complete chamfer-free thread engagement are not verified. |
| Is the frame structurally qualified? | No. The failed force-recovery results are rejected numerical evidence, not proof of a physical failure or permission to size joints from those forces. |

[Full 278-position axial report](top-joint-engagement.json) includes source
hashes and product-generation endpoint scenarios. Reproduce with
`uv run python -m mini_moonboard.connection_engagement --output docs/top-joint-engagement.json`.
This diagnostic reconstructs final backing receivers with service reliefs but
without their own fastener pilots; it measures centerline material only.
The 17 focused axial-geometry/report tests pass; independent correctness,
testing and architecture review found no substantial remaining implementation
findings. That software review does not replace a qualified structural review.

## Assembly constraints—not an erection procedure

Install the obstructed rib screws before skins and the obstructed edge screws
before legs. The [access audit](product-frame-integration.md) identifies those
locations. Establish temporary support, handling and assembly sequence with the
reviewer before fabrication; a final-state clearance check cannot approve an
unsupported intermediate state. Do not fill or relocate holes in an existing
frame using the new-manufacture top-joint model.

## Remaining work, in priority order

1. Finish the per-member net edge/ligament audit, including the curved plywood
   legs and neighboring holes/reliefs. Record actual profile distances and
   strength-axis uncertainty, not bounding-box substitutes or assumed capacity.
2. Disposition US A21 proxy geometry, actual driver/head seating, steel fabrication,
   hold-specific bolt lengths/head seats, supplied insert-retainer screw geometry,
   and received LED connector/retention/access details. Exact unresolved items
   remain in the linked hardware documents; generic hold bolts are not a safe substitute.
3. Consolidate the qualified review of connection resistance, material direction,
   extended steel, and unanchored sliding/tipping/contact. Any further FEA must
   answer a specific decision with accepted force recovery and acceptance criteria.

No new lumber-size sweep or speculative solver work is planned before these
items have useful dispositions. Keep one climber, 250 lb intended maximum,
150/200 lb comparison cases and 300 lb sensitivity; these are not user ratings.
No anchors, pad support, assumed ballast or unverified composite action.

## Useful human checks now

Record actual sheet thickness, usable dimensions and stamp/strength direction;
identify the received hold-bolt seats, insert-retainer screws and LED revision.
These can proceed while the design audit finishes. Room measurements and an
offcut test are not prerequisites for this design phase. Before construction,
the unresolved fit, structural and installation gates still need resolution.
