# Reinforced candidate: panel and hold checks

**The current 25.4 mm T-nut flange exceeds the plywood face-bearing reference
under the upper main-panel load cases.** This result does not depend on how the
panel screws share load or on completing the frame solve.

At 300 lb ×2 downward load and 300 N horizontally outward, the 40-degree main
face receives **1945.370 N outward**. A single hold bolt with compression-only
front contact must carry at least that tension. Even an impossible solid,
unperforated 25.4 mm flange disk has only **1257.705 N** of plywood face-bearing
reference. The actual modeled annulus and three retention holes reduce that to
approximately **957.1 N**: demand/reference is **2.033** before any standoff
couple or clamp preload. This is a bearing/deformation reference exceedance,
not a prediction of sudden failure or a product pull-through test result.

[Saved checks](../fea/results/reinforced-panel-checks-v1.json) ·
[Calculator](../fea/reinforced_panel_checks.py) ·
[Tests](../tests/test_reinforced_panel_checks.py)

## Resistance basis

Keep the owned AC 23/32 PS1-09 plywood. APA D510C (2012) §4.4.7 gives dry
face-bearing references of **360 psi at 0.04-inch deformation** and
210 psi at 0.02 inch. Tables 9/10 supply AC family capacities; Group 4 reductions
provide the lower envelope over the four species groups. No Structural I or
impact increase is used. Section 4.5.5 reduces bending/tension for narrow panels.
[APA 2012 primary document](https://design.medeek.com/resources/structural/D510C_2012.pdf).

The resulting weaker-orthogonal references are:

| Quantity | Reference |
| --- | ---: |
| Flatwise bending moment per width | 113.003 N·mm/mm |
| Axial compression per width | 25.817 N/mm |
| Apparent bending rigidity per width | 477172.595 N·mm |
| Interlaminar/transverse shear per width | 5.108 N/mm |

For kicker stress running horizontally, the physical width perpendicular to
that stress is 225 mm; its bending/tension size factor is **0.527264**.
Vertical kicker stress uses the full 1219.2 mm physical width. Mesh-element
width is not substituted for panel width. Known principal directions can use
the appropriate directional family value; the present component API uses the
weaker orthogonal direction independently.

## Hold and flange equilibrium

Let N be outward force, V in-plane force magnitude, e the force standoff from
the panel face and a the largest usable distance from the bolt axis to the
front hold-contact resultant in the direction needed to resist the couple.
With one bolt, no independent bending couple carried by that bolt, no separate
hold set screw or retention-fastener moment path, and compression-only front
contact:

```text
M = |V| e
contact compression >= M/a
bolt tension >= max(0, N + M/a)
```

Here **a is a missing hold dimension**, not the T-nut flange radius. The report
runs a = 25, 50 and 100 mm as explicit sensitivities, never as an installed
load-spread assumption. For the upper main-face case and e = 100 mm, a = 50 mm
gives a minimum bolt tension of **5648.740 N**. The required plywood bearing
area under the same reference is approximately **2276 mm²**. Merely adding
panel screws does not increase the local T-nut bearing area.

The modeled hole is 11.112 mm. With flange diameter 25.4 mm and three separate
3.2 mm retention holes, the optimistic available annular area is

```text
A = π/4 × (25.4² − 11.112² − 3 × 3.2²) mm²
bearing reference = A × 2.482113 N/mm²
```

This assumes a fully seated flat flange and does not credit barrel friction,
retention screws, preload cancellation or an unmodeled backing plate. Flange
flexure or an uneven seat can reduce effective area; the full gross disk
comparison already exceeds the reference in the upper normal-load case.
An actual front-contact footprint can resolve the standoff-couple demand, but
cannot remove the outward-force-only reference exceedance.

## Exact local geometry and remaining inputs

Column F centers are 19.2 mm from the independent center seam. The current
flange leaves **6.5 mm** to that edge; the hole leaves **13.644 mm**. A centered
circular spreader confined to that panel could be no larger than 38.4 mm before
reaching the seam. No neighbor panel is credited as backing.

The current unrecessed barrel projection leaves **5.55625 mm nominal cover**
to the front face. A proposed recess of depth r would leave `5.55625 − r` mm
and reduce panel thickness to `18.25625 − r` mm locally; the current CAD does
not cut such a recess. The 12.7 mm body-depth datum and barrel OD remain
provisional. These values matter to bolt engagement and local wood geometry;
a generic statement that the hold hardware “fits” cannot supply them.

To finish a hold-level combined check requires the actual front-contact lever
arm/direction, bolt engagement and grade, tightening/preload basis, flange
bending resistance and any proposed recess/spreader dimensions. The present
normal-force bearing exceedance is established before those refinements.
The annular face-bearing calculation is not a circular punching-shear formula;
no panel rolling-shear table is repurposed as T-nut pull-through capacity.

## Global panel bending and attachments

The calculator supplies `section_check` for signed local membrane forces,
bending moments, transverse/membrane shear and deflection from an authenticated
response model. It compares each component without averaging peaks or inventing
an effective width. Compression/bending interaction, buckling and local hole
stress concentration are not represented as passing because separate component
ratios happen to be below one. The deflection acceptance limit is an explicit
input, not an invented climbing-wall criterion.

The paired `attachment_check` evaluates each recovered screw tension/lateral
force with the existing conditional wood interaction and separate head limit.
It does not use the earlier 450 equilibrium witnesses as actual sharing demands.
The [native section report](../fea/results/reinforced-panel-F10-k1000-v4.json)
now integrates 3762 sections across all six panels for one actual response run:
**F10, 500 lb downward, 300 N horizontal outward, 100 mm standoff**, with
1000 N/mm attachment springs. This is one load case, not a six-panel loading
envelope. Three through-thickness Gauss points are integrated at each of nine
in-plane locations per S8 element; all 66 individual attachment reactions are
checked through the shared current fastener consumer.

| Panel | Largest directional component ratio in this run |
| --- | ---: |
| Main lower left | 0.736, transverse shear |
| Main lower right | 0.566, transverse shear |
| Main upper left | 47.352, transverse shear near the applied patch |
| Main upper right | 1.161, transverse shear |
| Kicker left | 0.972, horizontal bending |
| Kicker right | 0.482, horizontal bending |

These are **conditional numerical-model/reference comparisons**, not actual
plywood failure predictions. The 20 mm prescribed load patch applies a force
and nodal couple; it is not the actual hold-seat traction field. The report
retains full-field extrema plus separate extrema outside the patch and at
least 50/100 mm from it, including coordinates and distances for every witness.
Even beyond 100 mm, the loaded panel reaches bending component ratios 1.528/1.385
and transverse-shear ratios 1.899/4.429 under this lower-family reference.
Excluding the patch does not establish local hold strength or eliminate other
point-attachment/contact idealizations.

The largest recovered panel screw demand is **1618.184 N tension and 439.589 N
lateral**, at `round_panel_upper_left_center_3`. Under the current TER 120 lbf
head basis, its head ratio is **3.032**; its wood-interaction ratio is **2.618**.
Seven of 66 screws exceed at least one current conditional reference in this
run. These are recovered spring-model forces, not the prior equilibrium
witnesses or an equal-sharing allocation. See the
[current fastener applicability basis](reinforced-fastener-applicability.md).

Maximum absolute panel-node displacement is **23.661 mm**. It includes frame
motion; it is not relative panel bending deflection or a serviceability pass.
The run assumes homogeneous isotropic E = 7000 MPa, unperforated panels, specified
springs and sticking floor contact. That response is not a measured or fully
orthotropic prediction for the owned sheets. Contact iteration and equilibrium
converged, but floor friction admissibility remains separate.

A second [converged response](../fea/results/reinforced-panel-F10-k10000-v5.json)
uses 10000 N/mm attachment stiffness. This sensitivity gives:

| Quantity | 1000 N/mm | 10000 N/mm |
| --- | ---: | ---: |
| Maximum absolute panel displacement | 23.661 mm | 12.831 mm |
| Governing screw tension | 1618.184 N | 2303.746 N |
| Same screw lateral force | 439.589 N | 877.454 N |
| Governing screw head ratio | 3.032 | 4.316 |
| Same screw wood-interaction ratio | 2.618 | 4.260 |
| Attachment reference exceedances | 7/66 | 28/66 |
| Upper-left transverse shear ratio beyond 100 mm from patch | 4.429 | 4.540 |

Greater assumed stiffness reduces displacement while increasing some connection
forces. Neither stiffness is calibrated to the installed assembly; two samples
do not bound every possible physical stiffness. Both preserve the stated model's
reference exceedances. The sensitivity removes unintended kicker-floor friction;
baseline kicker-floor normal/tangential reactions were zero, so no active baseline
load path is credited by that removed law.

Recorded native artifact/snapshot hashes were checked against the corrected v4
run. Its consumed-source inventory includes the parser omitted from the earlier
trial. The section consumer separately records its parser, material-check and
shared fastener-consumer hashes. The parent archives the complete reproduction
bundle; hash checks alone are not an independent full replay.

**The local flange seat exceeds the declared bearing/deformation criterion;
the specified native response model also exceeds panel and screw component
references. Neither result releases construction or demonstrates a particular
physical rupture mechanism.**

## Practical remedy to develop

Retain the owned T-nut and place a **flat steel spreader between its flange and
the plywood rear face**, with no plywood recess. This changes the bearing
footprint rather than asking the existing small flange to carry a higher
average pressure. A 3 mm plate would reduce the modeled barrel's projection
into wood from 12.7 to 9.7 mm; hold-bolt length and engagement must be matched to
that resulting stack. Three retention screws need an explicit compatible detail.
Plate thickness 3 mm is an example stack change, not a released bending design.

For the normal-only upper case, required bearing area is 784 mm². Including the
100 mm standoff/50 mm contact-arm sensitivity requires 2276 mm². A 36 × 70 mm
rectangle minus the 11.112 mm barrel hole supplies approximately 2423 mm²,
corresponding to a 6.01 kN face-bearing reference. Those dimensions illustrate
the area needed; they do not establish uniform pressure, plate flexural
resistance, stable contact or a permissible footprint.

Fit is a real design constraint: the centered width at column F is limited to
38.4 mm by the independent seam. Lower main row 6 lies only 15.95 mm below the
service receiver, so a symmetric 70 mm-high rear plate would collide with that
receiver. Some plates would need an offset hole and verified eccentric plate
bending, or a revised receiver detail. LED apertures must remain open. A generic
large washer is therefore not yet a complete remedy for every hold.

The manufacturer's [Standard 3-Hole product page](https://escapeclimbing.com/products/hd3hnut)
provides an installation guide but no numerical load rating was found there.
The different [Industrial Gym product](https://escapeclimbing.com/products/hditnut)
reports testing to 12 kN in 18 mm Baltic birch. That product/material assembly
result does not qualify the owned Standard T-nut in Roseburg AC plywood.
The present APA bearing/deformation exceedance is not a statement that standard
commercial climbing T-nuts rupture at that load.
