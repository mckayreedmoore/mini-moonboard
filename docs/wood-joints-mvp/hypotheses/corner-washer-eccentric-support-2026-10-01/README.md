# Primary-corner washer eccentricity and support

Checked 2026-10-01 for `compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`. This is a read-only geometry
screen for the six primary-corner bolts and their twelve outer washer seats.
It adds no washer, bolt, wood, or joint resistance result.

The previous coaxial screen centered each washer on its modeled bolt axis.
That leaves a real geometric question in the declared model: the washer
opening can move around the nominal smooth bolt body, and the body can move
inside the larger wood bore. This packet keeps those movements as separate
conditional cases.

## Dimensions and motion cases

The pinned candidate-axis inputs record a **6.35 mm nominal smooth-body
scenario** and a **7.5 mm wood bore**. The STEP solids contain matching
coaxial 3.75 mm-radius cylindrical bore faces at all twelve seats. The radial
body-to-bore clearance is therefore 0.575 mm in this model. These two
diameters are checked separately; neither is an inspection of delivered
hardware or wood.

The K.L. Jack `25NWUS` catalog bounds are ID 0.307–0.327 in (7.7978–8.3058 mm)
and OD 0.727–0.749 in (18.4658–19.0246 mm). The separate `25NWUS8Z` F436
candidate screen gives OD 0.729–0.749 in (18.5166–19.0246 mm), but describes
its dimensional envelope only as “similar.” Its cases therefore combine
that separately sourced OD with the `25NWUS` ID bounds as **mixed-source
geometry sensitivities**, not a matched F436 product envelope. No material
property or resistance transfers between these scenarios.

Washer play is `(washer ID − 6.35 mm)/2`: 0.7239 mm at the catalog minimum ID
and 0.9779 mm at the maximum ID. For the separate combined geometry case,
the washer play is aligned with the bolt's 0.575 mm radial bore clearance,
giving washer-center offsets of 1.2989 and 1.5529 mm. The CAD annulus
(OD 18.6436 mm, ID 8.0 mm) is retained as a non-catalog comparison: its
washer-only offset is 0.825 mm and its combined offset is 1.4 mm.

The 6.35 mm body is the recorded nominal smooth-body geometry scenario, not
a minimum delivered shank diameter. No bolt tilt, seat drift, fabrication
tolerance, or delivered dimensional bound is included. The combined value
is not a bound on every standard-conforming or delivered stack and does not
predict an installed position or force equilibrium.

## Circular overlap result

Let `I(r1, r2, d)` be the exact area where two circular disks of radii `r1`
and `r2`, whose centers are `d` apart, overlap. It is zero when
`d ≥ r1+r2`, equals `π min(r1,r2)²` when `d ≤ |r1−r2|`, and otherwise is

```text
r1² acos((d²+r1²−r2²)/(2 d r1))
+ r2² acos((d²+r2²−r1²)/(2 d r2))
− 0.5 sqrt((-d+r1+r2)(d+r1−r2)(d−r1+r2)(d+r1+r2)).
```

For washer outer radius `R`, inner radius `a`, wood-bore radius `b`, and
washer-center offset `e`, the unsupported part of the washer annulus caused
by the wood bore is
`I(b,R,e) − I(b,a,e)`. Subtract this from
`π(OD²−ID²)/4` to obtain supported area. This is an area geometry result,
not a contact-pressure distribution.

## Source-BREP envelope and direct checks

The checker imports the prior pinned packet and its four validated finished
member STEP solids. It also checks each target bore's radius and axis against
the actual cylindrical STEP faces. For the maximum declared catalog OD and
combined offset, it tests the complete inward swept annulus from the 3.75 mm
wood-bore radius to 11.0652 mm radius on every seat, at probe depths 0.01,
0.05, and 0.1 mm. The lowest BREP support fraction was
`0.9999999999994897`; the largest numerical unsupported volume was below
`1.1e-11 mm³`. Outward probes over the same full radial disk had zero
positive-volume overlap at all three depths on all twelve seats.

This full swept-region check bounds every in-plane direction and every
smaller declared OD/offset case within the pinned BREP and its kernel
tolerance. It verifies that no neighboring cut or exterior edge in that
region changes the hole-only formula. The finite 0°, 45°, and 90° probes
below are additional direct measurements, not a global directional bound.
The model bundle has no semantic cut inventory, so the check cannot establish
that cuts absent from the frozen STEP solids are represented.

| Washer dimensions | Motion case | Offset (mm) | Unsupported area from bore (mm²) | STEP-supported area across 12 seats, directions and depths (mm²) | STEP support fraction across same samples |
| --- | --- | ---: | ---: | ---: | ---: |
| CAD 18.6436 × 8.0000 mm | Bolt held | 0.8250 | 3.635734 | 219.0904784823–219.0904784835 | 0.9836762200831–0.9836762200883 |
| CAD 18.6436 × 8.0000 mm | Combined | 1.4000 | 7.923542 | 214.8026699435–214.8026699447 | 0.9644247431357–0.9644247431411 |
| Plain 25NWUS: OD max, ID min | Bolt held | 0.7239 | 3.857819 | 232.6489099155–232.6489099167 | 0.9836883314910–0.9836883314961 |
| Plain 25NWUS: OD max, ID min | Combined | 1.2989 | 8.164476 | 228.3422528129–228.3422528143 | 0.9654788830088–0.9654788830143 |
| Plain 25NWUS: OD max, ID max | Bolt held | 0.9779 | 3.377468 | 226.7042100761–226.7042100773 | 0.9853205679157–0.9853205679208 |
| Plain 25NWUS: OD max, ID max | Combined | 1.5529 | 7.614721 | 222.4669573798–222.4669573812 | 0.9669042701690–0.9669042701750 |

Each STEP range is the deterministic Boolean support result across three
sample directions for all twelve seats and all three probe depths. The
largest absolute difference from the circle formula was below
`1.0e-9 mm²`. The minimum-OD plain cases and both OD bounds for the mixed-source
F436 sensitivities are also evaluated by the exact formula; the swept BREP
test establishes the hole-only applicability for those smaller footprints.

The unsupported footprint is a useful conditional input for later contact
work. A nonzero geometric unsupported area is not, by itself, a failure or
an adopted criterion result.

## Reproduction and limits

Run from the repository root with the existing environment:

```sh
uv run --no-sync python docs/wood-joints-mvp/hypotheses/corner-washer-eccentric-support-2026-10-01/check_eccentric_support.py --self-test
uv run --no-sync python docs/wood-joints-mvp/hypotheses/corner-washer-eccentric-support-2026-10-01/check_eccentric_support.py --check
```

Self-tests exercise disjoint, contained, concentric, partial-overlap and
tangent circle cases, a known hole-only area, the production BREP measurement,
and production inward/outward envelope checks with neighboring-bore and
protruding-boss fixtures. The check fails with a nonzero exit if an inward
swept support fraction is below `1 − 1e-7`, an outward overlap fraction exceeds
`1e-7`, or a direct STEP/formula area difference exceeds `2e-5 mm²`. Missing
or nonfinite direct comparisons also fail; rejection fixtures exercise these
gates. These numerical tolerances are not physical acceptance limits.
The full check reuses the prior packet's pinned
input and STEP validation and reports input digests to stdout; no raw result
file is written.

The results apply to the current frozen analytical solids under declared
catalog and nominal-body scenarios. They do not establish actual hardware,
actual wood or face condition, contact pressure, load transfer, any washer or
wood resistance, joint acceptance, the six-case envelope, or a physical
build. The prior packet's limits on omitted STEP cuts still apply. No native
solve or geometry modification was performed.
