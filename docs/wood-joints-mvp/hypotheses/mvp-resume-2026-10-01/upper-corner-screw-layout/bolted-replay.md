# Bolted component replay for the four moved panel screws

The maintained producers now accept a physical frame operator directory and a
separate case metadata seed directory. The remaining-joint replay is complete
for the six saved nominal-gap 250 lb states. The parent also completed the
top-corner geometry/component replay in its serialized slot. New component
results follow below; no complete-joint pass is claimed.

The force source is exclusively `frame-250-attempt02/response.npz`, keys
`case_id + '_gap_raw_force_n'`, with gap scale 1.0. The cases are A12-rear,
A12-forward, A12-left, K12-right, K12-rear and A1-rear. All six retain their
bounded fixed-force seating certificates and failed strict tangent/rank gates.
Neither representative positions nor component ratios establish stability,
dynamic acceptance, a climber rating or physical release.

## Binding and API

`remaining_joint_screen.bind_frame_sources(frame_dir, clearance_dir,
metadata_seed_dir=None)` authenticates the comparison, response, operator
assessment, producer snapshots and every source/output receipt. It returns
`frame_dir`, `clearance_dir`, `metadata_seed_dir`, `comparison`, `assessment`,
`metadata`, `model`, `rows`, `pins` and `force_scope`. Both producers use this
same binding. The four-screw replay additionally requires the six explicit
frozen hashes below and the specified operator, response and seed directories.

The row comparison finds exactly twelve changed rows at the four authorized
panel-screw axes. All bolt/contact rows, physical member nodes and proposed
corner bolt axes match the metadata seed. The new physical rows include the
two center screws' receiver changes to `base_rail_top`. These rows and the new
`D` and `F` operators supply the top-corner whole-body action accounting.
The original inventory remains applicable to the unchanged bolt geometry and
remaining-seat exception, and is independently pinned.

| Frozen input relative to this directory | SHA-256 |
| --- | --- |
| `frame-250-attempt02/comparison.json` | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| `frame-250-attempt02/response.npz` | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| `operators-attempt02/operator-assessment.json` | `1a82cd2adbfece3942bf8c90f593f1e21a150adb65db625135aadd258fd5024a` |
| `operators-attempt02/model.json` | `b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626` |
| `operators-attempt02/row-identities.json` | `cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27` |
| `operators-attempt02/operators.npz` | `c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3` |

The operator assessment also binds `model-inputs.json` at
`e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc`
and `B.npz` at
`d109f7db25cb05619e26560e501e7e82f3608fdbb3580f76e64f9beae916128a`.
The old `../corner-frame-attempt01/frame-results.json` is authenticated at
`34eb66332a655244a4018e1b77344985e4c145fc946cb2028405a437003d0c41`.
Its response hash is checked only as inherited seed provenance. Neither
producer opens that response array or reads its forces; old case passes do
not qualify the new vectors. Case metadata supplies order only, while the
new comparison supplies the current dead-load factor.

The callable APIs are:

```python
remaining_joint_screen.main(clearance, output, *, frame_dir=FRAME,
                            metadata_seed_dir=None)
corner_checks.run(frame_dir, clearance_dir, output, *, metadata_seed_dir=None)
```

Both CLIs accept `--frame`, `--clearance`, `--metadata-seed` and `--output`.
Omitting `--metadata-seed` retains the historical same-directory behavior.
The remaining screen's old frame, clearance and output defaults are retained;
the corner CLI's existing required arguments are retained. Existing output
directories are refused. No old result packet is overwritten.

## Completed remaining-joint arithmetic

`bolted-replay-results/remaining-attempt02` contains 92 included physical axes
(80 candidate and twelve retained), 96 lateral interfaces, 576 plane states,
1,104 outer-seat states and 46 duties. The eight top-corner axes and four
lower-left outer service-cleat axes retain their existing exclusions.
There are 384 eligible candidate single-shear states and 72 retained states.
The 72 end-grain states and 48 multi-receiver plane states retain null lateral
resistances. Separate planes of continuous bolts are not summed.

| Conditional comparison | Previous unchanged-screw screen | Four-screw replay |
| --- | ---: | ---: |
| Peak retained lateral ratio, 92 ksi scenario | 0.952117 | 0.953383 |
| Peak eligible candidate lateral ratio, 92 ksi scenario | 0.281050 | 0.277387 |
| Peak ideal full-annulus wood-pressure ratio | 0.365049 | 0.361594 |

The previous column is the recorded summary from
`../remaining-joint-screen-attempt04/all-two-receiver-92ksi/screen.json`, hash
`5b85139b2acaefd8ff74df916229766438c0caf3bc9c3a1a7b5080f8f393033a`;
it supplies no new force vector. These are separate component envelopes,
not a combined simultaneous interaction or inherited acceptance.

The new retained peak is `rail_front_bolt_left_2`, A12-forward:
V=1043.406307 N, simultaneous T=194.713830 N and conditional reference
1094.425549 N. The eligible candidate peak is
`bottom_outer/clip_horizontal_bottom_left_1/side_1`, A1-rear:
V=243.434807 N, simultaneous T=174.435184 N and reference 877.600262 N.
No eligible lateral ratio exceeds one under the retained 45, 92 or 106 ksi
component hypotheses. Product Fyb, group/edge/splitting behavior, bolt bending
and coupled axial/lateral resistance remain unqualified.

The ideal pressure peak is the `knee_outer_right_side_2` seat on
`knee_outer_right_spine`, K12-right: T=332.872962 N,
pressure=1.558191 MPa and ratio=0.361594 to the base perpendicular wood
reference. This uses a uniformly loaded full catalog-minimum annulus;
actual supported pressure and washer metal resistance remain null.
Retained washer dimensions/support remain unbound and their pressures null.

The known partial nut seat on `center_principal_right_2` retains no
full-annulus pressure or ratio, including its plane records. Its signed ties
are 8.503991, 7.188811, 9.139026, 22.952333, 9.306831 and 4.193471 N in
the case order above. The opposite seat retains only its own ideal reference.
The supported-footprint and washer-transfer work remains separate.

Runtime was Python 3.12.3, NumPy 2.5.2, SciPy 1.18.1 and CadQuery 2.8.0
from the existing repository environment. Imports of maintained helpers
load the CadQuery library, but the remaining screen performs no STEP import,
geometry operation, CAD rebuild, native solve or frame solve. No tests or
review loop were run.

Attempt 02 corrects the revision's geometry-change metadata to true. Its
numerical bolt and washer CSV bytes are identical to preserved attempt 01;
the producer snapshot and receipt explicitly bind the corrected metadata.

| Completed artifact in `bolted-replay-results/remaining-attempt02` | SHA-256 |
| --- | --- |
| `screen.json` | `abe988897087ad9d07f94c5def6a7427cfeb9c493a26ef50d3d13b8baac94d45` |
| `bolt-states.csv` | `8b94a882735962fd2cb48422d539b746fc20bd1483f5e48a7815f23a1d163480` |
| `washer-reference-states.csv` | `43da5dab2bc0ed8761959767aecec466a645a3832509c7162e494cc4da17f35b` |
| `source-pins.json` | `dcf262937dd26d679265f217413c71aed2f8636a4cf1575e8a4feeb86543d596` |
| `producer.py.snapshot` | `4d9ea0e03ab98ba4bc8c9e4641a85d5e54603c59cf2ab1d17385de4c16dc964f` |

## Completed top-corner replay

The parent's `corner-attempt01` completes 48 simultaneous bolt states,
sixteen saved finished grain paths with 32 shear planes, sixteen washer
seats, 30 body-balance states and 24 host-splitting states.

| Top outer cleat | Peak conditional lateral ratio | Finished-path reference ratio | Ideal washer wood-pressure ratio |
| --- | ---: | ---: | ---: |
| Left | 0.722296 | 0.142295 | 0.717681 |
| Right | 0.813949 | 0.160367 | 0.822681 |

These are distinct component envelopes; they are not added or substituted
for a coupled joint result. The finished paths use the preserved saved STEP
geometry. New screw-hole slices are separately excluded by the
[member replay](member-replay.md); these saved-path ratios do not qualify
new-hole concentration or complete splitting behavior. Washer metal stress
is a demand, not a supplied material resistance. Source gap/seating limits,
conditional Grade 5 inputs and the separate axial/lateral steel limitations
remain explicit in the output.

`corner-attempt01/component-results.json` SHA-256:
`401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6`.
Producer/snapshot SHA-256:
`177e13712575b735dfb2cd4d1314d006e3f8fc77d3cbc9b3e117609fbe561bb0`.

## End-grain and lower-service replay

The same frozen nominal-gap vectors also supply twelve end-grain bolt axes
and four lower-left outer service-cleat axes. These are separate reference
methods; end-grain axes are already included in the remaining-bolt census,
while the four service axes fill that method's explicit exclusion.

The end-grain route checks 72 signed states. Maximum individual
`V/(Ceg Z)` is 0.074412, 0.052042 and 0.048484 at the declared 45, 92 and
106 ksi steel hypotheses. At 92 ksi the governing axis is
`center_principal_header_right_2`, K12-right, V=29.886721 N and
simultaneous T=20.747985 N, against 574.275802 N. The proposed alternate
stock/grain route remains unadopted; no parallel-force-direction comparator
falls below 3.5D. This does not establish the complete placement/group check
or transfer forces to changed material orientations.

The service method checks 24 states. Its 92 ksi maximum is 0.007467569 at
`lower_side_2`, A1-rear, V=7.092263 N and simultaneous T=7.191758 N,
against 949.741839 N. Washer transfer, splitting/group behavior, actual
hardware and complete service-joint acceptance retain their recorded limits.

Fresh end-grain attempt 02 and service attempt 03 correctly report that the consumed geometry
includes the four owner-authorized panel-screw moves. Preserved attempt 01
packets had a stale false geometry-change field; their numerical force and
reference results are unchanged. Service attempt 03 also sorts the imports;
its numerical states match attempt 02. Neither replay changes geometry or solves
the frame.

| Fresh artifact, relative to the resume packet | SHA-256 |
| --- | --- |
| `end-grain-route-attempt03/four-screw-250-attempt02/route.json` | `277e7754b2c62e5a98d140de497c753a7cd0362080cef10185cc79be549f3261` |
| `end-grain-route-attempt03/four-screw-250-attempt02/six-case-signed-states.csv` | `535f48b90e660b40c2e994fdd29c4d10070560c1a382aa290f643fcc61c985c8` |
| `end-grain-route-attempt03/four-screw-250-attempt02/producer.py.snapshot` | `5b9faca5696d6c7add02e9ac6d5056363896bb2a7badb7ab7bb3fa8bfc9fe5d4` |
| `service-joint-current-attempt03/four-screw-250-attempt03/result.json` | `850a31de41efc8e710cb45660f9822852469303e0e391fb70ed325977558293c` |
| `service_joint_checks.py` | `5b50911a2bc2bc0517388323fb66814ac72141dfa74e1fcdff0fdbe5639a7492` |

The parent checked all 143 end-grain and 139 service source pins after the
runs, plus the three end-grain artifact pins. All matched.

## Reproduction

Run from the repository root. For a fresh saved-array replay, substitute a
new output child; completed attempts 01 and 02 are preserved:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/remaining_joint_screen.py \
  --frame docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/operators-attempt02 \
  --metadata-seed docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/corner-frame-attempt01 \
  --clearance docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/frame-250-attempt02 \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/bolted-replay-results/remaining-attempt03
```

The parent ran the command below during its geometry slot, with the shared
ledger idle. For reproduction choose a fresh output child. The CLI retains
its exclusive ledger lock. It imports saved STEP solids and evaluates the maintained finished
tear-out paths and sixteen washer envelopes before replaying the six new
vectors. It does not launch a native or frame solve:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/corner_checks.py \
  --frame docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/operators-attempt02 \
  --metadata-seed docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/corner-frame-attempt01 \
  --clearance docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/frame-250-attempt02 \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/bolted-replay-results/corner-attempt02
```

Observed maintained census is 48 simultaneous bolt states, sixteen finished
grain paths with 32 shear planes, sixteen washer seats, 30 body-balance states
and 24 host-splitting states. It reports conditional lateral/seat/steel
references and required washer bending stress; it establishes no washer metal
capacity, coupled bolt interaction, complete joint pass or release. The parent
recorded the actual result and hashes above after running it. The replay
worker prepared the command; the parent executed it.

The completed remaining and corner replays remain active local
evidence. Their raw children are ignored (about 1.21 MiB for the completed
remaining packet); no permanent bulk artifact or new status packet is added.
Older packets remain historical evidence, with no pruning, staging or commit.
