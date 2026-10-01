# Ordinary contact route review — attempt01

**Disposition: read-only diagnostic; no contact method change selected.** The
latest ordinary-joint replay fails its contact-element-count convergence gate.
Pinned CalculiX 2.23 source confirms that this is a solver gate on generated
face-to-face penalty springs, not a CEL or stdout artifact. The existing
outputs do not show the signed clearance, pressure, or force at each switching
point, so they do not establish whether the changes are negligible near-zero
classification switches or mechanically important contact changes. No
physical chatter, joint response, capacity, or acceptance is established.

This packet records only evidence inspection. It did not run CalculiX or edit
the solver source, current ordinary input/deck, contact law, geometry, queue,
or artifact manifest. Exact file pins and machine-readable gates are in
[`decision.json`](decision.json).

## What the ordinary runs establish

Attempt03 accepted only the `0.001 s` startup state. Its frozen force amplitude
was `9.8506e-6` at a 1 N reference scale; the applied field was below the
`0.01 N` force floor, with `q = 2.48346e-7 mm` and maximum loaded-node motion
`1.94976e-8 mm`. Its contact/CEL and displacement outputs are iteration
diagnostics, not a response or load-bearing pass. The result is pinned at
`ordinary-external-force-transient-attempt03/RESULTS.md`.

Attempt04 is an output-only, source-pinned diagnostic replay of the same 44
frozen inputs. Its corrected coupon passed, but the replay again accepted only
the same startup state. Of its 44 complete convergence rows, the two first
iterations fail the separate `iit > 1` prerequisite; the remaining 42 rows
include 41 count-gate failures and one accepted row at attempt03 increment 1,
iteration 18. Specifically, increment 2 has 26 rows: iteration 1 fails only
the iteration prerequisite, and iterations 2–26 fail only
`contact_change_gate_clear`. Residual, displacement, and visco predicates pass
on all 44 completed rows. All 25 increment-2 count events set the recorded
contact-change flag with `delcon = 0.001`; their relative count changes range
from `0.122619%` to `299.469885%`. The run stopped on the accepted-state /
monitor-progress watchdog, with Docker `OOMKilled=false`. A contact/CEL-only
iteration-27 tail is incomplete and excluded from convergence claims.

The attempt04 parent README is stale relative to that final replay: it reports
21 increment-2 transitions through iteration 22, while the replay result and
trace audit report 25 failing transitions through iteration 26. The four
completed keys at iterations 23–26 are replay-only relative to attempt03.
The latest terminal result and hashed trace audit control this review.

## Source interpretation and method limits

The official source archive is pinned at SHA-256
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7` and the
local 2.23 manual at
`a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`. Source
`contactpairs.f` maps `TYPE=SURFACE TO SURFACE` to `mortar=1`; for that path,
`nonlingeo.c` compares generated spring counts using `delcon`, and
`checkconvergence.c` requires the resulting contact flag to be clear. In
`gencontelem_f2f.f`, master-face matching is cached within an increment while
the current geometry supplies the signed clearance; the dynamic path excludes
positive-clearance candidates and generates springs for retained candidates.
The count represents discrete integration-point spring elements, not a count
of physical interfaces or a force/pressure measure.

Thus the count changes are real solver-state changes and expected algorithmic
possibilities when signed clearances cross the unilateral contact threshold.
Their physical significance remains unresolved because the replay does not
capture each switched point's signed gap, pressure, or force. `CEL`, `CVG`, and
the last-iteration displacement stream cannot supply that missing quantity.
Keep `delcon` and the reviewed geometry/contact law unchanged until a direct
local-state diagnostic exists.

MORTAR is not a ready drop-in for this run. The pinned manual restricts it to
`*STATIC`, while the ordinary replay uses implicit dynamics. The current
attempt03 contact fragment also makes the bottom-center-right cleat slave on
both of its adjacent wood interfaces; the two frozen slave node sets share
labels `[7, 12, 122, 123, 124, 125, 126]`. Pinned `remlagrangemult.f` removes
MORTAR multipliers at slave nodes shared among contact pairs. In the analogous
small shared-slave coupon, the MORTAR case emitted that warning, reached 201
iterations, and accepted no state. This warns against transferring the simple
MORTAR pass to the current role topology; it does not prove the cause of every
full-model failure. The simple C3D10 full-step MORTAR/penalty coupon passed
only its open/compression/reopen endpoints and does not qualify shared edges
or dynamics. The 2.23 MORTAR `CELS` energy channel is not independently
validated, so a zero print cannot satisfy a work/energy gate.

The owner audit is direct against the pinned attempt03 `mesh.json`: both slave
sets map to `W00_BOTTOM_CENTER_RIGHT_CLEAT`, while pair 1's master maps to
`W01_BASE_RAIL_BOTTOM_RIGHT` and pair 2's master maps to
`W02_BASE_PRINCIPAL_CENTER_RIGHT`. The machine-readable record pins this mesh
and reports the four set sizes and zero slave/master cross-role intersection.

Node-to-surface is not a count-gate workaround: pinned source sets its contact
flag on any generated-count change for that formulation, and the 2.23 manual
cautions against quadratic/C3D10 slave surfaces. MASSLESS is an explicit
dynamics method and does not reproduce this implicit run. This review therefore
selects no replacement formulation.

## Bounded next benchmark proposal

Use the prepared `shared_slave_penalty` known-answer case alone, in a fresh
parent-reviewed one-case freeze. Its unchanged input is
`contact-mortar-shared-edge-known-answer-attempt02/input/shared_slave_penalty.inp`,
SHA-256
`d7e517bca0a63fc02bbb77bae8116bc2b014b3545a5c40566e64cdaac47668e7`. It uses
the existing frictionless surface-to-surface linear penalty law
(`K = 100000 N/mm³`) on two orthogonal C3D10 interfaces with the same
shared-slave role pattern as the current wood interfaces. The 3-cube fixture
has an independent 4 N-per-axis analytical force/compliance oracle. Use the
unmodified pinned CCX 2.23 image and binary required by its `expected.json`;
do not reuse the four-case parent runner scope, overwrite the prior MORTAR
failure, change pair roles, or change contact law.

The original four-case input freeze contains the penalty deck hash, but the
attempt02 runner stopped after the first `shared_slave_mortar` failure; the
`shared_slave_penalty` case is **prepared, not executed**. A new single-case
freeze and isolated output directory are required. The recorded per-case
limits are 1 CPU, 1 GiB memory plus swap, 60 seconds, 100 MiB output, and 5 MiB
combined stdout/stderr cap. This proposal is not a solver launch or a claim of
native authorization by this review.

Pass only if the predeclared known-answer gates all hold:

- Exactly one accepted `*STATIC,DIRECT` increment at relative time 1, with no
  rejected attempt or cutback; accepted STA state matches the final CVG key.
- The two contact pairs and frozen role checks match the prepared case, with
  81-node U/RF coverage in DAT and FRD and no support/slave-node overlap.
- Each remote normal support is `4 N ± 0.041 N`. Normal compliance is
  `5e-5 mm³/N ± 5.001e-7 mm³/N`; expected outer approach is `5e-5 mm` and
  interface overlap is `1e-5 mm`.
- Normal profiles, interface gap, and face warp each remain within
  `1e-7 mm` of the frozen oracle. Transverse/auxiliary reaction and global
  force-closure norms are at most `0.041 N`; global first-moment closure is at
  most `0.041 N·mm`.
- Requested CDIS/CSTR values are finite and FRD contains at least one finite
  contact node; these are availability diagnostics, not pointwise pressure or
  force acceptance. Recompute the CVG contact-count sequence against the
  source `delcon = 0.001`, reporting all iterations and confirming the
  accepted state satisfies the source gate.

A pass qualifies only this small static shared-slave penalty fixture. It does
not explain the full transient's switching points or establish ordinary-joint
response, resistance, or acceptance. The next direct diagnosis still needs a
separately reviewed source trace of stable pair/slave-face/integration-point/
master keys, full-precision signed clearance, and spring force/energy for each
switching point on the exact frozen full-model inputs. Validate that new trace
on a known-answer open/closed/released coupon before using it on the full
model. If the proposed penalty coupon fails, retain the failure and revisit
the method/model decision without widening thresholds or inferring physical
chatter.

## Fixture status boundary

| Evidence | Status and permitted inference |
|---|---|
| Attempt04 diagnostic coupon attempt01 | Numerical parity passed but trace verifier failed because it expected contact events at first iterations. Preserved validator failure, not a mechanics failure. |
| Attempt04 diagnostic coupon attempt02 | Executed and passed source-trace alignment and baseline numerical parity. Validates the instrumentation on that coupon, not joint mechanics. |
| C3D10 full-step contact coupon | Executed and passed the simple single-interface MORTAR and penalty endpoint gates. No shared-edge or transient validation. |
| Shared-edge MORTAR coupon | Executed `shared_slave_mortar` only; 201 iterations, exit 201, zero accepted states, with shared-slave multiplier-removal warning. Remaining three cases, including `shared_slave_penalty`, were not run. |
| Shared-edge full-cap penalty-motion coupon | Its recorded attempt01 failed while reading the input deck before solution; it is not a penalty mechanics result. The later preparation was not run. |
