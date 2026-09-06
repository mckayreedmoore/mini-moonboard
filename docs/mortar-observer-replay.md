# Mortar observer arithmetic and accepted-state replay

`fea.mortar_observer_replay` consumes the exact event schema emitted by
`fea/mortar_observer/patch.py` and a matching CalculiX `.sta` file. It launches
no solver and changes no archived result or acceptance gate:

```sh
uv run python -m fea.mortar_observer_replay observed.log observed.sta
uv run pytest tests/test_mortar_observer_replay.py tests/test_mortar_linear_law.py
```

The tests cover synthetic protocol mutations and two frozen instrumented cube
logs from the [observer comparison](../fea/mortar_observer_build/cube-qyk279w_/report.json).
Those regressions bind the comparison, launch script, build result/manifest,
deck, context, log and STA hashes and run without Docker or a solver.
A real run must separately bind its source, patch, executable, libraries,
launched deck, terminal status and output hashes.
The standalone parser does not establish that provenance or the intended
number of steps from a deck. See the [local audit basis](mortar-local-audit-basis.md)
for the numerical-law boundary.

The 0.25-increment cube log contains 28 calls and 8 accepted increments
(72 eligible accepted-node observations); the 0.125 log contains 45 calls and
16 accepted increments (144 observations). Neither has an accepted forced
override. The largest absolute accepted normal residual is approximately
`2.602085e-9` in both. This is a frozen arithmetic result, not an adopted
local-law tolerance or qualification of the complete frame.

## Bounded supported scope

The stream must start at step 1, increment 1, attempt 1, iteration 1 and end
with a completed accepted step. Only static mechanical `nmethod=1`, implicit
`iexpl=0/1`, `ithermal=0/1`, `uncoupled=0`, ordinary `mortar=2` and
`iflagdualquad=2` are supported. Normal and tangent regularization must both
be mode 1. Frictionless arithmetic follows the source's separate branch.
Contact inventory must remain fixed, with nonempty contact pairs and unique
physical slave nodes; overlapping contact ties and remeshing are unsupported.
Thermal/network, uncoupled thermal, dynamic, restart and other mortar paths
fail closed instead of borrowing a preceding contact observation.

Each call must contain the ordered sequence BEGIN, INVENTORY, pair/raw/sparse
records, all LAW records, all POST_RAW_AFTER_ACTIVE_LOOP records, both override
summaries, RETURN, PRE_CHECK and POST_CHECK. Counts, identities, sparse column
entry sequences, source/destination coverage and complete node phases are
checked. All fields have an exact schema and finite numeric types; duplicate
JSON keys, events, sparse entries and nodes are rejected. Ordinary solver
stdout is ignored, but malformed observer-prefixed lines are rejected.

Acceptance is derived from the convergence transition: `icntrl=1`,
`icutb=0`, and `theta` advancing by the attempted `dtheta`. Initial or
continuing `icutb=0` is not acceptance. Retry attempts retain their increment,
increase cutback count and restart iteration 1; continuation increments the
iteration; accepted increments advance the increment number. Step transitions
require completion of the preceding step. The source's `1e-6` normalized-step
termination condition is used only for that control-flow check.

Every terminal decision matches a `.sta` row by step, increment, **pre-check
cutback count plus one**, iteration and time. Accepted rows refer to endpoint
time; `U` rows refer to increment-start time. Matching uses the half-last-digit
representation bound of the printed STA tokens. Success resets the cutback
count, so using its post-check value to identify the accepted attempt would
mislabel retries. Missing, extra or mismatched STA rows invalidate the replay.

## What is reconstructed

For every observed slave node, the parser independently accumulates sparse
`DDTIL * lambda_raw` and `DDTIL * lambda_start` in exported column order.
It projects those weighted vectors onto the exported frozen normal and two
tangents, checks an orthonormal basis for eligible nodes, and compares the
resulting `Ln`, `Lt` and `Lt_start` with the source LAW observation. Sparse
`column_slot` records the emitting column; `source_slot` retains the solver's
actual inverse-node mapping. Off-diagonal terms are retained.

The committed `fea.mortar_linear_law.residuals` then recomputes normal/tangent
regularization, the algorithmic bound and signed residuals and compares them
with the source's values **before** absolute-value conversion and active-set
updates. The maximum absolute residuals and post-update activity counters are
also checked against the source summaries. Post-update state is reported
separately; it cannot replace the pre-update branch used for residual replay.

Arithmetic comparisons use relative `1e-10` and absolute `1e-12` bounds to
detect inconsistent serialized calculations. These are not contact-law,
solver-convergence or physical acceptance tolerances. A replay mismatch raises
an error; a successful arithmetic comparison is never reported as a local-law
pass.

Excluded states `-3/-2/-1` and nodes with no active mechanical DOFs remain
explicitly ineligible. Accepted calls whose iteration exceeded the source's
`ndiverg` threshold retain a forced-override marker and the pre-override flag:
`stressmortar.c` can clear that flag despite excessive residuals. Thus an
accepted call can correctly contain nonzero or large law residuals.

The parser does **not** independently reconstruct gap/displacement kinematics,
segmentation, the origin of the frozen bases or matrices, increment-start
history from a complete solver state, coupling forces, or equilibrium. It
does not prove a continuous contact law, material resistance, leg sharing,
floor friction, buckling or a climber rating. Its status remains
**OBSERVER ARITHMETIC/COVERAGE REPLAY ONLY; WEAK LAW AND PHYSICAL CAPACITY NOT VALIDATED**.
