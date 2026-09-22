# Bottom-center pair — one detached X/bolt-row revision

Owner-layout diagnostic only. The original same-side 139.7 mm X trial remains
unchanged via `owner_layout_bottom_center_pair.screen()`. This source-distinct
revision keeps its 139.7 mm local N, 57.15 mm local T, kerf-right finished
timber, ±180 mm center posts, two original bracket duties, 66 panel/kicker
screw axes, and 12 frame bolt axes. It proposes X = 77 mm per block with
rail-bolt rows 26 and 51 mm from the actual same-side butt. No baseline frame
cuts, protected services, or historical sources are changed.
This local front screen still carries the old PB02 side-cleat envelope as a
conservative historical check; the unified 24-duty assembly does not include
that cleat or rear-return chain. The front REVISE verdict instead rests on
E1/G1 installed-stack and tool conflicts, not that absent cleat.

The left rail stock profile has X = [−1130.3, −89.05] mm and local
N = [209.840968, 349.540968] mm. Thus N = 279.690968 mm (69.85 mm into the
rail) reaches the center butt. The 0%-wood first-trial second bore at
X = −174.05 mm instead lies wholly within the existing 38.1 mm-diameter
E1–E2 timber passage centered X = −189.2 mm, N = 279.690968 mm: center
separation 15.15 mm plus trial bore radius 3.75 mm is 18.90 mm, below the
passage radius 19.05 mm. This is real removed wood, not a rail cutback.
The revised far rail row X = −140.05 mm has 26.35 mm nominal radial separation
from that passage after both radii; actual finished-wood CAD remains the gate.

E1 and G1 lower hold centers are X = −219.2 and +180.8 mm. Their modeled
25.4 mm flange X intervals are [−231.9, −206.5] and [168.1, 193.5] mm.
The current kerf-right viewer solids give E1/G1 wire X bounds
[−221.1465, −187.2] and [178.8535, 212.8] mm, and E1/G1 LED body X bounds
[−225.548, −212.852] and [174.452, 187.148] mm. These are actual STL
bounds, not zero-length hold-axis assumptions. Current E1/G1 T-nut Y/Z
bounds are [22.39,45.2387]/[352.1865,375.4831] mm; the two wire Y/Z
bounds are [−65.6397,90.9585]/[306.9738,448.1838] mm. The provisional
rearward hold projection extends 50.8 mm from the rear seating datum.
The 77 mm front-face block X intervals are [−166.05, −89.05] and
[89.05, 166.05] mm. The right nominal flange X gap is just 2.05 mm; that
is not a tolerance-qualified or construction clearance. The maintained
50.8 mm provisional hold projection, LEDs, wires, 66 panel screws, and 12
frame bolts are all explicitly screened as finite 3D solids in the single
bounded CAD run; a flange X interval alone is not a complete clearance.

A direct full-N rear-face flip was rejected by bounds *before* the run.
It would place the block in local T = [183.474134, 240.624134] mm and local
N = [209.840968, 349.540968] mm. The retained right PB02 side-cleat blank
contains world point (X,Y,Z) = (100,−125,350) mm, which also lies inside
that rear block (T = 187.767104, N = 320.731219 mm). Shifting the rear
block down to N ≈ [160,299.7] would narrowly avoid the cleat by about 3 mm
at its near T plane while placing its low corner only about 4 mm above the
approved relocated center-post blank. The lower E1/G1 LED and wire region
also occupies the rear-facing vicinity and overlaps a full-width rear block
in X by the actual STL bounds above. Such a multiple-change rear variant
is not accepted by this one-pose screen. It would need separate finite 3D
checks and tolerance work, not merely a T-nut-only clearance argument.

The proposed 77 mm X pose itself has only 26 mm nominal far bolt end distance
and 2.05 mm nominal G1 flange X separation. Load direction, service routing,
delivered hardware, tool sequence, and fabrication tolerance are unverified.

The one bounded focused CAD suite passed **3/3 tests in 33.65 s**. It confirms
all eight nominal bores have complete intended wood/block coverage, both
contacts are positive, the right side cleat and other modeled timber do not
intersect either block, and neither block intersects the finite protected
solids. The two blocks do not touch modeled panel-screw or frame-bolt shafts.
The fixture did **not** emit the complete feature-hit report, so no numeric
intersection volumes or all-clear for bores, installed stacks, and tools can
be claimed from that run. No second heavy run is authorized.

There are nonetheless exact analytic *occupied-space* witnesses in the
modeled stack, even before discussing fabrication tolerances. The right
principal-1 far tool cylinder has X = [168.05,208.05] mm, local center
(T,N) = (307.299134,259.840968) mm, and radius 20 mm. G1's provisional
hold path runs at X = 180.8 mm, T = 299.824134 mm, through
N = [245.840968,296.640968] mm with radius 5.55625 mm. Thus the point
(X,T,N) = (180.8,299.824134,260) mm lies inside both. Its installed far nut
has X = [168.05,177.05] mm and radius 9 mm; point (176,300,260) mm lies
inside that nut and the same provisional G1 path. The same point with
N = 295 mm witnesses right principal-2 far-nut/hold-path overlap. The far
tool also reaches the G1 T-nut flange, while the corresponding left
principal-1 far tool reaches the E1 flange. These are real modeled
intersections, not merely overlapping axis-aligned boxes, but their exact
CAD volumes and any other feature hits were not retained by the test.

Disposition: **REVISE**, unselected and blocked as a viewer *joint pose*
pending a new bottom-center concept. The front 77 mm pose solves the first
block and missing-wood issues only; the installed tool/nut and provisional
hold-path conflicts remain. It may only be displayed as explicit conflict
evidence, never as the assembled choice. No mechanics verdict, native solve,
drilling plan, or build release.
