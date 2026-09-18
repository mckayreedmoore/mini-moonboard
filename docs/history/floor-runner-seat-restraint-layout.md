# Square-seat restraint layout: bounded catalog rejection

## Decision

The first practical layout examined here is an inward plywood cheek spanning
the square-ended rim, its fitted timber seat and the existing 6×6 outer post,
using Simpson SDS screws. **Do not advance this layout to CAD or solves:** the
thin cheek and short seat do not meet the applicable SDS report geometry.
This rejects this specific catalog-fastener route, not all plywood connections
or the square-ended rim direction.

The construction remains a feasibility option. No timber, drilling, hardware,
selected candidate or structural solve was changed.

## Actual interface planes

Coordinates below describe the left side; mirror X for the right side.

| Part | X interval, mm | Grain |
| --- | --- | --- |
| Existing 6×6 outer post | −1308.1 to −1168.4 | Z |
| Rim and proposed timber seat | −1219.2 to −1130.3 | Rim inclined in YZ; seat Y |
| Proposed single 23/32-inch cheek | −1130.3 to −1112.04375 | Plywood orientation must be specified |
| Required post packing, if pursued | −1168.4 to −1130.3 | Must be independently specified |

The inward faces differ by **38.1 mm**. A flat cheek cannot touch all three
wood receivers without that packing or an explicitly offset connection.
An outward cheek is worse geometrically: those faces differ by **88.9 mm**.
Calling either arrangement flush would conceal an actual gap. A packing block
would be part of the connection, with its own interface and bearing actions;
it cannot be assigned composite action with the post.

All proposed cheek fastener axes run along X into **side grain** of rim, seat
and post. None enters the header end as a withdrawal receiver. The header
retains its X grain, Y[−175.7,−36], Z238.9–277 envelope. The proposed cheek
must bridge the header height without inventing lateral restraint from its end.

## Exact SDS geometry conflicts

The current [ICC-ES ESR-2236, §4.1.6 and Table 4B](https://cdn-v2.icc-es.org/wp-content/uploads/report-directory/ESR-2236.pdf)
permits its generic NDS wood-to-wood lateral route only with a side member at
least 38 mm thick and main-member penetration at least 38 mm. It also requires
76.2 mm end distance for parallel-grain loading. These are product-specific
conditions; a generic bolt spacing rule cannot replace them.

1. **Cheek thickness:** 18.25625 mm is less than 38 mm by **19.74375 mm**.
   A single owned-type plywood cheek does not meet this route. Stacking sheets
   would introduce a new assembly; it does not automatically establish the
   required side-member properties or load sharing.
2. **Seat end distance:** even before toe relief, the extended-heel seat spans
   Y−175.7 to −41.497331208, only **134.202669 mm**. Its best possible centered
   axis is Y−108.598665604, giving **67.101334 mm** to each end, short by
   **9.098666 mm** at each end. The sloping boundary can further reduce the
   actual material available at screw elevation. No single axis can satisfy
   the two 76.2 mm end distances in this footprint, before spacing multiple
   screws or adding a fabrication allowance. Any toe truncation worsens this.

These are zero-load placement failures. A small historical force, longer screw
or optimistic equal sharing cannot fix them. A rated steel-side SDS value is
also not transferable to the plywood cheek.

## Eccentricities cannot be omitted from another fastener route

The proposed cheek midplane is X−1121.171875. Its offset from the rim/seat
centroid X−1174.75 is **53.578125 mm**. Its offset from the post centroid
X−1238.25 is **117.078125 mm**. The packing does not remove these offsets.
Fastener-group loads, plywood bending, withdrawal/head bearing and receiver
loads must follow their actual application planes.

For scale only, apply the preserved flush A12-left vertical bearing witness
**V=401.9 N** to the proposed frictionless square seat. It would imply
**H=337.234 N** and normal force **524.643 N**. This force transformation is
a diagnostic assumption, not a new response result. At the cheek/rim offset,
H alone corresponds to **18.068 N·m** about Z. If V also passed through the
cheek, its corresponding moment about Y would be **21.533 N·m**; the actual
seat/header contact might carry some or all V and must be solved explicitly.
At the cheek/post offset those respective moments would be **39.483** and
**47.054 N·m**. Do not add these separate body comparisons as one joint demand,
and do not assign half to another cheek without a compatible stiffness model.

## What remains available

A standard bolt or conventional lag connection could use a different published
design route. That is a separate layout and calculation, not an SDS substitute
with retained capacities. As one geometric probe, a 1/4-inch X-directed bolt
at seat `(Y,Z)=(-130,310)` has 45.7 mm to the rear end, 33 mm above the base
and approximately 41.3 mm below the local sloping top. This is only a single
axis: it does not establish an independent couple restraint, a complete cheek
layout, adequate plywood/washer bearing, catalog bolt length or clearance from
all existing hardware. No drilling is released from this probe.

The [NDS 2024 Chapter 12, Tables 12.5.1A–D](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
requires load-direction-dependent distances and spacing for the corresponding
fastener route. A conservative screen may examine both loading directions,
but must not be mislabeled as an explicit minimum for every oblique joint.
Use actual sloping boundaries and applicable geometry factors. A viable next
layout must establish the rim, seat and post groups together, including packing,
plate bending, fastener yield, local wood splitting, complete hardware stacks,
and installation access before a frame solve can qualify its loads.
