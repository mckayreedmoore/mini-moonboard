# Horizontal-base layout study

**Geometry only; not a build plan or structural approval. Connections are
deliberately omitted, not implicitly approved.**

[Inspect the new layout from behind](https://mckayreedmoore.github.io/mini-moonboard/?model=base-bearing-concept&view=rear)
or [download the STEP assembly](../exports/base-bearing-concept/base-bearing-concept.step).
The [part schedule](../exports/base-bearing-concept/base-bearing-concept_parts.csv)
includes metric and imperial blank dimensions, not approved machining instructions.

## Changes

- The climbing-face envelope remains 2438.4 mm wide. Side rims move inward
  38.1 mm so the plywood sits in front of them. Redundant edge infills disappear.
- The top crossmember remains continuous. Its ends now fit between the inset
  side rims; paired midpoint rails meet the two central supports.
- A continuous, horizontal 2×12 header replaces the lower ledge/angle/splice
  arrangement. Sloped side and central members end on a level bearing cut,
  rather than touching a horizontal support at one corner.
- Four short vertical posts carry the header to the floor. The 225 mm kicker
  remains separate face plywood; crash pads remain excluded.
- The four existing plywood leg plies move inward with the side rims. They
  still sit outside the framing. Previous bolt lengths and grip calculations
  no longer apply.

## Corrected hole datums

This variant explicitly uses `panel_grid_v2`, not the old grid. Lower-panel
T-nuts are measured from the top edge; upper-panel T-nuts from the bottom.
For the assumed 1219.2 mm square sheets, row stations are 99.2–1099.2 mm and
1319.2–2319.2 mm, with a 220 mm gap between rows 6 and 7. The viewer's number
labels use those same stations.

The nominal 1220 mm drawing instead gives 100–1100 mm and 1320–2320 mm.
The 0.8 mm stock adaptation is explicit; dimensions are not scaled. Lower LEDs
also retain top-edge references, placing the lowest at 19.2 mm above the main
face bottom. Row 7's LED lies 20 mm below the seam on the lower panel. Thus the
lower panels contain seven LED rows and the upper panels five. No main-grid
LED holes belong on the kicker. The purchased LED system's installation guide
still needs reconciliation with these drawing-specific boundary exceptions.

Sources: [metric panel template](https://moonclimbing.com/media/moonboard-pdf/Mini_MoonBoard_Template_Guide_Metric.pdf),
[official build FAQ](https://us.moonclimbing.com/blogs/guides/how-to-build-your-moonboard).

## Buildability and disassembly

This removes several small lower-joint pieces and makes the compression load
path easier to inspect. It does not eliminate the need for connections resisting
separation, sideways motion and racking. The broad header and level cuts are
tradeoffs: fewer joints, but a wider base component and angled cuts on long stock.

The intended primary removable portions remain the board including its base,
plus two legs. A separately removable base is an optional future connection
design, not an extra disassembly requirement. Do not glue that interface merely
to make this conceptual model appear complete.

## Required before a buildable revision

1. Design header/post support, including the header's rear cantilever beyond
   the 88.9 mm-deep posts. Check bending, bearing and the resulting floor reactions.
2. Select detachable board/base and leg attachments; qualify plywood joints,
   bolt grip, edge distances, washers, driver access and separation resistance.
3. Design panel perimeter screws and back-side T-nut/LED service clearances.
   This layout has face bores but no framing pockets or retained screw schedule.
   Ten row-7 LED exits currently hit the lower seam rails; only column F is
   clear. The main panels' bottom edges also need backing between the uprights:
   the horizontal header is below their backplane and does not supply it.
4. Resolve long-stock availability before cutting. Side-rim blanks are about
   2602.7 mm (102.47 in), longer than an 8 ft plywood sheet; do not invent an
   unqualified splice. Central upright blanks are about 2532.6 mm (99.71 in),
   requiring 10 ft lumber. Check grain, actual thickness and cutting tolerances.
5. Run new contact/joint and structural analyses on the finished connection
   geometry. Historical FEA of `b23ffbe` cannot validate this layout.

The concept intentionally exposes these unfinished details. A nonintersecting
wood layout and visible holes do not establish a safe climbing structure.
