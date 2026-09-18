# Bearing-frame structural progress

Evaluated September 7, 2026 against `bearing-lean-frame`, geometry commit
`b23ffbe`. **This is not construction or climbing approval.** No CAD substitution
or geometry change accompanies these results. The current viewer remains an
inspection model with provisional connector geometry.

**Subsequently identified datum error:** this geometry and its load targets use
the old, incorrect main-panel hole grid. The corrected template has a 220 mm
gap between T-nut rows 6 and 7; row 1 is 100 mm above the nominal 1220 mm panel
bottom, not 80 mm. Main LEDs must not be placed on the kicker. These results
remain reproducible diagnostics of `b23ffbe`, not evidence for the corrected
grid or the proposed panel-over-frame/base redesign. Both require new checks.

## What the new evidence establishes

The bulk stiffness solver now completes with valid straight-sided quadratic
elements. The eight leg-wall bolts pass a bounded nominal dimensional-stack
screen. Manufacturer research supplies real ML24Z/SDS geometry and a panel
screw candidate with plywood-specific data. These advances do not establish
the real frame's joint capacities, material strength or unanchored safety.

## Stiffness diagnostic

The earlier curved-element meshing approach failed before a structural solve.
A controlled experiment on the current bulk geometry held the same 41,376
tetrahedra: first-order elements had no nonpositive Jacobians, curved quadratic
elements had 32, and straight-sided quadratic elements had none. This isolates
curved midside placement as the cause in this experiment, rather than proving
that all CAD details are appropriate for every meshing method.

The new solver uses the documented Gmsh `Mesh.SecondOrderLinear` option, retains
second-order displacement interpolation and independently verifies that all
midside nodes lie at edge midpoints. It does not bypass invalid-element checks.
Curved boundaries are faceted; gross volume agreement is not a local hole or
stress-accuracy guarantee. [Gmsh manual](https://gmsh.info/doc/texinfo/gmsh.html).

| Check | 60 mm mesh | 40 mm mesh |
| --- | ---: | ---: |
| Quadratic tetrahedra | 41,376 | 76,535 |
| Nodes | 77,006 | 142,255 |
| Absolute CAD/mesh volume discrepancy | 0.0444% | 0.0462% |
| Maximum loaded-node displacement, 1.2 kN downward | 1.20955 mm | 1.21065 mm |
| Maximum loaded-node displacement, 2.4 kN downward | 2.41910 mm | 2.42130 mm |
| Maximum loaded-node displacement, 1.2 kN downward + 0.3 kN outward | 1.56325 mm | 1.56484 mm |

Both runs passed positive-Jacobian, independent corner-volume/midside,
connected-mesh, load/support inventory, force-equilibrium and moment-equilibrium
checks. The approximately 0.09% difference in the downward displacement is
encouraging sensitivity evidence, not a general convergence proof: the nearest
load nodes move between meshes, and point loads do not establish local stresses.

**These are deliberately optimistic bulk calculations:** timber is isotropic
with E=7,000 MPa and Poisson ratio 0.3; contacting pieces and separate leg plies
are artificially bonded; all floor nodes are fixed in all directions; gravity,
actual fasteners, connection slip, separation, buckling and material strengths
are omitted. Steel angles are omitted. Loads are equally shared by five row-12
nodes. The reported maximum is among those loaded nodes, not the entire frame.
Single-hold, F-column and joint failure cannot be inferred from these numbers.

The numerical stiffness results do **not** support replacing the unresolved
joint design with a claim that the frame is safe because displacement is small.

## Separate moment screen

The current drilled geometry gives 182.445 kg of included mass at the assumed
wood/steel densities, excluding fasteners, holds, LEDs and glue. All 96 selected
downward-force envelope cases meet the illustrative 1.5 edge-moment target.
Minimum factors are 1.958, 1.924, 1.891 and 1.859 for 150, 200, 250 and 300 lb.
This envelope includes 1x/2x gravity, 0/300 N horizontal force over all azimuths,
0/50/100 mm standoff and 80%/100% included mass at fixed CG. It is not a sliding,
contact, dynamic or user-rating qualification. Historical exploratory opposite
normal-force results are not superseded by this downward envelope.

## Joint and product findings

- **Leg-bolt dimensions:** all eight 139.7 mm bolts have four contiguous raw-CAD
  receivers totaling 114.3 mm. Using maximum selected washer/nut dimensions
  and a project-assumed 2.54 mm bolt underlength leaves 10.2362 mm nominal tip
  projection, compared with the selected 3.175 mm two-pitch screen. This does
  not prove complete threads, washer bearing, plywood resistance or load sharing.
  Delivered thread/chamfer/stock tolerances still matter.
- **Unselected hardware:** eight kicker-block and four lower-corner screws
  still have generic representations without a selected product identity.
- **Actual connector geometry:** the [ML24Z research](ml24z-qualification.md)
  found materially different factory hole coordinates and a current lateral-load
  letter. Earlier proxy collision passes are not actual-product fit checks.
- **Lower-ledge load direction:** the bearing-installation table does not list
  the separation direction corresponding to downhill ledge loading. The single/end
  table cannot be transferred without establishing the installation and grain
  configuration. This is an unresolved design gate, not an assigned zero strength
  or an automatic pass from the other tabulated directions.
- **Panel attachment:** [SPAX research](panel-fastener-qualification.md) provides
  a useful candidate but identifies eight existing corner end-distance failures.
  The old generic pilots cannot be carried into a qualified product installation.
  Plywood material assignments and combined-load distribution remain unresolved.

## Next design actions

1. Replace the connector proxies with manufacturer-backed nominal geometry and
   rerun complete body, hardware, driver and service-clearance checks.
2. Resolve the lower-ledge load direction through a supported installation
   classification or a changed load path. Do not assume the bearing table covers
   separation. The unsent manufacturer question is in the connector research.
3. Develop the panel attachment around a verified product and material basis,
   correcting corner distances and installation details without simply dividing
   the climber load equally among 48 screws.
4. Select the remaining kicker/corner products and establish actual leg/kicker
   demands, washer support and independent-ply behavior. Historical monolithic-leg
   FEA is not transferable to the present joint.
5. Only then use connection-aware, orthotropic/contact analysis and qualified
   structural review to evaluate construction readiness.

## Reproducible evidence

- [Leg-bolt stack and hardware inventory](../fea/results/bearing-joints/report.json)
- [Current moment envelope](../fea/results/bearing-frame/stability.json)
- [60 mm stiffness result](../fea/results/bearing-frame/mesh60.json)
- [40 mm stiffness result](../fea/results/bearing-frame/mesh40.json)

Each stiffness result links by filename/hash to adjacent compressed input deck,
displacement/reaction output, run context, log and step-status files. They can be
decompressed and replayed without rerunning the solver. Large visualization FRD
files remain local; their hashes are recorded but they are not required for the
committed loaded-node/reaction replay. Source closures are checked against the
unchanged CAD and analysis code.

For a fresh run, use `uv run python -m fea.prepare_bearing_structural`, then run
`python3 -m fea.solve_bearing_frame --size 60` and `--size 40` in the existing
`mini-moonboard-fea:box-v1` Docker image with the repository mounted as its working
directory. Preparation refuses to overwrite frozen output. An ordinary checkout
already contains the committed stability report: reproduce in a separate scratch
copy that excludes `fea/generated/bearing-frame` and
`fea/results/bearing-frame/stability.json`. Keep the original checkout and its
evidence intact; do not erase prior evidence to force a rerun.
