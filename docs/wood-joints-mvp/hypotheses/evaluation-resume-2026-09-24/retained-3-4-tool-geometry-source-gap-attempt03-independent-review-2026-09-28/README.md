# Independent review — retained 3/4-in wrench source search, attempt03

**Verdict: SUPPORTED_WITH_CLARIFICATION.** Attempt03 supports the bounded
conclusion that its reviewed, accessible Wera routes did not provide a
traceable exact-part full-profile model or complete dimensioned drawing for
Wera Joker part `05073287001`. It does not claim that no such model exists.
Inaccessible exact-part PDF routes, the login-gated media database, an
inaccessible Data Cockpit host, and oversized catalog PDFs remain unknown.

The exact variant is bound on Wera's [6000 Joker Imperial product page](https://www.wera.de/en/tools/6000-joker-ratcheting-combination-wrenches-imperial):
part `05073287001` is 3/4 in, with listed scalar dimensions of 246 mm overall
length, 42 mm open-end external width, 9.5 mm jaw-head thickness, 34.8 mm
ratchet external width, and 11 mm maximum ratchet-head height. These values,
the 30-degree return and 80-tooth mechanism do not specify the full exterior
profile, datum, tolerances, or engagement contours. The linked datasheet is
headed for `05073280001` (5/16 in); its family table does include the target
row, so it corroborates discrete target dimensions but is not target-cover
geometry evidence.

The generic [Wera AR page](https://www.wera.de/en/experience-wera/wera-ar/)
describes rotatable 3D product views, but does not identify a model for
`05073287001` or provide downloadable, measurable model bytes. An independent
search also surfaced an Olander distributor listing that labels the exact
part “View 3D CAD Model.” Attempt03 correctly treats that as an unqualified
lead: the reviewed record does not supply model bytes, Wera authorship,
revision, datum, units, or exact geometry provenance.

The target set reconciles to the four T08 lumber-leg reference axes
(`lumber_leg_bolt_left_1`, `lumber_leg_bolt_left_2`,
`lumber_leg_bolt_right_1`, `lumber_leg_bolt_right_2`) whose preserved Bolt
Depot `#407` reference has a 3/4-in head across flats. They remain
`NOT_RUN_SOURCE_GAP`. The other eight retained axes use `#367`/`#368` size
references and are outside this 3/4-in comparator target. Attempt02's
source-gap verifier and attempt03's local verifier both pass.

One schema wording clarification is advisable but does not change the result:
some inaccessible or oversized routes store `complete_profile_coverage:
false` while their adjacent notes say coverage is unknown or unparsed. Read
that boolean as “no complete profile was established from this retrieval,”
not as evidence that the underlying file lacks a profile. The README, route
limits, and global absence boundary otherwise make this distinction.

To resolve the four axes, obtain Wera-issued or Wera-authorized geometry
traceably bound to `05073287001`—preferably a preserved STEP/native exterior
model, or a complete manufacturer drawing—with model/drawing revision, units,
datum/orientation, and the full jaw/holding-plate/limit-stop contour, head
transitions, handle, ring end, and their relative positions. Preserve and hash
the original before considering a bounded comparison against the unchanged
four axes. This source review performed no tool selection, geometry change,
tool-motion or physical-fit check, operation clearance, solver, or Docker run.

`review-record.json` records the independent checks and SHA-256 pins.
`terminal-hashes.json` binds the review README and record.
