# Closer panel-fastener spacing

This candidate adds 71 screws to the split-center frame, for 151 ordinary
panel/kicker screws. Each existing interval on an interior principal is divided
uniformly into segments no longer than 150 mm, separately for each panel and
receiver. Existing axes and endpoint screws remain. The rule does not span
independent panel joints or imply a maximum distance from panel edges.

The raw wood, separated center principals, posts, brackets and through-bolts
are unchanged. New holes are cut from the complete current connection schedule.
The center hold-bolt/LED corridor remains open, and all bolt heads, nuts and
washers remain individually selectable. Neither extra screws nor improved
deflection establishes acceptable connection resistance.

**This remains an unqualified development candidate, not construction plans.**
The requested build-ready endpoint still requires current frame/joint resistance,
actual plywood properties and support behavior, and the actual floor interface.

## Current package

- [Interactive model](https://mckayreedmoore.github.io/mini-moonboard/?model=infill-panel-development&view=rear)
- [Frame render](../exports/infill-panel-development/open-frame.png)
- [Base detail](../exports/infill-panel-development/base-connection.png)
- [Bolt ends, visualization-only timber cutaway](../exports/infill-panel-development/bolt-ends-cutaway.png)
- [STEP](../exports/infill-panel-development/infill-panel-development.step)
- [Wood schedule](../exports/infill-panel-development/wood-parts.csv)
- [Connections](../exports/infill-panel-development/connections.csv)
- [Fit audit](../fea/results/infill-panel-audit-v1.json)
- [Panel comparison](../fea/results/infill-panel-comparison-v1.tar.xz)
- [Conditional connection screen](../fea/results/infill-connection-screen-v1.json)
- [Rigid-floor screen](../fea/results/infill-panel-floor-v1.json.gz)

## Fit and inventory

The full audit passes the tested drilling, receiver material, screw spacing,
service, hardware collision and future-insert-reserve gates. All old connection
axes and raw wood geometry are retained. The interval check covers all twelve
panel/principal lines, not just the center pair.

The package contains 34 wood/plywood parts, 34 brackets, 204 manufacturer-specified
bracket screws, 151 panel/kicker screws and sixteen complete bolts. Five meshes
per bolt expose its shaft, head, nut and two washers, giving 503 viewer entries.
Future insert reservations remain solid wood, not pilots or approved repairs.
Visualization cutaways do not alter the fabrication geometry.

## Bolt colors and base gussets

Red bolts in the preceding viewer were a hardware category, not failed strength
tests. Ordinary bolt components now appear steel gray. Red is retained only for
an explicit clearance-failure flag; even that is not a strength rating. The
current sixteen bolts have complete head, nut and washer geometry and no detected
fit failure. Static CAD renders retain their historical red hardware-category
color. Neither display color establishes connection resistance.

Both `timber_base_gusset` parts remain. On each side, bolts `_1` and `_2` join
the outer rim to its gusset; `_3` and `_4` join the gusset to the outer post.
This is the only direct fastened outer-rim/post bridge in the current assembly.
Removing it would retain rim/header compression bearing and indirect paths
through the top/bottom rails and interior principals, but no direct outer-rim
to header bracket. A connected graph is not proof of stable or adequate joints.

The appropriate removal trial is a direct rim-to-header bracket at each outer
corner, with installation/clearance checks and a current force comparison of
retained and replaced gussets. Bearing, uplift, sliding and connector stiffness
must be explicit; unknown friction and panel diaphragm action cannot supply
missing resistance. Extra interior supports alone do not justify removal, so
this published candidate retains both gussets and their eight bolts.

Any separate outer-angle replacement candidate requires its own fit and load
evaluation. Its changed base connection is not part of this infill comparison.

## Final panel-spacing diagnostic

The archived comparison uses 15 and 10 mm maximum meshes for both the retained
80-screw split-center frame and this 151-screw candidate. Eight independent hold
cases cover all four panels and both seam directions. Each case applies the
same 1,945.370 N outward-normal projection of the 300 lb sensitivity scenario
to a hypothetical 20 ×20 mm patch. The panels remain undrilled isotropic shells
with ideal normal restraints at screw axes. Actual plywood directionality,
backing contact, frame flexibility, screw slip, tangential forces and standoff
moments are excluded.

| Hold case, 10 mm mesh | Prior patch movement (mm) | Infill patch movement (mm) | Prior vertical-seam maximum (mm) | Infill vertical-seam maximum (mm) |
| --- | ---: | ---: | ---: | ---: |
| D6 | 0.301813 | 0.264503 | 0.100658 | 0.099006 |
| D7 | 0.317786 | 0.279205 | 0.108264 | 0.115113 |
| H6 | 0.313538 | 0.272853 | 0.204543 | 0.186630 |
| H7 | 0.328046 | 0.289554 | 0.208784 | 0.184919 |
| F3 | 2.071062 | 0.510189 | 2.442881 | 0.706059 |
| F10 | 1.176937 | 0.578246 | 1.558258 | 0.772407 |
| G3 | 0.930341 | 0.705395 | 0.487715 | 0.394954 |
| G10 | 1.150940 | 0.703064 | 0.524111 | 0.415434 |

Loaded-patch movement decreases in these surrogate cases, but not every seam
response improves. Infill horizontal-seam maxima increase in D6, D7, H6 and H7;
H7 reaches 0.502829 mm versus 0.450635 mm previously. Different independently
loaded panel cases must not be combined into a physical seam-opening result.

All displacement/compliance metrics pass the declared 5% mesh-change gate;
their largest change is 0.879%. However, six revised cases—D6, D7, H6, F3, F10
and G3—fail the individual-reaction gate at one or more screws. That gate checks
each signed reaction change against the greater of 0.5 N and 5% of its fine-mesh
magnitude. **Overall numerical comparison acceptance remains false.** A stable
maximum reaction does not establish convergence of the other attachment loads.

The largest fine-mesh tensile diagnostic is 2,022.908 N in F3 at
`infill_main_lower_left_base_principal_center_left_2_1`. Scaling only the modeled
normal component to the prior 250 lb request gives **1,725.59 N**, using
0.8530222433. This exceeds the conditional 733.60 N withdrawal reference below.
It flags an unresolved attachment issue; it is neither a qualified physical
demand nor proof of an actual connection failure. More screws have not
demonstrated adequate attachment resistance.

## Conditional hardware references

The current [DrJ report 2010-02](https://www.drjcertification.org/report/download/1936)
identifies the XFT08P-2000 screw's 1.24-inch nominal thread length. Table 10
explicitly includes the tip when calculating embedded-thread withdrawal and
requires at least one inch of embedded thread. All 1.24 inches fit behind the
modeled 23/32 panel. For the stated DF-L SG 0.50 basis, the unadjusted reference
is 133 lbf/in ×1.24 in = **733.60 N**. No guessed tip deduction is applied.

The 23/32 plywood head pull-through reference is **943.02 N** only when its
required assigned SG 0.50 applies. A separate minimum-19/32, SG 0.39 entry is
533.79 N. Purchased Roseburg product identity does not verify either assigned
specific-gravity condition. The report's 51 lbf lateral entry specifies SPF
framing and is not assigned to DF-L here. Exact references, source identity and
limits are recorded in the [hardware reference](infill-panel-hardware-reference.json).

Applicable adjustments and installed material conditions remain unresolved.
The normal-only ideal reactions are diagnostic comparisons, not physical
demand bounds or an actual utilization calculation. Positive support reactions
represent compression and are not counted as screw withdrawal tension.

Simple screw upsizing is not a demonstrated remedy. The same report's #10 flat
and washer-head plywood pull-through references at SG 0.50 are 1,303.33 N and
1,432.33 N, respectively, below the F3 normal-only diagnostic. Longer threads
can improve withdrawal without resolving that head-to-panel limit. No applicable
plywood head-pull-through value is supplied there for #14, and #12 is not listed.
Investigate an engineered load-spreading attachment or a through-bolted panel
connection, checking panel bearing, steel bending, receiver geometry and the
complete fastener load path. An arbitrary washer or assumed equal load sharing
does not establish a capacity. This is a next design investigation, not selected
replacement hardware or permission to change the current drilling schedule.

## Floor and construction limits

The current drilled CAD and complete hardware give an estimated mass of
195.622 kg under the retained 600 kg/m³ timber/plywood and 7,850 kg/m³ steel
assumptions. The current floor report replays the same 1,296 prescribed cases;
it does not inherit the prior mass or acceptance. At assumed friction 0.1,
664 cases have admissible polygon witnesses and 632 do not; 504 violate the
necessary circular-friction bound. At 0.2 and 0.4 all sampled cases have
admissible witnesses. This is finite rigid-equilibrium feasibility, not actual
friction, contact response, frame resistance or a floor qualification.

The [split-center release gates](split-center-development.md#design-basis-and-release-gates)
remain applicable, with this candidate's new connection schedule and results.
Do not transfer historical drilling, assembly instructions or frame forces.

The published archive retains all 32 solver cases and the cantilever benchmark,
including raw outputs and current source snapshots. Its final report reuses those
33 completed jobs after verifying the pinned solver identity, byte-identical
regenerated input/decks and every saved raw-artifact hash, then reruns the current
auditors. `fresh_solver_jobs` is zero; this final provenance replay is not a new
solve or an improvement in numerical convergence. The report records the source
report and job hashes for each reuse.
