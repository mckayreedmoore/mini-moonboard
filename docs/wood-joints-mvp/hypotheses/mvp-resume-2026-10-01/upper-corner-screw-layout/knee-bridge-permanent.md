# Knee-bridge permanent comparison: executed STOP

[knee-bridge-permanent.py](knee-bridge-permanent.py) exposes
`run(output: Path) -> dict` and `source_pins() -> dict[Path, str]`.
The output must be a fresh immediate child of
`rawlocal/knee-bridge-permanent/`. The API imports no mechanics or CAD until
`run`; the parent owns readiness, serialized execution and final validation.
The parent executed producer `3eddb384…` in
`rawlocal/knee-bridge-permanent/attempt01`; it exited 1 with
`STOP_PERMANENT_COMPARISON`. Zero gap passed the conditional coupled laws;
nominal gap stopped on `normal active-set cycle`. The comparison is incomplete
and transfers no member or joint acceptance.

The parent reported and resolved an integrity incident in the frozen
`rawlocal/knee-bridge-washer/attempt02/receipt.json`, whose expected SHA-256 is
`041067657335395f4b1723a237e11574a0ed0b3efcba4e95f32e25db77d3630f`.
That receipt is absent from both owned preparation pin maps and was not read
or written by this implementation. The parent confirmed byte-exact restoration
from a verified archive and preserved the damaged bytes separately at
`/tmp/mini-moonboard-washer-receipt-corruption-preserved-1791047411.bin`.
The parent also confirmed the scalar attempt02's 500 pins/two outputs and
stability's 392 pins/three outputs match. The consumption hold is lifted;
original pins remain unchanged and no mechanics rerun is needed for this
incident. The later permanent comparison STOP below is a separate numerical
result and does not identify another source-integrity incident.

## Saved execution result and publication receipt

The parent attempted exactly the two declared states with the pinned runtime.
The saved state outcomes are:

| State | Saved outcome | Numerical evidence |
| --- | --- | --- |
| Zero gap | `PASS_CONDITIONAL_COUPLED_LAWS` | Force residual 2.4016344468691386e-12 N; moment residual 1.3902021894773853e-9 Nmm; finite-law error 2.484119028256515e-7 N; rigid rank 300 |
| Nominal gap | `STOP_UNACCEPTED_STATE` | `ValueError: normal active-set cycle`; final audit is null |

The exact nominal-state stop is the repeated-normal-active-set guard in
`right_corner_clearance.solve()`: at the beginning of an iteration, the tuple
of active unilateral normal rows was already present in `seen`. The helper
raises before solving that repeated branch and before constructing its final
equilibrium, connector-law, floor-law, domain and rank audit. This is a branch
cycle of the existing numerical method, not a recorded physical strength or
stability failure. The saved packet does not retain the nominal branch
history, repeated tuple or iteration number, so it supplies no exact repeated
row identities or further cause. No rerun or new diagnostic method was used
to infer those missing details.

The preserved dead-load `solve_state()` adapter only handles the later
`unrestrained rigid coordinate` exception at nominal gap with its existing
bounded-seating certificate. It does not handle an active-set cycle. That
certificate was therefore not computed for the failed state. The outer
producer saved the exception and last available nominal `f`, `q`, `a`, then
raised `STOP: one or both declared frame states stopped; no member acceptance
transferred` because only one accepted response existed.

`response.npz` contains the three zero-gap arrays
`permanent-only_zero_raw_force_n`, `permanent-only_zero_lumped_q_mm` and
`permanent-only_zero_rigid_coordinates`, plus the unaccepted nominal arrays
`permanent-only_gap_unaccepted_f`, `permanent-only_gap_unaccepted_q` and
`permanent-only_gap_unaccepted_a`. The failed nominal `f` is in the lumped
solver coordinates; it is not an accepted raw connector force vector.
No `comparison.json`, member actions, body balances, intact strength ratios,
adapted geometry, section coverage, opening register or exception witnesses
were produced. The six-bore geometry adapter and member arithmetic were never
reached. Existing rated-case or historical permanent passes do not fill this
missing permanent-state result.

The executed snapshot is byte-identical to the maintained producer. All four
artifact hashes recorded in `stop.json` match the preserved files; the STOP
record itself is also frozen below. Its source map records 220 bindings.
The producer authenticated sources before execution; its post-comparison
authentication was not reached. This inspection authenticated the saved
output bytes, not a new mechanics result.

| Artifact under `rawlocal/knee-bridge-permanent/attempt01/` | Bytes | SHA-256 |
| --- | ---: | --- |
| `stop.json` | 68,081 | `c3e568102c6cc921e09e526955f55860c01aa7be3e8f9b08b7ba8724f4918b7e` |
| `response.npz` | 44,470 | `df426ebdf6a8e6fe6ba9e7dbd36cbcf06aea3296a587bd96707c73b0e08bcaa1` |
| `inputs.json` | 45,302 | `0fd81c9f7c6ddcc4cabfaebb4da61a2bc10c3ba74d741a47c361dc5f2ab8da2f` |
| `producer.py.snapshot` | 30,563 | `3eddb384ac05820203bed59369ee270661b643bdc07e69159baec904eb5979a7` |
| `.gitignore` | 2 | `cdbcae15105d6b781e620813c79c7e868740d4e9cc53ce6f5fcbbc12387adf4b` |

Publish the maintained adapter and this note with the explicit STOP
disposition. Preserve the failed raw child as recoverable evidence. No
threshold was relaxed, source repinned, producer changed or mechanics rerun
performed during this diagnosis.

## Frozen scope

There are exactly two states: permanent gravity plus the existing proportional
25 kg equipment allowance, once, at zero and nominal clearance. Unfactored
gravity column zero of the fresh operators supplies `e`, `W` and physical `F`.
The mass is **225.19791414318078 kg** and the equipment factor is
**1.1110134616260479**. No climber gravity, horizontal hold force or hold moment
enters the load. The old permanent comparison's 224.9499553141194 kg gravity
is historical method evidence and is never the new demand source.

The no-slip floor, contact, filled-bore gross elastic compliance, material
orientation, connector laws and candidate timber restraint hypotheses remain
the recorded ones. The adapter preserves **1,888 raw rows, 88 clearance planes,
eight floor footprints and 300 rigid coordinates**. All **104 global bolts and
66 Hillman screws** remain in the simultaneous response. The unadopted proposal
has **108 bolts**, including four internal static bridge bolts with no global
connector rows. Their previous rated-state static allocations are provenance;
they are not permanent-state allocations or local compatibility evidence.

Permanent wood strength references use the existing **C_D = 0.9** for Fb,
parallel Ft/Fc and Fv. The preserved helper recomputes beam/column stability
factors. Emin, Euler references, perpendicular compression, elastic stiffness
and hardware references receive no duration factor. The shear helper evaluates
its existing 180 psi reference before its ratios receive 0.9. Strength
exceedances, domain exceptions and sensitivity exceedances remain explicit;
numerical completion does not require every comparison to pass.

## Reused functions and geometry

The adapter imports `dead-load-check.py` as a private module and calls its
`solve_state()` and `replay_members()` functions. It does not call its old
`run()` pipeline. Its own orchestration calls the pinned `simple_frame.lump_floor`
and the existing right-corner/circular/bounded clearance functions. Saved point
actions, physical F/W closure, opposite cut sides, normal checks and compatible
rectangular shear/torsion use the preserved member helpers.

Only that private module's `FRAME`, `SOURCE`, `MEMBERS`, `STABILITY` and geometry
`read` are temporarily adapted; a `finally` block restores each parameter.
The imported shared mechanics modules and their globals are never patched.
Import path and bytecode settings are restored. No pinned file is changed.

The **42 unchanged timber bodies** retain their exact saved section records.
The **two modified outer spines** use the pinned proposal geometry inputs and
six-bore STEP exports, preserving four original u bores plus two new v bores at
100 and 250 mm, radius 3.75 mm. The original member-screen descriptors still
describe four bores; they supply stock axes, outer planes, point locations and
provenance only. `proposal_records(method)` is a reusable parent API returning
the adapted geometry packet when called during serialized arithmetic.

When member replay is reached, the existing
`longitudinal-bore-geometry.validate_geometry()` validates the
six-bore recipe, and `member_screen.rectangle_at()` regenerates spine
applicability using all six intervals. Existing stations remain; new bore
centers, tangencies and flanks 0.001 mm from each tangent are added. Opening
cuts are excluded from intact rectangular resistance arithmetic, including
tangencies within the helper's existing tolerance. No old intact rectangle
qualifies a new hole. The original intact-prism stability dimensions and old
receiver restraint stations remain conditional; the four new bolts add no
brace credit.

The planned `section-coverage.json` retains every before/after signed cut with its exact
applicability or missing basis. `opening-register.json` names every source
opening, including all **12 openings across the modified spines**, and links
its two-state demand samples. Every opening resistance ratio stays null.
The planned `member-actions.npz` includes point-action arrays, complete signed cut arrays
and per-body `__cut_stations_mm` arrays. Together with `geometry.json`, these
would give the parent's opening-coverage work an exact geometry/demand interface.
That work must bind this comparison's own response and outputs; the earlier
six-case member arrays remain extraction provenance, not permanent demands.

## Pins and recorded method evidence

| Source | SHA-256 |
| --- | --- |
| Preserved dead-load functions | `ffdb2ee797000c055cd67c6e46ac80e549b4865a79346e728074625767bf213d` |
| Fresh gravity assessment, `knee-bridge-gravity/attempt01` | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| Fresh operators | `7877699053a8285b77621ca0cfcb7b09d22b19e5c20729c193e1e5c3f4840e4f` |
| Fresh frame attempt02 comparison | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` |
| Fresh frame attempt02 response | `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` |
| Six-bore geometry manifest | `254dd58d2f311553b32637b01b85b8bacbc0b474acfee667597333c501afe147` |
| Six-bore geometry inputs | `25c3a49825d898815e4311c95ea0f16be1bcf415d9983d496feb0371d157d965` |
| Integration attempt02 manifest | `1744bb616354159c06694e99fb239251578dba3a6e860da5391dae19b5d7026c` |
| Fresh member point/cut arrays | `3be032470253e872690637b09566076256374071adfe7d057ed4d329debef596` |
| Recorded permanent method evidence | `20802196776a89ea8b041832b413ef8d8613493b1bf36f89a3810807c5166e75` |

`source_pins()` authenticates the direct and recorded transitive closures,
including the exact historical bottom-helper snapshot and its already recorded
reporting-only substitution. It binds the new gravity/operator/response/geometry
artifacts separately. The frozen old permanent report supplies its recorded
floor and circular-gap known-answer results. Their identical helper hashes
support reuse of those methods within their recorded limits; they provide no
proposal acceptance. No coupon or software test is rerun.

Preparation authenticated **220 pins** in
`rawlocal/knee-bridge-permanent/sourcepin-attempt02/api-freeze.json`.
Final adapter SHA-256 is
`3eddb384ac05820203bed59369ee270661b643bdc07e69159baec904eb5979a7`.
Ruff passed; ignored output status was checked. The earlier preparation
snapshot remains preserved in `sourcepin-attempt01`; use attempt02 for the
current adapter. Neither preparation child contains mechanics results.

Runtime pins match the fresh frame: Python **3.12.3**, NumPy **2.5.2**, SciPy
**1.18.1**, OSQP **1.0.4**. A differing runtime stops before mechanics imports.
Sources are authenticated before execution and after a completed bounded
comparison; attempt01 stopped before the latter check. Output receipts include
the executed producer snapshot and generated artifact hashes.

## Parent execution and remaining gaps

Preparation is available without mechanics:

```sh
python3 -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-bridge-permanent.py \
  --sourcepin-only \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-permanent/<fresh-preparation-child>
```

The parent's executed command used the following form, with the output child
`attempt01`. It is recorded for reproduction, not an instruction to rerun:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python -B \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-bridge-permanent.py \
  --run \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-permanent/attempt01
```

The CLI acquires the existing shared analysis lock and requires its slot to be
idle. API callers own the same serialization. The two fresh frame states use
attempt02 forces only as numerical guesses. Expected recovery is 88 body/state
balances, intact comparisons for the 42 unchanged bodies and applicable samples
on both modified spines, all signed cuts, all non-applicable sections, and full
exception witnesses. A numerical state failure remains unaccepted and is saved;
the other declared state is still attempted. An incomplete response stops
member replay and preserves both state records. No retry or additional load
variant is introduced.

The immediate remaining gap is an accepted nominal permanent response and
the resulting two-state member replay. The saved cycle does not establish how
to obtain that response; further method work is outside this handback.
Other remaining gaps are finite opening and
profile resistance, bore concentrations and ligament transfer; permanent-state
allocation and compatibility of the four internal bridge bolts; actual
six-bore elastic stiffness; and complete member/joint/hardware qualification.
Strict frame stability belongs to the parent's separate `frame-stability.py`;
whole-model disposition belongs to its register. Bounded nonunique seating
is not strict stability, and a completed conditional comparison does not
select the proposal or authorize fabrication or climbing.

The two adapter files stay active as the maintained method and STOP
disposition. Preparation snapshots and the failed attempt01 remain in their
ignored owned children; no raw run has been pruned or archived. The parent
performed the two frame attempts; no native or CAD run occurred. This worker
used saved evidence and output hashing only for the execution diagnosis. No
software tests, review, staging or commit were performed by this worker.
