# Single-2x12 unbraced leg placement screen

This bounded placement screen preserves the selected spliced-knee design and
investigates a separate unbraced candidate. It does not transfer the braced
frame's forces or resistance acceptance. Reproduce the arithmetic with
`uv run python -m scripts.compact_2x12_layout`.

## Original row: rejected placement screen

Retain the 88.9 × 139.7 mm rims and compact 2x6 base. Replace each rear leg with
one 38.1 × 285.75 mm piece, leaning rearward 17.5 degrees from vertical. Move
the bolt-group center 225 mm down the rim from the preserved braced candidate's
center. Use four 12.7 mm bolts in a single centered row along rim grain, at
65 mm pitch. Keep the leg top 150 mm along its grain above the group center.

| Quantity | Geometric result |
|---|---:|
| Group center, Y / Z | 984.718 / 1608.663 mm |
| Foot center Y | 1491.927 mm |
| Full square-top, horizontal-foot stock length | 1881.778 mm |
| Full-length weak-axis slenderness, L / 38.1 | 49.391 |
| Leg loaded-edge reserve above 4D, after 3 mm face allowance | 6.844 mm |
| Rim loaded-edge reserve above 4D, after 3 mm face allowance | 16.050 mm |
| Leg top-end reserve above 7D, after 3 mm face allowance | 5.713 mm |
| Adjacent bolt spacing reserve above 4D | 14.200 mm |

**Correction:** this original 65 mm row has **164.461 mm** of cross-grain
spread in the leg. It fails the retained 127 mm shrinkage screen, which the
first arithmetic omitted. Its initial geometry-only recommendation is
withdrawn. The original row remains a separate diagnostic trial; its fit
margins above do not establish a passing layout.

## Corrected staggered candidate

Keep the same leg angle, stock, group center, foot and 150 mm top extension.
Replace the centered row by these four offsets from the group center in the
rim's grain/depth-normal coordinates, in millimeters:

| Bolt | Along rim grain, s | Along rim normal, q |
|---|---:|---:|
| 1 | −81 | +13 |
| 2 | −27 | +3 |
| 3 | +27 | −3 |
| 4 | +81 | −13 |

The rim normal is `(0, rim_grain.z, −rim_grain.y)`. The pattern gives
122.660 mm leg cross-grain spread, retaining 2.340 mm below 127 mm after
allowing 2 mm relative drill-axis variation. Minimum center spacing is
54.332 mm, retaining 1.532 mm above 4D after that same variation. Adjusted rim
edge reserve is 3.050 mm, and adjusted leg top-end reserve is 3.615 mm after
the 3 mm combined boundary/axis allowance. Both members pass the repository's
existing `layout_check`; general oblique load-row applicability remains its
explicit conditional interpretation, not a newly invented universal rule.

This geometry is implemented separately in
`mini_moonboard/compact_2x12_staggered_frame.py`. Neither the row trial's loads
nor the braced candidate's forces qualify it. The retained cross-grain limit
addresses restraint of wood shrinkage; see the AWC discussion of NDS
12.5.1.3 in [Practical Solutions and Details from the 2015 NDS](https://web-media.awc.org/wp-content/uploads/2021/12/17210649/StructureMag-NDS2015-PracticalSolutions-1611.pdf).

The foot center moves only 76.082 mm forward from the braced candidate. Actual
CAD must check the four holes against existing service openings and other
hardware, along with complete washer seating and the full horizontal foot cut.
The weak-axis slenderness is close to the retained 50 limit; fabrication must
not lengthen the member beyond the assessed geometry. This limit alone is not
a stability resistance check.

Keeping the previous attachment height with four bolts gives about 2027 mm
stock length and L/d = 53.21, failing that limit. Making the leg near vertical
improves overlap but moves its foot substantially toward the climbing face,
which is not a reasoned optimization of the assembled support system. The
chosen 17.5-degree lean retains more of the established rear footprint. A
200 mm downward shift at the same angle was geometrically possible, but left
less useful stock-length reserve. No additional angle sweep is needed before
checking this actual candidate under newly calculated unbraced loads.

## Hardware fit candidate

The outward tip installation puts the bolt head against the 4x6 rim and the nut
against the thinner 2x12 leg. Wood grip is 127 mm. With the existing USS
washer maximum thickness of 3.3528 mm, the nominal-diameter quarter-thread
route requires full-diameter body through the thread transition to reach at
least **120.8278 mm from the underside of the head**. Recalculate this with
actual stock and washer dimensions; ordinary procurement and assembly checks
must also establish nut seating and complete formed-thread engagement.

A 6-inch Grade 5 bolt is not an assured choice: its catalog minimum thread
length is 1.25 inches and its length tolerance is +0/−0.10 inch. Even using
nominal length and minimum threads gives only 120.65 mm of nominal unthreaded
length before allowing for transition. See [Bolt Depot product 403](https://boltdepot.com/Product-Details?product=403).

A purchasable 6.5-inch Grade 5 partial-thread candidate is WholesaleBolts
**12C612HB5Z**, listed with ±3/16-inch length tolerance. The catalog establishes
availability, not a guaranteed thread-transition location. See the
[supplier's product listing](https://www.wholesalebolts.com/1_2-13_x_6_1_2_zinc_grade_5_hex_bolts.aspx).

The standard minimum thread reference for 1/2-inch bolts longer than 6 inches
is 1.5 inches. At nominal 6.5-inch length this leaves 127 mm before the
nominal threaded region, which can fit the needed body length while allowing
the nut to seat outside the 127 mm wood grip and washers. Minimum thread
length is not maximum thread length, so this arithmetic is a procurement
candidate, not a guaranteed delivered dimension. See
[Bolt Depot's minimum-thread table](https://boltdepot.com/fastener-information/Bolts/US-Thread-Length?nv=res).

Keep the existing specified Grade 5 nut and USS washers only where the new
connection resistance calculation supports their catalog minimum dimensions.
No strength acceptance is established by this placement/hardware note.
