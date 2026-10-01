# Ordinary-joint characterization: next method decision

Date: September 27, 2026. This decision preserves the reviewed geometry,
current material/contact scenarios and free cleat. It authorizes no native run
or change to a frozen packet. Joint and structural acceptance remain false.

## Separate the two questions

The existing external force-history hold applies to simulation of a physical
service-demand event. It still requires simultaneous signed six-component
wrench histories at both current local ports, their datums and a time basis.
Applied whole-frame loads do not supply those local histories without a
current transfer solution.

A separately labeled numerical component characterization may instead
prescribe external-port motion and measure response. Its numerical time is
not a climbing-event history, and it cannot provide current-frame demand.
A quasi-static interpretation still needs accepted response, independent
work/energy accounting and matched rate/time-step evidence. This distinction
avoids making absent service histories a blanket prerequisite for studying
a conditional component response. It does not select a ready solver method.

## What the completed checks establish

The corrected shared-edge penalty/full-cap-motion fixture passes both static
cases. Its method evidence does not repair the earlier dynamic prescribed-MPC
failure: the pinned 2.23 replay differs from the full-inertia reference by
0.00560773 mm, while the reference omitting prescribed-motion inertia matches
to 4.967e−9 mm. The historical prescribed-MPC transient producer stays disabled.
Static map algebra and a static contact pass cannot establish dynamic inertia.

The idealized 1 mm translation witness also remains admissible without
wood-bore bearing. Do not choose another endpoint from the withdrawn 1.15 or
1.3 mm estimates. An eventual endpoint/path decision must account for actual
bore surfaces and allowed cleat, bolt and washer motion; commanded travel
alone is not observed bearing.

First resolved CFN on one receiver side is only a local contact event. A free
bolt can receive force on one side before transmitting it through its other
receiver. The response observation must distinguish that event from a
complete rail–bolt–cleat–bolt–principal transfer path, including any alternate
modeled contacts and inertia. Neither every bore being active nor any single
active pair is a substitute for signed force/moment accounting. Retain the
first-event record and subsequent accepted states; do not claim a complete
joint response from that event counter alone.

## Bounded next action

Inspect the pinned 2.23 explicit structural formulation before any further
joint launch. The official versioned HTML describes `DYNAMIC,EXPLICIT=2`,
lumped mass, one integration iteration per increment and a conditional stable
time step. This offers a specific possible route around the diagnosed implicit
contact-count iteration stall. The documentation alone does not establish
correct prescribed-MPC inertia, C3D10 mass treatment, nut-constraint behavior,
reaction/work observability or affordable time steps for this model.

The source-feasibility audit must identify those paths and limits. Only if it
finds a viable formulation should the parent freeze the smallest known-answer
check for the unresolved behavior. If source evidence rules it out, record why
and assess an independent implementation; do not launch the full joint to
find out. No new general coupon series is selected by this decision.

Use penalty contact for this question; the pinned manual restricts MORTAR to
static procedures. Do not request the explicit minimum-step option that can
scale element mass or reduce spring stiffness. No mass scaling, stiffness
scaling, cleat restraint, friction, preload, gap adjustment or custom solver
behavior patch is approved here. A static endpoint pass cannot transfer to
explicit dynamics, and an explicit accepted state cannot by itself qualify
a quasi-static response.

The absolute work floor, state-complete output contract, bearing/transfer
observations and numerical comparison gates must be frozen before a candidate
run. Those remain joint-specific work, separate from the passing small tests.

## Source snapshots

Repository paths below are relative to the evaluation-resume directory. The
HTML files are the existing local official 2.23 documentation cache; their
hashes bind the exact pages read. The prior force-history review records the
official HTML archive SHA-256 as
`ed14b31b51972d5492209a42fcd52a062e36cbc7843bcd358617cb3aee0da736`.
The public PDF fetch timed out on this check; no newer manual was substituted.

| Source | SHA-256 |
| --- | --- |
| [contact-penalty-shared-edge-motion-known-answer-attempt02/input-freeze.json](../contact-penalty-shared-edge-motion-known-answer-attempt02/input-freeze.json) | `6635c91f8d34cfb3d48964d31c985a43b4fe978866104b46bb007afc33a32bd0` |
| [contact-penalty-shared-edge-motion-known-answer-attempt02/verifier.json](../contact-penalty-shared-edge-motion-known-answer-attempt02/verifier.json) | `f15267a20d5f75672fd60719f8e211e3e3c3ae14222095ef98f1c66adfd45283` |
| [calculix-2.23-upgrade-attempt01/README.md](../calculix-2.23-upgrade-attempt01/README.md) | `754bd28fdb1530ff3233f462e73a3720fbe913b248ff5390a1f6a20de4e07456` |
| [calculix-2.23-upgrade-attempt01/cross-version-comparison.json](../calculix-2.23-upgrade-attempt01/cross-version-comparison.json) | `e061ca7f61a2235915edee732a7a9895e7685bf68b66d814f994b2595ce1bf35` |
| [ordinary-external-port-transient-attempt01/README.md](../ordinary-external-port-transient-attempt01/README.md) | `2f6eb00d8a47499f9493d2a26f13a613b413216f41e4b84144b2d09df3ec93af` |
| [ordinary-external-force-history-review-attempt01/README.md](../ordinary-external-force-history-review-attempt01/README.md) | `4846ef486b0a01e0159aa7c14580e0f6eb032884c0295177904a7f1aeea62391` |
| [ordinary-port-translation-witness-audit-attempt01/admissibility-decision.md](../ordinary-port-translation-witness-audit-attempt01/admissibility-decision.md) | `92d12b1e069aba823ce129b572532a9d9199edcf2b24cb4e5b132da6400bfaf0` |
| Official 2.23 HTML `node180.html` | `b4766a18f82f1ed1d5aa9846366626476fa81c1d6104869aa415b16d3399140c` |
| Official 2.23 HTML `node273.html` | `c36c738d851edf257e10a428e9fffe8d8a01166536311dadb5fa07ae7d4a73b8` |

## Source audit and selected small check

The source audit identifies a constraint-mass concern before any current-joint
explicit run. `e_c3d.f` first lumps C3D10 element mass; `mafillsm.f` then
transforms mass through MPC elimination, including off-diagonal terms. The
ordinary explicit acceleration branch in `nonlingeo.c` divides the residual
by the mass diagonal. The reviewed joint's nut fits have physical dependent
nodes, so switching to physical force ports would not remove this question.
The subsequent native known answer now observes the predicted discrepancy.

The selected [single-tetrahedron check](../explicit-c3d10-mpc-known-answer-attempt01/)
compares direct physical coordinates with an invertible homogeneous-MPC
coordinate representation of the same physical system. Both receive identical
constant nodal forces proportional to the documented lumped masses. The
independent full-mass calculation gives uniform acceleration in both cases;
the diagonal-only calculation predicts a different initial acceleration in
the mapped case. This isolates the constraint-mass behavior without contact,
prescribed acceleration, or a joint-scale solve. Preparation and independent
review preceded parent freezing and serialized execution. The
[result](../explicit-c3d10-mpc-known-answer-attempt01/RESULTS.md) is direct PASS
and physical-dependent mapped FAIL: both complete all 100 increments, but
mapped physical motion differs substantially from uniform acceleration.
No scaling or native execution error explains the difference.

The fixture uses a freely selected numerical material and mass normalization;
it represents neither timber nor hardware. Its result cannot qualify contact,
the actual nut fit, a complete joint, or a quasi-static interpretation. No
current-joint explicit run is selected. The completed [actual nut-chain review](../explicit-current-coupling-feasibility-attempt01/README.md)
rules out controller-first ordering under the pinned explicit mixed-MPC
restriction. It confirms that all 24 historical dependent controls feed
generated nonlinear rigid-body equations. The current active zero-density
nut solids also have a source-inferred stable-increment problem; this has
not been tested at runtime. Reordering alone supplies no validated explicit
route. Preserve the failed evidence and current kinematics.

The completed [observation design](../implicit-contact-switch-observability-review-attempt01/README.md)
separates generator gaps/membership from corrected trial forces on that set.
A first [coupon-only trace build](../implicit-contact-point-trace-attempt01/README.md)
passes the [matched-thread static regression](../implicit-contact-point-trace-attempt01/static-regression-attempt02/RESULTS.md),
with unchanged recorded outputs and complete trace coverage. The first
[dynamic analytic coupon](../implicit-contact-point-trace-attempt01/dynamic-known-answer-attempt01/RESULTS.md)
failed at re-contact under `DIRECT` stepping after 19 accepted increments.
The completed [impact review](../implicit-contact-point-trace-attempt01/dynamic-known-answer-attempt01/postrun-impact-review.md)
separates the cleared count gate from the impact-energy stop. Automatic
stepping is not assumed to fix the prescribed-motion fixture's zero recorded
external work. The separately frozen
[free-impact correction](../free-impact-known-answer-attempt02/RESULTS.md)
now passes all 70 accepted states in the original and trace executables,
including compression, rebound and separation with accounted initial energy.
The original law-ID verifier failure remains preserved; the new contract
corrects that ID without changing numerical gates. This qualifies the small
fixture, while current-joint contact remains unqualified. Verified
adjacent-iteration state joins, inactive-force/work bounds
and bounded full-joint capture remain incomplete. Existing count-only traces
cannot establish that the changes are negligible. No convergence relaxation,
solver behavior patch or heavy retry is selected.

The separate [implicit C3D10 free-coordinate fixture](../implicit-c3d10-mpc-known-answer-attempt01/RESULTS.md)
now passes direct and mapped uniform translation through 100 increments.
It verifies that mode's mass row sums and load mapping under the pinned
four-point rule. Current offsets, rotational mappings, zero-density carriers
and contact still require their own evidence.
