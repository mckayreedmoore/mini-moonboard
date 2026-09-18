# Fabricated steel base-shoe development

This is a separate, **provisional fabricated-steel candidate**, implemented in
[`steel_base_reinforcement.py`](../mini_moonboard/steel_base_reinforcement.py).
It is not a purchased rated angle, approved fabrication drawing or construction
release. The selected `round-structural-development` model remains unchanged.

The change replaces the two outer ML24Z angles and their twelve SDS25112 screws
with two welded shoes, sixteen 3/8-inch through-bolts and sixteen separate square
bearing plates. The other 22 ML24Z connections, all 56 panel/kicker screws and
all eight original complete leg bolt stacks remain. No historical plywood
base gusset, old gusset bore or old connection capacity is reinstated.

## Actual proposed geometry

Each shoe has a 9.525 mm horizontal foot plate and an outer-side 9.525 mm web.
The foot spans absolute X = 1035–1240 mm and Y = −245 to −32 mm, resting on the
existing header top at Z = 225 mm. Each rim's horizontal bearing cut is
explicitly raised by 9.525 mm, to Z = 234.525 mm, replacing that wood thickness
with the steel seat while preserving all upper framing and panel coordinates.
The header is not moved or enlarged. This is a new cut in a separate candidate;
it is not silently applied to the selected drawing set.

The web follows rim coordinates N = 20–125 mm and ends at slope station S =
280 mm. Its exterior location avoids the retained bottom rail and its clips.
A modeled 6 mm external fillet joins web and foot along the web's bottom edge;
no internal weld intrudes into the timber seat. The weld size, electrode,
procedure, inspection and force resistance are not qualified. A passage in
the web provides 2 mm radial clearance around each intersecting current rim
LED bore. That clearance is a provisional fabrication allowance.

Each side has four rim bolts at S = 170 and 230 mm crossed with N = 45 and
100 mm. These pass through shoe, 38.1 mm rim and a 32 × 32 × 6.35 mm inner
bearing plate. They sit above the bottom rail and its clip envelopes.
Four vertical header bolts per shoe cross absolute X = 1060 and 1110 mm with
Y = −210 and −80 mm. Their separate 32 mm plates
sit under the header, inboard of the full-depth outer posts and their clips.

All sixteen new stacks use provisional 3/8-16 × 3-inch A307 Grade A bolts,
A563 Grade A nuts, and two maximum-envelope SAE washers from the existing
hardware model. The separate square plate spreads load into the wood; the SAE
washer seats against steel. Grip is 53.975 mm:
9.525 mm shoe + 38.1 mm timber + 6.35 mm bearing plate. Both head and nut,
both washers, the full shaft and the separate drilled bearing plate are
modeled. Nominal nut engagement and protrusion are checked, but actual product
availability and dimensional tolerances require procurement confirmation.
New heads and nuts use the existing inspectable hex geometry, rather than
circular display envelopes.

## Why this is a calculable next connection

The rim's four noncollinear bolts transfer a simultaneous six-component wrench
to the web. The web, weld and foot transfer it to the header's four noncollinear
bolts plus compression bearing. The geometry provides explicit lever arms for
both groups; it does not depend on assigning ML24Z an unlisted force or moment
rating. This does not imply that the chosen plate thickness, weld or bolts have
adequate resistance.

Specified material properties can be established independently of a connector
catalog. [SSAB's A36 specification](https://www.ssab.com/en-us/brands-and-products/commercial-steel/structural-steel/astm-a36)
identifies 36 ksi minimum yield and 58–80 ksi tensile strength for the stated
plate thickness range. These are **conditional procurement properties**, not
measured properties of steel already owned. The mill certificate must identify
the specified grade. [ASTM A307](https://store.astm.org/a0307-21.html) identifies
Grade A's 60 ksi minimum tensile strength; it does not establish a minimum
bolt yield strength. Do not transfer SAE Grade 2 yield properties to A307.

The next resistance calculation must use the actual signed rim/header wrenches
and contact reactions. It must include plate bending and prying, the actual
one-sided weld group, steel net section and hole bearing/tear-out, bolt combined
shear/tension and threaded shear planes, plate-washer bending, timber bearing,
directional dowel resistance and wood group/splitting failure. Rim end bearing,
header pressure distribution and the supporting posts are part of this load
path. There is no clamp-friction credit and no sum of unrelated catalog ratings.

## Geometry evidence and limits

[`steel_base_reinforcement_fit.py`](../fea/steel_base_reinforcement_fit.py)
checks the added steel against all retained bodies and fasteners, the added
bolt components against existing hardware and their drilled receivers, each
raw material interval along the bolt stack, nominal nut/thread geometry, and
25 mm diameter × 50 mm long socket allowances at both ends. It also compares
retained panel-screw receiver intervals before and after the rim-end trim.
The socket envelopes are project assumptions, not a selected tool drawing.

The [final v3 fit result](../fea/results/steel-base-reinforcement-fit-v3.json)
records the precise signed coordinates, receiver list,
removed wood volumes, and any collisions. A geometry pass is not a resistance
pass. The parent combined candidate must separately check its added kicker
screws and recalculate actual steel mass and global support assumptions.

The retained-screw check includes both panel screws and SDS screws entering the
changed rims/header. It compares receiver intervals after the new bolt holes
are cut, excluding each retained screw's own bore. The preserved v1 trial used
the −60 mm front header row; v2 moved that row to −80 mm. V3 also uses explicit
hex ends and the expanded receiver check. Earlier trials do not replace v3.
