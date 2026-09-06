# Matched whole-frame MORTAR increment refinement

## Predeclared experiment

Retain the original 0.25-increment experiment and compare two new runs with
initial/maximum increments 0.125 and 0.0625 in **both** nonlinear steps.
Automatic cutbacks remain enabled; the existing 200-increment ceiling stays
unchanged. Each new run has a 1,200-second solver runtime cap and two OpenMP
threads. A timeout is incomplete numerical evidence, not physical failure.

Only the two `*STATIC` increment lines change. The frozen 62,020-node,
32,511-C3D10 original untied 2×8-foot100 timber mesh, materials, gravity,
five-node 1,200 N load, contact slopes, assumed friction 0.5, and three ground
bricks remain identical. Only the twelve noncontact ground-bottom nodes are
restrained; there are no timber restraints. Exact source snapshots, deck,
context, and solver outputs are retained separately for each run. Every
consistent nodal gravity weight is checked against fresh curved-mesh
integration before launching, not merely against total mass.

Comparison quantities are all three external force and moment residual
components at accepted increments, all three bottom-support reaction
components per floor patch, each patch moment about the global origin and its
fixed undeformed bottom-node centroid, and displacement vectors of the
original five loaded nodes. Compare common accepted times; full-gravity and
full-load endpoints are compared only if available. No further increment
trials are authorized by this experiment if these runs are incomplete or
their trends are not stable.
The existing 0.1 N/component and 1 Nmm/component diagnostic gates remain
unchanged. A displacement plateau alone does not override a failed gate.

This experiment tests increment sensitivity, not mesh convergence, actual
floor compliance/friction, joint capacity, or local weak-contact admissibility.
It cannot independently select a construction design or authorize climbing.

The generic CLI permits increments from 0.005 to 1; 0.005 leaves no automatic
cutback headroom within 200 increments. This study uses only 0.125 and 0.0625.
