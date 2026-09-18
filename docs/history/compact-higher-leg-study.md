# Two higher three-bolt leg trials

This study follows the owner's approval to verify half-inch hardware and test
at most two further leg positions before reconsidering the structural layout.
Both retain solid 4×6 legs/rims, the compact 2×6 base, all panel attachments and
commercial connections. Neither changes the 250 lb target, doubled downward
force, 300 N rearward case or adopted duration factor of 1.0.

| Trial | Joint reference shift along slope from original two-bolt frame | Rearward foot-center shift |
| --- | ---: | ---: |
| upper225 | 225 mm | 150 mm |
| upper300 | 300 mm | 225 mm |

Leg bodies use actual rebuilt stock, level floor contact and preserved depth
offset/top allowance. Three half-inch bolt positions are fitted independently
of each leg body's defining reference line; moving the bolt pattern does not
silently move the leg. The prior 76×56 mm pattern was screened before native
analysis and flagged directional edge problems, so copying its previous
placement acceptance is not justified.

## Hardware basis

The [specific hardware assessment](compact-half-inch-hardware.md) identifies
Bolt Depot 407 Grade 5 1/2-13×8-inch bolts, matching Grade 5 nuts and USS washers.
A 90 ksi bending-yield calculation is supported as a specified-material
candidate through the NDS tensile-yield route and Grade 5's 92 ksi tensile-yield
specification. It remains conditional on the supplied material and actual
thread-bearing geometry. Grade 8 is not needed just to reach this reference.
The thread transition and fully formed nut engagement receive practical
preassembly acceptance checks in the hardware document.

Nominal CAD washers do not represent every delivered washer at the catalog's
minimum thickness. Resistance comparisons must additionally use the stated
catalog tolerances; no previous nominal-washer result transfers automatically.

## Decision rule

A native solve must converge before its forces are used. Actual-angle lateral
resistance, directional placement, hardware and affected timber checks remain
separate. A fixed-resultant screen only selects an assembly to investigate;
it does not predict the changed whole-frame forces. A passing isolated lateral
ratio does not release drilling or the completed frame.

## First assembled upper300 result

Both original higher-position models pass the complete actual receiver audit.
The upper300 three-bolt solve is numerically accepted after 12 contact iterations.
At the unchanged A12 doubled-downward +300 N rearward case it gives:

| Comparison | Result |
| --- | ---: |
| Actual-angle individual lateral ratio, Fyb=90 ksi, Cd=1 | 0.828 |
| Original maximum-angle individual lateral ratio | 0.858 |
| Original full-root sensitivity | 1.155 |
| Minimum directional edge/end margin | −29.23 mm |
| Minimum conservative component-row spacing margin | −7.50 mm |
| Maximum sampled rim net-section ratio | 0.460 |
| Maximum sampled leg net-section ratio | 0.213 |
| Header gross-section ratio | 0.501 |
| Conservative trimmed-end shear ratio | 0.0844 |
| Quarter-area bearing sensitivity | 0.0456 |
| Catalog-tolerance washer bending ratio | 0.401 |
| Maximum timber displacement | 10.05 mm |

The controlling edge flag is not a negligible force component: left bolt 1
carries 1304.68 N laterally, including 1304.14 N across the leg grain. Its rim
also has a loaded-edge flag. The same force directions were not predicted by
holding the preceding two-bolt assembly's resultants fixed. The actual left
joint moment is 199.77 N·m. This confirms why a favorable held-wrench screen
cannot replace the new assembled solve.

The 56 mm rim-aligned spacing also falls below the retained conservative
63.5 mm perpendicular-row component reference. This is reported separately
from unresolved general oblique-row applicability; it is not presented as a
universal rule for every oblique bolt group. A corrected pattern should clear
that comparison so the design does not depend on resolving this interpretation.

[Archived first upper300 result](../fea/results/compact-next-study/upper300-rear/manifest.json)
retains the exact model, actual geometry, nominal hardware checks and full
catalog-tolerance/local-wood checks. The 33 ksi washer yield remains an explicit
analytical material reference; catalog dimensions alone do not certify it.

## Final upper300 pattern screen

A final bounded search uses the actual accepted upper300 three-bolt forces,
not the preceding two-bolt forces. It checks three half-inch bolts, both pattern
pitches from 64 to 150 mm in 2 mm increments, all four omitted-corner triangle
orientations, and independent centroid shifts from −40 to +40 mm in 5 mm
increments. The minimum reserve is 3 mm. No layout meets the retained directional
edge/end constraints, so stronger steel cannot supply an eligible layout within
this family. The minimum pitches also clear the earlier 63.5 mm component-row
spacing reference. This does not prove every possible connection impossible.

[Actual-force search evidence](../fea/results/compact-next-study/position300-actual-layout.json)
contains the exact inputs, search bounds and authenticated launch source.
The upper300 geometry and its failed evidence remain preserved.

The second planned physical position, upper225, is retained for one assembled
trial with its spacing-corrected 76×68 mm triangle (omit corner 3, centroid
LN=+10 mm and RN=+25 mm). These parameters come from the separately preserved
preliminary screen; they are not assigned the upper300 forces as a final result.
The leg body remains exactly the prior upper225 body, while the revised bolt
pattern receives its own candidate identity and fresh drilling.

## Second assembled position and bounded conclusion

The spacing-corrected upper225 model passes the complete machined-receiver audit
and its A12 solve is numerically accepted after 11 contact iterations. It gives
actual-angle lateral ratio **0.770**, original maximum-angle ratio 0.844,
conservative component-spacing margin **+4.50 mm**, maximum sampled rim
net-section ratio 0.524, leg ratio 0.241, header gross ratio 0.588, trimmed-end
shear ratio 0.0894 and quarter-area bearing sensitivity 0.0485. Catalog-tolerance
washer bending ratio is 0.537 with the stated material reference. Maximum timber
displacement is 15.63 mm.

The remaining directional edge failure is left bolt 1 in the outer rim:
1747.94 N total lateral demand includes 860.85 N across the rim grain. Its
adjusted loaded-edge distance is approximately 21.40 mm versus the retained
50.80 mm (4D) reference, a **29.40 mm shortfall**. This is a real placement
concern under the retained screen, not a failed steel bolt or a failed kicker
base. The original full-root sensitivity is 1.282; its applicability depends
on the delivered thread-bearing condition described in the hardware assessment.

[Archived upper225 result](../fea/results/compact-next-study/upper225-refined-rear/manifest.json)
records the distinct final pattern and exact sources. Neither higher-position
assembly is released: both improve individual lateral resistance but fail
loaded-edge placement under the recovered forces. Further sideways/reversed-load
cases and construction publication were not run because the initial assembly
check already blocks either selection. The viewer and prior construction
schedules retain their preceding candidate; none of the failed drilling is
published as build-ready.

This closes the two-position search. The supported next structural study is one
knee brace that transfers turning moment through a larger triangle while
retaining the preferred 4×6 members and compact 2×6 base. It is a proposed next
study, not an installed or qualified connection. More bolt-grade substitutions
alone do not fix insufficient wood edge distance.

The subsequent [knee-brace study](compact-knee-study.md) now has a numerically
accepted paired-bolt trial. It improves the worst individual bolt ratio to
0.472, but an upper-leg bolt still fails directional placement and the brace
tabs require explicit stiffness/local-detail assessment. It is not released.

## Reproduction

```sh
uv run python -m scripts.compact_three_leg_study --leg upper300 --output fea/generated/compact-three-upper300-a12
uv run python -m scripts.compact_three_leg_study --leg upper225-refined --output fea/generated/compact-three-upper225-refined-a12
uv run python -m scripts.compact_three_leg_results fea/results/compact-next-study/upper300-rear
uv run python -m scripts.compact_three_leg_results fea/results/compact-next-study/upper225-refined-rear
```

Native output directories must be new; the commands above name the already
completed local jobs for identification. Recomputing archived resistance checks
does not run the native solver.

Verification: 413 default tests passed, 15 historical tests deselected; Ruff and
whitespace checks passed. Both archived full resistance reports recomputed
successfully. Software verification does not override either placement failure.
