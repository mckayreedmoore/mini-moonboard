# Freestanding base ties: bounded design options

Research and read-only CAD inspection: 2026-09-06. This is a proposal for a
separate comparison candidate, not a rated design or fabrication release.
Existing CAD, candidates, connection schedules, and historical results remain
unchanged. No floor/building anchors, ballast, crash-pad support, or improved
floor-friction property are assumed.

## What a base tie can change

Investigate **two detachable longitudinal side rails connecting the kicker-side
structure to the corresponding rear leg**, one on each side. Their purpose is
to carry opposing spreading forces inside the frame. This is the same general
load-path principle by which a correctly connected low rafter tie can resist
gravity-induced outward thrust; the American Wood Council describes that
mechanism for roofs. Its roof details and capacities do not apply to this
continuous plywood-leg frame. [AWC: rafter ties and thrust](https://awc.org/faq/what-is-the-difference-between-a-collar-tie-and-a-rafter-tie/).

For the whole assembled board, the two end forces of each tie are internal and
cancel. They cannot balance an external horizontal climbing force. Force and
moment equilibrium still require external reactions from the floor. A rail
that remains above the floor also does not enlarge the support polygon merely
because its outline is wider. Added mass and its location must be included,
but are separate effects. [OpenStax: static equilibrium](https://openstax.org/books/university-physics-volume-1/pages/12-1-conditions-for-static-equilibrium).

For horizontal external resultant `H`, nonnegative floor reactions `N_i`, and
friction assumptions `mu_i`, the necessary global condition remains
`|H| <= sum(mu_i N_i)`. It is insufficient by itself: each contact region must
also satisfy its local friction bound and the complete moment balance.
At zero friction, an otherwise stable frame may carry a vertical load through
internal ties, but cannot statically resist a nonzero net horizontal load on a
level floor. Static friction is bounded by `mu N`, not automatically equal to
that maximum. [OpenStax: friction](https://openstax.org/books/university-physics-volume-1/pages/6-2-friction).

The existing curved leg has weight, knee bending, a finite foot, and a four-bolt
upper joint; it is not a pin-ended two-force strut. Consequently neither
`V cot(alpha)` nor a previous floor reaction is a ready-made tie design force.
The added tie changes the member/joint load distribution. Its height above the
floor also introduces a local moment `T z_t`, and its lateral offset introduces
another moment `T e`. Retain those effects in the model.
See [the existing connection/free-body discussion](footprint-connection-gates.md).

## Options worth comparing

| Option | Intended benefit | Main unresolved issue |
|---|---|---|
| Two rigid timber side rails, bolted through designed end connections | Familiar fabrication; can be designed for both tension and compression/reversal; removable for transport | Connection slip, splitting and eccentricity; compression/weak-axis buckling over the long unbraced span; side clearance |
| Two steel rods or straps with designed end clevises/plates | Slender tension load path and smaller visual envelope | Tension-only behavior, slack, adjustment/locking, snagging, and reversal; a slender unsupported strap is not a compression rail |
| Two rigid steel-section side rails with designed end plates | Potentially smaller section for a bidirectional member | Fabrication, local plate/bolt behavior, weld details if used, corrosion and timber-interface demands; no section selected |

Start with the timber-rail geometry below. Keep a tension-only steel tie as the
comparison if width or transport makes timber unattractive. Do not add a
crossbar between the two legs across the landing area. Separate side ties also
do not automatically brace the assembly against transverse racking or yaw.

Manufacturer strap tools explicitly use tension demand and require strap,
fastener, quantity, and wood-species inputs. They demonstrate a connection
family, not an approved 1.66 m unsupported strap installation on a plywood leg.
[Simpson: coiled-strap design inputs](https://www2.strongtie.com/webapps/CoilStrapCalculator/DesignCalculator.aspx).

## Actual geometry and a bounded first envelope

The reference is `footprint_frame.parts(100, False)`, the undrilled
`2x8-foot100` candidate. World X runs across the panel, Y toward the rear-leg
feet, and Z upward. Measured right-side bounds are:

| Existing part | X bounds, mm | Relevant Y/Z bounds, mm |
|---|---:|---|
| Climbing panel edge | up to 1219.2 | Existing face/hold coordinates retained |
| Kicker cheek | 1219.2 to 1257.3 | Y -159.067 to -18; Z 0 to 343.369 |
| Rear leg | 1257.3 to 1295.4 | Floor toe Y 1500.331; at Z≈100, Y 1269.478 to 1462.182 |
| Cheek/rim splice | 1181.1 to 1219.2 | Z begins at 192.105 |

Use this **occupancy envelope only**, mirrored left/right. The first geometry
variant should use centre Z=275 mm; retain Z=100 mm as the lower-tie comparison:

- Straight rail section: 38.1 mm across X by 88.9 mm vertically.
- Right rail X=1295.4…1333.5 mm; left rail mirrored.
- Each rail Y=-159.067…1500.331 mm, length 1659.398 mm.
- Recommended comparison rail Z=230.55…319.45 mm; lower comparison
  Z=55.55…144.45 mm. Credit no rail/floor support. End plates, bolts and
  deformation must preserve intended floor clearance.

Read-only CAD boolean checks found no positive-volume intersection between
either mirrored envelope at centre heights 100, 275 or 294.45 mm and any
existing undrilled part solid (including nominal angle parts). Tangency to the
leg side is intentional. Each envelope is
5,620,532 mm³; both would add 6.745 kg at the existing **600 kg/m³ comparison
density**, excluding all fittings. This is not a selected lumber density or
member-capacity check.

The timber envelope widens the outer leg-body dimension from 2590.8 to
2667.0 mm, before bolt heads, plates, nuts and installation clearance. It adds
no Y extent beyond the existing cheek/leg extremes. Both rails lie outside the
panel's projected width, but **that does not establish that they are outside
the climber's fall or access zone**. The manufacturer's Mini build guide
explicitly requires space beyond board width/depth for a safe fall zone; this
repo's custom 225 mm kicker and frame geometry must retain their own datums.
The source's dimensions are not substituted for them.
[Moon Climbing: DIY guide, Mini page](https://moonclimbing.com/media/moonboard-pdf/How-to-build-a-MoonBoard_v2.3.pdf).

Before accepting the envelope, overlay the actual room, landing area, starts,
sideways movements/falls, entry/exit route, pad positioning without structural
credit, and assembly/tool sweeps. The existing requirement to keep the landing
space clear remains a gate. No straps hidden beneath pads and no exposed
projecting threaded ends are part of this proposal.

### Height comparison and recommendation

The front cheek has a sloping top. Moving the rail up brings it into the
existing cheek/rim transfer zone but reduces the available cheek material.
These are measured projected areas in the 88.9 mm rail-height band, not joint
areas with established allowable stress. For the overlap check, the existing
splice was translated 38.1 mm in X solely to compare its Y/Z silhouette with
the cheek; this does not represent a physical CAD modification.

| Rail centre / vertical band, mm | Cheek area in band, mm² | Cheek-and-splice projected overlap, mm² | Consequence |
|---|---:|---:|---|
| 100 / 55.55…144.45 | 12,540.86 | 0 | More low-cheek material and smaller tie-height moment, but load must travel up to the existing splice |
| 275 / 230.55…319.45 | 7,243.52 | 5,743.18 | Preferred first geometry variant: intersects the existing transfer zone with more cheek material than the higher option |
| 294.45 / 250…338.9 | 5,182.85 | 4,600.96 | Less cheek material; at the rail top the cheek has only about 5.33 mm remaining in Y; not the preferred starting point |

At centre Z=275, the cheek's Y range at mid-height is -159.067…-77.582 mm;
at the rail top it narrows to -159.067…-130.555 mm. Do not use the whole rail
rectangle as assumed attachment material. Two existing right-side front splice
screws lie within that height band, at approximately (Y,Z)=(-113.721,240.049)
and (-144.363,265.761) mm. New through-bolt axes, plates, washers and tool access
must be checked against them and against the actual cheek/splice profiles.

The recommendation is for a **separate geometry-only candidate**, not a chosen
connection. Compared with the low tie, the higher tie produces a larger
`T z_t` moment at the lower leg and changes its effective triangulation. That
mechanical tradeoff must be included before selecting the height. No base
rail removes the need to preserve the climbing underside/front-left access
and the conditional side-fall clearance check.

## Connections are the first design problem

The leg and kicker cheek are in different X planes. The proposed rail's inner
face is 38.1 mm outside the cheek's outer face. Rail-to-cheek centreline offset
is 76.2 mm; rail-to-leg centreline offset is 38.1 mm. A long bolt across an empty
gap is not the proposed front connection. Investigate a positively fitted,
designed spacer/block with plates, or a designed clevis that transfers force
through the cheek broad face while accounting for these eccentricities.

At the rear, investigate a detachable broad-face lap/side-plate connection to
the intact low leg region, preserving the full floor-bearing cut. Establish
hole positions from actual leg sections, loading directions, edge distances,
and access, rather than placing them from the bounding box. Through-bolts must
be designed for bearing/shear and associated plate demands; bolt clamping
friction is not an assumed structural capacity.

At the front, connecting a tie to the thin climbing/kicker panel or merely to
the existing bottom-batten end screws is not a demonstrated thrust path.
The existing cheek/rim splice starts above Z=192 mm, so the lower comparison
at Z≈100 must transfer force through the cheek into the upper frame. The
recommended Z≈275 geometry intersects the existing transfer zone and may avoid
an added deep front transfer bracket, but still requires a designed tie-to-cheek
and cheek-to-rim path, including splice bending/shear/opening. A short designed
gusset may still be necessary; none has been dimensioned or added.

Wood fastening behavior depends on material/grain direction, hole fit,
spacing, member stiffness and load sharing. Multiple bolts do not necessarily
share load equally. Include timber bearing/splitting/net section, plywood
layup and lamination integrity, bolt bending, plate bending/prying, and slip;
do not transplant solid-lumber connector values into this laminated plywood
detail. [USDA Wood Handbook, chapter 8, particularly pp. 8-16 and 8-24](https://research.fs.usda.gov/download/treesearch/62253.pdf).

No bolt count/diameter, steel thickness, connector SKU, adhesive or allowable
tie force is selected here. A proprietary connector would need its documented
substrate, orientation and complete installation checked; published connector
loads reflect specific test/calculation conditions.
[Simpson: how allowable connector loads are determined](https://www.strongtie.com/products/connectors/wood-construction-connectors/technical-notes/allowable-loads).

## Required comparisons before choosing a base detail

1. Preserve the current no-tie candidate and add a separately named tie variant.
   Report timber/fitting mass, CG, actual contact polygon, overall/tool-access
   envelope and transport/disassembly changes. Do not count a floating rail
   as a new support edge.
2. Begin with a transparent side-frame equilibrium/member model, including
   tie height and lateral offset, then model both sides together. Compare
   no tie, an explicitly ideal internal axial tie, and a finite-stiffness tie
   with connection slip. An ideal tie only tests whether the proposed load
   path can reduce spreading demand; it does not validate real fittings.
3. For each comparison, retain gravity, the original 1200 N diagnostic load,
   and the separately documented one-climber 250 lb envelope with its
   asymmetric/horizontal sensitivities. The 1200 N diagnostic alone is not a
   replacement for that use envelope. Include compression/reversal and
   one-sided load sharing; a tension-only tie must be permitted to slacken.
4. Report each floor patch's normal and tangential reactions, local contact
   bounds, tie end forces/moments, upper-joint and cheek-splice demand, foot
   spreading, transverse racking, and both tipping directions. Show the
   external force/moment balance separately from internal tie-force transfer.
5. Compare the original friction assumptions and lower-friction cases without
   selecting a favorable coefficient as a floor property. A zero-friction
   vertical-load diagnostic may isolate internal spreading restraint, but its
   free horizontal rigid-body modes need explicit treatment and cannot prove
   stability against horizontal loads. Do not accept artificial final guides.
6. Carry the contact verification issues from
   [the continuation study](floor-contact-continuation.md) into any new solve:
   complete endpoints, correct released boundaries, local law checks, ground
   force/moment balance, and mesh/load-history sensitivity remain necessary.
   A new member does not resolve the earlier numerical audit discrepancy.
7. Resolve actual structural material/connection properties and a controlled
   connection/assembly verification plan before a construction decision.
   Retain [the existing joint and floor gates](footprint-connection-gates.md).

The decision this comparison should answer is whether the two side rails
reduce opposing local friction demands enough to justify their connections,
width and access costs while preserving global sliding/tipping margins.
There is no engineering rating or acceptance claim in this document.

## Inspection provenance

Separate geometry exports now exist for [Z=100 mm](../exports/tied-base/z100/candidate.step)
and [Z=275 mm](../exports/tied-base/z275/candidate.step), with adjacent JSON
summaries. Each retains the original 45 timber solids and adds two rails and
two fitted front spacers. At the comparison density, rails **and spacers** add
7.318 kg; the resulting mass is 191.281 kg. Neither changes the actual floor
support polygon. These exports do not contain designed new fasteners or joints.

Eleven geometry tests cover the original-part identity, new-part collisions,
required face adjacency, unchanged floor polygon, export overwrite refusal,
and the actual published STEP solids, dimensions, centroid and source hashes.
Independent correctness, testing and architecture review passes found no
remaining substantial issues after adding direct published-export regression
coverage. These are geometry/software checks, not structural approval.

CAD inspection ran at repository HEAD `b9c8ff2`, using `parts(100, False)` and
in-memory CadQuery boxes/intersections only. No source, STEP, mesh or historical
solver artifact was modified. Hardware component solids and drilled/washer/tool
clearances were not included in the envelope intersection check.

- `mini_moonboard/footprint_frame.py` SHA-256:
  `20184d3087e39afa87c418db69c65ab9caf23c542e172162c6a87c4d2f86c022`.
- `mini_moonboard/shallow_frame.py` SHA-256:
  `da01677d76160bb544007f9dbcae5b9c381a7d9504cb698b4b1c18e15bffcdc5`.
