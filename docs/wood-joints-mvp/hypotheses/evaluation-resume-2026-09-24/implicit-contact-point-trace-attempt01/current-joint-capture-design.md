# Current-joint contact trace capture design

Date: 2026-09-27. This is a source-bound instrumentation proposal only. It
does not authorize a build, freeze, or current-joint native run, and it does
not qualify a wood joint.

## Decision and current limits

If the parent later pursues a motion-controlled diagnostic on the reviewed
geometry, the attempt09 full-cap motion deck is the candidate to evaluate:
[`port_motion_n_plus.inp`](../ordinary-port-motion-attempt09-common-map/port_motion_n_plus.inp),
SHA-256 `e94220362d6a4925dc71089b855f84daa540eb477103628291b319b4a9728def`.
This note selects no joint run or method and does not redefine or feed the
separate source-bound physical force-history question. Bind this proposed
diagnostic to its included contact fragment and ordered 35-pair manifest.
The common-map mesh is geometry-only:
116,162 nodes, 57,643 C3D10 elements, and 19 bodies. Its contact manifest
has 35 pairs: three wood interfaces, sixteen seat interfaces, eight
bolt-shank/wood-bore pairs (IDs 20–27), and eight bolt-shank/washer-bore
pairs. The manifest records 13,001 slave faces and 9,846 master faces. The
eight wood-bore pairs start open with nominal 0.575 mm radial clearance; they
are source geometry observations, not accepted bearing thresholds.

Current evidence does not qualify a joint response. Attempt09 is a pinned
2.21 static run that did not accept its first increment; it gives no accepted
motion or contact result. The trace patch's matched-thread static regression
passed output-equivalence checks, but that establishes static diagnostic
noninterference only. Its first dynamic direct-motion coupon stopped at
recontact after 19 accepted increments and did not reach the compression and
reopening endpoints.

Preserve the free-impact known-answer attempt01 as **FAIL**. Its frozen
[`verifier.json`](../free-impact-known-answer-attempt01/verifier.json),
SHA-256 `7632ca5f04e4d91feb55f1f5c6e3f92a021da97709470da7b26d0314121a11c4`,
expected law ID 1 while all 7,896 MAP rows reported ID 2. Its
[`RESULTS.md`](../free-impact-known-answer-attempt01/RESULTS.md), SHA-256
`efb4853216a5a3d3117221bf3f9ba2fb0d3fa32c23fc461d33cadd9c8092e034`,
records this frozen classification failure. Attempt02 corrected the
predeclared law ID before freeze: its
[`verifier.json`](../free-impact-known-answer-attempt02/verifier.json),
SHA-256 `9b77b85a508740c004d2f531eda0e70932c1a80207ed1c378c720774e62a6fba`,
passes the baseline, trace and comparison, with 70 accepted states in each
case. Its
[`input-freeze.json`](../free-impact-known-answer-attempt02/input-freeze.json),
SHA-256 `5efc117c64a614eb73c07a75e8f539bde3315f9b92cd9969e2dee640a890c656`,
and [`independent-postrun.md`](../free-impact-known-answer-attempt02/independent-postrun.md),
SHA-256 `e3fd5c96861da9ad8520f8ee80183d717fadd0f28814a4a96f47dfdf7f2edad6`,
bind and independently audit that result. Attempt02 passes this narrow
free-impact trace fixture only; its mechanical/work-energy/joint acceptance
and release flags remain false. Neither attempt establishes current-joint
response or capacity.

The pinned source archive used for the trace build is SHA-256
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`; the
additions-only diagnostic patch is SHA-256
`8fb9e5a88a72109a095ccb1dab650860535102f7d806f0dd6d230c23127af7ff`, and
its field contract is in [`trace-format.json`](trace-format.json), SHA-256
`4b99257628d3a27723a02be6b547dad64ac9bbfe957697d89f19d14e53321917`.
These pins describe the current prototype; they are not a qualified
current-joint executable or a freeze.

## What the existing records mean

`CCXPT_MAP` is emitted in `gencontelem_f2f.f` during contact generation,
before the nonlinear solve. It contains raw signed gap, the final
classification gap, area, penalty modulus, normal, local coordinates, and
the final `isol` decision. `native_isol != 0` means a generated spring;
`isol` is not a Boolean and may contain a positive triangle index. For a
dynamic calculation the pinned source drops positive-clearance points for
ordinary unilateral laws at `gencontelem_f2f.f:554–561`. A MAP record is not
the force state that was assembled or a corrected geometry snapshot.

`CCXPT_TRIAL` is emitted by `nonlingeo.c` after `results()` and any applicable
static line-search reevaluation. It describes the corrected state of the
springs that were already generated for that solve, before the convergence
test. It is not a trial row for every candidate point, nor a same-state
match for the MAP rows. Signed positive-gap trial pressure must be preserved:
the source law does not clamp a spring retained in the old set. The tangent
fields are raw native values, not qualified friction or slip measurements.
Spring energy is available only when `energy_enabled == 1`; the printed zero
otherwise is a placeholder.

For the source's linear overclosure law, `springforc_f2f.f:186–201, 248–253`
uses `stiff = -A*K*g/kscale`, stores signed pressure `p = -K*g/kscale`, and
stores `E = A*K*g^2/(2*kscale)` when energy is enabled. A `LINEAR`
pressure-overclosure input is represented by source law ID 2 in the pinned
path. Do not expect ID 1: the source assigns that value to exponential
overclosure. Any row with another law, unsupported pressure law, invalid
normal, missing area, or unavailable scale is outside this reconstruction.

The source order matters for joining records. In `nonlingeo.c:2317–2373`,
contact generation runs before `nonlinmpc`. `results()` runs at
`nonlingeo.c:3162–3182`; corrected `v` is copied to `vold` at line 3300;
the convergence check follows at lines 3437–3455. A cutback restores `vold`
from `vini` at lines 3531–3533. `CCXPT_TRIAL` is inserted after the corrected
copy. Therefore:

* A MAP and TRIAL with the same step, increment, attempt, iteration, and
  point key describe the two ends of that solve's contact correction. They
  are a transition, not a same-geometry pair. This join also requires the
  trial's mapped master face to agree with that MAP record; otherwise fail
  the pointwise join and report a within-iteration mapping mismatch.
* A TRIAL from iteration `i` and MAP from the next iteration `i+1` may share
  the corrected geometry only if an explicit displacement-state comparison
  proves it. The current patch contains no such comparison, so it cannot
  currently make this join.
* Equal displacement state does not guarantee equal contact projection.
  Projection/search may choose a different master face or local coordinate
  at the same geometry. Keep the displacement-state token separate from a
  mapping fingerprint. A mapping change is a remap event, not a failed
  displacement comparison and not proof of a physical gap change. Exact
  full-map fingerprint equality is not a general state-match requirement.
* Never join across a cutback/attempt, step or increment transition, accepted
  terminal state, missing point, or failed displacement-state comparison.
  There is no retroactive join for the old attempts.

## Bounded state and point accounting

Use the frozen ordered `WJCP_001`–`WJCP_035` contact-pair order as the stable
pair ID. The stable point identity should be
`(tie, slave_face_index, gauss_index, slave_face_encoded)`. Treat the mapped
master face, master local coordinates and normal as per-state mapping
attributes, not identity fields. Keep `generation_loop`, step, increment,
attempt and native iteration as row identity. The temporary contact spring
element number (`wje+1`) is useful only within one solver iteration; do not
use it as a persistent point key. Check point-key uniqueness and the
relationship between `gauss_index`, slave-face index, and encoded source
faces against a small known-answer model before relying on it.

Add a displacement-state token over the exact binary64 `vold` coordinates
of all nodes referenced by the pair's slave/master faces. Compute it at
contact-generation entry and again from the corrected `vold` immediately
after its copy at `nonlingeo.c:3300`. The smallest robust comparison is an
in-process exact comparison against a saved diagnostic snapshot; emit the
token and equality result for independent audit. Do not use a rounded
displacement print or iteration number as proof of equal geometry. The
iteration `i` MAP token should equal the preceding corrected snapshot, and a
later `i+1` MAP token can be joined to TRIAL `i` in displacement state only
when that equality and the stable slave-point identity match.

Track the per-point projection separately by a mapping fingerprint over
master face, local coordinates, normal, and mapped area. If a stable slave
point's fingerprint differs between otherwise equal-state records, classify
it as remapped. Compare its old and new mapping only as a projection change;
exclude that point from pointwise gap-change, force-difference and work
calculations. Continue pair-level census with separate unchanged/remapped
counts. Pointwise work is bounded only for unchanged mappings. If remaps are
common or carry material force/energy, mark the local bound incomplete and
require a small projection-remap known-answer check before relying on any
cross-sweep pointwise interpretation. Do not fail the physical-state match
solely because the projection changed, and do not silently treat the
different projections as the same contact point.

The current patch emits MAP or UNMAPPED only inside its point loop. In
`gencontelem_f2f.f:296–301`, `mint2d == 0` skips a slave face before the point
loop, so a missing row is otherwise ambiguous. Add per-pair/per-sweep
begin/end accounting with:

* an independently derived expected quadrature-point count from the frozen
  slave-face definitions and pinned quadrature setup;
* face-visit and point-visit counters, including explicit zero-point faces;
* exclusive mapped, unmapped, and generated counts, unique-key count and a
  deterministic key-set digest;
* a reason code for each non-generated or unmapped point, including a
  no-master mapping and a positive-gap unilateral filter; and
* a global end marker with expected and emitted totals, byte count, and
  overflow/truncation status.

Every expected candidate must land in exactly one category. A missing end
marker, count mismatch, duplicate key, unexplained `isol == 0`, unmapped
candidate, or output overflow makes the capture incomplete. UNMAPPED means
no mapped gap; it must not be converted to zero gap or zero force. Count the
`mint2d == 0` skip at face level rather than inventing a contact point.
The independent expected count must be computed from the frozen pair/mesh
input and validated against solver enumeration on a coupon, not learned from
the trace being checked.

For each completed sweep, emit compact per-pair summaries: candidate,
mapped, unmapped and generated counts; counts by signed-gap class; minimum
and maximum raw/classification gap with point keys; active-set digest;
area/K/normal/kscale range; and a count of energy-enabled trial rows. In the
trial summary also emit signed resultant, sum of absolute point-force
magnitudes, stored-energy sum, positive-gap trial count and point-key digest.
Keep values finite and separately count missing/nonfinite values. A trace
moment needs each point's physical position; the current rows do not include
it. Either accumulate moments at a source call site that has the point
coordinates or add enough qualified point-position data to reconstruct it.
Do not claim a trace moment from normals and gaps alone. Detailed point
records should be limited to status changes, near-zero gap witnesses,
extrema, and deterministic audit samples, with a fixed maximum record count.
The summary/census remains complete even when detail is capped; reaching the
cap must emit an explicit overflow status and invalidate any decision that
requires the omitted detail.

## Force and contact-correction work estimates

For a retained generated point, verify the logged trial pressure against
`p = -K*g/kscale` and, when enabled, energy against
`E = A*K*g^2/(2*kscale)`. Report each pair's vector force as sums over point
normals, alongside sums of absolute point-force magnitudes and point
energies. Add trace moments only when the actual point positions are
available as described above. The absolute sums are needed because local
bearing on curved bore pairs can cancel in a net vector. Compare these
aggregates with accepted-state pair output as a separate check, not as a
replacement for local trace coverage.

For same-iteration MAP-to-TRIAL correction transitions, a source-law spring
that remains generated and retains the same point mapping, `A`, `K`, normal
and `kscale` has exact linear stored-energy change
`DeltaE = A*K*(g_post^2 - g_pre^2)/(2*kscale)`. Here `g_pre` is the
pre-solve constitutive clearance reconstructed for the frozen method, and
`g_post` is the corrected trial gap. Do not assume `classification_gap`
equals the constitutive clearance: validate that relation for the selected
method, since the static initialization path can adjust the classifier gap
and `springforc_f2f.f:157–164` applies its own initial-penetration rule.
Also report the sum of absolute per-point `DeltaE` so opposite changes
cannot hide one another. Qualify the pressure/gap convention and this
equation on an analytic coupon before using the result. This is contact
spring energy change for that correction only; it is not whole-model work
balance or the joint's physical demand.

For a point absent from the active old set, a candidate force is not an
observed force. A separate source-law reconstruction at a verified common
state may report a **candidate** value, never add it to solver arrays. For
the pinned linear unilateral law, a mapped point known to be excluded solely
because its gap is positive has zero compressive candidate force; a retained
old-set spring at positive gap can still have a signed tensile trial force
and must be reported as such, not clamped. A mapped penetrating point that
is not generated for any other reason, or any unmapped point, has no
defensible omitted-force bound until its exclusion reason is proven. Do not
call a generated-set count change a force bound.

The current trace has no direct nodal contact-correction work output. The
pointwise energy change above is the smallest conservative diagnostic for
the frictionless linear normal spring if its assumptions pass. If the
decision specifically needs nodal virtual work, instrument the contact
element force vector at `resultsmech.f:423–440` and compute its work against
the same correction vector. `results()` executes `resultsmechmt` in worker
threads and joins them in `results.c:230–245`; any force/work accumulation
there must be thread-local and merged after the join. Do not write shared
per-point records from those workers. This more invasive extension is
unnecessary unless the source-law energy delta is insufficient, and it too
needs a known-answer check.

## Current-joint interpretation and output limits

The current pair output contract is explicitly not qualified. In pinned
2.23, `CFN` is the net normal force vector and moment for a pair about the
global origin, not an integral of positive pressure magnitude. On a curved
bore, local forces can cancel. For the eight wood-bore pairs (IDs 20–27), a
resolved nonzero accepted-state resultant can witness some bearing after a
frozen numerical threshold is set; zero does not prove no local contact or
identify the first local contact. Pair force/moment output still needs
finite-value checks. Its zero-area centroid/mean-normal diagnostics are
undefined, not force evidence. This source contract is recorded in
[`source-review.json`](../current-pair-output-contract-review-2026-09-27/source-review.json),
SHA-256 `73ed00e9a2e0643bfbbc8bc764249ef0dd3e1a35b1d23cdccf987fb3534c4eac`.

The existing T patch is unfiltered and has no current-joint output-size
guard. A separate point-map analysis observed 104,244 point rows across 35
pairs; the attempt09 2.21 static run reported an active-spring count of
188,068 at its failed first increment. These are scale indicators from
different artifacts, not a predicted 2.23 run count. At roughly 0.4 kB per
formatted row, one 104,244-row map sweep is about 42 MB; 188,068 trial rows
are about 75 MB. Repeating both for a few dozen iterations can produce
multiple gigabytes. Do not route full-point output through an unbounded
stdout capture or assume a small-coupon output cap is sufficient. Prefer
complete in-process counts/aggregates plus bounded switch detail; any
overflow, truncation, missing end marker, or runner output-limit termination
fails closed. If full rows are needed for a specific bounded diagnostic,
predeclare its size and a separate output file/cap before any freeze.

No trace result here establishes load-path adequacy, contact onset, bolt
engagement, equilibrium, material response, sensitivity, or capacity. This
proposed attempt09 scenario is a diagnostic port motion, not a
service-demand history. Any later static/transient acceptance gates and
post-bearing sequence remain parent-owned and must not be inferred from
these instrumentation summaries.

## Shortest defensible next sequence

1. Preserve attempt01's frozen failure and record attempt02 as the passing
   bounded free-impact trace fixture. Qualify the added state-token and
   projection-remap logic,
   point census, reason code, work calculation, and cap behavior on a tiny
   analytic coupon, including omitted point, unmapped point, projection
   change at equal displacement, cutback/state mismatch, duplicate key, and
   overflow rejection controls.
2. Preflight the exact attempt09 motion deck, 35-pair ordering and
   independently computed point inventory against the pinned 2.23 source.
   Confirm all pair laws/scales are supported by the reconstruction; fail
   closed on any unsupported law or unexplained filtering.
3. Parent may then review a bounded output-only diagnostic build and freeze
   the exact source, executable, deck, expected coverage, byte cap and stop
   rules before deciding whether to run. The capture must preserve reviewed
   joint geometry and all solver mechanics; this design authorizes no run.

## Evidence pins

| Artifact | SHA-256 |
| --- | --- |
| Trace patch | `8fb9e5a88a72109a095ccb1dab650860535102f7d806f0dd6d230c23127af7ff` |
| Trace field contract | `4b99257628d3a27723a02be6b547dad64ac9bbfe957697d89f19d14e53321917` |
| 2.23 source archive | `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7` |
| Current pair manifest | `50f7d8c9b85197f43732d49d13e75240fa6d5423673d28274e278829878a594d` |
| Current contact fragment | `35a4513b7877b04b0c2be053f3084d07178a148c606780d12d54388636574b24` |
| Attempt09 mesh manifest | `1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07` |
| Attempt09 motion deck | `e94220362d6a4925dc71089b855f84daa540eb477103628291b319b4a9728def` |
| Pair-output source review | `73ed00e9a2e0643bfbbc8bc764249ef0dd3e1a35b1d23cdccf987fb3534c4eac` |
| `free-impact-known-answer-attempt01/verifier.json` (frozen **FAIL**) | `7632ca5f04e4d91feb55f1f5c6e3f92a021da97709470da7b26d0314121a11c4` |
| `free-impact-known-answer-attempt01/RESULTS.md` (failure report) | `efb4853216a5a3d3117221bf3f9ba2fb0d3fa32c23fc461d33cadd9c8092e034` |
| `free-impact-known-answer-attempt02/verifier.json` (**PASS_FREE_IMPACT_KNOWN_ANSWER**) | `9b77b85a508740c004d2f531eda0e70932c1a80207ed1c378c720774e62a6fba` |
| `free-impact-known-answer-attempt02/input-freeze.json` | `5efc117c64a614eb73c07a75e8f539bde3315f9b92cd9969e2dee640a890c656` |
| `free-impact-known-answer-attempt02/independent-postrun.md` | `e3fd5c96861da9ad8520f8ee80183d717fadd0f28814a4a96f47dfdf7f2edad6` |
| Dynamic coupon attempt01 result | `f18e909ac4548a5be14c56cfac261a3f753a520b37b3b5275e4a89196faeb22f` |
