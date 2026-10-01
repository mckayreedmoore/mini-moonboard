# Contact-point diagnostic preparation, attempt 01

The separate CalculiX 2.23 diagnostic executable now passes its
[matched-thread static regression](static-regression-attempt02/RESULTS.md),
with an [independent postrun review](static-regression-attempt02/independent-review.md).
All required outputs and inherited events match, and the new trace covers all
1,680 active-point records. The earlier cross-thread byte-comparison failure
remains preserved in [attempt 01](static-regression-attempt01/RESULTS.md).

The [first dynamic analytic coupon](dynamic-known-answer-attempt01/RESULTS.md)
failed at re-contact after 19 accepted increments: native impact handling
requested automatic incrementation, while the deck used `DYNAMIC,DIRECT`.
Its partial trace observes the intended positive-gap old-set trial with the
expected pressure and energy, but the planned compression and reopening
endpoints were not reached. Full analytic validation remains incomplete.
The record also retains a review-only provenance discrepancy: the independent
preflight author added source hashes after parent froze the review; mechanical
inputs and code remain unchanged. The completed
[impact review](dynamic-known-answer-attempt01/postrun-impact-review.md)
distinguishes the cleared count gate from the impact-energy stop. The
prescribed-motion fixture records zero external work, so automatic stepping
is not assumed to fix it. The separately frozen
[free-impact correction](../free-impact-known-answer-attempt02/RESULTS.md)
now passes all 70 accepted states in original and trace executables, including
compression, rebound, separation and the old-set tensile trial. It checks
7,896 MAP and 5,544 TRIAL rows with no unmapped points. The
[first free-impact attempt](../free-impact-known-answer-attempt01/RESULTS.md)
retains a verifier law-ID failure; the corrected attempt changes that ID and
its synthetic control, with unchanged inputs and numerical gates.

The [independent code review](code-review.md) confirms field types, indexing
and source phases. This work supports the
[source-bound observation design](../implicit-contact-switch-observability-review-attempt01/README.md);
it does not select a current-joint replay or change convergence criteria.

The additions-only patch preserves the existing attempt04 contact-count and
convergence-gate records. It adds mapped and unmapped integration-point
records from contact generation and active-spring records from the final
corrected trial state, after any static line search and before those arrays
are freed. These are separate phases. Signed tensile trial pressure remains
visible; it is not clipped to zero. `trace-format.json` defines the exact
fields. Native `isol` can be a positive triangle index, so generated membership
means nonzero rather than exactly one. Energy is unavailable when its enabling
flag is off, even though the output placeholder is zero.

This initial executable emits all points. Its small-fixture restriction is
enforced by the parent runner and output cap, not a source-level size guard. Before a current-joint replay, the observation design still requires
verified displacement/mapping snapshots for any adjacent-iteration join,
filtered and aggregate capture with overflow detection, and any omitted-force
or correction-work reconstruction needed by the decision. None is qualified
by compilation. No interpretation of contact switching as negligible is made.

`prepare_patch.py` binds the official source archive and inherited attempt04
patch, permits only inserted source lines, and records original/modified
hashes in `patch-lock.json`. The separate `build-attempt04` pins all seven
build-context files, verifies the existing local base-image ID before and
after, applies exact patch contexts, compares the complete upstream archive
manifest, and preserves both historical executable hashes. Its image is
`sha256:f00deed9be383c1095cdc03a1556d00cf8982f54100217a05ffae079e8a3bb36`;
`/usr/local/bin/ccx-contact-point-trace-2.23` has SHA-256
`3f949f639ead34b7ca62e2226480635cc0f5dbeda14afc200dcb523cf640b203`.

Build attempt 01 failed before source compilation because Docker interpreted
a local image ID as a registry reference. Attempt 02 used the verified local
image tag and `--pull=false` and compiled, but independent review found an
integer passed to a floating-point diagnostic format without a cast. It was
not used for a native run. Attempt 03 adds an explicit double cast to that
output argument. Before native use, attempt 04 also replaced a diagnostic
Fortran implied-DO over native loop variable `k` with explicit normal-component
reads, so logging does not alter that local. All prior build inputs, records,
logs and executables remain preserved; none was used for a native run.
No solver calculation was changed.

The free-impact check qualifies the tested one-coordinate contact method and
its signed gap, pressure, resultant and spring-energy outputs. Current-joint
state joins, bounded capture and inactive-force/work reconstruction remain
unqualified. These fixture results do not qualify joint mechanics, physical
inertia-reaction output, external work, or a service-demand trajectory. Parent owns input freezing,
serialized execution and final validation.
