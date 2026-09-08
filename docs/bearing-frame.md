# Lower bearing and purchased-angle revision

**Inspection design, not construction or climbing approval.** This revision
addresses two lower-frame details in the
[continuous-rail predecessor](continuous-frame.md): the gap below the central
uprights and the four front-driven ledge screws. The predecessor remains
unchanged as a source-bound comparison.

**Known historical hole-layout error:** do not use this revision's panel or
kicker drilling schedules. The corrected panel-edge datums and subsequent
base redesign are separate work; none of this revision's results qualify them.

The [new structural results](bearing-structural-results.md) include valid bulk
stiffness runs and a leg-bolt dimensional audit, but no joint approval. Official
ML24Z geometry differs from the current proxy, and the lower-ledge load direction
still requires qualification. Do not treat the earlier nominal clearance tests
as verification of the purchased connector.

## What changes

The continuous lower 2×6 rail moves **1.6 mm uphill**, from board-local
S=100–138.1 mm to S=101.6–139.7 mm. Its rear-normal extent remains
N=38.1–177.8 mm. Existing lower rail connectors and their holes move with it.
The central uprights still start at S=139.7 mm, so their ends now meet the
rail instead of stopping 1.6 mm above it.

Each upright has a nominal bearing footprint of **38.1 × 101.6 mm**, or
3,870.96 mm² (1½ × 4 in, or 6 in²), on the lower rail. This is the geometric
contact area, not a qualified bearing capacity. Upright grain runs along S;
rail grain runs across the board. Rail compression perpendicular to grain,
upright compression, local splitting and the complete load path still require
evaluation. Contact provides compression bearing only, not resistance to
separation or reversed loading.

Four purchased ML24Z angle proxies replace the four GRK R4 lower-ledge screws.
Their connector origins are at X=−919.2, −519.2, 480.8 and 880.8 mm, with
S=101.6 mm and N=38.1 mm. These are board-local inspection coordinates; they
are not positions measured from an individual timber end or an approved
installation template.

The new angles span the interface between the flat ledge's rear face and the
lower rail's downhill face. Each proxy is rigidly rotated, not cut, bent or
redrilled. Its 101.6 mm width runs across the board. Three modeled screws enter
the rail and three enter the ledge. The revision changes how this connection
transfers load; it does not establish its mixed-direction resistance.

## Stock and hardware

**Wood stock sizes and piece count are unchanged** from the continuous-rail design.
Both full-width rails remain 2438.4 mm / 96 in long nominal 2×6 members, with
assumed actual sections of 38.1 × 139.7 mm. The upright cut lengths, faces,
paired midpoint rails, service gap, plywood legs and localized lower flat ledge
remain. The two lower edge infills start at S=190.5 mm instead of S=188.9 mm
to clear the relocated outer connector bodies. Each infill is therefore
**939.8 mm long instead of 941.4 mm**, a 1.6 mm reduction. This changes two
cut lengths without adding pieces or increasing the cut count. All other cut
lengths remain unchanged; the lower rail itself moves without being shortened.

The inventory changes from **16 to 20 ML24Z connectors** and from **96 to
120 SDS25112 connector screws**, purchased separately. Adding 24 connector
screws and removing four GRK R4 screws produces a net increase of **20 fastener
assemblies**. Other hardware remains as specified in the generated schedule.

The [Simpson connector catalog](https://ssttoolbox.widen.net/content/orplhjaqw1/pdf/C-C-2026.pdf)
is the product reference. Factory hole locations, bend geometry, tolerances,
actual fit and application-specific resistance remain unverified in this CAD
proxy. A catalog product name and collision-free geometry do not qualify the
rotated connector for these loads. No custom metal fabrication is intended.

## Assembly implications

1. Lay out the new lower rail position from the common board-plane datum.
   Do not reuse the predecessor's lower connector holes without checking the
   changed positions.
2. Dry-fit both upright ends against the lower rail and verify full intended
   contact. Do not assume an uneven end or an installation gap develops the
   nominal bearing footprint.
3. Fit the four purchased ledge angles while their locations remain accessible.
   Use the actual products to establish timber drilling positions; the proxy
   coordinates are not instructions to drill or modify factory steel.
4. Check actual driver access and service clearances before installing the
   climbing panels. Follow the qualified product installation instructions,
   including the required screw type and quantity.
5. Complete the retained leg and kicker connections from this variant's
   schedule. Plan lifting and temporary support separately.

This change trades four long, front-driven screws for more purchased hardware
and installation operations. It preserves the localized two-layer lower
transition; it is not a claim that all framing is single-layer or all joints
are compression-only.

## What remains unqualified

The new bearing interface and rotated angles require structural checks.
The geometry checks below do not establish connection resistance.
Panel screws and T-nut pull-through, the F-column unsupported edge region,
racking, rail and upright net sections, independent leg-ply behavior, leg
bolt groups and the kicker splice remain review items. Unanchored stability,
floor friction/contact and dynamic loads remain separate from connection
geometry. No glue or clamp-friction capacity, anchors, ballast or transferred
FEA approval is assumed; the crash pad remains a separate excluded element.

## Verification performed

The focused suite passed 17 tests: 11 current-variant geometry checks, three
export checks and three checks of the preserved predecessor's moment evidence.
The current geometry checks cover positive-area upright bearing, full-width
rails, unchanged connector shape under rigid rotation, body/hardware collisions,
open hold/LED service paths, receivers and flat floor contact faces. Export
checks compare source hashes, STEP/STL geometry and metric/imperial schedules.

The real browser loaded all 289 selectable meshes without reported JavaScript
or failed-request errors. Front/rear views, central-upright selection and the
new lower-angle selection were exercised; the angle inspection card displayed
101.6 × 50.8 × 50.8 mm and imperial dimensions. Captured views were visually
inspected. Two independent correctness/testing/dataflow review passes found
no remaining implementation defects after strengthening the connector-copy
regression test. These are nominal implementation checks, not physical fit,
driver-access, strength, contact or construction approval.

## Inspection files

[Open the revised backing](https://mckayreedmoore.github.io/mini-moonboard/?model=bearing-lean-frame&view=rear).
Download the [STEP assembly](../exports/bearing-lean-frame/bearing-lean-frame.step),
[parts schedule](../exports/bearing-lean-frame/bearing-lean-frame_parts.csv),
[connection schedule](../exports/bearing-lean-frame/bearing-lean-frame_connections.csv),
[grouped blanks](../exports/bearing-lean-frame/bearing-lean-frame_blank_groups.csv)
and [hole-entry coordinates](../exports/bearing-lean-frame/bearing-lean-frame_hole_entries.csv).
Schedules contain metric and imperial dimensions. These are inspection
documents, not approved fabrication templates or a construction release.
