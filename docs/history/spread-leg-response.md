# Revised leg joint: 100×50 mm bolt group

This is a separate development trial for **2×6 and 2×8 legs, +300 mm rear footprint,
100 mm along-leg × 50 mm along-rim bolt spacing and a square top 150 mm beyond
the group centre**. It does not inherit approval or joint forces from the
[compact-pattern comparison](lumber-leg-response.md).

[Open the revised 2×6/+300 mm geometry](https://mckayreedmoore.github.io/mini-moonboard/?model=lumber-leg-spread-2x6-e300)
or [compare 2×8/+300 mm](https://mckayreedmoore.github.io/mini-moonboard/?model=lumber-leg-spread-2x8-e300).
The viewer contains drilled stock and the eight repositioned bolt assemblies,
with selectable metric/imperial part dimensions. It is a CAD view, not a stress
plot or construction approval; the default board is unchanged.

## Native preparation and checks

The new independent C3D10 leg meshes include the additional 30 mm of top stock.
Their volumes, centroids, full floor faces and frame-interface faces are checked
against actual CAD. The remainder of the frame retains its existing node
coordinates and element connectivity. All eight leg springs move to the new
bolt points, using separate interpolation weights on the leg and rim meshes.
The eight existing gusset releases remain unchanged.

The runner reuses the compact trial's deck, solver-output audit and load
combination functions. Only geometry preparation and source identities differ.
This retains the numerical force/moment, interpolation and energy gates while
preserving the original trial's frozen sources and evidence.

The three per-axis spring assumptions remain 100, 1000 and 10000 N/mm, with
nine native basis cases and 216 linear combinations per stiffness. The frame
and legs initially retain equal E=7000 MPa and ν=0.3. Floor nodes are fixed in
XYZ; gravity/contact, orthotropic behavior, bolt holes, local bearing,
splitting and connection strength are not modeled. These assumptions are
**not physical limits, permitted anchors or construction approval**.

```sh
uv run pytest -q tests/test_spread_leg_mesh.py tests/test_spread_leg_response.py
uv run python -m fea.spread_leg_response 2x8 --extension 300 --output /tmp/spread-leg-native.tar.gz
```

## Completed native comparison

The [2×6 archive](../fea/results/spread-leg-response/2x6-e300-m40-E7000.tar.gz)
and [2×8 archive](../fea/results/spread-leg-response/2x8-e300-m40-E7000.tar.gz)
each contain 27 native basis solves and 648 linear combinations. All numerical
gates pass. Eight archive replay/rejection checks pass for this revision;
the original six archives retain their 24 passing checks. No solver is needed
to replay this evidence.

The table uses the stiffest **assumed** connection, 10000 N/mm per axis.
Displacement and forces are separate maxima. R is instead the maximum
same-case lateral demand divided by its direction-dependent single-bolt
reference from the [conditional resistance screen](lumber-leg-response.md).
It excludes axial interaction, group effects and other qualification gates.
Values below 1 are not a connection pass or a climber weight rating.

| Stock | Climber, lb | Loaded-hold displacement, mm | Bolt lateral peak, N | Bolt axial peak, N | R |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2×6 | 150 | 1.300 | 523.60 | 90.46 | 0.633 |
| 2×6 | 200 | 1.646 | 663.68 | 114.51 | 0.803 |
| 2×6 | 250 | 1.993 | 803.75 | 138.56 | 0.972 |
| 2×6 | 300 | 2.339 | 943.82 | 162.61 | 1.142 |
| 2×8 | 150 | 1.262 | 562.89 | 79.15 | 0.727 |
| 2×8 | 200 | 1.598 | 714.05 | 100.43 | 0.923 |
| 2×8 | 250 | 1.934 | 865.21 | 121.70 | 1.118 |
| 2×8 | 300 | 2.270 | 1016.37 | 142.97 | 1.314 |

All governing R cases are left bolt 4, A12, twice body weight plus 300 N in +Y.
At 250 lb the simultaneous lateral demand/reference is **762.52/784.29 N**
for 2×6 and **865.21/773.84 N** for 2×8. In particular, do not divide the
2×6 separate lateral maximum of 803.75 N by the first reference.

At 250 lb, changing spring stiffness from 100 to 1000 N/mm gives loaded-hold
displacements of 6.180 to 2.690 mm for 2×6 and 6.105 to 2.645 mm for 2×8.
Their maximum R values change from 0.386 to 0.695 and 0.387 to 0.702,
respectively. Real connector stiffness has not been measured; this sweep is
not a guaranteed envelope. The compact 2×8/+300 trial had R=1.090 at the
stiffest assumption: widening its bolt pattern did **not** improve that ratio.

```sh
uv run pytest -q tests/test_spread_leg_native.py tests/test_lumber_leg_native.py
uv run python -m fea.lumber_leg_summary fea/results/spread-leg-response/2x6-e300-m40-E7000.tar.gz
uv run python -m fea.lumber_leg_resistance fea/results/spread-leg-response/2x6-e300-m40-E7000.tar.gz
```

## Development recommendation and release boundary

**Advance 2×6/+300 mm with this spread joint as the lighter comparison
candidate, not a construction selection.** Its 250 lb conditional lateral
ratio is only slightly below 1 and its 300 lb sensitivity exceeds 1. Wider
2×8 stock buys about 0.06 mm less displacement at 250 lb in the stiffest trial
but worsens that connection ratio. Neither design is ready for use.

Both alternatives use straight, grain-aligned, nominal 1.5-inch-thick lumber,
one level floor cut and a square top; there is no leg lamination or custom
metal fabrication. The wider bolt spacing needs new stock/drilling, not an
extra set of holes in an existing compact-pattern leg. The extra 300 mm is
rear foot-centre extension, not 300 mm added to the stock length. All twelve
stock/extension variants retain geometry checks; full assembly interference
checks cover the two revised +300 mm cases and 2×6 at the original footprint.

The next useful engineering step is **connection qualification/redesign and
actual restraint definition**, not another increase in lumber width. Resolve
combined lateral/axial bolt action, washers, group action, splitting and actual
material/fastener specifications together. Then reassess full-member combined
bending/compression, net sections and unanchored contact with those details.
The present default board, hardware schedule and release gates are unchanged.

The [next connection checkpoint](solid-leg-connection-next.md) checks whether
verified full-body 3/8-inch bolts could improve the conditional reference
without larger holes. Nominal thread length alone does not establish that credit.

## Why no full-member strength pass is claimed

The clear prismatic section checks exclude the bolt-loaded region and floor
bevel. A new same-case diagnostic reconstructs the actual interpolation-node
forces and scans bending through the loaded region, retaining eccentric axial
moments exactly once. It finds moments above the clear-strip envelope in
1296/1296 case-leg rows for 2×6 and 1295/1296 for 2×8. This is a scope limitation
of the clear-strip check, not evidence of material failure. The local nodal
load distribution is itself an idealization, not bolt-hole bearing.

An equivalent resultant below the bolt group does not establish the eccentric
end-loading idealization in [NDS Chapter 15, section 15.4](https://web-media.awc.org/wp-content/uploads/2021/12/17210150/AWC_NDS2024_20231129_AWCWebsite_Chapter15.pdf).
The diagnostic therefore returns **no interaction ratio**. Likewise, K=1 and
bearing-end anti-roll conditions require physical justification under
[NDS Chapter 3](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf)
and [Appendix G](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf);
they are not assured by fixing the numerical floor nodes. Sway/sliding,
torsion, floor bearing, stock defects and all existing non-leg frame release
gates remain open. No additional native mesh-convergence study has been made
for the revised joint; the earlier compact-leg refinement is not its proof.

```sh
uv run python -m fea.leg_beam_column_screen fea/results/spread-leg-response/2x6-e300-m40-E7000.tar.gz
uv run pytest -q tests/test_leg_beam_column_screen.py
```

## Updated unanchored floor screen

The changed stock and drilling are included in new drilled-CAD mass/CG studies
for [2×6/+300 mm](../fea/results/spread-leg-floor/2x6-e300.json.gz) and
[2×8/+300 mm](../fea/results/spread-leg-floor/2x8-e300.json.gz). Each has admissible
compression-only equilibrium for all 1296 tested cases at assumed μ=0.2 and 0.4.
At μ=0.1, only 678 and 696 cases respectively are feasible. These remain rigid
equilibrium witnesses, not compliant contact predictions, measured friction,
floor-bearing checks or a stability approval.

```sh
uv run python -m fea.spread_leg_floor 2x8 --extension 300 --output /tmp/spread-floor.json.gz
uv run pytest -q tests/test_spread_leg_floor.py
```

## MVP audit record

Focused verification completed with 110 geometry, floor, meshing, preparation,
summary and resistance checks; 32 old/new native replay and rejection checks;
and 30 diagnostic/viewer checks. Ruff and whitespace checks passed. Independent
correctness, testing and package-consistency reviews covered the comparison;
actual desktop and narrow browser views were inspected. These checks establish
reproducibility and scoped model consistency, not a structural certification.

The comparison MVP is complete as an engineering decision aid. Its unresolved
release gates are deliberately retained above; no plan, hardware purchase or
physical assembly should treat this document as permission to climb.
