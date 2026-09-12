# MoonBoard hold bolts and selected T-nuts

The owned Mini 2025 bundle uses **3/8-16 hardware** with the selected Escape
three-hole screw-in T-nuts. Moon publishes useful bolt-kit lengths: **3.5-inch
countersunk bolts for wood holds; 2.5- and 3.5-inch cap-head bolts for plastic
holds**. These are kit contents, not a location-by-location installed schedule.

## Published US bolt guidance

| Hold family | US kit | Published contents | Hex key |
| --- | --- | --- | --- |
| Wood B/C | [60-202-WO-USA](https://us.moonclimbing.com/products/moonboard-wood-hold-bolts) | 32 × 3/8-16 × 3.5-inch (88.9 mm), flat/countersunk head | 1/4 inch |
| School PE/PU | [60-202-USA](https://us.moonclimbing.com/products/universal-bolt-kit) | 32 × 3/8-16 × 2.5-inch (63.5 mm) and 20 × 3/8-16 × 3.5-inch (88.9 mm), cap head | 5/16 inch |

Moon recommends one kit per hold set. Its [Mini 2025 bundle](https://us.moonclimbing.com/products/mini-moonboard-2025-hold-set)
contains 138 holds: Original School including kicker footholds, School F, Wood B
and Wood C. Thus the published kit guidance corresponds to two wood kits and
two plastic kits; this is a quantity inference, not a purchase action. The bundle
excludes bolts, T-nuts and LEDs. Moon describes the bolts as high-strength steel
but does not provide a steel grade, complete head drawing or threaded-length
schedule on these pages.

The wood kit supplies a single nominal length. The plastic kit does not identify
which numbered hold uses which length. Neither listing establishes where a
bolt head sits relative to this custom panel without the actual hold's recess
and seat depth. Installed bolt geometry therefore needs that datum; adding kit
guidance does not justify placing bolt heads directly on the bare plywood.

## Engagement and rear clearance

The selected T-nut maker's [installation guide](https://cdn.shopify.com/s/files/1/0051/0374/7160/files/2020_Website_Editorial_HoldInstallation_Final02_fa528c3c-9929-4c46-af56-5f88bca8e014.pdf?v=1668023898)
requires a bolt that seats the hold fully and threads through the complete
T-nut. It gives 6–9 full turns depending on barrel length and warns that partial
engagement reduces retention. An unthreaded shoulder must not stop the hold
from tightening. The inspected guidance does not prescribe an extra protrusion
distance beyond the T-nut. Check rear clearance against timber, wiring and other
hardware with the actual hold installed. The generic Escape guide's flat-head
wrench example differs from Moon's wood-kit listing; use the product-specific
Moon wrench size above.

## T-nut geometry for CAD

The [recorded user measurements](site-survey.md#plywood-and-hardware-samples) identify
Escape three-hole screw-in T-nuts, Amazon ASIN B00FJGT7QI. These are retained
with screws, not hammer-in prongs. The [Escape product page](https://escapeclimbing.com/products/hd3hnut)
confirms the three-hole screw-in design, included screws and 7/16-inch drill-bit
option; it supplies no complete dimensioned manufacturer drawing.

| Quantity | Recorded value | Evidence |
| --- | --- | --- |
| Flange diameter × thickness | 25.4 × 1.86 mm | User measurement |
| Body depth | 12.7 mm | User measurement; datum ambiguous |
| Retention holes | Three, approximately 3.2 mm diameter | User measurement |
| Adjacent hole spacing | 15.98 mm center-to-center | 12.78 mm inside gap plus 3.2 mm hole |
| Panel bore | 7/16 inch = 11.1125 mm | Selected product/recorded bore |

The CAD representation uses explicit approximations: 11.0 mm barrel outside
diameter, an 8.0 mm smooth opening standing in for unmodeled internal threads,
an equilateral three-hole pattern at the recorded adjacent spacing, and arbitrary
clocking. The 12.7 mm depth is interpreted as projection into plywood from the
flange seating face, giving 14.56 mm overall depth. If the original measurement
included the flange, that interpretation must change. These assumptions are
not manufacturing dimensions or thread geometry. Retention-screw dimensions
remain unknown; no exact screw model follows from the included-screws claim.

## Regional hardware distinction

The [metric kits](https://moonclimbing.com/moonboard/parts-and-components/moonboard-holds-bolt-kit-metric-m10-1.html)
use M10: wood 32 × 90 mm countersunk with a 6 mm hex key; plastic 32 × 60 mm
plus 20 × 90 mm cap heads with an 8 mm key. M10 and 3/8-16 are not
interchangeable. Moon's [build guide](https://us.moonclimbing.com/blogs/guides/how-to-build-your-moonboard)
also lists its own imperial T-nut bore as 1/2 inch and barrel as 0.393 inch;
its metric version uses 13 mm and 10 mm. Those Moon-branded dimensions do not
replace the selected Escape bore or measured hardware.

[Machine-readable references and unresolved fields](moonboard-hold-hardware-reference.json)
record the published sources and the distinction between measurements and CAD
assumptions. No installed hold-bolt schedule or connection-strength release is
established by this reference.
