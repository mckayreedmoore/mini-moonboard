# Logging-only mortar observer patch

`python3 fea/mortar_observer/patch.py SOURCE_DIRECTORY NEW_DIRECTORY`
validates both original files before writing patched copies and a hash manifest.
The destination must not exist. No original source, image, binary or evidence is
updated. This is a patch, not a verified solver or a contact-admissibility result.

The source is official [CalculiX 2.21](https://www.dhondt.de/ccx_2.21.src.tar.bz2),
archive SHA256 `52a20ef7216c6e2de75eae460539915640e3140ec4a2f631a9301e01eda605ad`.
`patch.py` binds the two exact source hashes. The compressed/base64 fixture
contains those unchanged upstream files with their original GPL notices, for
hermetic tests; it is not a modified solver distribution. It is a tar of only
`stressmortar.c` and `nonlingeo.c`, gzip-compressed and base64-encoded. Decode
base64 and open as tar.gz to recover the exact original bytes. The accompanying
`COPYING` provides GNU GPL version 2; upstream's retained notices specify
version 2 or any later version. No copyright notices were removed.

## Record contract

Each stdout line starts `MORTAR_OBSERVER ` followed by one JSON object. Every
record has `kind` and process-monotonic `call_id`. Doubles use `%.17g`, source
integers use `ITGFORMAT`; call IDs use C long. Nonfinite printf tokens are not
JSON and must reject the stream. JSON object fields are defined directly in
`patch.py`; no runtime library or extra solver call is introduced.

- `BEGIN`: caller context just before stressmortar. `step`, `inc`, `cutback`,
  `iteration`, `time`, `dtime`, `ttime`, `tper`, `theta`, `dtheta`, `icntrl`,
  `nmethod`, `iexpl`, `ithermal`, `uncoupled`, `mortar`, `iflagdualquad`.
- `INVENTORY`: C-tie `pair_count`, `slave_count`; `PAIR`: zero-based `pair`,
  inclusive `start` and exclusive `end` slave slots. These declare coverage.
- `PRE_RAW`: `pair`, `slot`, physical `node`, pre-update `activity`,
  `lambda_raw[3]`, increment-start `lambda_start[3]`, `ddtil_count`.
- `DDTIL`: `pair`, `column_slot` (PRE_RAW count owner), `source_slot` (actual
  islavnodeinv mapping), `destination_slot`, original sparse `entry`,
  `value`. Every declared source-column entry is exported, including zeros.
- `LAW`: `pair`, `slot`, `node`, `activity`, `ndof`, frozen `normal[3]`,
  `tangents[6]` (first tangent then second), `ln`, `lt[2]`, `lt_start[2]`,
  `q`, `ut[2]`, `gn`, `gt[2]`, `b`, `constant_n`, `constant_t`, `mu`,
  `normal_mode`, `tangent_mode`, `normal_inverse_stiffness`,
  `tangent_inverse_stiffness`, `p0`, `beta`, `iwan`, signed `rn`, `rt[2]`.
- `POST_RAW_AFTER_ACTIVE_LOOP`: `pair`, `slot`, `node`, updated `activity`,
  `lambda_raw[3]`, updated `gap`. This is after **all** active-set updates, not
  the later contact-force redistribution phase.
- `SUMMARY_PRE_OVERRIDE`: `ndiverg`, `flag`, `keepset`, `max_n`, `max_t[2]`,
  `lm_t_av[2]`, `nstick`, `nslip`, `ninactive`, `nnogap`, `nolm`.
  `SUMMARY_POST_OVERRIDE`: `flag` after the iteration-count override.
- `RETURN`: stressmortar returned; **not** acceptance.
- `PRE_CHECK`, `POST_CHECK`: separately named records carrying the same context
  fields as BEGIN, on opposite sides of checkconvergence. Do not mix their
  changing iteration, cutback, time or theta values.

The supported replay scope is static mechanical `nmethod=1`, `iexpl<=1`,
`ithermal<2`, `uncoupled=0`, ordinary `mortar=2`, `iflagdualquad=2`, normal and
tangent modes 1. The logger does not change other solver paths; the reader must
reject unsupported scope. Accepted classification requires POST_CHECK
`icntrl==1`, `cutback==0` and theta advanced from PRE_CHECK. A nonzero post
cutback with `icntrl==1` is a retry, not an accepted endpoint. STA attempt is
PRE_CHECK cutback + 1. Explicit classification belongs to the strict replay
reader; the patch logs source decision fields, not a second acceptance rule.

## Observation locations and limitations

Upstream stressmortar.c 391: PRE_RAW and sparse mapping before weighted
multiplier construction and before any active-set mutation. Line 569: LAW
before signed residuals become absolute. Line 830: separate post-loop snapshot.
Line 1024: summaries bracket the forced flag override. nonlingeo.c 3084 and
3106 bracket the contact call; 3425–3440 bracket convergence checking.

Multiplying exported Ddtil by the complete pre-snapshot reconstructs the
source's weighted pre-law multipliers; the complete post-snapshot permits a
separate weighted post-update reconstruction. Neither reconstructs segmentation
or independent kinematics from geometric endpoints. Excluded and ndof-zero
nodes are exported, never silently counted as law passes. Existing arrays and
regularization outputs are observed without re-evaluating solver functions.

Tests verify exact source hashes, insertion-only reversibility, chronology,
wrong-source/reapplication rejection and CLI preservation. Local syntax-only C
checking passed with `-DARCH=Linux` and the original headers (existing upstream
string-header warnings). No observer binary or solver run is asserted here.
