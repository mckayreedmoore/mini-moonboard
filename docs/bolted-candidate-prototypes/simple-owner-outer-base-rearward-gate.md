# Outer-base header bolt rearward-only gate

The [static source-backed gate](../../scripts/simple_owner_outer_base_rearward_gate.py)
rejects a Y-only move of the outer-base vertical header bolt at the six
reported outer-header clashes. It assumes the reported overlapping X/Z
location remains fixed; changing the outer-header block or the joint
topology is outside this bounded trial.

The selected header starts at Y = −175.7 mm. With a nominal 6.35 mm bolt,
the conditional 4D rear loaded-edge marker requires its center at
Y ≥ −150.3 mm. The outer-header block begins at Y = −150.3 mm and shares
the header underside Z plane. To avoid that block, the shaft center must
be at Y ≤ −153.475 mm; the 25.4 mm washer requires Y ≤ −163.0 mm and a
40 mm access tool requires Y ≤ −170.3 mm. These bounds cannot coexist
with the 4D marker. Even ignoring 4D, a washer fully seated on the header
requires Y ≥ −163.0 mm, giving only exact tangency with the outer-header
block at −163.0 mm and no clearance or tolerance.

The suggested 70 mm Y-grain block from −185.7 to −115.7 mm gives its
proposed header bolt at −160.3 mm a 25.4 mm *block* rear edge, but only
15.4 mm to the actual header receiver's rear edge. Its washer still
overlaps the outer-header block's Y extent by 2.7 mm. The block's front
face stays at −115.7 mm, so the previously screened bottom-outer PB09
near-tool Y separation is not worsened, but other protected-solid and
tool clearances were not re-run: this trial already fails necessary
header-edge and washer conditions. No alternative ordinary pose, joint
strength, drilling, or fabrication approval follows from this gate.
