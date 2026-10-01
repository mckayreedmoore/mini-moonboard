# Bounded contact capture proposal

This is an offline, output-only proposal for a later parent-selected
CalculiX 2.23 diagnostic. It specifies neither a solver patch nor a run,
freeze, acceptance threshold, or joint decision. It does not authorize a
build or native execution.

The proposed engineering decision is narrow: if a future reviewed-geometry
motion diagnostic stalls on contact-set changes, determine whether the
observed changes are broad and carry resolved force/energy, or are limited to
near-zero/remapped points with small observed spring-force and spring-energy
effects. The shortest candidate input is the preserved attempt09 full-cap
motion deck, but that deck is only a candidate: its prior 2.21 static attempt
failed at the first increment, and no historical result qualifies the joint.
This is not a service-demand history, load rating, or structural acceptance.
It does not answer the separate physical external-force-history question.

The capture uses the pinned 2.23 source and the 35-pair manifest to freeze a
static ordered **face roster**. At each contact-generation sweep it reports
every face, including zero-span faces, and conserves the live `islavsurf`
offset ranges into the reported `nintpoint`. It never assumes three points
per C3D10 face. The pinned implementation starts with `mint2d=3` for a
C3D10 face, then overwrites it with the runtime offset difference; clipping
and projection can create zero or variable spans. Therefore these rows prove
internal census conservation, not an independently predicted geometric
point count. An independent point-count oracle would require a separate
same-state implementation of search, projection, clipping, and cutoffs.

MAP, UNMAPPED, and TRIAL are different source phases. Each sweep is keyed by
step, increment, cutback attempt, native iteration, and generation loop.
MAP is pre-solve; TRIAL evaluates the old generated set after the corrected
state is copied and before convergence. A same-iteration MAP/TRIAL comparison
is a transition. Adjacent-iteration comparison is allowed only when an
in-process exact coordinate-snapshot comparison proves identical geometry,
with no cutback or increment transition. Equal geometry does not imply equal
projection: a changed master face/local projection is recorded as a remap
and excluded from pointwise force, gap-change, and work comparisons. The
temporary `igauss`/spring-element indices are sweep-local; neither is a
persistent point identity.

This supersedes the earlier design's suggested independent predicted point
count and its proposed cross-sweep `gauss_index` identity. The census review
shows neither is justified: the face roster is static, spans and points are
sweep-local, and an independent geometric count requires reimplementing the
same-state search/projection/clipping path.

The machine contract defines full face/span conservation, one outcome per
runtime point, pair aggregates, bounded deterministic detail sampling,
capture end markers, and fail-closed size/overflow behavior. Pair summaries
include signed force resultants and sums of absolute point-force magnitudes,
so cancellation on curved bores stays visible. For IDs 20–27, an accepted
nonzero pair resultant can witness some bearing after a parent-frozen
resolution threshold; zero cannot prove no local bearing, and a first single
pair does not establish the complete rail/bolt/cleat/principal load path.

For the frictionless linear unilateral law, a *mapped point independently
shown to be excluded solely for positive clearance* has zero compressive
candidate force. An actual retained old-set TRIAL at positive gap remains a
signed tensile trial and must not be clamped. An unmapped point has no gap and
cannot be assigned zero force. A mapped penetrating point excluded for any
other reason also has no defensible omitted-force bound without a source-
faithful reconstruction. The contact-point census itself cannot bound
geometric candidates omitted before point generation.

If energy is enabled and the exact pressure/gap/area convention is qualified,
the capture can report generated-spring force and stored-energy aggregates;
for unchanged mappings, a same-solve pointwise spring-energy change may be
reported from pre/post constitutive gaps. That is not whole-model work or
nodal virtual work. Neither current MAP/TRIAL fields nor pair resultant
outputs provide the nodal contact-force vector dotted with the same-iteration
correction. That question requires separately validated source instrumentation
of contact nodal forces and correction vectors, or independent clipping and
force reconstruction. This proposal adds neither.

Proposed ceilings are 64 generation sweeps, 16,384 detailed rows, 128 MiB
for the compact capture stream, 16 MiB each for stdout/stderr, 4 GiB per
native output file, and 8 GiB total native output. These are hard stop limits,
not claims that the current deck fits them; the exact frozen output requests
must be size-preflighted before any run. Missing end records or any cap hit
invalidates the capture.

The validator is intentionally offline. Run:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/implicit-bounded-contact-capture-attempt01/validate_capture_contract.py
```

It verifies pinned artifact hashes and exercises synthetic conservation,
join, marker, cap, and missing-force fail-closed controls. A pass validates
only this proposal and its synthetic checks; it is not a solver, input, or
joint readiness result. Parent review must first select a specific diagnostic,
freeze its exact 2.23 input/build and output requests, and qualify the added
observables on the already-bounded analytic trace fixtures. No solver build,
native run, model edit, or canonical update is part of this packet.
