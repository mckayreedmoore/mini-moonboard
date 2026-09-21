# PB05 outer-base 4D cleat search — geometry only

The earlier 38.1 × 38.1 × 30 mm cleat cleared the protected model but had only
12.7 mm of edge distance. A 6.35 mm bolt's **conditional** 4D target is 25.4 mm;
this is a screening target, not a complete NDS joint check or a hardware rating.

The reproducible [search](../../scripts/simple_pb05_outer_base_4d_search.py)
compares ordinary full-section 2×4 stock in both orientations with a 4×4.
Either 2×4 orientation has one 38.1 mm plan dimension, below the 50.8 mm needed
to place a bolt 25.4 mm from both edges. A 63.5 mm long, unnotched 4×4
(88.9 × 88.9 mm actual section) is a nominal geometric candidate at **each**
outer-base duty. Its forward face is at Y = −203.2 mm and rear face at
Y = −114.3 mm. The side-rim bolt is at Y = −149.5 mm, Z = 308.75 mm; the
vertical header bolt is at Y = −140.5 mm and the 4×4 X midpoint. Their
nominal wood grips are **177.8 and 101.6 mm**, respectively: the side bolt
crosses the 88.9 mm rim and the 88.9 mm cleat. It is not a 127 mm grip. The
two bolts have separate bores.

The smallest reported cleat/receiver edge margin is **26.2 mm**, above the
conditional 25.4 mm target. Both bores intersect both intended host members.
Exact solid-volume checks find no collision with the other 12 frame-bolt axes,
all 66 unchanged panel/kicker axes and panels, the eight PB05 blocks and their
bores/stacks/tools, lower rails, retained angles, other legacy angles/SDS axes,
or other timber. The test includes generic washer, nut, 40 mm tool envelopes,
and full nominal 8-inch side and 5-inch header bolt shafts. The cleat makes
positive contact with both the side rim and base header on each side.

For the side bolt, the provisional PB05 stack of two 1.651 mm washers, a
5.7404 mm nut, and 2.54 mm for two thread pitches needs **189.3824 mm**
under-head length. An 8-inch (203.2 mm) nominal bolt has 13.8176 mm length
margin; its tip projects 23.749 mm beyond the wood and 16.3576 mm beyond the
nominal nut. The full tip remains inside the modeled 40 mm far-side tool
envelope and has no modeled neighbor collision, but that much exposed thread
is a handling/assembly issue, not a strength endorsement. On the listed
six-inch-thread assumption for the 8-inch Everbilt lead, the nominal nut
starts beyond the inferred thread start. Complete usable thread/runout and
delivered length are not certified. A **6-inch side bolt is 36.9824 mm too
short** for the same stack, regardless of retailer; even its 152.4 mm nominal
length is shorter than the 177.8 mm bare wood grip. The 5-inch header stack
has the same nominal length margin and tip projection, but its retail thread
length remains unselected. The collision solids use generic conservative
head/nut/washer and 40 mm access envelopes, not certified SKU dimensions.

This is **GEOMETRY PASS, CONDITIONAL**, not a structural choice or drilling
release. The protruding cleat is only partly supported by the header and side
rim; those actual bearing areas and the short 63.5 mm grain length require
local joint checks. Signed NDS end/edge rules, all applicable yield and
withdrawal/splitting modes, washer bearing, exact purchased shank/thread
geometry, member capacity, assembly sequence, price, and a new native solve
remain open. The two original angle/SDS duties stay active until an accepted
replacement is modeled and independently reviewed. No panels or panel-screw
axes are changed.
