# Continuous-knee replay

The maintained knee producers accept the frozen four-screw physical operators
and saved bounded nominal-gap forces. The parent executed both prepared
commands and authenticated the resulting receipts. No STEP operation, CAD
rebuild, native solve, frame solve, tests or review workflow was run.

The three-member screen covers 24 bolt cases, 48 planes and twelve groups.
Its preserved summed-endpoint scenario peaks at 1.317816 with the lower
45 ksi steel hypothesis (seven states exceed one) and 0.922843 with the
conditional 92 ksi hypothesis (none exceed one), A12-left,
`knee_outer_left_side_1`. These scenarios do not establish a normative
asymmetric-bolt capacity or actual delivered steel resistance.

The separate affine bearing construction covers 24 bolt fields and 96
endpoint witnesses. Maximum nominal wood-bearing ratio is 0.357992 and
the same-state steel envelope is 0.592947. All endpoint nominal bounds
are met by the static constructions. They do not prove common-bolt
displacement/contact compatibility.

| Completed artifact relative to the resume packet | SHA-256 |
| --- | --- |
| `three-member-screen-attempt02/four-screw250/screen.json` | `ccd5b3bef3ff48a2468b47cc73da984f2a9ec7421e624bce3929032107ca17ba` |
| `three-member-screen-attempt02/four-screw250/source-pins.json` | `16a8f1972b99f18d57940af70b4aebd1505020d138fc598f294f1c4ea1edaa4b` |
| `knee-bearing-attempt02/checks.json` | `b56cc77e8a088f5cf7c1b6a84d8b8844cdfe335ecd2d2da68d6da138f0f2facb` |

All 156 three-member and 166 bearing source pins and their generated output
pins matched after execution. Historical packets remain untouched.

## Fresh common-shaft placement

The parent also replayed [knee_bore_fit.py](../knee_bore_fit.py) against both
saved gap states, using the same authenticated operator/response/metadata
binding. All 96 straight-shaft witnesses were found. Minimum conservative
radial margin is 0.435895 mm for the total-interface-motion fits, and
0.002082 mm for saved rigid components considered alone. Maximum scalar
projection residual is 0.007000 mm. The small rigid-only margin is not an
actual fit tolerance; neither representative-pose calculation supplies a
full bore-deformation field, a motion envelope or loaded bore-wall reactions.
The four source zero-clearance laws remain unchanged.

`../knee-bore-fit-attempt03/fit.json` SHA-256:
`d4c8f42e2103082c2e11f29c21b99bd8d1f65e59a6570417b86401a5683af49e`.
Producer/snapshot SHA-256:
`8993b3e5bc89d516841f644c34755ccc56642facd40e119a284d85b4fe30e252`.
All 141 source pins match. The existing attempt 02 was preserved; the parent
used fresh attempt 03 after the CLI refused that occupied destination.

## Inputs and binding

`three_member_screen.main(clearance, output, *, frame_dir=FRAME,
metadata_seed_dir=None)` uses
`remaining_joint_screen.bind_frame_sources`. The CLI adds `--frame` and
`--metadata-seed`; historical frame, clearance and output defaults remain.
Omitting the seed keeps the historical same-directory behavior. The old
fixed hash of the remaining-screen implementation is replaced by the stable
helper's authenticated current implementation pin; old evidence is untouched.
Historical material, stack-order, profile, geometry and datum assumptions
remain in force, including the original frame-input hash for that frame.

The helper requires `operators-attempt02`, `frame-250-attempt02` and the
`../corner-frame-attempt01` metadata seed for this four-screw replay. It checks
the frozen operator outputs, comparison, response, snapshots and source
receipts, plus exactly twelve changed rows belonging to the four authorized
panel-screw axes. Bolt/contact rows and physical member nodes remain bound
to the seed geometry. Seed response bytes are hashed only for provenance;
seed force arrays and historical case acceptance are not consumed.

| Frozen input relative to this directory | SHA-256 |
| --- | --- |
| `frame-250-attempt02/comparison.json` | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| `frame-250-attempt02/response.npz` | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| `operators-attempt02/operator-assessment.json` | `1a82cd2adbfece3942bf8c90f593f1e21a150adb65db625135aadd258fd5024a` |
| `operators-attempt02/model.json` | `b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626` |
| `operators-attempt02/row-identities.json` | `cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27` |
| `operators-attempt02/operators.npz` | `c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3` |

`knee_bearing_checks.main(output, *, source_dir=SOURCE)` adds CLI `--source`,
accepting a three-member output directory or its `screen.json`. The default
remains `../three-member-screen-attempt01/all-two-receiver` with its original
screen hash enforced. Fresh sources must retain the complete six-case,
four-axis census, two declared steel scenarios, nominal gap scale and false
acceptance/release fields. Upstream pins, saved output hashes and the
three-member producer snapshot are checked before bearing arithmetic.

Both result receipts identify the physical operator and metadata seed,
comparison/response hashes and force key. The three-member receipt copies
`owner_authorized_screw_movements` from the pinned model; the bearing receipt
propagates that list and its true geometry-change flag. Bolt geometry remains
unchanged. Both retain `complete_joint_acceptance=false` and
`physical_release=false`.

## Reproduction and coverage

Run these commands sequentially from the repository root. Both reject
existing output directories. Completed targets are
`../three-member-screen-attempt02/four-screw250` and
`../knee-bearing-attempt02`; choose new attempts if either already exists.

```sh
task_packet=docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python "$task_packet/three_member_screen.py" \
  --frame "$task_packet/upper-corner-screw-layout/operators-attempt02" \
  --metadata-seed "$task_packet/corner-frame-attempt01" \
  --clearance "$task_packet/upper-corner-screw-layout/frame-250-attempt02" \
  --output "$task_packet/three-member-screen-attempt02/four-screw250"

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python "$task_packet/knee_bearing_checks.py" \
  --source "$task_packet/three-member-screen-attempt02/four-screw250" \
  --output "$task_packet/knee-bearing-attempt02"

sha256sum "$task_packet/three-member-screen-attempt02/four-screw250/screen.json" \
  "$task_packet/three-member-screen-attempt02/four-screw250/source-pins.json" \
  "$task_packet/knee-bearing-attempt02/checks.json"
```

The first producer calls its preserved `geometry()` function for descriptor
and vector arithmetic. Execution is left to the parent under the worker's
no-geometry-function restriction. The replay requires no new STEP operation,
CAD rebuild, native solve or frame solve. The second producer performs only
saved-field arithmetic. No heavy execution command is required for this
bounded replay.

Observed coverage, enforced by the producers, is six nominal-gap states
(A12-rear, A12-forward, A12-left, K12-right, K12-rear and A1-rear), four
continuous knee bolts, 24 bolt cases, 48 plane states, twelve group states,
72 receiver-wrench rows, 96 face-contact rows and 36 BG003 sampled-profile
states. Bearing replay produces 24 bolt fields and 96 endpoint witnesses
(two planes and two steel scenarios per case/bolt). Actual result hashes
and peaks are recorded above.

## Preserved law and limits

The affine bearing field, receiver force/first-moment constraints, polynomial
extrema, free-end equilibrium checks, nominal Fe/Fyb constants and spatial
steel envelope calculations are unchanged. Endpoint witnesses remain static
constructions. No common-bolt displacement/contact solution, adjusted NDS
capacity, complete convex admissible set or endpoint embedding is established.
Actual thread/runout and hardware properties, axial/lateral interaction,
washer transfer, splitting, group behavior and finished wood resistance remain
open under the existing evidence limits. The sampled finished-profile query
covers BG003 only; BG004 is not mirrored from it.

The bounded force-state contract is propagated unchanged. Representative
seating positions do not establish unique motion, strict tangent stability,
floor verification, Hillman qualification or release. Four panel moves change
the source model metadata; the knee scripts perform no new movement.

| Owned implementation relative to the resume packet | SHA-256 |
| --- | --- |
| `three_member_screen.py` | `6e62243484841f05e2b07d40d5d39d120d0b984c49f6498524e41c8c6229e486` |
| `knee_bearing_checks.py` | `df99f624b1fa6f612c3c4faddf9214230f5547f3c66268c9ef04bc43dbe2f621` |

The maintained producers and frozen four-screw inputs stay active for parent
integration. Earlier knee packets remain historical evidence. Raw outputs
stay local and ignored; no historical output was archived or pruned.
