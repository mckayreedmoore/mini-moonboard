# Lumber base and connection development

**Not build-ready.** This revision models the connections and removes the
previous layout's known stock-length, bottom-backing and straight LED-access
problems. It does not establish joint capacities or climbing safety.

[Inspect the assembly](https://mckayreedmoore.github.io/mini-moonboard/?model=timber-base-development&view=rear)
· [STEP](../exports/timber-base-development/timber-base-development.step)
· [Parts and nominal dimensions](../exports/timber-base-development/timber-base-development_parts.csv)
· [Connection schedule](../exports/timber-base-development/timber-base-development_connections.csv)

## Lumber instead of long plywood rims

Use two full-width, one-piece nominal **2×8×10 ft Douglas-fir** side rims,
with modeled actual sections of 38.1 × 184.15 mm (1½ × 7¼ in). This replaces
the 177.8 mm-deep laminated-plywood concept; it is not a plywood splice or a
ripped 2×8. Two nominal **2×6×10 ft** pieces supply the long central uprights,
modeled at 38.1 × 139.7 mm (1½ × 5½ in). Their level bearing cuts fit 10 ft stock.

Product listings checked September 7, 2026:
[Lowe's #2 BTR kiln-dried Douglas-fir 2×8×10](https://www.lowes.com/pd/2-in-x-8-in-x-10-ft-Douglas-fir-Kiln-dried-Lumber/5015832067)
and [#2 Prime kiln-dried Douglas-fir 2×6×10](https://www.lowes.com/pd/2-in-x-6-in-x-10-ft-Douglas-Fir-Kiln-dried-Lumber/1000571227).
These establish listed products, not availability at a particular store or
the grade/species stamp of delivered stock. Confirm those before procurement.
The purchased 23/32 CAT Douglas-fir face plywood remains unchanged. Leg plies
and the two short base gussets retain an assumed 19.05 mm plywood thickness;
do not substitute the face-stock thickness silently.

## Wood and service details

- A continuous flat 2×4 backs the lower main-panel edge. It fits complementary
  88.9 mm-long × 38.1 mm-deep front housings in the two central uprights,
  leaving 101.6 mm of their rear depth continuous before local bores.
- Corrected hold/LED locations reserve 40 mm-diameter × 45 mm-deep access
  volumes behind the face. The lower seam rails retain 94.7 mm rear depth
  behind these pockets. Pockets can break through a narrow member's front
  edge; they are not all closed-bottom round holes.
- The lowest LED pocket locally cuts through the flat backing. Backing is
  continuous as a part, not uninterrupted material at every point.
- Four short vertical 2×12 blocks now support the full 285.75 mm header depth,
  removing the earlier header overhang beyond shallow 2×4 posts.
- All corrected face bores remain: 132 hold, 132 LED and ten kicker hold holes.
  Straight access reservations do not qualify wire bend radii or installation
  tool access. Flexible wiring still needs a routed service plan.

## Connections and assembly

There are 16 purchased ML24Z angle models with six separately purchased
SDS25112 screws each: twelve at the upper/mid framing and four under the base
header. Their bend, flange, hole and screw-head geometry uses the
[manufacturer reference](ml24z-qualification.md), not the older guessed pattern.
Published capacities still require matching installation, grain, load direction
and material conditions; the frame does not receive a blanket catalog rating.

Eight 3/8-16 × 3¾ in leg bolts replace the previous overlong leg bolts. Their
modeled grip is 76.2 mm across one rim and two leg plies. The
[Conquest HBA-38X334](https://www.fastenersplus.com/products/3-8-16-x-3-3-4-conquest-a307-grade-a-hex-bolt-plain)
is the selected nominal family. Six 2½ in stitch-bolt candidates join the leg
plies. No composite-action or clamp-friction capacity is assumed.

Two short plywood side gussets bridge each rim to its outer base post, using
four 3/8 in × 3 in through-bolt candidates per side. These supply a positive
retention concept without fabricating steel. Two recessed 3/8 in × 6 in bolt
candidates connect the lower backing to the principals. Their heads sit behind
the face panels; the panels must be removed to access these two bolts.
Their principal side-edge distance is only 19.05 mm (2 bolt diameters). Do not
credit cross-grain racking resistance without resolving the applicable loaded
edge-distance requirement; an axial-fit pass does not resolve that condition.

Forty-eight main-panel and eight kicker screws use nominal SPAX XFT08P-2000
#8 × 2 in geometry. Corner positions move away from timber ends; the top
corners have a larger setback because the principals terminate below the top
rail. [Product and plywood-capacity limitations](panel-fastener-qualification.md)
still apply. The modeled cone is a clearance proxy, not a manufacturer head
profile. Screw cylinders are occupied geometry, **not a pilot-hole specification**.
Kicker screw rows are Z=60 and 140 mm, leaving at least 46.9 mm to the nearer
post end for the upper row. The earlier Z=160 trial failed the product end-
distance screen and is not used.

Primary transport pieces remain the board/base and two removable legs.
The gusset bolts also permit base removal. Do not repeatedly remove and
reinstall wood screws as the normal transport joint. Base removal requires
supporting the board and keeping people out of its fall/tip path.

## Qualification still required

Body/head/washer/shaft and service-envelope checks address fit only. Remaining
structural work includes gusset bearing/net section/splitting, bolt-group load
sharing, housing net sections, panel attachment resistance, connector load
directions, floor friction and separation. Actual hardware/stock tolerances and
driver access also need review. New bulk FEA must use this revision and corrected
grid; historical base/bearing results do not transfer.
