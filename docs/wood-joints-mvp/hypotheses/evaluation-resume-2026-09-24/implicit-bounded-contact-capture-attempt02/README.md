# Bounded 2.23 contact-capture patch — attempt 02

## Status and decision

This packet contains an additions-only CalculiX 2.23 source patch, an isolated
compiled binary, a strict offline reader, and synthetic negative-control tests.
The final source delta is built offline from the pinned archive. The packet is
not frozen, has not run CalculiX, and has not run a current-joint model. No
contact result or structural criterion is accepted here.

The engineering question for a separately parent-selected motion diagnostic is
whether the *captured in-loop contact regeneration* has a stable, complete
runtime face census and whether mapped candidate churn coincides with observed
penalty-spring resultants/energy. Such output can help distinguish harmless
mapping churn from a substantial generated-spring response. It cannot establish
an independent geometric contact census, a joint capacity, a first local
bearing event, a force-history demand, or complete work transfer.

The pre-loop `contact()` call at `nonlingeo.c` around line 1884 initializes
contact state before nonlinear iterations. It is deliberately outside this
capture lifecycle: it has no matching corrected-state/trial/convergence event
at that point, so the patch does not emit a generation record for it. The
captured call is the in-loop regeneration around line 2317, whose generation
end, corrected-state/trial summary, and convergence link share the nonlinear
iteration lifecycle. Because `gencontelem_f2f.f` is shared, its generation-end
hook is a no-op unless an in-loop capture is pending; a later seed-scan return
cannot duplicate or close the prior generation. Nothing in this sidecar
reveals the excluded pre-loop seed scan.

## What is bound

The build uses the 2.23 source archive at
`build/context/source.tar.bz2`, SHA-256
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`, and the
pinned upstream image ID recorded in
[`build/artifacts-r5/build-manifest.json`](build/artifacts-r5/build-manifest.json).
The additions-only patch is
[`build/context/capture.patch`](build/context/capture.patch), SHA-256
`1a8f0278d847b6a81b153a5ff84406de126b268e40743bebcaf469833d9e182d`; the
capture sink is `capture-sink.inc`. The r5 binary and image IDs are recorded in
`build/artifacts-r5/` and `source-pins.json`.

The patch inserts callbacks in `nonlingeo.c` and `gencontelem_f2f.f` only. It
does not assign native mechanics/contact arrays, loads, contact decisions,
solver controls, or model data. The build manifest records all 1,197 upstream
source file hashes and verifies the two changed members against the generated
addition-only delta. The upstream executables are hash-checked before and after
compilation. This is source-level nonreplacement evidence; it does not itself
prove runtime equivalence or solver qualification.

## Capture stream

Set a unique `CCX_CONTACT_CAPTURE_PATH` and bind these SHA-256 environment
values for each future process: `CCX_CAPTURE_INPUT_SHA256`,
`CCX_CAPTURE_INCLUDE_SHA256`, `CCX_CAPTURE_SOURCE_SHA256`,
`CCX_CAPTURE_PATCH_SHA256`, `CCX_CAPTURE_BINARY_SHA256`,
`CCX_CAPTURE_PAIR_SHA256`, and `CCX_CAPTURE_FACE_SHA256`. Set decimal-only
`CCX_CAPTURE_EXPECTED_TIES` and `CCX_CAPTURE_EXPECTED_FACES`. The output file is
created exclusively; a pre-existing path is an error. Missing/malformed
bindings, a mismatched run roster, an unclassified branch, allocation/write
failure, or a cap hit marks the terminal record incomplete. The executable
continues its native calculation; the parent runner must reject incomplete
capture even if the solver exits normally.

Records are UTF-8 tab-separated lines with LF endings and `%.17g` finite
numbers. The ordered records are `CCXCAP`, `RUN_BEGIN`, then for each captured
in-loop sweep: `GEN_BEGIN`, both `FACE`-census/map passes, `MAP_SUMMARY`,
`STATE_JOIN`, `GEN_END`, `STATE_CORRECTED`, `TRIAL_SUMMARY` when generated
springs exist, and `ITERATION_LINK`; `RUN_END` is last. Field order and widths
are frozen in [`capture-contract.json`](capture-contract.json).

The face census emits every roster face on both map passes, including deleted
and zero-span faces. Each pass must conserve contiguous source offsets through
the live `nintpoint`; each tie/pass must account for every point in its live
span. Candidate reasons distinguish generated, unmapped, positive-clearance,
source-state and aleatoric branches. Unknown reason 99, reserved reason 3,
or any aleatoric reason 4 fails deterministic validation. `isol` is kept as an
integer outcome: nonzero values may identify a master triangle and are not
Boolean `1`.

The point identity used for in-process duplicate detection and adjacent-state
joins is tie, face ordinal, encoded slave face, local point ordinal, and the two
slave-face coordinates. `igauss` is only a sweep-local lookup key. Adjacent
point joins are attempted only after an exact full-vector `vold`/corrected
state `memcmp`, same step/increment/attempt, and adjacent native iteration.
A changed master projection, gap, initial penetration, normal, area, penalty,
or scale is counted as remapped, not treated as a same-point force difference.
State tokens and record digests are auxiliary FNV summaries; they are not
cross-run identities or proof of equality.

For each generated old spring, the post-`results` hook aggregates
`-A*p*n` as the force on the slave, sum of absolute point-force magnitudes,
trial-gap extrema/counts, and native stored spring energy when `nener==1`.
Energy-disabled values are reported `NA`, never zero. These are aggregate
native observations; the stream has no point-level force/energy detail and does
not independently recompute `p=-K*g/kscale` or the energy law for every row.
The exact-touch coupon is prepared for a later parent-only source/output
qualification of signs and energy. It has not been run with this patch.

## Evidence limits and next review

`gencontelem_f2f.f` assigns runtime offsets after search, projection and
clipping. The stream proves conservation of the offsets that the solver created;
it cannot show that the geometric search found every physically relevant point.
Unmapped points have no finite gap and must never be interpreted as zero force.
A positive-clearance compression-only exclusion is only a source-specific
candidate bound; unknown or penetrating exclusions remain unavailable.

`STATE_JOIN` provides counts, not per-point transition records. A net resultant
can cancel on curved bore surfaces. The patch does not capture the point force
vector paired with the nodal contact correction vector, so it cannot calculate
contact correction work or a whole-model energy balance. It also cannot
attribute aggregate force/energy to the exact remapped points or produce a
moment from point locations. Separate independent clipping reconstruction
would be required to bound omitted geometric candidates.

The source routine and its caller are synchronous in the pinned source path;
the capture sink uses process-global state and is only appropriate for that
single-threaded contact-generation call path. `results()` has returned and its
worker joins occur before the post-results trial walk. Do not generalize these
thread assumptions to another hook or solver build.

Before any native use, the parent must review the patch, pair/face-roster
binding, exact input/include closure, run caps, and the analytic coupon contract.
This packet does not grant that execution or freeze.

## Offline reproduction

From this directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
bash build/run-build-r5.sh
```

The build script uses the pinned base image, `--pull=false`, and
`--network=none`; it compiles and extracts the binary but does not invoke it.
The tests compile a standalone C sink harness and exercise positive and
negative synthetic capture streams, roster/state identity, force/energy signs,
reason partitioning, face-span conservation, accepted links, byte caps, and
addition-only source policy. No command here launches CalculiX on the coupon or
joint. The copied `coupon/reference-output/` files are prior frozen upstream
2.23 evidence from the source exact-touch fixture, not output from the r5
binary.
