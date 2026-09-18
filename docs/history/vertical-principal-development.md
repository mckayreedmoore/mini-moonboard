# Additional principals instead of middle rails

This development candidate replaces the four middle horizontal rails with
four separate full-height 2×6 principals. The top crossmember, split bottom
backing and base header remain. Existing center framing, rear legs, both
plywood base gussets and their through-bolts remain.

[Interactive model](https://mckayreedmoore.github.io/mini-moonboard/?model=vertical-principal-development&view=rear),
[open-frame render](../exports/vertical-principal-development/open-frame.png),
[base detail](../exports/vertical-principal-development/base-connection.png),
[STEP](../exports/vertical-principal-development/vertical-principal-development.step),
[wood schedule](../exports/vertical-principal-development/wood-parts.csv), and
[fit audit](../fea/results/vertical-principal-audit-v1.json).

## Framing and connections

The new principal centers are X−770, −370, +430 and +830 mm. Each is one
38.1 ×139.7 mm member with a level bottom bearing cut. Their positions avoid
the modeled 40 mm hold/LED service cylinders, without cutting service pockets
in these four members. Existing central and outer framing is preserved.
The old middle rails and their brackets are removed completely.

Every new principal receives a top connection and a bracket to the header.
A separate, aligned short 2×10 post supports the full depth of the header
under each new principal, with its own header connection. These posts avoid
relying on the header to bridge from the new bearing locations to the old
three posts. Their wider depth covers the sloped member's bearing footprint;
they are single pieces, not stacked 2×6 substitutes. The original center and
outer post geometry is unchanged, so the existing rearward header-transfer
question at those supports remains open.

The bottom rails become six pocket-free segments between principals. Their
ends have explicit brackets. This keeps the lower panel backing without
cutting housings into the new principals. There are no middle crossmembers.

Eight panel screws whose middle-rail receivers disappear are removed. Thirty-two
new panel screws attach the four new full-height receivers, for 80 panel/kicker
screws total. Bottom screw locations are reassigned to actual split receivers.
All holes are generated from the new schedule, not retained as an additional
old pattern. Ordinary panel screws remain modeled; inserts and machine screws
require a separate checked hardware revision. Nominal future insert reservations
are not installation pilots or proof of anchorage in damaged wood.

## Panel seam and gusset questions

Four existing square face panels remain. Their horizontal seam has independent
upper and lower edges between principal contacts. Removing the rails does not
join these edges together or establish that their movement is acceptable.
The comparison must examine loads close to the seam, relative edge movement,
panel screw forces and actual directional plywood properties.

Additional principals and supported base connections may redistribute forces,
but **no reduction in gusset demand or required hardware is established**.
Existing gussets and all through-bolts are retained. More connections can change
load sharing in either direction, depending on member and connection stiffness.
The new layout also removes intermediate crossmember restraint; plywood bracing,
frame racking and member stability require explicit verification.

APA identifies panel orientation and edge support as relevant to span-rated
performance. Its building-panel guidance is context, not a climbing-wall load
rating. See [APA plywood guidance](https://www.apawood.org/engineered-wood-products/plywood-osb/plywood/).

## Evidence limits

The model and schedules remain **not build-ready**. Fit and source-integrity
checks do not qualify plywood bending, commercial bracket combined loading,
timber net sections, bolt groups, gussets or the actual floor interface. No
older finite-element force, floor equilibrium result or material rating is
transferred to this geometry.

## Limited panel-flex comparison

The [archived shell comparison](../fea/results/vertical-panel-comparison-v1.tar.gz)
contains eight solves, a separate cantilever benchmark, input decks, raw output,
reports and exact source snapshots. It compares the paired-rail layout against
this 80-screw vertical-principal candidate. This is a comparison of ideal screw
support locations, **not a whole-frame or gusset-force analysis**.

Two left panels are solved separately under individual 1,200 N outward-normal
loads. Each load is distributed over a hypothetical 40 ×40 mm patch centered
at X−419.2 mm and S1099.2 or S1319.2 mm, adjacent to the horizontal seam. The
patch is not the measured hold or T-nut contact footprint. Each panel is an
undrilled, homogeneous shell, 18.25625 mm thick, with assumed isotropic
E=7,000 MPa and Poisson ratio 0.3. Those are surrogate properties, not verified
directional plywood properties. Only normal displacement is fixed at actual
screw axes; framing flexibility, wood backing contact, holes, screw slip and
panel-to-panel transfer are omitted. Therefore the results are neither measured
deflections nor rigorous upper/lower bounds for the real assembly.

| Separate load case, 25 mm maximum mesh | Paired rails | Additional principals |
| --- | ---: | ---: |
| Lower panel: mean displacement at loaded patch | 0.977151 mm | 0.178387 mm |
| Lower panel: maximum absolute seam-edge displacement | 0.458198 mm | 0.231769 mm |
| Upper panel: mean displacement at loaded patch | 0.642784 mm | 0.188621 mm |
| Upper panel: maximum absolute seam-edge displacement | 0.156914 mm | 0.280422 mm |

In this surrogate, loaded-patch compliance decreases about 82% and 71%, while
lower seam movement decreases about 49%. **Upper seam movement increases about
79%.** The maximum may occur away from the load patch. Each case loads only one
panel; its neighbor remains unloaded and independent. Do not subtract results
from different load cases to invent a seam-opening result.

Both 40 and 25 mm meshes were run for each configuration and panel. Patch
compliance and maximum seam displacement changed by less than 2.54%, passing
the declared 5% numerical comparison gate. This gate does not establish
convergence of individual screw reactions or local stresses. The cantilever
benchmark differed from its independent beam/shear reference by about 0.0039%.
Force and moment balance were checked for every panel solve.
Maximum absolute residual components were below 0.000484 N and 0.546 N·mm,
against the declared 0.1 N and 2 N·mm gates.

Moving the upper screw row from 80 to 30 mm above the seam, or adding a second
row there, did not improve its maximum seam displacement in the diagnostic.
The selected candidate therefore retains the simpler 80-screw pattern. More
screws alone are not a demonstrated remedy for this free-edge response.

Recommended next comparison: reduce vertical support spacing near the seam or
develop an explicitly connected panel joint, then test more hold positions,
both sides of the frame, actual plywood orientation and compliant connections.
Keep the gussets until a separate whole-frame analysis establishes their forces.

## Fit results

The four new principal/post paths have full nominal bearing projection. New
principals clear the modeled service cylinders by at least 10.15 mm and need
no service pockets. The main unsupported horizontal edge spans have a maximum
clear length of 392.05 mm; the audit also records the existing tiny service-pocket
opening in the center member, rather than merging it into solid backing.

The lumber schedule contains seventeen 2×6 members, two single 3×6 center
members and five single 2×10 members (header plus four new posts). Hardware is
80 panel/kicker screws, 16 bolts, 31 brackets and 186 bracket screws. Stock
availability, material properties and resistance remain unqualified.

## Verification

Twenty-four targeted tests passed, including the new fit audit, archived
shell-result replay, source/artifact authentication, retained paired-rail
checks and selector behavior. The browser loaded all 345 entries, selected
the central member, exercised navigation and grid placement, and captured
desktop/mobile views without browser or request errors. The CAD overview and
cropped base detail were inspected directly. Ruff and diff checks passed.

Independent correctness, testing and consistency reviews found no remaining
substantive issues within this development scope. A separate mechanics review
checked the shell setup and its interpretation. None of these checks establishes
construction approval or a gusset-force reduction.

```sh
uv run pytest -q tests/test_vertical_principal_frame.py \
  tests/test_vertical_principal_audit.py tests/test_vertical_principal_artifacts.py \
  tests/test_vertical_panel_comparison.py tests/test_vertical_panel_evidence.py
```
