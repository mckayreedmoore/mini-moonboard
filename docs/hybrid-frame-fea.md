# Full hybrid candidates: matched bulk FEA and stability

Next-stage investigation: [support-envelope comparison](hybrid-footprint-study.md),
[load-basis audit](hybrid-load-basis.md), and [joint work plan](hybrid-joint-next-steps.md).

**Numerical comparison, not structural approval.** Both complete candidate
geometries are frozen at `93c2b51`, with actual geometry-source and STEP hashes
in each result. The [candidate drawings and connection limitations](hybrid-full-candidates.md)
remain essential: no screw, bracket, glue or timber failure capacity is established.

## Matched bulk results

The existing Docker Gmsh/CalculiX workflow solved six independent load cases
for each candidate at 60 and 40 mm mesh settings: **24 completed cases**.
Like the [published plywood bulk screen](updated-board-fea.md), these use five
equal nodal loads near A12/C12/F12/H12/K12, isotropic E=7000 MPa, nu=0.3,
perfectly bonded timber contacts, no holes, no gravity and fixed floor nodes.
This is an equal-property geometry comparison, not realistic lumber selection.

Displacements below are the maximum **among the five loaded nodes**, not
the maximum anywhere in the model. Units are millimetres, at the 40 mm mesh.

| Independent load case | Plywood reference | 2×10 hybrid | 2×12 hybrid |
| --- | ---: | ---: | ---: |
| Downward 1.2 kN baseline | 0.368 | 0.545 | 0.389 |
| Downward 2.4 kN sensitivity | 0.737 | 1.090 | 0.778 |
| Downward 1.2 kN + outward 0.3 kN sensitivity | 0.477 | 0.702 | 0.502 |
| Downward 1.2 kN + inward 0.3 kN sensitivity | 0.260 | 0.388 | 0.276 |
| Outward/downward normal, exploratory | 0.570 | 0.832 | 0.597 |
| Inward/upward normal, exploratory | 0.570 | 0.832 | 0.597 |

The 2×12 is about **5.6% more flexible** than the plywood reference in the
sampled downward baseline; the 2×10 is about **47.9% more flexible**. These are
not allowable-deflection checks. The normal-load symmetry follows linear
elasticity and bilateral fixed supports; it does not establish that the
unanchored board can sustain either direction.

This comparison includes the full design changes—backing, ribs, rim depth,
leg profiles and top cap—not just changing plywood to lumber. Added mid-panel
screws themselves have no discrete stiffness in this perfectly bonded model.
The earlier C10 local connection result cannot be updated by scaling this table.
Real angle/screw compliance could materially alter these results.

## Numerical checks and limits

| Candidate | 60 mm nodes | 40 mm nodes | Baseline at 60 mm | Baseline at 40 mm |
| --- | ---: | ---: | ---: | ---: |
| 2×10 | 65,272 | 130,735 | 0.54565 | 0.54483 |
| 2×12 | 67,836 | 134,733 | 0.38605 | 0.38900 |

Baseline displacement changes by about 0.15% for 2×10 and 0.76% for 2×12.
The largest change across the six cases is about 0.19% and 1.21%, respectively.
That is a numerical consistency check, not a formal convergence proof. Nearest
load nodes lie approximately 3.6–10.8 mm from their ideal hold targets and move
between meshes. The two hybrids use matching target distances at each mesh;
the reference plywood mesh differs slightly. No stress or failure convergence
is claimed, and stresses/joint forces were not published from this bulk screen.

Every accepted mesh has positive minimum element Jacobian. All cases require
five complete finite loaded-node displacement vectors, force balance within
0.1 N, and **all floor-node reactions** with moment balance within 1 N mm.
The audit reparses the actual INP load vectors and fixed support definitions,
not just the intended metadata. Printed-node reaction sums must also balance.
Moment re-audits use coordinates serialized in the INP rather than Gmsh's
pre-serialization doubles; the negligible rounding comparison tolerance does
not relax the 1 N mm equilibrium threshold.

Steel angles and fasteners are omitted from the bulk stiffness solids. Their
actual interfaces are replaced by perfectly bonded touching timber. Thus this
model cannot approve angle bends/welds, bolt bearing, screw withdrawal, end-grain
connections or relocation joints. It also omits buckling, orthotropy, load
duration, cyclic/dynamic response and unanchored lift/slip.

## Separate row-12 rigid-body stability screen

Assume 600 kg/m³ for all wood and 7850 kg/m³ for the candidate angle steel.
These are not measured masses or selected-material densities. Fasteners, holds,
LEDs and glue are omitted. The plywood reference has no angle steel; its
published approximately 188.6 kg is timber only. Candidate mass includes their
angle plates, so the distinction is explicit rather than silently comparing
different component inventories.

| Quantity | 2×10 | 2×12 |
| --- | ---: | ---: |
| Modelled wood + angle mass | 205.1 kg | 216.3 kg |
| Centre of mass, Y | 742.1 mm | 734.3 mm |
| Kicker-side extreme floor toe, Y | −198.0 mm | −236.9 mm |
| Leg-side extreme floor toe, Y | 1398.5 mm | 1398.8 mm |
| Downward + outward 0.3 kN overturning factor | 2.03 | 2.17 |
| Same case: aggregate friction coefficient required | 0.093 | 0.090 |

Both candidates have positive contact reactions and exceed the existing 1.5
**2D screening** moment target in the downward baseline and the three listed
downward sensitivities. This is not a complete standards check. Actual friction
is unknown; the reported coefficient is demand without a sliding safety factor.

**Both exploratory normal directions still produce uplift:**

| Case and negative reaction | 2×10 | 2×12 |
| --- | ---: | ---: |
| Outward/downward normal: kicker reaction | −332 N | −269 N |
| Inward/upward normal: leg reaction | −746 N | −643 N |

These failures are retained, not discarded—but the exploratory vectors are
not established governing climbing loads. Fixed-floor FEA can resist tension
that the real unanchored floor cannot. Establish a justified load envelope,
measured mass/centre of gravity and floor interface before recommending ballast
or footprint changes. This sagittal screen does not address lateral tipping,
individual foot contact, uneven floors or hold stand-off.

## Design recommendation from this comparison

Keep **2×12 as the stronger candidate for further development of stiffness**,
not a strength-approved selection. The present 2×10 loses substantially more
stiffness without delivering a lighter-than-reference complete model under
these assumptions. The new backing and steel offset the narrower rims' savings.

Neither candidate is automatically simpler: each currently has 45 timber parts,
20 custom steel angles, 88 bolts and 132 screws. Before adoption, reduce or
standardize the connection hardware where the load path permits, select
traceable fasteners/materials, and resolve end-grain connections. Compare cost,
cuts, laminated stock, handling and assembly effort as well as displacement.
Next structural work should resolve real connection behavior and the load basis;
another perfectly bonded rerun alone will not settle those questions.

## Reproduce and audit

```bash
uv run python -m fea.prepare_hybrid_frame
docker run --rm --user "$(id -u):$(id -g)" -e OMP_NUM_THREADS=2 \
  -v "$PWD:/work" mini-moonboard-fea:box-v1 \
  python3 fea/solve_box_frame.py --candidate 2x12 --size 60 --audited
# Repeat for --size 40 and for --candidate 2x10 at both sizes.
uv run python -m fea.record_hybrid_results
uv run pytest tests/test_hybrid_results.py
```

Do not regenerate frozen input geometry while its solves are running. Full raw
INP/FRD/log files stay under ignored `fea/generated/hybrid/<candidate>/`.
The [published results](../fea/results/hybrid/) contain all four DAT files,
summaries, source/INP/DAT hashes and the support/load-node coordinates needed
to independently recheck force and moment balance without the large meshes.
Audit-context hashes identify the re-audit scripts, not immutable execution
provenance. Stability records are separate from the incremental stiffness cases.
