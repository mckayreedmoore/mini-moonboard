# WJ24 center backer load-path and mechanics contract

Status: **mechanics evidence plan; no demand, resistance, acceptance, or release**.
This contract applies to the complete WJ24 development layout recorded in
[`hypotheses/wj24-integrated-static/README.md`](hypotheses/wj24-integrated-static/README.md).
It preserves the four fixed center-kicker Hillman axes and the WJ24 geometry.
It is a focused input to WJ-08 methods and WJ-09 fresh candidate cases; it does
not replace the selected baseline or make a build instruction.

The parent-run WJ24 geometry extraction for these joints is archived in
[`attempt-01`](hypotheses/wj24-backer-mechanics/attempt-01/README.md), with the
[geometry manifest](hypotheses/wj24-backer-mechanics/attempt-01/geometry.json),
[execution record](hypotheses/wj24-backer-mechanics/attempt-01/execution.json),
and [hash/size readback manifest](hypotheses/wj24-backer-mechanics/attempt-01/archive-manifest.json).
It confirms the opposed finished-face orientation and binds the four bolt and
four Hillman receiver-cut geometries. This is input evidence only: no fresh
case demand, resistance, active contact law, or complete downstream load path
has been accepted.

## Bound geometry and path

The full WJ24 static diagnostic reconciles all 66 fixed Hillman panel/kicker
axes, all four center receiver redirects, 12 starting frame-bolt arrangements,
and all 24 former duties. The current report passes its implemented static and
source-tracking gates. It does not establish a force demand, connector
resistance, complete assembly, or candidate acceptance.

The four fixed center-kicker axes remain as recorded in
[`source-inventory.json`](source-inventory.json):

| Fixed Hillman axis | Receiver in WJ24 | Start point, global mm | Axis | Purchased length | Nominal uncut backer beyond kicker back |
| --- | --- | --- | --- | ---: | ---: |
| `round_kicker_left_center_1` | `inner_kicker_backer_left` | (−70, −17.74375, 60) | (0, −1, 0) | 63.5 mm | 45.24375 mm |
| `round_kicker_left_center_2` | `inner_kicker_backer_left` | (−70, −17.74375, 192) | (0, −1, 0) | 63.5 mm | 45.24375 mm |
| `round_kicker_right_center_1` | `inner_kicker_backer_right` | (70, −17.74375, 60) | (0, −1, 0) | 63.5 mm | 45.24375 mm |
| `round_kicker_right_center_2` | `inner_kicker_backer_right` | (70, −17.74375, 192) | (0, −1, 0) | 63.5 mm | 45.24375 mm |

These are the purchased Hillman 42605 #10 × 2-1/2 in panel/kicker screws.
Their axis-cylinder diameter in CAD is the historical 4.1402 mm occupancy
screen, not a Hillman published screw diameter, pilot, or bore instruction.
Do not transfer SPAX or SDS properties to these screws. WJ05 confirms nominal
receiver continuity in each backer; it does not establish screw resistance.
WJ05 also places its three-point inner-edge sample sets inside both backers;
those nominal samples do not establish edge bearing, splitting resistance, or
a case-specific load path from the kicker edges.

Each separate solid 4×4 backer is 88.9 × 88.9 × 238.9 mm, with backer grain
along global Z. Each is seated against the underside of `base_header` at
Z = 238.9 mm and attached by two provisional vertical 1/4-20 through-bolts.
The candidate axes are:

| Joint | Axis IDs | Bolt centers, global X/Y mm | Spacing | Receivers |
| --- | --- | --- | ---: | --- |
| Left backer/header | `backer_header_left_1/2` | (−35, −97), (−35, −63) | 34.000 mm | left backer and `base_header` |
| Right backer/header | `backer_header_right_1/2` | (41, −98), (25, −76) | 27.202941 mm | right backer and `base_header` |

Each vertical bolt crosses 238.9 mm of backer and 38.1 mm of header. The
nominal clearance bore is 7.3 mm. The current WJ05 geometry uses a 20 mm
nominal diameter × 7 mm deep open counterbore for each bottom head/washer; it
models three Type A washers at the top. These are provisional geometry inputs,
not a selected fastener or fabrication schedule. The top and bottom faces,
bores, head/nut seats, clearances, and installed stacks must stay bound to one
finished-part fingerprint.

The downstream frame paths are separate connections on the same
`base_header`; they do not make the backers directly attached to posts. WJ24
provides the following center-frame interfaces:

- `center_post_cleat_left/right` connect to `base_header` with two vertical
  header bolts per side (`center_post_header_left/right_1/2`) and connect to
  the shifted `base_post_center_left/right` with two horizontal post bolts per
  side (`center_post_left/right_1/2`). The center post top faces meet the
  header underside nominally at Z = 238.9 mm. Actual finished bearing faces
  and their net areas still need to be extracted from WJ24 geometry.
- `center_principal_cleat_left/right` connect to `base_header` with two
  vertical header bolts per side (`center_principal_header_left/right_1/2`)
  and to `base_principal_center_left/right` with two bolts per side
  (`center_principal_left/right_1/2`). These are additional paths from header
  into the climbing-frame principals; they do not assign the backer reactions
  to an equal share of any bolt group.

The four source duties `clip_split_header_center_left/right` and
`clip_split_base_center_left/right` are now represented in WJ24's owner/layout
map. Their exact actions, contact states, and resistance remain open. Trace the
header's complete candidate path under each case: both backer joints, both
center-post cleat joints and their post interfaces, both center-principal
cleat joints and their principal interfaces, plus the header's own internal
forces and any applicable retained frame connections. Preserve simultaneous
reactions from all connected duties; do not assign all backer load to one
center joint by bookkeeping convention.

The WJ12 statics report's finished-shape hashes for both backers and
`base_header` match WJ24's current finished geometry. Its two-side contact
geometry therefore remains useful as a bound diagnostic for these exact
shapes. Its loads remain synthetic unit wrenches, so that identity does not
supply WJ24 demand or acceptance.

| Finished solid | WJ24 shape SHA-256 |
| --- | --- |
| `base_header` | `0c00d109f7b0b89b325c0c3e0be61657f1d96d5e48f35bd08e5bbce86029e98e` |
| `inner_kicker_backer_left` | `2e0a9533844e587b3be0a97a489a4ceb249e2405f287430dc22346aff83d6063` |
| `inner_kicker_backer_right` | `b07599b036ab0d5d9aace3b974652c7c36b875f08f20c9e01f5833d1967e6656` |

## Actions required from the fresh full-frame cases

For each of the six adopted cases, rerun the complete WJ24 frame with one
frozen geometry, hardware, contact, and stiffness configuration. At every
physical interface listed below, export one signed, simultaneous 3D wrench
`(Fx, Fy, Fz, Mx, My, Mz)` with units and an explicit local-to-global
transform. Shift wrenches to declared group/contact datums using
`M_q = M_p + (p − q) × F`; retain all signs and components from the same case.
Do not combine independent component maxima from different cases.

1. **Four Hillman kicker receivers.** Export each screw's axial withdrawal
   force along its Y axis, both transverse shear components, screw bending
   action at the receiver/head reference, and the resultant wrench for each
   two-screw backer group. Record how the group result is assembled from the
   fresh frame load and how screw-to-backer deformation affects the share.
2. **Each backer/header joint.** Export the complete wrench at the actual
   Z = 238.9 mm mating-face datum and the wrench on each of the two bolts.
   Resolve bolt axial tension, transverse shear/bending, unilateral wood
   compression, contact opening, and equilibrium at the same time. The
   signed reactions must close the applied interface wrench.
3. **Header and center-frame interfaces.** Export header section resultants
   on each side of every backer, post-cleat, and principal-cleat joint station;
   export complete wrenches and per-fastener actions at every listed cleat
   connection. Include normal bearing/opening at actual faces, all three
   shears, all three moments, and member axial force, biaxial shear, torsion,
   and biaxial bending where applicable.
4. **Frame continuation.** Continue those actions through both center posts
   and both center principal members into the rest of the candidate frame.
   Verify whole-frame equilibrium and the load path to the modeled support
   reactions under the explicit no-slip floor assumption. Do not add floor
   friction or an anchor action.

For every reported resultant, also emit its source point, receiving point,
member/interface IDs, case ID, local axes, force and moment units, and force
and moment equilibrium residual. Retain every branch contribution at the
header. These records are the exact complete-joint demand input; a force
component alone, a closed local unit-wrench construction, or a non-simultaneous
set of maxima is insufficient.

## Contact, compatibility, and net-section evidence

The nominal backer/header mating plane is horizontal and has normal global Z.
The backer grain is parallel to that normal; the header grain is global X and
therefore perpendicular to the mating-plane normal. For the WJ12 exact
finished faces, the backer material area at the header contact plane is
7,819.502 mm² per side after the two 7.3 mm bolt bores; its unbored gross area
is 7,903.210 mm². Treat these as geometry only. The area in contact under load
can reduce or open and requires the fresh contact solution. Do not credit face
friction or bolt preload without a supported and frozen model.

WJ12's two unit-statics constructions use (a) ideal point fasteners and (b)
finite annuli/disks Boolean-contained in both finished faces. The point model
leaves the bolt-row-axis moment unresolved. The finite-contact construction
adds compression-only patches and tension-only bolt reactions to close that
synthetic mode, but its 4.15–6.15 mm annuli and 2 mm-radius edge disks are
witness choices, not pressure footprints, selected contact dimensions,
load-sharing predictions, capacity, or stiffness. It still idealizes
transverse bolt support as point reactions. Do not scale its 1 N or 1 Nmm
cases into real demand.

The sampled sections report these exact local areas for the WJ12/WJ24 backer
geometry:

| Plane / feature | Finished area | What it does and does not show |
| --- | ---: | --- |
| Header contact face after through-bores | 7,819.502 mm² | Available material on the actual backer face; not active contact pressure or resistance. |
| Bottom counterbore midpoint plane | 7,274.891 mm² | Net material at that sampled plane with the two 20 mm pockets and their bores; not a whole-member minimum or strength. |
| 3 mm above counterbore floor | 7,819.502 mm² | Net material at that separate sampled plane after the pocket ends; not a critical-section selection. |

The right counterbore centers are only 27.202941 mm apart; if the current
20 mm pockets were machined as modeled, their nominal intervening ligament
would be 7.202941 mm. The left pair has 14 mm between 20 mm pocket perimeters.
These are measurements of the diagnostic envelopes, not accepted cut
geometry. Require exact cut-bound section extraction and evaluate the
remaining foot, hole-to-hole, hole-to-edge, screw-to-bolt, and group tear-out
paths for both asymmetric backers. A single section area is not an adequate
splitting, net tension, row tear-out, block/group tear-out, shear, or bearing
check.

For each finished backer, header, post cleat, center post, principal cleat,
and principal member, the mechanics record must identify the governing
section(s) from the same full-cut WJ24 solids. Sample all bolt and receiver
centers, counterbore floors/shoulders, structural cuts, section changes, and
contact edges. Report local grain axes, actual net polygons/areas, centroid,
section properties, force/moment interaction and applicable member limit
states. Include any hole and cut interactions and local splitting/tension
perpendicular to grain; where the chosen design basis supplies no applicable
resistance, record the method gap instead of substituting a gross-section or
unrelated bolt-yield value.

Compatibility must be solved with one evidence-backed interface model shared
by the frame response and resistance checks. It must describe measured or
bounded hole clearance/free travel, bolt stretch and bending, wood bearing
stiffness in each grain direction, washer/head/nut compliance and support,
face gaps and unilateral compression/opening, rotation, and slip. The 7.3 mm
modeled clearance around a provisional 6.35 mm bolt implies 0.475 mm nominal
radial geometric clearance before bearing; this is not an installed tolerance
or a no-slip connection. Derive lower/upper response sensitivities for inputs
that remain uncertain and rerun the same cases with those bounds. The current
unit statics and nominal geometry provide none of these stiffness or pressure
inputs.

## Resistance-method and input gaps

Use the official [AWC 2024 NDS](https://awc.org/resources/2024-nds/) as the
wood-connection basis only after the specific provisions, supplement values,
current errata, design format, adjustment factors, actual DF-L No. 2 member
basis, and geometry are frozen for this candidate. The official AWC
[Technical Report 12](https://awc.org/wp-content/uploads/2026/06/TR-12_2026_formatted.V3.pdf)
provides a candidate method for applicable dowel-type lateral connection
yield checks. Its published scope is lateral connection values; it does not
by itself supply the demand distribution, full joint tension/contact law,
washer behavior, or six-component compatibility model required here. That
scope distinction is an inference from the source's stated method limits and
the joint configuration.

The following inputs or applicable methods are still absent:

- **Hillman receiver screws:** no current calculation here establishes #10
  screw withdrawal, lateral resistance, bending, head pull-through, combined
  action, two-screw distribution, pilot effects, edge/splitting resistance, or
  stiffness in the actual kicker/backer species and grain directions. Bind
  the exact 42605 product information and a source-supported applicable wood
  screw method or product data for these installed conditions. Retain the
  owner-selected lead-hole pilot plus face countersink as recorded shop
  policy; do not treat CAD occupancy diameter as either bit size or hole.
- **Backer/header through-bolts:** select and document an actual structural
  bolt and delivered dimensions, material/grade, shank/root diameter, thread
  transition, nut engagement, washers, grip, bearing lengths and shear
  planes. WJ05's conditional receive screen requires no more than 9.525 mm of
  thread bearing in the 38.1 mm header if nominal diameter is used under the
  applicable NDS thread provision; otherwise measured root diameter belongs
  in the lateral-yield method. Complete nut engagement and at least 3.175 mm
  thread beyond the nut remain required. With the provisional three-washer
  top stack, WJ05's conditional underhead transition interval is 262.507 to
  275.918 mm. This is a receive criterion for that geometry hypothesis, not
  selected hardware or evidence that a product complies.
- **Dowel action:** calculate direction-specific lateral yield/bearing in the
  238.9 mm backer and 38.1 mm header from actual bolt/thread geometry, grain,
  thickness, gaps and applicable adjustments; check bolt steel tension,
  shear and bending, and all relevant simultaneous components. Demonstrate
  whether the two-fastener group/group-action treatment and current AWC
  provisions apply to this eccentric through-bolted support.
- **Wood and washer limit states:** evaluate washer bending and supported
  bearing beneath the bottom head and top nut stack; header compression
  perpendicular to grain at top-washer bearing and at the backer/header
  contact; backer bearing parallel to grain; local splitting, net-section
  tension, row/group tear-out, shear/block failure around both through-bolts,
  counterbores and four fixed receiver axes; and combined header/post/principal
  sections. Where these interactions lack a demonstrated applicable method,
  keep the affected joint open. Do not infer wood tension perpendicular to
  grain resistance from a geometry area.
- **Receiver-to-frame and global sharing:** complete joint methods and
  stiffness for both center-post cleats, both center-principal cleats, their
  fasteners and real wood contact faces; fresh WJ24 actions at those joints;
  and a shared sensitivity model showing how their compatibility changes the
  forces delivered through the header. Local backer equilibrium cannot
  replace these global frame reactions.
- **Physical inputs:** actual stock/species/grade and grain for every member,
  actual cuts/bores, actual bolt/washer/nut dimensions, and installed screw
  observations are not verified. Keep shop Actual/Disposition cells blank
  until observed. No purchase, drilling, fabrication or climbing release is
  granted by this contract.

An evidence bundle closes only when the frozen WJ24 geometry and hardware
fingerprints, six fresh complete-case action records, compatible response
inputs, critical finished sections/contact faces, cited method revision and
scope, all applicable resistance checks, and the equilibrium/error record are
linked per case and per interface. Track the applicable rows in
[`criteria-method-map.md`](criteria-method-map.md), especially `receiver_fit`,
`center_kicker_receiver_paths`, `complete_joint_actions`, `joint_stiffness`,
`complete_load_path_coverage`, and `angle_rated_force_components`. WJ12 unit
statics and WJ24 geometric static gates remain supporting diagnostics only.
