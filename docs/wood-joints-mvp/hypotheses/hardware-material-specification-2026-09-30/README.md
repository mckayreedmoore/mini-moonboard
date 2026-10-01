# Hardware and material inputs for the reviewed wood joints

This packet supplies conditional calculation and hardware requirements for
`led-clearance-2x6-runner-seated-blocks-v1`, with the connected BG001, BG003 and
BG045 corner first. It preserves the reviewed geometry and frozen response
studies. It selects no purchase, assigns no property to received material, and
accepts no joint or formal criterion.

| Calculation input | Record |
| --- | --- |
| Bolt profile, nut position and length requirements for all 92 candidate axes | [Requirements](requirements.md), [producer](produce.py) and [tests](test_requirements.py) |
| Exact catalog leads, mechanical properties and product limitations | [Fasteners](fasteners.md) |
| Conditional wood values, grain directions and adjustment factors | [Materials](materials.md) |
| Existing simultaneous corner actions | [Complete resistance register](../mvp-acceleration-2026-09-28/current-corner-complete-resistance-register-attempt01/README.md) and [three-case axial seats](../mvp-acceleration-2026-09-28/current-corner-three-case-axial-seat-register-attempt01/README.md) |

## Primary corner specification

All distances below are millimetres from the underside of the bolt head.
The catalog-envelope scenario uses two USS washers, each 1.2954–2.032 mm
thick, a finished nut 5.3848–5.7404 mm high, and a separate three-pitch
projection allowance of 3.81 mm for 1/4-20. These are declared calculation
inputs, not measured stack dimensions. See the linked source notes for their
applicability and the distinct inherited 3.175 mm projection comparator.

`LB` is the end of the declared smooth body; everything after it is treated
as thread-bearing wood for the NDS quarter-bearing screen. The full-form
male thread must separately cover the declared nut interval. A published
grip-gage dimension `Lg` cannot establish that full-form interval.

| Connection family | Physical bolts | Wood grip | Required LB with frozen CAD washer | Required LB with maximum catalog head washer | Latest full-form thread start for the full-height nut scenario | Required full-form thread end | Minimum physical tip with three-pitch allowance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BG001 exterior post/spine and mirrored right family | 4 | 76.2 | 68.326 | 68.707 | 78.7908 | 86.0044 | 89.8144 |
| BG003 spine/side/inner block and mirrored right family | 4 | 215.9 | 195.326 | 195.707 | 218.4908 | 225.7044 | 229.5144 |
| BG045 inner block/header and mirrored right family | 4 | 177.1 | 169.226 | 169.607 | 179.6908 | 186.9044 | 190.7144 |

The full-height nut scenario deliberately requires complete male thread over
the entire physical nut height. It is a dimensional screening requirement;
nut chamfers, tolerances, internal-thread form, effective engagement and
stripping still require their own method. A part can satisfy a declared
profile without that profile being guaranteed by a catalog listing.

BG001, BG003 and BG045 identify the left primary corner, two bolts per group.
The table aggregates dimensional requirements for their mirrored right
families as well. These dimensions do not transfer left-corner demands to
right-side joints. BG045's first and second axes have opposite receiver
orders; its family `LB` is the larger of their separate requirements.

BG003 is one continuous bolt through three receivers. Its two lateral
interfaces and two exterior washers are parts of the same joint. Do not
introduce a middle nut or washer, split it into two independent bolts, or
combine independently governing receiver peaks into a simultaneous state.

## Inputs that can be used now

For an explicitly specified 1/4-in SAE J429 Grade 5 bolt scenario, published
supplier technical data support direct steel minima of 92 ksi yield,
120 ksi tensile and 85 ksi proof stress. A separate J995 Grade 5 finished
1/4-20 UNC nut scenario has a 120 ksi proof-stress reference; multiplied by
the nominal 0.0318 in² tensile stress area, that is 3,816 lbf. These are
component references, not complete-joint strengths. The 106 ksi dowel-bending
estimate remains non-adopted; direct steel yield does not resolve its method
basis. See [fasteners](fasteners.md).

The conditional DF-L No. 2 reference row is **Fb 900, Ft 575, Fv 180,
Fc-perpendicular 625, Fc-parallel 1,350, E 1,600,000 and Emin 580,000 psi;
specific gravity 0.50**. Parent review visually checked printed page 34 of
the official 2024 Supplement. The adjacent No. 1 row has different values;
the existing frozen No. 2 scenario agrees with the actual No. 2 row.
Adjustment factors remain property- and operation-specific. The four ripped
blocks have explicit hypothetical final-section scenarios, without inheriting
their original stock grade. See [materials](materials.md).

Choose washer wood-bearing properties by receiver grain. BG001 and BG003
exterior washer normals are perpendicular to their proposed grain directions.
At BG045, the inner-block washer normal is **parallel** to proposed block
grain, while the header washer normal is perpendicular to header grain.
Applying 625 psi to both BG045 seats would use the wrong property for the
block. Neither uniform annulus pressure nor the wood reference proves washer
metal resistance or actual pressure distribution.

The plain USS washer envelope also supplies a declared minimum complete-ring
area: `pi/4 × (18.4658² - 8.3058²) = 213.6279 mm²`, using minimum OD and
maximum ID. Its smallest opening is 7.7978 mm, larger than the primary
seat record's modeled 7.5 mm bore. Under a full, sound-wood support assumption,
the three-case maximum tie of 119.343 N would give a uniform average pressure
of 0.55865 MPa on that ring. This is a catalog-envelope sensitivity, distinct
from the frozen CAD annulus of 222.7262 mm²; it changes no response model and
does not establish metal bending or the finished support polygon. The tie
comes from the [axial-seat register](../mvp-acceleration-2026-09-28/current-corner-three-case-axial-seat-register-attempt01/README.md),
raw SHA-256 `7e1c393f0670b4f7428946a856dde757315307d0e92ecfa77e72d70f40bdde90`.

## Remaining decisions for the mechanics coordinator

Use the declared profiles and material scenarios to proceed with conditional
component calculations. The catalog leads do not yet establish a complete
compatible purchased stack: the 9.5-in BG003 lead lacks part-specific J429
and transition evidence; the primary nut engagement profiles remain absent;
and ordinary and hardened washer listings do not supply a numerical yield
minimum. A supported washer bending and timber-contact method is also needed.
These are specific source and method gaps, rather than a requirement to wait
for physical receiving before doing conditional arithmetic.

Keep bolt bending, continuous three-receiver behavior, splitting, group
effects, finished sections and combined loading in the connected corner
evaluation. Bind comparisons to signed actions from the same accepted state.
Hardware or geometry changes needed to satisfy these requirements must be
reported before changing the reviewed model.

The quantity reconciliation remains **92 new candidate stacks plus 12
retained frame stacks: 104 bolts, 104 nuts and 208 separate washers**.
The 66 Hillman panel/kicker screws remain separate. The twelve retained
arrangements are identified for reuse of applicable original resistance work;
this packet does not rerun their original qualification or assign new passes.

## Reproduction and source review

The local producer checks pinned geometry and inventory inputs, computes
member-specific thread-bearing limits, and keeps declared profile screens
separate from catalog and received-part status. Its raw JSON and downloaded
source PDFs/HTML remain local under the repository's evidence policy. Source
URLs, dimensions, hashes and numerical requirements are published in the
linked notes; no received-part observation has been filled in.

From the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/produce.py --write
python3 docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/produce.py --verify
python3 -m unittest discover -s docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30 -p 'test_requirements.py'
```

No native solve is part of this packet. The analysis coordinator owns response
inputs, heavy-run serialization and engineering acceptance. Existing studies
remain reproducible under their frozen assumptions.

Parent and independent Luna maximum-reasoning review completed September 30,
2026. All 12 focused tests passed, the three generated outputs replayed
exactly for 92 axes, and the producer/tests passed Ruff. All eight material
source pins and the packet's local links were checked. Review corrected
coordinate-table consistency and added rejection tests for nonfinite lengths
and negative wood coordinates; it did not change the frozen geometry or
material studies. This validates the packet's arithmetic and scope, not
engineering acceptance.
