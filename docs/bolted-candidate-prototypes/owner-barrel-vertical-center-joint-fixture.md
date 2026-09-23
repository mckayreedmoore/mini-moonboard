# Two-vertical-bolt principal/header joint fixture

Status: **BLOCKED**. This is a source-built CAD and reduced-mechanics
diagnostic, not a fabrication release or a complete-joint qualification.

## Fixture

The fixed header and rigid principal use the current modeled combined cuts and
hardware pose:

- two vertical bolt/thread points at X = ±70 mm, Y = -146/-66 mm, Z = 305 mm;
- bolt seat Z = 238.9 mm and principal/header face Z = 277 mm;
- 66.1 mm seat-to-thread stack;
- 70 refined exact-area tributary contact cells per side, totaling
  5,024.764388 mm²;
- two tension-only bolt rows with zero assumed preload;
- radially coupled lateral bolt springs after 0, 0.575, or 1.15 mm clearance;
- no friction and zero initial modeled face gap.

The solver applies six rigid-body compatibility equations and checks force and
moment equilibrium. It ran 28 combined old-topology proxy directions (14
original and 14 full reversals) plus 12 isolated signed component directions.
Each was run with three explicit positive-stiffness sensitivities and three
clearance values, for 360 numerically converged diagnostics. A declared
small-kinematics screen limits interpretation to rotation norm at most 0.05
radian and maximum modeled point motion at most 2.0 mm. It is a numerical
domain check, not a material limit.

The stiffness values are numerical sensitivities, not evidence bounds. There
is no supported lower or upper complete-joint stiffness bound. The repository
also has no supported positive lower value for the complete axial path, face
contact, barrel capture, or lateral bore path.

## Result

The positive-stiffness captive-barrel model has a two-direction equilibrium
path, but compatibility does not support equal row sharing. Across the screen:

- 285 cases were inside the declared small-kinematics screen and 75 were
  outside it;
- rear-row axial share ranged from 0.163594 to 0.969572, and rear-row shear
  share ranged from 0.166638 to 0.971140, inside that screen;
- maximum screened bolt tension was 846.705806 N;
- maximum screened bolt shear was 136.053023 N;
- maximum screened combined bolt vector resultant was 852.008835 N;
- maximum screened radial slip was 1.184194524 mm in the 1.15 mm clearance
  case, including 0.034194524 mm spring overtravel;
- maximum screened cell-average face pressure was 5.012591 MPa; and
- maximum screened face opening was 1.677863207 mm.

The deliberately soft numerical model reached 11.964828230 mm opening and
large rotation. That result is outside the linearized fixture domain. It is a
stiffness/blocking warning, not a resistance demand.

At the reference numerical stiffness and 0.575 mm centered clearance, isolated
±My = 10,589.378494 N-mm required approximately 318 N tension in each bolt,
0.646 mm maximum opening, and 1.093 MPa maximum cell-average pressure. Isolated
±Mx = 48,931.774026 N-mm produced strongly unequal rows: the governing row was
496.391286 N for negative Mx and 463.892513 N for positive Mx.

These values are mode-specific actions inside the valid screening subset. They
are neither fresh design demands nor capacities; required design resistance
remains uncomputable. Cell pressure is a tributary-area average, not a local
elastic peak. The 8×8 source-face partition has no mesh-convergence proof and
uses cell centroids rather than integrating partial-cell contact.

## Why the answer is BLOCKED

The tight/captive positive-stiffness fixture equilibrates, so the modeled
geometry is not a kinematic no-go. The evidence-backed lower model has no
positive lateral stiffness. It is therefore an unbounded Fx/Fy/Mz mechanism;
the captive-barrel diagnostic cannot be promoted to a stiffness bound without
controlled bore fit and a defensible shank/barrel/wood contact model.

The model uses nominal source-built cuts only. No adverse bore-axis, diameter,
washer-seat, timber-section, or combined machining-tolerance solid has been
run. The reduced point stack also omits explicit bolt-head/washer contact,
thread engagement, barrel-body contact, bolt bending, and cylindrical bore
bearing.

The following resistance modes also remain unsupported: bolt/barrel axial and
thread action; bolt shear and bending; header/principal embedment; washer
bearing and flexure; barrel projected bearing and wall bending; splitting,
signed net tension, two-plane and group tear-out; and nonuniform face seating.

Fresh 48-pair six-case demands cannot yet be produced. The moved center posts
miss four inherited header/post barrel axes by about 120 mm. Those axes now
land inside the new seam backers, while both the moved-post/header connection
and backer/frame connection are undefined. The current 48-pair count therefore
does not describe a closed whole-frame load path. Repository instructions also
forbid a native solve.

## Finite unblock

1. Define the four moved-post/header connections and the seam-backer/frame
   attachment without changing the retained 66 panel/kicker screw count.
2. Build and source-bind the resulting 48-pair whole-frame CAD assembly.
3. Obtain controlled one-sided bore/shaft clearance and complete axial/lateral
   stiffness inputs, or replace them with an accepted conservative model.
4. Close every resistance mode listed above using controlled hardware and wood
   inputs.
5. Prepare the six cases. Only after the repository's no-native-solve rule is
   explicitly changed, run and replay the fresh complete combined actions.

The executable fixture is
[`scripts/owner_barrel_vertical_center_joint_fixture.py`](../../scripts/owner_barrel_vertical_center_joint_fixture.py).
