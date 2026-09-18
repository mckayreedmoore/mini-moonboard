# Panel fasteners: product research and remaining qualification

**Research recommendation only. No screw substitution or hole relocation has
been implemented in the CAD.** The current
[bearing-frame candidate](bearing-frame.md) retains 48 generic main-panel screw
representations. Their geometry is not a qualified fastening specification.

The most useful candidate found is the carbon-steel **SPAX #8 × 2 in flat-head
T20 screw, XFT08P-2000**. Unlike a timber-only head test, its product report
includes plywood-specific head pull-through and plywood-to-lumber lateral
data. That makes it worth evaluating; it does not qualify the existing layout.

## Source and nominal product dimensions

The manufacturer's [product page](https://spax.us/products/unidrive-combination-ph-sq-flat-head-yellow-zinc)
links to [DrJ report 2010-02](https://dxf82wtg340bb.cloudfront.net/resources/DrJ-Report-Altenloh-Brinck-Co-US-Inc-SPAX-6-Construction-Screw-2010-02.pdf),
revised November 4, 2025, with renewal listed for January 1, 2027. Use that
manufacturer-linked revision rather than the older report found on the DrJ
website. The product page includes other drive variants; XFT08P-2000 is the
specific T20 candidate discussed here, not permission to substitute any #8 screw.

Table 2 lists the following nominal dimensions:

| Feature | Metric | Imperial |
| --- | ---: | ---: |
| Overall length | 50.8 mm | 2 in |
| Thread length, including tip | 31.496 mm | 1.240 in |
| Head diameter | 8.128 mm | 0.320 in |
| Major diameter | 4.1402 mm | 0.163 in |
| Minor diameter | 2.54 mm | 0.100 in |
| Shank diameter | 2.921 mm | 0.115 in |

These are not a complete tolerance drawing. Coating, head profile and actual
hardware fit must be resolved before replacing the generic model.

## Conditional reference values

The manufacturer [publishes separate withdrawal and plywood pull-through values](https://spax.us/products/unidrive-combination-ph-sq-flat-head-yellow-zinc).
For a #8 flat head, the 23/32-in plywood pull-through entry is **212 lbf**, with
plywood specific gravity 0.50. Sawn-lumber withdrawal is **133 lbf per inch of
embedded thread for Douglas Fir, SG=0.50**, or **127 lbf/in for SPF/Hem-Fir,
SG=0.42**. Reference values require applicable adjustments, not just a screw count.

With the modeled 18.25625 mm / 23/32-in face, nominal penetration is
32.54375 mm / 1.28125 in. This exceeds the candidate's entire 31.496 mm thread
length, leaving that thread nominally within the receiver. Multiplication gives
164.92 lbf for the Douglas-fir withdrawal case or 157.48 lbf for the SPF case,
before adjustments. These are arithmetic screening values, not allowable
climber loads. Actual thickness, seating, engagement, material and installation
must satisfy the applicable product basis.

Report Table 13 gives **51 lbf lateral reference resistance** for the listed
#8 × 2-in configuration with 23/32-in plywood and 1 9/32-in penetration into
**SPF framing, SG=0.42**. It expressly identifies that main-member species;
the plywood must meet its PS 1 and specific-gravity conditions. **Do not label
51 lbf a qualified Douglas-fir framing capacity.** A different main member
needs a supported calculation or product-engineering confirmation, even if
using the SPF value appears intuitively conservative.

The purchased AC Douglas-fir plywood is not automatically verified as the
SG=0.50 material behind the 212 lbf pull-through entry. Its grade stamp,
thickness and applicable material assignment still matter. Likewise, selecting
Douglas-fir framing does not establish the properties of every purchased piece.

## Eight existing corner positions still fail the receiver-end screen

Table 19 requires #8 end distances of 31.75 mm for perpendicular loading or
parallel loading away from the end, and 44.45 mm toward the end. Its 9.525 mm
edge requirement fits the nominal narrow-member centerline, but these current
outer corner positions are only **19.05 mm from their receiving rail ends**:

- `lean_panel_lower_left_1` and `lean_panel_lower_left_5`
- `lean_panel_lower_right_4` and `lean_panel_lower_right_8`
- `lean_panel_upper_left_1` and `lean_panel_upper_left_5`
- `lean_panel_upper_right_4` and `lean_panel_upper_right_8`

Thus a hardware-only swap at all 48 existing axes is not justified. Resolving
the corners requires a layout or receiver-detail change and another geometry
review. The remaining positions have not thereby received a complete group,
panel-edge, splitting or mixed-load qualification.

## Installation and load-path limits

The report requires flush installation without overdriving; lead holes are not
required. **Do not transfer the current generic 3.2 mm receiver pilot** to this
product and assume published performance: that bore exceeds the listed minor
diameter. Any proposed pilot needs a compatible product basis. Existing CAD
bores are inspection geometry, not instructions to predrill purchased stock.

Do not divide a whole-panel load by 48, or add lateral and withdrawal capacities.
A concentrated hold can load one panel region and a limited subset of fasteners.
Panel bending, connection slip, mixed-direction interaction, head pull-through,
local splitting, service-hole ligaments and racking can control. Applicable
adjustments and load combinations must remain consistent throughout the check.

Next qualification work is to establish the actual materials, resolve the eight
corner details, verify the installation dimensions, and evaluate a defensible
distribution of concentrated hold loads through the panel and its screw group.
No product research here changes the separate leg, kicker, floor-contact or
unanchored-stability review gates.
