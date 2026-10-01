# Fixed full-step contact fixture result

**PASS — this small method fixture and its fixed endpoint schedule.** Both
MORTAR and matched surface-to-surface penalty contact pass the unchanged
analytical force, displacement, interface-gap and compliance checks at opening,
compression and reopening. This does not qualify subincrement response, the
current multi-interface joint, or a physical release.

## Execution and acceptance

The two frozen inputs ran serially with the same unpatched CalculiX 2.23 image
and binary as the previous fixtures. Each completed in approximately 0.319 s,
exit zero, no OOM and no stop. Each accepts exactly three states: one increment
and one attempt in each of the three steps, with step-relative time and dt
both 1. There are no rejected attempts, cutbacks or extra CVG attempt groups.
Each increment needs three iterations: nine CVG rows per case, all matched by
the complete stdout trace and final STA iteration counts. The MORTAR source's
iteration-greater-than-14 override is not reached. Independent read-only review
by `coupon_gate_strategy` recomputed all endpoint checks and confirmed the raw
STA/CVG/stdout identities, complete output hashes, toolchain/source pins and
the result tables below.

The [frozen audit](verifier.json) is `PASS_METHOD_FIXTURE`. All input and output
hashes, invoked image/binary/deck, container terminal states, DAT node coverage
and FRD output gates pass. Contact fields remain finite availability diagnostics;
acceptance does not equate transformed MORTAR contact fields with a pointwise law.

## Observed endpoints

Compression force is the magnitude of the top-face RF3 sum. Geometric gap is
the mean upper-minus-lower interface displacement, with initially coincident
faces. Every matching interface node and all 54 nodal U3 profiles are checked.

| Quantity | MORTAR | Penalty | Frozen linear reference |
| --- | ---: | ---: | ---: |
| Compression force (N) | 399.519883391 | 399.519899999 | 400 |
| Compression geometric gap (mm) | -0.000998800 | -0.000998800 | -0.001000000 |
| Pressure compliance (mm3/N) | 0.000050060086698 | 0.000050060084617 | 0.000050000000000 |
| Maximum compression U3 profile error (mm) | 0.000000600 | 0.000000600 | at most 0.000010000 |
| Compression face warp (mm) | 0 | 0 | at most 0.000010000 |
| Open/reopened geometric gap (mm) | approximately +0.001 | approximately +0.001 | +0.001 |
| Largest open/reopened support-force norm (N) | below 2.2e-9 | below 2.2e-9 | at most 0.001 |

The compression forces differ by only `0.0000166078174 N`. Both agree with the
pre-run explanatory St Venant-Kirchhoff value `399.519872024 N` and pass the
original 400 N linear-reference tolerance. The nonlinear reference did not
replace any acceptance gate. Force closure and tangential support-force gates
also pass at all three states.

## What this establishes

The exact input change from the original three-step fixture is the three
`*STATIC` schedule pairs: automatic 0.1 increments become `*STATIC,DIRECT`
with `1,1`, giving one full increment per step. Mesh, contact stiffness,
materials, constraints, target displacements, solver and analytical tolerances
are unchanged. No solver logic or source instrumentation was changed.

The earlier [three-step failure][prior] and [monotonic failure][mono] remain
valid evidence. The new result shows that the same original endpoint sequence
recovers its analytical response with this fixed full-step schedule. Together
with the [source gap-history screen][source], it supports sensitivity to
step/time-fraction handling. It does not isolate every contributing internal
operation or prove that every other contact geometry will pass. It also does
not validate the omitted intermediate states of the earlier schedules.

Before current-joint use, resolve the already recorded shared-boundary and
cross-role contact eligibility, specify matched penalty/mortar loading and
output contracts, and freeze the next bounded characterization inputs. Any
future run using partial-step increments needs its own applicable evidence;
this pass cannot be transferred to it.

## Immutable identities

| Artifact | SHA-256 |
| --- | --- |
| Input freeze | `978f8e49e79d6569dc033595ce565ce8587e36c4c5845c5615f120582634e8b0` |
| Execution | `a485410aada87d2e149b39ee77b78d3efcada065c833a0c7e91acf1a60312574` |
| Verifier | `d86d98494241657b1f8dda8ea42d747dac851c2319b914458f520008bc3a572b` |
| Passing audit | `813b7b2e2613a1aea7f3026517ca0d5fefef099164f136ce42cc5ed9314b0d14` |

[Execution](execution.json) binds every native output hash and terminal state.
[Parent review](parent-review.json) records independent input and verifier reviews.
Frozen preparation records retain their pre-run status. Candidate geometry,
selected-baseline evidence and physical observation fields are unchanged.

[prior]: ../contact-mortar-c3d10-known-answer-attempt01/RESULTS.md
[mono]: ../contact-mortar-c3d10-monotonic-attempt01/RESULTS.md
[source]: ../contact-mortar-c3d10-known-answer-attempt01/source-gap-history-screen.md
