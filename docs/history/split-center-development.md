# Separated center principals

This revision replaces the former single 3×6 center principal and post with
two independent 2×6 principals and aligned full-depth support posts. The four
additional principals from the preceding revision remain. The center pair is
spaced apart, not laminated or treated as a composite member.

The candidate is **not released for construction or climbing**. The owner's
requested endpoint is build readiness; the release table below records what
still prevents that endpoint. No earlier frame, floor or joint result qualifies
this changed assembly.

## Current package

- [Interactive rear view](https://mckayreedmoore.github.io/mini-moonboard/?model=split-center-development&view=rear)
- [Open frame](../exports/split-center-development/open-frame.png)
- [Base connection](../exports/split-center-development/base-connection.png)
- [Bolt ends with visualization-only timber cutaway](../exports/split-center-development/bolt-ends-cutaway.png)
- [STEP assembly](../exports/split-center-development/split-center-development.step)
- [Wood schedule](../exports/split-center-development/wood-parts.csv)
- [Connection schedule](../exports/split-center-development/connections.csv)
- [Current geometry audit](../fea/results/split-center-audit-v1.json)

## Center service path and panel attachment

The center principal axes are X−70 and +70 mm, each with a 38.1 ×139.7 mm
section. Their inner faces leave a 101.9 mm clear corridor. The modeled
40 mm hold-bolt/LED service cylinders fit through this corridor without
service pockets in the new principals. This envelope remains a design
reservation: actual hold-bolt projection, T-nut hardware, LED connector
dimensions and installation access must fit it.

Each half-panel fastens to its own center principal. The panel's vertical
joint edge overhangs that principal's inner face by 50.95 mm. The two panel
edges are not joined, and the analysis must not introduce a hidden connection
across the gap. The horizontal panel seams also remain separate edges between
the discrete principal supports. Moving receivers away from service hardware
does not by itself establish panel strength or acceptable seam movement.

The current fit audit measures 11.75 mm minimum clearance between the left
center principal and the full service envelopes, and 50.15 mm on the right.
All eight rim/principal bearing footprints project fully over their aligned
posts, with zero nominal rear overhang beyond those posts. The two outer posts
were deepened as well. This resolves the geometric support omission; it does
not determine contact pressure, timber bearing resistance or header stresses.

The schedule contains 34 timber/plywood parts: seventeen single 2×6 members,
nine single 2×10 members (eight posts and the header), and eight plywood parts.
There are no remaining 3×6 members. Hardware comprises 80 panel/kicker screws,
34 brackets with 204 specified bracket screws, and sixteen complete through-bolts.
Separating the bolt components produces 432 selectable viewer entries without
changing those physical counts.

Ordinary panel screws remain the installed development hardware. Future insert
reservations are solid wood, not predrilled pilots or approved repairs.
Manufacturer-specified bracket screws and the existing through-bolts remain.
The insert direction requires verified installation geometry and applicable
wood anchorage resistance before it can replace the screw-based schedule.

## Bolt inspection

The preceding viewer already contained both ends of all sixteen through-bolts.
Its heads and nuts used cylindrical dimensional envelopes and could be hidden
behind opaque timber. This candidate distinguishes each shaft, head, nut and
washer as a selectable viewer component. Head and nut geometry is hexagonal;
thread and chamfer details remain simplified. The connection schedule still
counts complete bolts, rather than mistaking the separate meshes for extra
hardware.

The bolt detail removes part of the timber only for visualization. Its hardware
stays at the assembled coordinates; the fabrication STEP and STL timber bodies
do not contain this cutaway. The export's `visualization.json` records that
distinction. Do not machine the illustrated visualization cut.

## Current floor screen

The [source-bound rigid-floor report](../fea/results/split-center-floor-v1.json.gz)
recomputes mass and floor footprints from this candidate's drilled timber,
brackets and complete fasteners. Estimated mass is 195.244 kg using assumed
600 kg/m³ timber/plywood and 7,850 kg/m³ steel. Holds, lighting and wiring are
omitted; hardware shapes simplify threads. This is not a measured assembly
mass or a proven conservative mass/center-of-gravity bound.

The 1,296 finite cases span 150/200/250/300 lb climbers, 1×/2× downward force,
80%/100% included mass at fixed center of gravity, nine selected holds, and
eight 300 N horizontal directions plus a vertical-only case. Hold standoff is
100 mm. Contacts are compression-only on a level floor; the friction cones use
an inscribed sixteen-ray polygon.

| Assumed friction coefficient | Feasible witnesses | Polygon-infeasible cases | Analytically proven friction failures |
| --- | ---: | ---: | ---: |
| 0.1 | 664 | 632 | 504 |
| 0.2 | 1,296 | 0 | 0 |
| 0.4 | 1,296 | 0 | 0 |

The 504 proven failures violate the necessary circular-friction bound
`horizontal force ≤ μ × total normal force`. The other 128 polygon failures
are not proofs of circular-cone infeasibility. None of the sampled cases
violates the necessary normal-resultant support-polygon condition. At 250 lb,
132 of its 324 cases are polygon-infeasible for μ=0.1; all 324 have witnesses
at μ=0.2 and 0.4.

All 3,256 feasible witnesses passed independent force, moment, nonnegative
normal-force and circular-friction checks. Maximum residual components were
below 4.55×10⁻¹² N and 1.91×10⁻⁸ N·mm. Those forces are nonunique equilibrium
witnesses, not predicted reactions for designing the gussets or brackets.
Actual floor friction, compliance, unevenness, pressure, slipping dynamics and
structural response remain unqualified. μ=0.2 is an assumed test value, not a
certified minimum or a declaration that a particular floor is safe.

## Panel and attachment diagnostic

The [archived panel comparison](../fea/results/split-center-panel-comparison-v1.tar.gz)
contains an independent cantilever benchmark and 32 solves: both framing
variants, all four face panels, eight hold locations across two seam regions,
and 40/25 mm mesh sizes. Each load acts on one independent panel; its neighbor
remains unloaded. The two variants use their actual screw coordinates.

The applied 1,945.370 N outward-normal force is the projection of the 300 lb
sensitivity case with twice-weight downward force and 300 N world+Y force.
The corresponding 250 lb normal component is 1,659.444 N, so linear results
scale by 0.853022 for that normal component alone. This corrects the earlier
1,200 N comparison load, which did not cover that provisional force projection.
The 2× multiplier and horizontal force remain prescribed analysis scenarios,
not an independently established climbing-wall design-load standard.

The 20×20 mm patch is centered on the actual hold datum and kept within its
individual panel. It is a hypothetical numerical patch, not a measured hold
seat or T-nut footprint. The shell is undrilled and isotropic, with assumed
E=7,000 MPa, Poisson ratio 0.3 and thickness 18.25625 mm. Normal motion is fixed
only at ideal screw points. Actual directional plywood, hole effects, framing
flexibility, backing contact, screw slip, tangential force and the 100 mm
standoff couple are omitted. No frame/gusset force or actual panel strength is
qualified by this comparison.

| Hold case, 25 mm mesh | Prior patch movement (mm) | Split-center patch movement (mm) | Prior vertical-seam maximum (mm) | Split-center vertical-seam maximum (mm) |
| --- | ---: | ---: | ---: | ---: |
| D6, lower left | 0.305612 | 0.296350 | 0.037978 | 0.102758 |
| D7, upper left | 0.322341 | 0.312396 | 0.033200 | 0.110427 |
| H6, lower right | 0.328441 | 0.308358 | 0.066179 | 0.203515 |
| H7, upper right | 0.347406 | 0.322709 | 0.051228 | 0.208295 |
| F3, lower left | 1.991055 | 2.059220 | 2.330957 | 2.429921 |
| F10, upper left | 0.935356 | 1.164410 | 1.326963 | 1.546177 |
| G3, lower right | 1.355250 | 0.924831 | 0.560600 | 0.491636 |
| G10, upper right | 1.505472 | 1.145258 | 0.826600 | 0.517993 |

The split improves several loaded-patch responses but worsens the left
center-seam cases. The F10 loaded-patch movement increases about 24.5%; the
largest split-center vertical-seam movement is 2.429921 mm at F3. The smaller
remote vertical-seam movements in D/H cases also increase. Horizontal-seam
maxima range from 0.044903 to 0.445134 mm in the split candidate. There is no
assigned physical acceptance limit for either seam direction.

The largest ideal screw reaction is 2,193.6 N at `timber_panel_upper_left_8`
in F10, or about 1,871.19 N after the stated 250 lb normal-only scaling.
These point-restraint reactions have not been shown converged and are not
physical demand bounds. They nevertheless flag the attachment pattern for
further connection design; extra principals alone have not demonstrated
acceptable screw loads. A useful next trial is infilling the long center screw
rows, with fresh service, spacing, hardware and insert-reserve checks, followed
by applicable product/material resistance and compliant-support analysis.
Additional rows cannot be assumed to divide load equally or solve the other
panel attachments.

All cases passed independent equilibrium checks and the declared 5% refinement
gate for loaded-patch compliance and both seam displacement maxima. The largest
change was 2.455%. Maximum force and moment residual components were below
0.000564 N and 0.844 N·mm. Those numerical checks do not close any of the
physical release gates below.

## Design basis and release gates

Retain the prior one-climber 250 lb request, with 300 lb sensitivity, pending
any owner revision. The existing procurement basis is DF-L No. 2 or better,
kiln-dried untreated solid-sawn lumber and the already purchased Roseburg
23/32-category face plywood. See [material identification](purchased-materials.md).
The old member-size schedule on that historical page is not this candidate's
cut list. Actual thickness, grade marks, moisture and strength-axis orientation
remain material inputs; the plywood category is not a measured thickness.

| Release requirement | Evidence required before closure |
| --- | --- |
| Actual service and machining fit | Current occupied-hardware audit plus measured hold-bolt, T-nut, LED and stock dimensions; verify assembly/tool access |
| Panel strength and seam behavior | Directional plywood properties, hold-specific loading and attachment, support/connection compliance, both seam directions, screw withdrawal and head pull-through |
| Current whole-frame forces | New geometry-specific solution with explicit bearing/contact and connector behavior, numerical balance and sensitivity; no inherited force distribution |
| Member and joint resistance | Compare current demands with applicable timber net-section, buckling, bearing, bracket, screw, bolt-group, washer and gusset resistances |
| Floor stability | Actual floor/foot interface and levelness, adequate friction or an explicitly designed anchorage system; rigid equilibrium alone is insufficient |
| Final construction release | Resolve the above, synchronize final dimensions and installation schedule, obtain appropriate structural review and define physical verification and inspection |

More support points do not establish lower gusset forces. Both gussets and their
bolts remain until the revised force distribution and connection checks justify
a change. Likewise, a passing geometry or numerical equilibrium check is not a
climbing load rating.

APA distinguishes plywood properties by panel identity and strength-axis
direction, and its tabulated building-panel spans assume particular loading
and support conditions. Those tables do not directly rate this drilled,
concentrated-load climbing assembly. See [APA plywood selection and design
guidance](https://www.apawood.org/engineered-wood-products/plywood-osb/plywood/).

## Verification and release status

Thirty-eight targeted tests passed, covering current geometry and complete
bolt stacks, authenticated exports, independent replay of the floor witnesses
and panel results, preserved predecessor geometry and newest-first selection.
Ruff and diff checks passed. Browser checks loaded all 432 entries, selected
both a head and a nut through actual pointer clicks, checked the hold grid,
and captured desktop/mobile and bolt-detail views without request errors.
The CAD overview, bolt cutaway and actual viewer images were inspected.

Independent correctness, mechanics, testing and consistency reviews found no
remaining substantive defects within this development scope after stale
historical pointers and missing floor-report replay coverage were corrected.
These are software, geometry and conditional-analysis checks. They do not
complete the owner's requested build-ready endpoint. The release gates above
remain open; current construction instructions and a climbing approval are
not issued.
