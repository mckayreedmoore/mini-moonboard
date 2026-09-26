# Current patch static-q rank disposition

**Disposition: no.** One prescribed scalar `q` plus six global rigid-body
gauges cannot establish a unique static response or joint stiffness. The
existing 114-coordinate rigid screen has rank 62 and 52 null dimensions after
the six gauges; adding the exact finite-patch `q` row raises rank by one and
leaves 51 null dimensions.

The reproducible calculation is [`rank_analysis.py`](rank_analysis.py); its
hash-pinned output is [`rank-result.json`](rank-result.json). Run it from the
repository root with:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/static-q-rank-disposition-attempt01/rank_analysis.py
```

The script verifies every source hash before calculating. It maps the
actuator's 662 physical nodal terms through the frozen mesh to the 19 rigid
bodies. That row matches the analytic relative cleat/principal translation
along local N at the named finite patch datum to `2.6e-16` relative error. The
actuator artifact is input-only and its unit force/moment distribution closes
to print precision; it is not a solved response.

| Added kinematic rows to the existing six-gauge model | Rank / 114 | Nullity |
| --- | ---: | ---: |
| None | 62 | 52 |
| One exact `q` row | 63 | 51 |
| Six relative rail/principal components | 65 | 49 |
| Six relative components plus `q` | 66 | 48 |

These exact nullities use a relative SVD rank threshold of `1e-10`. Counts
are unchanged at `1e-9` and `1e-11`; at `1e-12`, two additional near-singular
directions are retained in every case (singular-value ratios near
`4.7e-12`–`5.7e-12`). The no-go conclusion does not depend on those two
threshold-sensitive directions.

The six relative components are translations and rotations at the direct
rail/principal butt-seat datum. This is a physical component-test boundary
condition, unlike an arbitrary internal spring or an additional global gauge.
In the symbolic screen, the six rows alone leave one cleat-related wood mode;
the additional `q` row removes that mode. With both imposed, the tested rigid
relative motions across all three wood interfaces project to zero in the
remaining nullspace. That does **not** show the actual unilateral model has a
unique equilibrium after `q` is released: the screen treats every wood face
and seat as closed bilateral normal contact and assumes four axial bolt/nut
MPC rows.

The combined rows still leave 48 internal hardware modes. Sixteen are the
reported pure bolt/washer/nut component-axis spins; they are gauge-like for
non-torsional response only under an axisymmetric, no-torque connection law.
Thread torque, nut seating, or friction can make those spins relevant to the
six-component response. Removing those 16 leaves 32 additional hardware-body
modes. All residual nullspace participation in this kinematic screen is on
metal bodies; the 32 modes are not global gauges or the identified pure spins.
Their energetic relevance is not proved, so do not silently remove them or
assume they cannot change load transfer.

There is separate native evidence that the candidate cleat-slip vector has a
near-zero residual in the emitted zero-load reference tangent: translating all
9,369 cleat nodes 1 mm along N left a maximum nodal residual of `2.578e-6 N`
and scaled residual `1.375e-12`. The native record does not prove the contact
active set or zero-pressure state, so this is a vector-residual witness rather
than proof of a physically equilibrated free mechanism or total tangent
nullity. The rigid screen remains a maximal-closure sensitivity.

`q` moves the cleat relative to the principal member inside the joint. It can
be used as a separately labeled clearance-seating diagnostic, but holding it
while reporting a service response would add an actuator load path. The
current diagnostic must release `q`, then show that the intended contact state
and equilibrium persist before extracting any response. No such post-release
static uniqueness result exists. The accepted-inc1 prefix comparison did pass
as an output-only diagnostic: six accepted-state FRD datasets and the 35-pair
contact triplets were compared within the frozen print bounds. The comparison
is pinned in [`accepted-inc1-comparison.json`](../dependent-residual-native-check-attempt01/comparison-adapter-attempt01/accepted-inc1-comparison.json),
SHA-256 `b1d9750339de6042b3943158d9af981b46ac86ec2aec51b7110267ebf03a93bd`.
Both complete solver runs later exited with code 201 at the endpoint; runtime,
full-step, full-trajectory-neutrality, and mechanical-acceptance checks remain
false. The accepted-prefix comparison does not make either full run successful.

The smallest interpretable direct component method is a complete current
three-timber/four-stack patch, with the cleat and hardware left to equilibrate
and only a remote six-scalar global gauge. A prescribed-displacement test can
control all six relative rail/principal components at the actual interface and
record their conjugate reactions. The response method also defines separate
signed interface unit-wrench cases; under unilateral clearance these are
different tests, so their results must not be treated as interchangeable.
Keep all three finite wood contacts, clearances, bolt/bore transfer, and stack
seats physical. The current six-row rigid screen leaves one cleat-related wood
mode; only actual contact or engagement after the clearance closes can resolve
it. If a named clearance must first be seated, run `q` as a distinct
conditioning case and release it before the response case. Confirm that the
unilateral equilibrium persists after release. A resulting mechanism is
`FREE_MODE_PRESENT`, not a reason to add stabilization. This adapts the
[ordinary-joint response method](../../../ordinary-joint-response-method.md)
to the current patch; the older WJ16 unit-response contract is method context
only and transfers no result to WJ24.

A reduced connection slip/stiffness model remains a viable *future* route, but
there is no qualified current bound to propagate. The response-method document
labels its cited `K_ser` relation as an older-edition comparison and requires
checking the published 2025 Eurocode before calling it current; its density
points are not bounds. The four current bottom-center bolt products are not
selected, and physical 1/4-20 thread engagement, slack, and seat transfer are
unresolved for this WJ24 patch. A usable reduction therefore needs a current
applicable fastener/wood law and evidence-backed lower/upper component
compliances, with the frozen modeled dimensional clearance scenario explicit
and distinguished from a measurement of received physical parts. A supported
provisional dimensional scenario may be analyzed conditionally. Keep bolt
bending, wood bearing, axial engagement, and seat compliance in series without
double counting. Only then can bounded
connection laws be carried through fresh whole-frame sensitivity cases, as
allowed by [current criteria coverage](../../../current-criteria-coverage.md).

Until that source gap is closed, retain the current transient as a
clearance/contact diagnostic only. Neither it nor an imposed `q` endpoint
provides zero-preload initial stiffness, capacity, or a service joint response.
No native solver, CAD, mesh generation, or full suite was run for this rank
artifact.
