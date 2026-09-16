# Uncut front joint: catalog bolt and washer option

Date: September 14, 2026. This is an **unselected, delivered-lot-conditional
hardware option** for the separate `compact-floor-uncut-development` candidate.
It preserves the 139.7 mm head-side post, 38.1 mm nut-side runner, 177.8 mm
wood grip and outward-facing nuts/tips. No CAD, stock, drilling or procurement
has changed. The [existing dimensional envelope](floor-uncut-front-bolt-envelope.md)
and its failed blanket 8-inch bolt screen remain historical evidence.

## Practical catalog arrangement

Per front bolt, use this order:

**Head → one thick flat washer → post → runner → one thick flat washer → nut.**

| Item | Published identity and dimensions |
| --- | --- |
| Bolt | [Grainger 29DK47, U01200.037.0850](https://www.grainger.com/product/Hex-Head-Cap-Screw-Steel-29DK47): ⅜-16 × 8½ inches, partially threaded Grade 5, ASME B18.2.1 / SAE J429; minimum thread length 1¼ inches. |
| Two washers | [Carr Lane CL-8-FW](https://www.carrlane.com/product/clamping-hardware/washers/flat-washers): 1-inch OD, 13/32-inch ID, 3/16-inch thickness; case-hardened 1010 steel, black oxide. |
| Nut | Retain [Bolt Depot 2571](https://boltdepot.com/Product-Details?product=2571), ⅜-16 Grade 5, subject to the existing 0.320–0.337-inch height envelope. |

These are closed, solid flat washers seated against wood, not air-gap spacers
or washer stacks. Four front joints would require four bolts and eight washers.
The existing nut basis is retained; no locknut or jam-nut substitution is made.

Grainger's [dimensional drawing](https://www.grainger.com/ec/pdf/grainger-29dk47.pdf)
shows 8.500-inch length and 1.250-inch thread length, but is a reference drawing.
Its product page explicitly warns that actual threading can exceed the stated
minimum. Neither source guarantees the required full-body length.

## Dimensional feasibility

For actual grip `G`, head washer `Wh`, nut washer `Wn`, nut height `N`, and
nut-side timber bearing length `T`, measure all distances from under the head:

- First reduced-body or transition location: `B ≥ G + Wh − T/4`.
- First fully usable thread location: `U ≤ G + Wh + Wn`.
- Usable full-diameter thread must span the seated nut; projected tip length
  alone is insufficient.

At nominal dimensions, `Wh = Wn = 4.7625 mm`:

| Quantity | Result |
| --- | ---: |
| Required full body `B` | **173.0375 mm** |
| Nut bearing face | **187.3250 mm** |
| Nominal start of the minimum-length thread | 184.1500 mm |
| Nominal thread-start-to-nut-face margin | **3.1750 mm** |
| Tip projection with maximum-height nut | 20.0152 mm |

The [CDE ASME B18.2.1 dimensional reference](https://cdefasteners.com/sites/default/files/product-specs/capscrewgr5-8.pdf)
lists a −0.18-inch length tolerance for this diameter above six inches and
0.312-inch maximum transition length. Used as an explicitly conservative
sensitivity, nominal length minus 1.25-inch threading minus 0.312-inch
transition gives **176.2252 mm** full body. At the shortest length, the same
subtraction gives **171.6532 mm**, which fails the nominal requirement by
**1.3843 mm**. These subtractions are not a guaranteed lower bound: threading
is not capped by the product's stated minimum, and the drawing is not a
delivered-lot certificate. The option improves practical fit but does not
create a blanket catalog pass.

## Proposed receiving limits for a concrete local fit study

These limits are project acceptance bounds, **not asserted Carr Lane
manufacturing tolerances**. No supplier lot has been measured.

| Measured item | Proposed acceptance |
| --- | --- |
| Each washer thickness | 4.50–5.00 mm |
| Each washer OD | 25.2222–26.1620 mm |
| Each washer physical bore | 10.00–11.5062 mm, with free passage over the actual bolt/underhead fillet |
| Bolt underhead length | 211.328–215.900 mm for this screening envelope |
| First reduced section, including all runout | **At least 173.275 mm**, for exact 177.8/38.1 mm wood dimensions |
| First complete usable thread | **No farther than 186.800 mm** from under head |
| Nut | Correct ⅜-16 thread, Grade 5 identity, full seating; height no greater than 8.5598 mm |

Those washer bounds give nut-face positions 186.800–187.800 mm and, with the
shortest accepted bolt and tallest nut, at least **14.9682 mm** projected tip.
Inspect complete formed threads through the entire nut and beyond it; the
projection allowance does not authorize seating on a transition or counting
the tip chamfer as usable thread. Account for measurement uncertainty when
accepting parts at any bound.

Actual wood variation requires recomputing the inequalities. Do not accept an
undersized post or reduce the grip merely to make a bolt qualify. A bolt that
fails the body criterion is rejected; do not silently switch to nominal
diameter in the lateral analysis. Underhead seating, fillets, washer flatness
and wrench access must also be inspected in the assembled detail.

## Bearing envelope and remaining resistance checks

The proposed maximum OD matches the existing 26.162 mm washer envelope.
Consequently the prior raw-profile perimeter gaps, including **12.338 mm**
between adjacent maximum-OD washers at the worst 38.5 mm hole spacing, remain
applicable as perimeter arithmetic. The added thickness needs its own axial
clearance and tool-access check. Flat seating around actual bores and other
machining is not established by perimeter clearance.

The washer's physical metal bore is **not** the timber bore used to calculate
wood contact area. For a centered flat seat, exclude at least the larger of
the actual wood opening and washer opening; eccentric drilling may remove
more support. Do not credit a smaller washer ID as extra wood bearing over
an existing larger timber hole.

Carr Lane's 1010/case-hardened description does not establish a minimum bulk
washer yield stress. **The previous washer's assumed 33 ksi value is not
transferred.** Before selecting this option, establish a supported material
basis and recalculate washer bending, head/nut contact, timber bearing and
the current connection resistance using the accepted dimensions and forces.
The thickness makes that a promising investigation, not a resistance pass.

The finite result is a purchasable arrangement with feasible nominal body and
nut seating, an explicit lot-inspection envelope and unchanged timber stock.
It remains unselected until the material/resistance and assembled fit checks
are complete. No supplier was contacted and no parts were ordered.
