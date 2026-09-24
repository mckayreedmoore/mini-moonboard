# WJ-04 ordinary workhorse diagnostic

Status: **REVISE, bound diagnostic geometry only.** The current probe at
[`wj04-probe.json`](wj04-probe.json) is for
`narrow_x95p25_ordinary_bolt_candidate` at
`clip_horizontal_lower_right_1`, with configuration SHA-256
`d1c63e1fa5617999e8af68d683cc0f3074fb84f518b048a087ec5ed276206c0e`. It does
not complete WJ-04, qualify hardware, establish capacity, or authorize a cut
or hole.

The active trial uses a 95.25 × 38.1 × 119.7 mm no-notch cleat, K.L. Jack
`25C375HCS5Z` rail and `25C600HCS5Z` principal bolts, `25CNFH5Z` nuts, two
Type A Wide plain washers per stack, and a cataloged FACOM `34.7/16` tool
candidate. A seller SKU for the washers is not selected. The current probe
models generic 40/50 mm tool envelopes; it does not establish the FACOM
wrench's installed access or working sweep. The current tool-access report is
a separate conservative-envelope diagnostic; it establishes neither physical
access nor impossibility. The early mechanics report carries only six
historical angle-demand cases; no fresh candidate demand or resistance is
established. See the
[ordinary hardware basis](ordinary-hardware-basis.md) and
[canonical configuration](../../mini_moonboard/wood_joint_wj04_config.py).

## Actual hosts and proposed connector

The source-bound right principal spans X = 50.95–89.05 mm. The lower service
rail begins at X = 89.05 mm and has a 38.1 × 139.7 mm section. The principal
grain follows panel tangent T; the rail grain follows X. Their rear faces
`planar_face_04` and `planar_face_02` are only 38.1 mm wide. The connector
bears on the principal's X end and the rail's upper T face. Both primary
members stay full-section and unnotched.

One solid-wood cleat has provisional local X × T × N size
**95.25 × 38.1 × 119.7 mm**, with grain along N. Its front starts 20 mm
behind the rail's front; its back ends at the rail's 139.7 mm rear limit.
The dimensions have a solid 2×6 stock lead: listed actual 38.1 × 139.7 mm
section, with 38.1 mm on T, one rip from 139.7 to 95.25 mm on X, then a
119.7 mm crosscut on N. No 4×6 or 6×6 resaw is needed for this orientation.
The reviewed Lowe's listing describes #2 Prime Douglas-fir KD, but says only
“Douglas fir,” notes anti-stain treatment without identifying it, and says it
does not meet AWPA standards. It does not qualify the final ripped width.
NDS §4.1.7.1 requires structural lumber that is resawn or remanufactured to be
regraded. This is a dimensional raw-stock lead only until post-rip grade
evidence or a traceable alternate source for the finished section is
identified; local stock, delivered dimensions, species group, grade, treatment,
kerf, and yield are unverified. See the [stock and cut basis](stock-and-cut-basis.md)
for the source details and receiving conditions. The measured
nominal contact patches are 4,560.57 mm² to the principal and
11,401.425 mm² to the rail. Contact is compression only. Each interface
has its own two-bolt group; no glue or structural wood screws are credited.

The diagnostic principal bolts enter from the cleat's outer X face toward
the principal's inner face. Their N centers are 293 and 320 mm in the
source world-projected datum. The rail bolts enter from its lower T face
through the cleat at X = 127.15 and 152.55 mm, N = 265 mm. These positions
separate the orthogonal groups. All four provisional bores are 7.5 mm.
The bolt axes, bores, washer seats, installed head/nut/shaft shapes, static
tools, withdrawal strokes, and a staged rail-nut removal path are modeled.
These are CAD occupancy values, not drilling or purchased hardware sizes.

## Current bound probe result

The source-bound report status is `diagnostic_revise`; all purchase,
structural, fabrication, and drilling release flags remain false. The local
cleat body has no sampled hit in the reported host, other-wood, panel, or
protected inventories and has **0.0 mm** excess beyond the 139.7 mm ordinary
local-N envelope. This is a local screen only: the four WJ-03 outer stations
are absent, and replacement outer-node geometry is not included.

All four modeled stacks have no installed head, washer, nut, or shaft clashes;
the eight washer seats have full modeled support. The two rail stacks use
95.25 mm `25C375HCS5Z` bolts over a 76.2 mm grip; the two principal stacks use
152.4 mm `25C600HCS5Z` bolts over a 133.35 mm grip. Each catalog candidate has
6.7056 mm nominal length reserve. The report places the provisional nut
within the catalog thread interval, but requires delivered-part receiving and
does not guarantee full-form threads at the bolt end.

The rail's sampled 50 mm tool envelope clears with only **0.764 mm** nominal
gap to the upper rail; the 40 mm envelope has 10.764 mm. The modeled temporary
rearward nut exit extends 21.872532 mm beyond the ordinary local-N limit. The
probe includes nominal insertion/withdrawal and detached-hardware envelopes,
but neither those envelopes nor the catalog FACOM nomination proves physical
tool operation, hand clearance, capture/retrieval, or tolerance-feasible
access. The current [`wj04-tool-access.md`](wj04-tool-access.md) report has
status `diagnostic_overlap_present`. Broad wrench envelopes overlap modeled
solids during head counterhold, nut stroke/reindex, and nut/washer removal on
the stacks; two-wrench overlap and bolt-withdrawal proxies are clear. The
model uses synthetic heading samples and bounding-box paths, not verified
FACOM jaw offsets, actual handle motion, hand clearance, or dimensional
tolerances. Thus it neither establishes access nor proves a real wrench path
impossible. Mechanics now consumes each probe finite-contact area and records
its method, probe depth, and source hash. Both consumers use 4,560.569999 mm²
for the principal contact and 11,401.398713 mm² for the rail contact. The
canonical bounds rectangle is listed separately as a coordinate audit:
4,560.570000 mm² principal (−0.000001 mm² delta) and 11,401.425 mm² rail
(−0.026287 mm² delta). This reconciles the consumer basis; it does not add a
strength or acceptance claim.

Conditional 1/4-in placement references still need signed force classification
under the applicable 2024 NDS provisions. The first rail bolt is 38.1 mm from
the rail grain end versus a conditional 44.45 mm 7D reference (6.35 mm short);
the rail bolt pitch is 25.4 mm, equal to 4D. The principal group's cleat T
edge is 19.05 mm from each axis versus a conditional 25.4 mm 4D reference
(6.35 mm short). These comparisons do not classify which edge is loaded or
decide compliance. Complete mechanics, stock qualification, tolerance, and
service-specific geometry remain open.

## Early mechanics screen

The current [`wj04-early-mechanics.md`](wj04-early-mechanics.md) binds the
six preserved selected-candidate angle wrenches to the canonical WJ-04 group
centroids. It reports a rail-side separation tendency in all six old cases
and principal-side compression, with rigid-statics witnesses for the
proposed groups. Its old case producer snapshot has four mismatched source
files per case, and those source actions were not replayed. It therefore
supports no current per-fastener demand, resistance, or capacity conclusion.
The rail tie path, signed NDS edge classification, stiffness/contact behavior,
and complete-joint limit states remain unresolved.

## Preconfiguration nominal geometry (historical for the active trial)

- Cleat and installed stacks have no modeled positive-volume clash with
  host wood, other wood, panels, or the protected inventory after the old
  angle and six SDS axes at this station are removed. The protected screen
  includes 66 purchased-length panel/kicker screw envelopes, T-nuts, trial
  hold projections, lights, wires, retained upper-rail SDS, and retained
  frame-bolt stack envelopes.
  The local inventory omits WJ-03's four former outer angle stations, while
  their new node parts are not included; this is not an integrated clash pass.
- All eight washer seats have full modeled annular wood support. Provisional
  6-in principal bolts have 7.4676 mm nominal length reserve; provisional
  3.5-in rail bolts have **1.1176 mm**. Thread location, delivered shank,
  washers, nuts, and tool products are unselected.
- A 50 mm static rail-nut tool fits. A 50 mm tool held through complete
  9.498 mm nut unthreading clears the upper service rail by **6.352 mm**
  nominal; a 40 mm tool clears by 16.352 mm. The nut then clears the shaft
  axially and can move rearward in a modeled 100 mm rectangular swept path.
  That temporary path extends about 21.87 mm beyond the ordinary local-N
  rear limit. The generic 50 mm straight detached-nut sweep also clears
  the screened solids. Real tool and hand space remain unverified.
- Rail bolt centers are exactly 25.4 mm apart. The first is 38.1 mm from
  the rail end, 6.35 mm short of a *conditional* 7D full-value benchmark;
  the second has 31.75 mm to the cleat's far X edge, 6.35 mm above a
  *conditional* 4D benchmark. Rail bolts run along T, so 38.1 mm T is
  bolt bearing length, not a lateral edge. The separate principal bolts
  run along X; their cleat T edge is 19.05 mm from each center, 6.35 mm
  short of a *conditional* loaded-edge 4D benchmark if their signed load
  makes that edge loaded. These comparisons do not classify signed loading or reject
  the joint under the applicable NDS rules. Group capacity, splitting, and
  tolerances remain open.

The nearby lower-right center panel screw remains at X = 70 mm, 19.05 mm
inside the butt. The two service-rail screws remain at X = 435.075 and
835.075 mm. No receiver axis moves in this trial. The upper service rail
has a 105.95 mm T gap to the lower rail; the shortened cleat and nut/tool
access depend on that gap.

## Prior local comparisons and current open work

A 139.7 × 57.15 × 139.7 mm shortened historical cleat fits ordinary N
depth but intersects `light_G7` by 1,520.122437 mm³,
`wire_078_G6_G7` by 1,088.22013 mm³, and `wire_079_G7_G8` by
239.270692 mm³. A 100 mm X width at the earlier 50.8 mm T thickness
intersects `wire_078_G6_G7` by 78.94403 mm³. A lower-T cleat hits the G6 T-nut
or trial hold path. The historical full-section overlap loses both fixed
service-rail screw receivers and clashes with the lower panel.

The prior **95.25 × 50.8 × 119.7 mm** trial used rail bolts at X offsets
44.45/69.85 mm and provisional 4-in bolts. It had a 3.652 mm nominal
40-mm unthread-tool gap, but its 50-mm moving tool and straight detached
nut path struck the upper service rail. That pose remains a comparison
diagnostic in the JSON; the thinner cleat is the active WJ-04 trial.

A new 101.6 × 38.1 × 119.7 mm cleat moves the rail bolt X offsets to
44.45 and 69.85 mm. This gives the rail's first bolt exactly 44.45 mm
to its grain-X end and the second 31.75 mm to the cleat's far X edge.
The cleat **intersects fixed `wire_078_G6_G7` by 102.93696 mm³** in
both length cases. It cannot replace the current trial without an
explicit service-safe connector change. All 66 panel/kicker screw axes
remain fixed.

| Provisional partially threaded rail bolt | Nominal length reserve | 50 mm tool gap during nut removal | Additional finding |
| --- | ---: | ---: | --- |
| 3.75 in (95.25 mm) | 7.4676 mm | 0.002 mm | No useful dimensional allowance; fixed wire clash remains |
| 4 in (101.6 mm) | 13.8176 mm | −6.348 mm | Tool hits upper rail; first path also hits retained upper-rail SDS |

At the wide pose a 40 mm tool would leave 10.002 or 3.652 mm nominal
gap, respectively. No exact partial-thread product, delivered shank,
thread root, nut engagement, socket, or dimensional tolerance is selected.
The rail bolt's T direction is its bearing axis; its loaded lateral edges
must be classified from signed action in X/N. The principal group has a
different axis and edge geometry. A zero or negative margin in the table
is a failed installation allowance under that particular tool envelope,
not a statement of wood or bolt strength.

The older 95.25 × 50.8 × 119.7 mm trial cleared only the named nominal access
paths under its generic 3.5-in rail-bolt model; its conditional end and T-edge
shortfalls and 1.1176 mm rail-bolt reserve prevented a tolerance-aware layout
gate. Those numeric results do not describe the active 95.25 × 38.1 × 119.7 mm
configuration. Its old probe numbers do not describe the active trial. The
active probe, early mechanics, and tool-access outputs are now
configuration-bound, but access remains unresolved and mechanics still uses
unreplayed old actions. Verify post-rip stock grade, delivered bolt/thread
transitions and nut engagement, actual wrench motion, tolerances, signed
end/edge treatment, fresh candidate demand, and complete joint resistance.
WJ-03 and other new connector parts must also enter the integrated screen.
No old angle capacity or six-case result transfers.
