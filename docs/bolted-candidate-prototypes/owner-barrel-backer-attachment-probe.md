# Detached kicker-backer attachment screen

This is a geometry-only trial on the current kerf-right, −85 mm outer-header
barrel viewer pose. It does not change the selected baseline, viewer, members,
or the fixed 66 panel/kicker screw and 12 frame-bolt axes. Run
`.venv/bin/python -m scripts.owner_barrel_backer_attachment_probe` to inspect
the machine-readable results.

The two existing 88.9 × 88.9 mm kicker-screw backers meet the underside of the
unchanged base header at Z = 238.9 mm. The shifted 38.1 mm center posts are at
X = ±180 mm and do not touch the backers. Attaching each backer to the header
is therefore the direct simple-joint trial; attaching to a center post would
need a bridging member or a changed backer, neither included here.

## Trial placement

Two vertically directed 1/4 in shaft envelopes, staggered diagonally in plan
on each backer, start at the header
top (Z = 277 mm) and cross a rear-inserted barrel envelope in that backer at
Z = 200 mm. These are *candidate coordinates*, not drilling dimensions:

| Backer | Rear pair X,Y (mm) | Front pair X,Y (mm) |
| --- | ---: | ---: |
| Left | −35, −100 | −20, −65 |
| Right | 20, −100 | 35, −65 |

The nominal 3½ in bolt trial includes a 2 mm washer under its head. Its shaft
passes the assumed barrel thread axis by 9.9 mm. The nominal tip is at
Z = 190.1 mm, **4.8962 mm beyond the modeled barrel far wall** at
Z = 194.9962 mm. The modeled 7.5 mm machine bore ends at Z = 186.1 mm,
providing 4 mm nominal tip-to-bore-end clearance. None of these nominal
numbers proves fit, usable threads, or that a delivered bolt avoids bottoming.
The rear cross-bores extend 32.901
and 67.901 mm into the two backers, respectively. The modeled 10.0076 mm OD,
16.002 mm long barrels are fully inside their timber; the machine and cross
bores meet. The smallest washer-to-principal gap in X is only about 5 mm, so
nominal non-intersection must **not** be read as a toleranced fit.

The finite CAD screen finds no positive-volume (>1 mm³) intersection for the
four trial pairs with unrelated wood, protected T-nuts, 50.8 mm provisional
hold-bolt projections, LED/wire display envelopes, 66 fixed panel screws, 12
retained frame bolts, or existing viewer barrel/bolt envelopes. The trial
shafts, barrels, bores, washers, heads, and individual driver paths also have
no mutually occupied positive-volume intersections. The two rear driver
envelopes overlap *each other*, but are used sequentially; the screen excludes
only driver-vs-driver simultaneous occupancy. Each driver remains screened
against fixed solids and other candidate hardware.

An initial more outboard trial intersected both existing center principals at
the header top. The inward coordinates above avoid that finite obstacle; the
probe contains only this final bounded candidate, not an open-ended search.

## Shorter ordinary-bolt sensitivity

The same four XY pairs were also screened with a **3 in (76.2 mm) nominal
bolt** and the backer barrel center raised from Z = 200 to **205 mm**. All
four nominal tips end 2.2 mm past their assumed barrel thread axes and
2.8038 mm *before* the modeled far barrel wall; the trial machine bores end
4 mm past the tips. The protected, unrelated-wood, other-viewer-hardware and
mutual-candidate finite screens remain free of >1 mm³ hits. This is a better
nominal tip position than the 3½ in trial, though 2.2 mm is still a narrow
axis-side margin and does not prove usable thread engagement or tolerance.

[Home Depot lists Everbilt 1/4-20 × 3 in galvanized hex bolt 805396](https://www.homedepot.com/p/204633284)
as an ordinary retail lead. Its product listing does not control the
delivered thread span, head/washer geometry or compatibility with the
provisional barrel; local store inventory varies. Nothing was purchased.
This Z = 205 mm variant remains detached from the viewer and unselected.

## Still open

- The Hillman-style barrel dimensions and thread-axis location are provisional;
  no delivered part, thread span, bolt length/grade, washer/head, or retail fit
  is verified. This does not select hardware.
- The detached 3 in / Z = 205 mm sensitivity removes modeled barrel overrun
  but is not adopted. Delivered shaft/thread dimensions, washer seating, and
  head/tool clearance still need evidence before hardware selection.
- Wood edge/end distances, hole tolerance, actual intersecting-bores workflow,
  complete wood/bolt/barrel strength, and four-joint load distribution are not
  checked. The ~5 mm nominal X clearance especially needs delivered hardware
  and cut tolerance evidence.
- The header-top bolt heads and rear barrel entrances appear geometrically
  reachable in the maintained model. Actual panel-installation order, driver
  sweep, repeated demounting, tool sizes, and access with delivered hardware
  remain unverified.
- Protected electrical solids and rear hold-bolt projections are model/trial
  envelopes, not measured installed items. No dynamic clearance or wiring bend
  radius is established.

`finite_clearance_screen_passed` means only this bounded nominal finite CAD
test is empty of recorded clashes. Retail, thread engagement, structural
capacity, head/tool fit, complete assembly sequence, drilling, and fabrication gates remain
**false**. There is no fabrication or climbing release.
