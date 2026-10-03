# Upper-left service joint: motion and stiffness decision worksheet

**Finite working-model study complete. Complete joint and physical release remain HOLD.**
Reviewed cleat, four bolt axes and 33 mm pitches remain unchanged. This improves
the [previous working scenario](../upper-left-service-transfer-preflight-2026-10-01/README.md)
for `left_service_outer_upper_cleat` / `clip_horizontal_upper_left_1`;
its source files and reports are preserved. All results use **2× the same 21
signed rail/side wrench pairs** from A1-rear, A12-rear and K12-rear. Missing
frame cases and the full 47-criterion authority remain unchanged.

## Normal-motion correction

The old solver skipped singular stiffness matrices. A zero-opening contact
could then be retained as an active restraint despite carrying zero force.
In the abstract pure-tension fixture, this selected an arbitrary tilt.
The revised solver includes singular equilibria and treats inactive/touching
contacts as unilateral inequalities. It chooses the minimum norm of
`[translation, L × tilt1, L × tilt2]`, with `L` the largest in-plane lever arm,
and reports the force-bearing rank and neutral-mode information separately.
This selects a reproducible representative; it does not invent rotational
stiffness. One neutral mode includes its feasible motion interval. With more
neutral modes, uniqueness is conservatively left unestablished.

The pure-tension fixture now selects zero tilt, reports rank two and a free
tilt interval, and permits an independently checked alternate pose with the
same forces. **All 1,134 actual receiver evaluations have force-bearing rank
three.** Corrected baseline normal motions match the previous values within
`1e-12`; face spin is unchanged. This bug did **not** explain the earlier
3.6° peak interface rotation.

## Explicit ranges and comparison

- Relative clearance: **0, 0.50, 1.15 mm**. Zero and 0.50 mm are hypothetical.
  The 1.15 mm value is the modeled 7.5 mm bore minus 6.35 mm bolt, with two
  receiver radial clearances combined. Actual fit is unobserved; these are
  sensitivity inputs, not bore or drilling instructions.
- Effective timber modulus: **150, 300, 600 MPa**, all hypothetical. It changes
  face compression, seat compression and the lateral foundation law together;
  it is not a measured DF-L elastic property.
- Seat-stiffness multiplier: **0.5, 1, 2** on `E × quarter-annulus area /
  18.4658 mm`, independently of the modulus choice. Combined seat stiffness
  therefore spans 0.25–4 times baseline. Effective contact areas stay fixed.

The full Cartesian grid has **27 scenarios**, each with 42 receiver states
and 21 same-state host pairs. The table varies one input at a time from
baseline clearance 1.15 mm / modulus 300 MPa / seat multiplier 1. Peaks in a
row can occur at different states; values are rounded.

| Variation | Peak bolt tension / shear, N | Both-host movement, mm | Both-host rotation |
| --- | ---: | ---: | ---: |
| **Baseline** | **119 / 73** | **2.63** | **4.20°** |
| Clearance 0 mm | 119 / 67 | 0.71 | 0.60° |
| Clearance 0.50 mm | 119 / 72 | 1.54 | 1.82° |
| Modulus 150 MPa | 119 / 72 | 3.30 | 4.19° |
| Modulus 600 MPa | 118 / 73 | 2.29 | 4.21° |
| Seat multiplier 0.5 | 114 / 73 | 3.19 | 4.19° |
| Seat multiplier 2 | 126 / 73 | 2.35 | 4.21° |
| All 27: range of scenario peaks | 114–126 / 67–73 | 0.23–4.43 | 0.18–4.21° |

Both-host movement means **rail relative to side at the common cleat datum**.
Each local motion is shifted using `u(x) = t + theta × (x - datum)` before
subtracting the two host motions. Combining the two interface translations
without this shift gives a different quantity. Baseline peak movement occurs
at full K12-rear; peak rotation occurs at the first A1-rear saved state.
Clearance take-up permits substantial rotation even at small forces in this
no-friction/no-preload model.

## Conclusions for the next decision

**Robust within this study:** correcting the neutral-tilt defect changes no
saved baseline result. Bolt-force peaks vary modestly across the chosen grid.
At 1.15 mm clearance, both-host peak rotation stays between **4.16° and 4.21°**
despite the stiffness variations. Stiffer seats reduce movement but can
increase bolt tension. Adding strength alone does not remove clearance motion.

**Assumption dependent:** translation, normal tilt and pressure sharing depend
on uncalibrated timber/seat laws. Even at zero clearance, soft timber/seats can
give 2.53 mm movement and 2.20° rotation at the common datum. The original
bending/root and quarter-annulus material sensitivities stay approximately
0.44–0.47 and 0.49–0.55 across the grid; these remain hypothetical component
references, not complete-joint capacities. The model uses rigid members,
small-motion kinematics, zero axial slack, no friction/preload credit and
independent interface inversions. The common-datum combination is **not a
coupled frame equilibrium or compatibility calculation**, nor a load-cycle
or installation-history prediction.

**Recommended single next check: frame compatibility with clearance included.**
All three authenticated source models use `bolt_gap_factor=0`. Check whether
the preserved frame can tolerate the joint's clearance-dependent rail/side
motion and resulting load redistribution, using a declared movement criterion.
This most directly decides whether the current arrangement can remain the
working design. Do not adopt a new bore, assume the source reactions survive
changed stiffness, or enlarge the joint from this worksheet alone.

## Reproduce and verify

[comparison.json](comparison.json) retains every returned motion, normal
opening, allocated force, rank/neutral-mode result and common-datum host pair.
Every evaluation checks returned spring traction, all six receiver-wrench
components and lateral compatibility at both bolt points. Focused tests cover
the free-tilt fixture, alternate equal-force pose, contact permutation, contact
release/bearing, returned mixed-load motions, and common-datum signs/shifts.
They also check all baseline motions against the preserved previous report
and distinguish clearance spin from normal tilt.

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/upper-left-service-motion-sensitivity-2026-10-01/study.py > /tmp/upper-left-service-motion-sensitivity-replay.json
.venv/bin/python -m unittest discover -s docs/wood-joints-mvp/hypotheses/upper-left-service-motion-sensitivity-2026-10-01 -p 'test_*.py' -v
.venv/bin/ruff check docs/wood-joints-mvp/hypotheses/upper-left-service-motion-sensitivity-2026-10-01
```

Use a fresh output path if the example `/tmp` file already contains other
evidence. Final checks and completion audit are in
[parent-validation.json](parent-validation.json). No CAD, native solve,
socket redesign, commit or push is part of this finite deliverable.
