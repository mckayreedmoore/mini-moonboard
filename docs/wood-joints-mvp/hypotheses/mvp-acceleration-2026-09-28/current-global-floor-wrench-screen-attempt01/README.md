# Global floor-wrench feasibility screen

This parent-scoped screen asks whether the six recorded external wrenches
necessarily require some modeled floor normal reaction to vanish or become
negative. It uses load inputs and floor geometry only, not a solved frame,
C11 response forces, an active-contact pattern, or a physical floor test.
Its purpose is a bounded dependency check for actual corner-block demands.

## Engineering result

For each of the six cases, all 100 normal forces can be strictly positive
while aggregate vertical-force, roll and pitch balance holds. Separate signed
tangential witnesses close horizontal force and yaw. This remains true for
the recorded `split_12_5_kg_hold_mean` accessory placement (25 kg estimated
total, face-projected hold positions). The force witnesses are saved in
[floor-wrench-screen.json](floor-wrench-screen.json).

The following values are the maximum possible **minimum normal cell force**
in the declared equilibrium-only linear program. They are witness metrics,
not lower bounds on actual floor reactions or capacity values.

| Source case | Recorded zero-accessory diagnostic (N) | Recorded 25 kg mean placement (N) |
| --- | ---: | ---: |
| a12-rear | 16.170 | 18.572 |
| a12-forward | 26.737 | 29.166 |
| a12-left | 22.142 | 24.570 |
| k12-right | 22.525 | 24.927 |
| k12-rear | 16.170 | 18.572 |
| a1-rear | 26.174 | 28.603 |

Thus global wrench balance alone does **not** require floor lift-off under
these two declared scenarios. It does not establish gross stability or show
that an all-bearing compatible deformation exists. Internal member forces,
contact footprints, receiver transfer and actual floor behavior can still
prevent such a response. No internal corner demand is obtained by distributing
these aggregate witness forces to posts or bolt groups.

The engineering action this result supports is testing an all-bearing floor
branch for compatibility in the chosen frame model. Only if every actual
normal reaction, deformation/contact sign and body equilibrium check passes
may it be treated as that conditional branch. The general conditional-stick
existence/selection limitation remains; this screen does not revise the law,
select references, authorize a native/frame run, or close readiness.

## Source and method

The source-bound inputs contain 778 unique gravity sources: 192 already
assigned member/T-nut rows and 586 deferred hardware rows. All are included
once; gravity is aggregated about the global origin. Each source case's
applied force is added at its recorded physical application point. Independent
reconstruction agrees with the source case totals; A12 rear also agrees with
the frozen C11 input's load-accounting audit. No rejected C11 response is read.

Floor geometry comes from the 100 frozen input `floor_normal` ownership rows,
all at Z=0 with upward normals. The linear program maximizes t subject to
`N_i >= t >= 0`, `sum(N_i)=-Fz`, `sum(x_i*N_i)=My`, and
`sum(y_i*N_i)=-Mx`. Row moments are divided by 1000 mm only for numerical
scaling. Signed tangential forces are a least-norm solution of aggregate
X/Y/yaw balance. Their unrestricted magnitude reflects the declared analytical
no-slip assumption; it establishes no friction coefficient, resistance,
anchorage, installed pad or verified floor. No floor-friction test is added.

[SciPy HiGHS documentation](https://docs.scipy.org/doc/scipy/reference/optimize.linprog-highs.html)
supports the existing linear-program interface; runtime version is recorded
in the JSON. Solver success is checked by physical force/moment recovery.
A four-corner square known answer returns 10 N per support for a centered
40 N load, and correctly rejects a normal resultant outside that square.
The two named accessory cases are not a bound on all unknown accessory
placements or hold offsets. The zero-accessory case preserves the earlier
diagnostic input; the added mean scenario is not observed construction.

The independent standard-library checker rebinds every floor coordinate,
reconstructs all gravity/case/accessory external wrenches, checks all 12
full force/moment witnesses, and recovers each normal resultant point.
Maximum residuals are 1.52e-11 N and 1.18e-8 N·mm. Producer reproduction and
the square fixtures pass. These are input/necessary-equilibrium checks, not
local wood, bolt, washer or compatible structural-response checks.

## Documented solver options checked online

[Abaqus 2025 interaction guidance](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEITNRefMap/simaitn-c-friction.htm)
documents rough contact as preventing slip while normal contact constraints
are active, with enforcement depending on the normal/contact formulation.
It also says rough contact is intended for nonintermittent closure and warns
about reopening difficulties, particularly after significant shear develops.
Its often-associated no-separation normal behavior would change our unilateral
floor assumption. A rough-contact option therefore exists in established
software, but its documentation does not demonstrate our positive-bearing
predicate, opening/reset policy or the current cases. Abaqus was not found on
this session's PATH; that is not a license or host-wide installation audit.
No solver substitution or purchase is made.

[Code_Aster v17 contact guidance](https://code-aster.org/doc/v17/manuals/man_u/u2/u2.04.04/R_solution.html)
describes Coulomb friction and a pressure-dependent threshold. That does not
supply the unknown floor coefficient or prove an exact no-slip-with-release
implementation. The existing CalculiX 2.23 limitation remains recorded in
[the completed method comparison](../next-gate-feasibility-plan-2026-09-29.md).
These targeted source checks do not reopen general solver selection.

## Reproduction and stop

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-global-floor-wrench-screen-attempt01/produce.py --verify
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-global-floor-wrench-screen-attempt01/check_witnesses.py
```

The input hashes are checked before calculation and embedded in the output.
Stop interpreting these witnesses at aggregate equilibrium feasibility.
Actual source-case corner boundary forces, complete-corner compatibility and
applicable resistance checks remain missing. Preserve the 92 new block axes,
12 original LEG/FLOOR-RUNNER arrangements and all reviewed geometry.
