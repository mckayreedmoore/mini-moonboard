# Kicker bottom-edge compression reference

**A conditional axial-compression calculation needs 63.76 mm of uniformly loaded width for the Group 1 plywood assumption. This is not an approved minimum floor-contact length.** The calculation resolves the correct published resistance category and its scale. It does not yet establish the local hold-to-panel-to-floor load path.

Keep the owned Roseburg AC exterior PS 1, 23/32-category plywood. The calculation uses a nominal 1219.2 × 225 × 18.25625 mm kicker, one 2669 N downward applied load and 29.467 N gross-panel weight at the project's assumed 600 kg/m³ density. Hold, bolt and accessory weight is additional. The load and density are analytical assumptions, not measurements. No physical floor measurements or tests are required by this review.

## Correct reference and orientation

[APA's current D510 publication listing](https://www.apawood.org/guides-tools-training/technical-document-library/technical-guides/panel-design-specification/) identifies the September 2020 revision. The APA-authored [D510F PDF hosted by the University of Michigan](https://wood.tcaup.umich.edu/lectures/2021/D510.pdf#page=32) was downloaded and its Table 10 pages visually inspected. Its SHA-256 is `b09fca5c358f16a598ed289cff46e7b515b783af4e5fb82919cc1af22155960a`.

For A-A/A-C, Group 1, 23/32-category plywood, Table 10, printed pages 28–29, gives:

| Stress relative to panel strength axis | Axial compression FcA, lbf/ft | Flatwise bending FbS, lbf·in/ft | Bending EI, lbf·in²/ft |
|---|---:|---:|---:|
| Parallel | 4800 | 775 | 320000 |
| Perpendicular | 2900 | 455 | 90500 |

Section 4.4.2 defines FcA as panel axial compression. Section 4.4.7's 360 psi bearing reference is for compression perpendicular to the **panel surface**; it is not the bottom-edge resistance of this standing kicker. Table 10's bending quantities cover flatwise panel bending, not edgewise bending of a deep horizontal beam.

Use the perpendicular column when the kicker's face-grain/strength axis runs horizontally; use the parallel column when it runs vertically. The existing grain verification requirement remains. Taking the lower perpendicular value bounds these two orthogonal orientations only; it does not establish an arbitrary diagonal-grain layout. The Group 1 assumption requires the applicable panel mark, not merely the retailer's “fir” description. No Structural I multiplier is applied.

## Conditional width calculation

For a uniform full-thickness compressive resultant over width `L`, the reference is `P = qL`. With the perpendicular Group 1 value:

`q = 2900 × 4.4482216152605 / 304.8 = 42.3223 N/mm`

`L = (2669 + 29.4673) / 42.3223 = 63.7599 mm`.

At an assumed uniform 64 mm width, the simple axial reference is approximately 2708.63 N. That narrowly exceeds this one downward-plus-plywood-weight scenario before the excluded mechanisms and accessory weight. It is not enough margin to designate 64 mm as a construction acceptance dimension.

The correct interpretation is a **necessary uniformly compressed section width** under these conditions. The floor bearing edge must have a supported load distribution that satisfies the local pressure and panel-section checks. A long nominal edge does not establish the effective width; a point load on a hold does not automatically spread across the full 1219.2 mm panel. Conversely, a short hard shim does not automatically establish a uniform compression strip from the hold to that shim.

[Reproducible code](../fea/round_structural_kicker_bearing.py) and [results](../fea/results/round-structural-kicker-bearing.json) include both orthogonal directions and the Table 11 alternatives. For the perpendicular direction, the Group 2, 3 and 4 compression multipliers are 0.73, 0.65 and 0.61; corresponding required uniform widths are 87.34, 98.09 and 104.52 mm. These are conditional alternatives for a known mark, not permission to assume an unknown grade.

All reported values assume dry service below 16% equilibrium moisture, ordinary temperature and normal duration, with no impact-duration increase. The calculation is isolated nominal arithmetic with no current CAD authentication. It records calculator/PDF hashes and refuses to overwrite an existing result. Reproduce into a new filename with `.venv/bin/python -m fea.round_structural_kicker_bearing --output /tmp/kicker-bearing-replay.json`. Five focused tests check units, load addition, orientation/species reductions and invalid inputs.

## What the support assumption must settle

The proposed installation assumption is a rigid, adequately strong floor with the kicker's sound bottom edge seated over an explicitly justified contact region. A mat or compressible floor covering beneath that edge, local void, sloping edge, damaged veneer or unsupported shim changes the assumed load path. This is an analytical installation condition, not a claim of measured floor stiffness, friction or capacity.

Full-thickness axial compression and a face-normal prying moment are distinct. If a downward hold load acts forward of the panel centroid, its moment must be balanced by the actual panel fasteners, backing contact and floor contact. Partial-thickness bottom contact concentrates load into only some plies. The tabulated full-panel FcA cannot simply be assigned to that reduced contact area without a layup/load-transfer justification. Out-of-plane buckling, simultaneous compression and flatwise bending also remain separate; a 225 mm height alone does not qualify restraint.

At the hold, establish the actual bolt/T-nut geometry, edge distances, flange/head contact and the force/couple delivered to the plywood. Retain the net-section and local shear, splitting, crushing and pull-through checks around the hold hole. T-nut prongs are not automatically the designed vertical shear path. The existing independent panel seams stay independent. The compression width calculated here qualifies neither those details nor the four kicker screws.

A completed kicker check can use this reference once the normal/prying equilibrium provides its simultaneous actions and a defensible effective load width/contact state. The [companion pitch calculation](round-structural-kicker-prying.md) now finds eleven conditional necessary-equilibrium failures among 45 sampled cases even with bottom-edge support; its limited two-dimensional witnesses do not establish actual contact width or strength. Report axial reference arithmetic as complete and actual kicker strength as unresolved.
