# PB-02 right header-to-principal: rectangular side cleat

**Nominal geometry accepted; non-fabricable and no drilling release.** This
is one alternate for the missing `clip_split_base_center_right` duty in the
[link-edge pose](simple-center-link-edge-probe.md). It leaves the selected
baseline and the existing side/rear cleats alone. The shifted right post,
backer, and fixed panel geometry are inherited. Historical clip forces are
not demand for this new load path.

## One joint pose

Add one solid rectangular timber cleat at X=0…50.95, Y=−175.7…−60,
Z=277…380 mm, against the left side of the right principal and the top of
the header. Assume its grain runs in Z. A single-piece 4×6 blank could be
ripped/crosscut to these nominal dimensions; actual stock and grain must be
checked. There is no half lap, pocket, steel fabrication, or structural wood
thread fixing.

Two illustrative 1/4-in (6.35-mm) through-bolts with nuts and flat washers:

| Path | Center / span (mm) | Intended wood |
| --- | --- | --- |
| Vertical | X=25.475, Y=−150; Z=238.9…380 | Header, new cleat |
| Crosswise | Y=−95, Z=330; X=0…89.05 | New cleat, right principal |

The vertical bolt exits the cleat's flat top, not the principal's inclined
top. Its lower nut is reached from the header underside behind the backer.
The crosswise bolt exits the principal's exposed right face forward of the
existing side cleat. Nominal 7.30-mm occupied bores, 10-mm-radius washer
seats, and 20-mm-radius × 20-mm straight tool envelopes are *screens*, not
bit, washer, socket, or purchased bolt specifications.

The CAD screen receives 100% of each bore in the named wood, finds no new
solid overlap or unintended wood/bore intersection, and gives all four flat
washer seats 100% bearing. All four tool envelopes clear wood and installed
panel/kicker solids. The new cleat and bores miss all 48 panel and 18 kicker
screw envelopes and existing center bores. Both inner kicker edges remain
supported, and all four center-kicker screw receiver fractions remain 1.0.
This is a nominal CAD envelope check, not a tolerance proof.

## Conditional 2024 NDS placement screen

For D=6.35 mm, [NDS 2024 Chapter 12, Tables 12.5.1A and
12.5.1C](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
gives the relevant conditional
benchmarks: 4D=25.4 mm at a perpendicular-to-grain loaded edge, 1.5D=9.525
mm at an unloaded edge, and 7D=44.45 mm at a softwood end under tension
parallel to grain for full geometry factor. The loading direction and final
grain/edge classification remain unestablished; these are placement screens,
not a connection calculation.

| Face-center distance | Nominal (mm) | Conditional concern |
| --- | ---: | --- |
| Vertical bolt, cleat X sides | 25.475 / 25.475 | Only 0.075 over 4D |
| Vertical bolt, cleat/header rear Y | 25.7 / 25.7 | Only 0.3 over 4D |
| Vertical bolt, cleat/header front Y | 90 / 114.3 | Clear of 4D |
| Cross bolt, cleat Y sides | 80.7 / 35 | Clear of 4D |
| Cross bolt, cleat Z ends | 53 / 50 | Clear of 7D if applicable |
| Cross bolt, principal rear Y offset | 87.7 | Sloped-grain end distance needs review |

The vertical bore runs **parallel to the assumed cleat grain** and enters its
end grain. The NDS dowel-bearing/end-grain treatment and local splitting
cannot be inferred from face clearances; changing grain direction changes the
end-distance checks. The header's grain is along X and the principal's is
inclined. Any combination of load reversal, tension, shear, and moment must
be classified and checked in each member. A single bolt per interface does
not by itself qualify moment transfer, withdrawal, bolt bending, washer
bearing, group action, or the complete load path. These are explicit
strength/mechanism gates, not load-path acceptance. The near-4D margins have
no allowance for stock variation, drill wander, or kerf.

A one-step width/center revision cannot solve the limiting rear-Y margin in
this pose. The existing backer starts at Y=−124.9 mm. Keeping a 20-mm-radius
straight tool below the header requires the vertical-bolt center at or behind
Y=−144.9 mm. The header rear edge is Y=−175.7 mm, so the **largest possible**
rear edge distance is 30.8 mm: only 5.4 mm over 4D, with the tool tangent to
the backer and zero access tolerance. Widening the cleat can improve its X
reserve but cannot change that header/backer limit. No revised pose is adopted
or additional geometry swept.

**Limit:** accepted as this exact nominal two-bolt geometry only, and
explicitly **not fabricable from these dimensions**. No NDS
capacity, verified delivered shank/length, purchased hardware, fabrication
coordinates, rating, or drilling release follows. Reproduce with
`.venv/bin/python scripts/simple_center_header_principal_cleat_probe.py` and
`.venv/bin/python -m pytest -q
tests/test_simple_center_header_principal_cleat_probe.py`.
