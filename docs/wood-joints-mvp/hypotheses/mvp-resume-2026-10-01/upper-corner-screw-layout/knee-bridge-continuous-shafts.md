# Fresh continuous knee side shafts

**Status: parent attempt02 completed with exit 0 and
`COMPLETE_FRESH_24_SHAFT_STATES_AND_96_PLACEMENTS`.** It reused all 24
independently closed same-fresh-input states, made zero new mechanical calls,
found all 96 placement witnesses and produced 96 interface fits, with zero state
copies. Attempt01's placement-validation `STOP`, suite, receipt, snapshot and
state files remain immutable. Attempt02 performed placement postprocessing;
it added no mechanics, tests, coupons, native solve, CAD, frame replay or review.

[knee-bridge-continuous-shafts.py](knee-bridge-continuous-shafts.py) exposes
`build(output, reuse_from=attempt01)`. Importing the module reads no evidence and
runs no mechanics. The continuation authenticates the same fresh input results
and regenerates only the placement diagnostics and continuation records.
The parent owns execution, source/output authentication, integration fixes and
publication. The implementation writes only a fresh immediate child of
`rawlocal/knee-bridge-continuous-shafts/`.

## Finite scope and retained geometry

The four existing continuous shafts are `knee_outer_left_side_1`,
`knee_outer_left_side_2`, `knee_outer_right_side_1` and
`knee_outer_right_side_2`. Attempt01 made one fresh local call for each of
`a12-rear`, `a12-forward`, `a12-left`, `k12-right`, `k12-rear` and `a1-rear`:
**24 nominal mechanical states**, with all 24 independent recovery closures
true. The completed continuation reused these exact same-fresh-input states;
it made zero mechanical calls and copied no state files. Earlier historical
force acceptance remains unused.

The retained helper/contract geometry specifies **6.35 mm smooth shaft
diameter**, **7.5 mm circular bores**, approximately **0.575 mm radial
clearance**, and **215.9 mm total wood grip**. The ordered bearing lengths are
38.1, 88.9 and 88.9 mm. Left receiver order is `knee_outer_left_spine`,
`base_side_left`, `knee_outer_left_inner_frame_block`; right uses the analogous
right names. The preparation gates compare the retained mechanics and placement
traces, interval endpoints, direction, receiver identities and transverse grain.
These are analytical geometry inputs, not observations of delivered hardware.

The existing 96 straight-shaft placement records remain a separate geometric
diagnostic: four shafts × six cases × two already saved gap scales (zero and
nominal) × two original motion fits. Each placement spans the same three
receivers. Both motion fits use the fresh saved response. The 96 interface-fit
records retain their original projection diagnostics. This consumes existing
poses and introduces no additional mechanical load case or solver variant.

New spine bores affect the net timber cuts handled by the knee owner. They do
not change this retained local bearing trace. The global operator remains a
filled-bore approximation; stiffness of the changed holes remains unqualified.

## Source authority

All paths below are relative to this packet unless indicated. Full pins and
consumed receipt closures are in the implementation.

| Authority | SHA-256 |
| --- | --- |
| Fresh frame `rawlocal/knee-bridge-frame/attempt02/response/comparison.json` | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` |
| Fresh frame `response.npz` in that directory | `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` |
| Fresh gravity `rawlocal/knee-bridge-gravity/attempt01/operator-assessment.json` | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| Fresh signed export `rawlocal/knee-bridge-response/attempt02/summary.json` | `da8fcfde95eda2fb6967194c1060e5b55647eeb1ea98efa25e8a9e8260294c70` |
| Fresh signed export `receipt.json` in that directory | `57163aa9f4e1ed7af338d29c4893f5614c21bd422e841532cf67feb67ac20933` |
| `rawlocal/working-joint-register/attempt03/register.json`, identities only | `c34745395481038e32c7474de1798882263de7e54a7cc494949948b4a5e3464c` |
| Retained geometry/laws `rawlocal/knee-compatible/prepare-attempt02/input-contract.json` | `f2876952e6b71d59acdbf20dacaef233444402e50bfcc6d3b9ec1967f2cad01f` |
| Historical method/reference suite `rawlocal/knee-contact-entry/suite-attempt01/suite.json` | `b707952e5ad740ad2ebc0306bce17a37e4718e88c1164cba568d9a39a6e8b79a` |
| Same-fresh-input attempt01 `rawlocal/knee-bridge-continuous-shafts/attempt01/receipt.json` | `1eba7e7047210366afe53e78d8dc6492281280ac0be6119a11e21383ea778e69` |
| Attempt01 `producer.py.snapshot` | `db24e035f4d1249030ae4a9447084f080ba1d283ff017e848668df29dba5b89d` |
| Attempt01 `suite.json`, original STOP retained | `0dcbc04ea9eb238551e11ceefca2d996789e3b71570c4a4f02266e294f73f857` |
| Attempt01 `fresh-inputs.json` | `19f292683521bbc4f4def787fffcaaf686a266631f87fc54a14d888b6920a28b` |
| Frozen continuation producer `knee-bridge-continuous-shafts.py` | `c5e45ddc8c92094879fbfdaacb7ef66f3eb06b7843eb5728c25cbae32c259e27` |

Fresh loads retain modeled mass 225.19791414318078 kg, dead factor
1.1110134616260479, a 250 lb climber with a 2× dynamic factor, signed 300 N horizontal loading
and the source's fixed 100 mm lever. The adapter checks the fresh source and
624 structural bolt / 396 screw / six nominal case census, then selects exactly
the four shaft identities and their 24 fresh allocations. Proposed internal
allocations are outside this consumer.

For each shaft, two signed lateral planes and one physical outer axial tie are
joined to the fresh operator rows by identity, receiver ownership, direction and
point. Every signed component and T must match the fresh export. Full receiver
forces and moments are recovered from fresh D at the retained common shaft
datum, including the body-datum shift and original rotational scaling. Signed
point recovery is an independent closure check; it does not replace D moments.
All three receiver wrenches and any retained numerical couple difference are
preserved. Unsupported middle axial force, torsion, unsaved transfer couples or
unbalanced boundaries stop preparation.

Historical contract/suite load metadata and hashes remain historical provenance.
The fresh contract uses explicitly named `fresh_load_sources` and
`legacy_source_receipts_geometry_and_method_only`; it copies no old boundary,
accepted historical mechanical result or force acceptance. The register supplies
identities only; its old per-state allocations and statuses are unused. Reuse is
limited to the newly authenticated attempt01 states with identical fresh frame,
gravity, signed export, retained geometry and contact-law inputs.

## Attempt01 STOP and saved pose API correction

Attempt01's original failure was `STOP: invalid fresh saved placement pose` in
`existing_placement_refresh`, after all 24 mechanical states closed. It returned
zero placement records and zero interface fits. That STOP and all its state
bytes are preserved; it is not a claim of physical interference or failure.

The actual saved array headers show **300 rigid coordinates** and **1612 lumped
q coordinates** in each of the six zero and six nominal responses. The pinned
`../simple_frame.py:lump_floor` API preserves **1588 nonfloor connector rows**
in original row-list order, then appends **three mean coordinates for each of
eight floor footprints**. The previous adapter incorrectly required q to have
only 1588 entries.

The corrected validation requires the exact 1612-entry layout and finite q,
plus the original 300-entry finite rigid vector. Knee motion fits index the
retained connector prefix, using its ordered port indices. Fit records now
expose `lumped_q_indices` alongside original `raw_rows`; raw global row numbers
are not displacement-vector indices. Floor means are outside these knee fits.
The original eight-port census, rank-six gate, projection diagnostics,
straight-shaft tilt/clearance witness, receiver geometry, laws and tolerances
are unchanged. No new case, method variant or acceptance threshold is added.

Before reuse, the continuation authenticates the pinned receipt and every
declared attempt01 output, including its suite, fresh inputs, snapshot and all
24 states. It checks the unchanged source closure, result identities, full
receiver targets, signed allocations and same-state T, plus the original
full-gradient, force and moment closure gates. It authenticates the old producer
through `producer.py.snapshot`. The new receipt pins the current live producer
and the old immutable snapshot separately; it does not install an incompatible
old hash for the revised live producer. Original attempt01 receipt metadata is
preserved unchanged.

## Retained local API and limits

The adapter authenticates and extracts only named pure definitions from
`knee-compatible.py`, `knee-contact-entry.py`, `knee-compatible-suite.py`,
`upper-right-combined-transfer.py` and `../knee_bore_fit.py`. The pinned AST
definition loader has an intentional `S102` annotation. It invokes the existing
`run_one` with the existing `evaluate`, kernel and contact-entry `solve` for the
initial mechanics path; no old
`prepare`, `main`, coupon, cached-witness or full suite pipeline is called.
The continuation extracts only the placement `witness` and never calls
`run_one`, `evaluate`, the contact-entry solver or stress postprocessing.

The original K20 wood foundation, K10000 head contact, E200000 smooth beam,
circular clearance, compression-only contact, middle receiver gauge, eight
elements per receiver, 25 beam nodes and 150-iteration budget are unchanged.
Original mixed/free/full gradient and force gates remain 1e-6 N; independent
moment recovery uses grip × 1e-6 N. Contact entry, Newton PSD checks and Armijo
selection retain their original constants. No preload, contact law tuning or
local feedback to the global frame is added.

Diagnostics use only the retained **92 ksi smooth steel hypothesis**. Each
full result keeps beam fields, stress fields at the same position, signed T,
bore reactions, outer seat tractions, accepted iterate and iteration history.
The original nominal bore Fe and mean washer wood seat references remain
diagnostics. They do not establish static endpoint resistance, adjusted joint
capacity, actual washer metal capacity or delivered hardware qualification.
Actual hardware, actual washer and native joint capacities remain `null`.
Shared knee-group compatibility, frame body-pose compatibility, actual wood,
complete joint acceptance and physical release remain unqualified.

## Parent execution and integration API

The continuation needs the existing shared NumPy environment. SciPy remains an
initial-mechanics dependency. The parent executed this exact serialized
continuation command for attempt02, which completed with exit 0:

```bash
packet=docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python "$packet/knee-bridge-continuous-shafts.py" \
  --output "$packet/rawlocal/knee-bridge-continuous-shafts/attempt02" \
  --reuse-from "$packet/rawlocal/knee-bridge-continuous-shafts/attempt01"
```

### Recorded attempt02 result

The following results and hashes were supplied by the parent. The producer
remains frozen at the hash recorded above.

| Result | Recorded value |
| --- | --- |
| Suite status | `COMPLETE_FRESH_24_SHAFT_STATES_AND_96_PLACEMENTS` |
| `all24_nominal_completed` | `true` |
| Same-fresh-input states reused / new mechanical calls / state copies | 24 / 0 / 0 |
| Placement witnesses found / records / interface fits | 96 / 96 / 96 |
| Peak same-state, same-position smooth steel proxy | 192.3687968568 MPa |
| Peak 92 ksi diagnostic index | 0.303268859834 |
| Peak case / shaft | `a12-left` / `knee_outer_left_side_1` |
| Maximum interface projection fit residual | 0.00699847963 mm |

| Attempt02 artifact | SHA-256 |
| --- | --- |
| [suite.json](rawlocal/knee-bridge-continuous-shafts/attempt02/suite.json) | `ec3b5bbc6d2c80c38bfcbe5877a4ea9ca6ac89f926f5f22fa799bfb9c76a701f` |
| [receipt.json](rawlocal/knee-bridge-continuous-shafts/attempt02/receipt.json) | `5496190db02ec1ed8fca6ced59f7538526503ab6735f946e651394ab225d1ffa` |
| [placements.json](rawlocal/knee-bridge-continuous-shafts/attempt02/placements.json) | `db20e9ae26ace0f34541af6e6a42d26e9711de8b18fbc6f062b754d947a95370` |

These are conditional local equilibrium and geometric witness results under
the retained method limits. The fit residual is a projection diagnostic, not
qualification of whole-group or frame body-pose compatibility. The smooth
steel index does not establish actual hardware or complete joint capacity.

`build(output, reuse_from=Path(attempt01))` returns the JSON object also written
as `suite.json`. The initial `build(output)` API remains available. The explicit
reuse path never falls back to new mechanics if authentication fails.

- `states[]` is keyed by `(case_id, axis_id)` in shaft/case order. Every returned
  entry includes `status`, `receiver_order`, `wrench_datum_mm`, complete
  `operator_connector_wrenches_on_receivers`, `physical_axial_tie_n`, closure
  diagnostics, fresh source hashes, and `result_path` / `result_sha256` pointing
  to its full local result in original attempt01. `single_physical_tie_n` is the
  same T. `reused_same_fresh_input_state` is true and the originating receipt
  hash is recorded; result files remain byte exact.
- `all24_nominal_completed` requires all 24 returned and independently closed
  nominal states. A completed continuation reports `counts.mechanics_calls=0`,
  `counts.same_fresh_input_states_reused=24`, `counts.source_mechanics_calls=24`
  and `counts.historical_states_reused=0`. `postprocess_only` is true and
  `mechanics_executed` is false for this continuation.
- `placement_diagnostics` reports the separate 96-record geometric census.
  `placements.json` contains the full geometric records and 96 interface fits.
  These records do not count as nominal local mechanical states. `pose_layout`
  records the exact saved q/rigid layout.
- `peak_same_state_same_position_smooth_proxy` and the per-state diagnostics
  expose finite conditional component summaries; completion establishes the
  recorded method/census only, with all acceptance boundaries preserved.
- The parent's integration reads
  `suite.status=COMPLETE_FRESH_24_SHAFT_STATES_AND_96_PLACEMENTS` and
  `all24_nominal_completed=true`. Attempt02 satisfied the full 96 placement and
  96 fit census and found every sufficient placement witness.

The continuation writes `producer.py.snapshot`, `placements.json`, `suite.json`
and `receipt.json`, plus an ignored-directory marker. It references the original
fresh-input file and states instead of duplicating those outputs. `reuse`
records the originating receipt, snapshot, suite, input hash and original STOP.
The completed receipt's `source_sha256` includes the unchanged fresh comparison
pin, current producer, old snapshot/receipt/state inputs and source closure.
Its `output_sha256` authenticates newly generated files; the parent's binder
also authenticates original state paths against their recorded hashes.

Sources are authenticated before consumption and again after execution. A source/API
gap, numerical defect, incomplete local closure or missing sufficient placement
witness produces `STOP`, retains available partial files and
`partial-debug.json`, and performs no fallback to historical forces. Normal
solver defects retain the returned accepted iterate and history. Exceptions
retain the last evaluated pose, explicitly marked as possibly a rejected trial;
nonfinite debug values are explicit tagged strings. An unlocated sufficient
line or numerical STOP does not claim physical interference or physical failure.

The frozen Python source, this MD and the ignored output folder remain active
for this packet. Attempt01 remains a required immutable input; attempt02 is the
completed continuation consumed by the parent. This result-recording handoff
changed only this MD. The parent owns working-package integration and
publication. No artifact is proposed for archival or removal.
