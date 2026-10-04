# Continuous-knee shafts coupled to the reviewed frame

This method replaces the twenty lumped connector rows belonging to four knee
shafts with distributed circular bore contacts, free continuous steel shafts
and two series end contacts per shaft. The reviewed 104-axis geometry remains
unchanged. The other 100 bolt axes, 66 Hillman screw axes, existing floor
footprints, six loads, 100 mm hold lever, gravity and proportional 25 kg
accessory allowance retain their original conditional frame definitions.
The unadopted 108-axis proposal is not used.

The completed port reduction is reusable. The finished coupled packet records
**fourteen dispositions: twelve audited equilibria and two zero-gap floor
stops**. All six nominal live cases and both gravity-only states satisfy their
unchanged force, motion and contact gates. A numerical stop is not an accepted
state or a physical failure. Complete joint resistance, strict stability and all
physical release flags stay open.

The stricter panel consumer subsequently detects two screw-law residuals above
its inherited 1e-4 N gate despite the frame's 0.1 N global gate passing.
`frame-attempt08` resolves both numerical residuals with exactly two bounded
source refinements. The other ten accepted fields are byte-identical, both
floor stops remain, and original packets and failed consumer results are preserved.

## Compatible equilibrium

The existing convention is

```text
q = D a + e - H f
D.T f = W
```

Here `H` contains the source free-body timber elastic compliance and the four
free-shaft elastic quotients. `a` retains 300 timber rigid coordinates, twenty
shaft coordinates and twenty-four washer-plane coordinates. Rotational
coordinates use the source 1000 mm scale. Every new wood action is applied at
its recorded point as `-f * direction_global_xyz`; metal-only contact ports
have empty wood term lists.

For a chosen no-slip bearing branch, the complementary energy is

```text
min 0.5 f.T (H + diag(1/k)) f - e.T f + sum(gap_i * norm(f_pair_i))
subject to D.T f = W and unilateral f >= 0
```

Only held floor tangents receive force variables when `k=0`. Each positive
circular gap uses an exact second-order-cone epigraph. A zero gap removes its
norm term and redundant epigraph. Exact positive diagonal force scaling sets
the finite quadratic diagonal to one; each physical force and cone coordinate
is reconstructed with its own scale. This changes neither a law nor a load.
Each fixed floor mask omits its inactive normal force variables and holds
only its bearing tangents. The candidate is audited against the **original**
normal stiffnesses: inactive normal forces must stay zero within the recorded
tolerance and their motions must satisfy the open-contact law. Observed mask
updates and one-contact pivots are attempted first; a deterministic finite
search covers at most all 256 masks for the eight footprints. It reuses the
existing [floor seed's mask iterator](floor_seed.py) without its incompatible
body-only QP adapter. Previous floor signs supply only the initial branch.

The pinned **Clarabel 0.11.1** interface follows its
[official Python problem format](https://clarabel.org/stable/python/getting_started_py/).
The recorded thread limit, solver selection and tolerances follow the
[v0.11.1 settings source](https://raw.githubusercontent.com/oxfordcontrol/Clarabel.rs/v0.11.1/src/solver/implementations/default/settings.rs).
Its terminal status is recorded along with the primal/dual residuals. Accepted
states additionally require independent physical spring laws, fifty timber
wrenches, four shaft wrenches, eight washer-plane wrenches, held/released floor
conditions and recovered continuous-beam nodal equilibrium. A stopped solver
result receives no accepted-state status.

## Frozen reduction and checks

The existing `prepare-attempt03` packet has 1,592 retained old ports and 1,600
new ports. Its request is
`fb6b9161ab8ba5bf50c7b446007ebf32586281b4e154136f8cb212b467612741`.
The saved
[reduction receipt](rawlocal/joint-frame-port-reduction/attempt01/receipt.json)
records **11.082 s**, 37,647 original native DOFs and six incident timber
bodies. All output hashes match. The reduction preserves the old H/D/e/W
entries byte for byte, verifies each point's force, moment and affine virtual
work, authenticates the existing quotient known answer, and checks native
quotient balance, energy and reciprocal new compliance. Global compliance
reciprocity is `9.383218293179273e-11`. No native solver or CAD operation is
launched by this reduction.

The original frame archive stores `*_raw_force_n`, with `raw = T.T f`.
Retained rows invert by identity; each distributed floor footprint inverts by
summing its normal and two tangent forces. This recovery reconstructs all
twelve frozen raw fields within `1e-10 N`. Applying `T` to raw forces would
average the floor weights a second time and is not the inverse.

The explicit `coupon` stage checks a loaded 3/4 N circular contact, two axial
spring/compliance series, a zero-gap contact and an open compression-only
contact. All four analytic answers pass after scaling. Two further equal-floor
coupons qualify fixed-mask entry and release. The first starts with four of
eight bearing footprints and recovers the analytic eight 10 N normals and
0.01 mm compressions. The second recovers seven 10 N normals plus a separated
eighth footprint with **exactly zero force and -0.98 mm motion**, audited
against its original nonzero normal stiffness. Beam preparation
separately checks exact annular area, centroid and second moments, the free
shaft projector, rigid modes and exact `EA/L` extension.

The source-bound
[short diagnostic](rawlocal/joint-frame-compatibility-completion/diagnostic-attempt01/diagnostics.json)
checks the A12-rear zero-gap initial floor branch. Its 3,188-variable quadratic
passes Cholesky, has minimum eigenvalue **8.500758416540116e-7 mm/N**, and full
rigid-map rank **344**. It took **2.333 s** on one BLAS thread. This excludes an
indefinite complementary energy or missing full-map coordinate as the cause of
the preserved initial numerical stop; it does not prove the final active
contact state's stability.

## Scope and retained attempts

The method uses gross filled-bore timber elastic compliance, first-order
geometry, Kwood 20 MPa/mm, head contact 10000 MPa/mm, steel E 200000 MPa,
concentric rigid washer planes and fixed 4-by-16 annular quadrature. It adds no
preload, friction, geometric stiffness, physical timber qualification or actual
head/nut profile. Contact quadrature convergence and complete resistance are
separate from satisfying this fixed discretization's equations.

`frame-attempt01` retains an interrupted preterminal calculation.
`frame-attempt02` preserves the source-key defect before a mechanics solve.
`frame-attempt03` preserves the unscaled Clarabel `NumericalError`, zero
accepted states and its false release flags. Their source snapshots and bytes
are unchanged. Completed preparation and reduction stay active dependencies;
failed attempts stay recoverable, with no pruning or archive operation here.
`frame-attempt04` completes the scaled A12-rear zero-gap pilot.
`frame-attempt05` completes four audited live states and preserves the
A12-left zero floor-mask cycle. Its partial packet is reused only for those
four accepted fields; the stopped state's iterate is not accepted. The later
fixed-mask continuation keeps its original stiffness/contact/no-slip laws.

The isolated `floor-pilot-attempt01` exhausts all 256 masks for A12-left zero
gap without an audited bearing branch. Its frozen trace contains 102 solved
branches, 151 primal-infeasible branches, two insufficient-progress results
and one almost-solved result. Among solved branches, 96 fail the original
spring law and released-floor opening checks, 73 fail the positive bearing
normal check, and 28 exceed the recorded 10 mm contact-motion domain; counts
overlap. Six branches pass every gate except **held normal force greater than
0.01 N**. None satisfies all floor conditions while failing a nonfloor spring
law. In step 1, mask `[1,2,3,4,6,7]` has minimum held normal
`1.715420178896852e-8 N` and maximum original spring residual `0.01856 N`.
Removing footprint 1 in step 0, mask `[2,3,4,6,7]`, produces a positive
released normal motion of `0.0214247 mm`. This is a floor-branch question,
not an accepted physical failure or evidence to add anchorage or slip.

The `diagnose` stage reproduces **one explicitly selected, receipt-bound
rejected mask** and saves exact forces, motions, rigid coordinates, shaft
poses, worst spring-law port labels and all eight footprint shears. It also
records the active-map nullspace after removing near-zero-normal footprint
rows. Diagnostic fields are never accepted frame states. The specific question
is whether a near-zero held normal carries substantial shear, or whether an
admissible force-fixed pose could satisfy the original released-contact laws.
The latter requires a separate pose-feasibility certificate; map rank alone
does not establish it. The nominal-gap live states remain the primary load
branch; zero gap is a declared sensitivity.

The completed one-mask
[diagnostic](rawlocal/joint-frame-compatibility-completion/floor-diagnostic-attempt01/diagnostic.json)
authenticates 61 source/output bindings; its receipt is
`bcbfb08bdfe9ad05b331271fee302e04f830fff08979b2407446f0aa0f8cb149`.
It exactly reproduces the frozen step-1 force/motion/audit values in **1.786 s**,
with one mechanics call and zero accepted states. Footprint 1 is
`base_floor_right`: its normal is `1.71542e-8 N`, normal motion is
`-0.01846175 mm`, and its held tangent forces are `[339.45127,-2.50355] N`,
norm **339.46050 N**. Its normal contact is open while its ideal tangents
carry substantial shear. Releasing the footprint would retain forbidden
tangential actions, so no force-fixed pose LP can repair this field. The
candidate active map after removing that footprint has rank 344 and nullity
zero. The worst nonfloor spring residual, `contact_43_20` at `0.0185566 N`,
passes its unchanged 0.1 N gate. The original positive-bearing criterion stays
failed; this field is not supplied to downstream demand consumers.

Parent owns all heavy execution. The next fresh output must be a child of
`rawlocal/joint-frame-compatibility-completion`; retain existing children.
The full declared comparison is six source cases plus `dead-only`, each at
zero and nominal gaps. Gravity-only loads are exactly the original column-zero
gravity times the recorded accessory factor, with no live column or elastic
duration multiplier. C_D=0.9 belongs to subsequent strength comparisons.
The saved original gravity-only response initializes the floor branch and
supplies old-force comparisons; its acceptance is not transferred.

Repeatable `--reuse-response` consumes completed coupled states through their receipt and
exact original producer snapshot. The reused field must satisfy the current
physical laws, equilibrium, floor branch and shaft recovery with unchanged
input operators. A12-rear zero from `frame-attempt04` is reused unchanged;
its added shaft/rank arithmetic requires no mechanics replay. Future receipts
bind immutable producer snapshots instead of mutable live producer paths.
The no-solve `reuse-check-attempt01` confirms this route, with one reused state
and zero new mechanics calls; `reuse-check-attempt02` validates all four
accepted `frame-attempt05` fields against the added inactive-normal guards.
Stopped packets contribute only actually completed, independently audited
fields. Distinct caches must have disjoint state inventories. Partial case runs
remain partial results.

`--continue-after-stop` preserves each failed state and evaluates subsequent
independent states. `--reuse-disposition` authenticates an isolated exhaustive
256-mask stop and records its case disposition without repeating it or inventing
a force field. Completed continuations write a `case_dispositions` inventory;
accepted entries correspond one-to-one to independently audited `states` and
saved response tags. Stopped entries point to receipt-bound failure traces.
Their overall status is
`PARTIAL_CONDITIONAL_COUPLED_FRAME_STATES_WITH_DECLARED_STOPS`, with incomplete
all-accepted scope and false release flags. Recording all fourteen dispositions
does not turn a stopped state into acceptance. The no-mechanics
`reuse-check-attempt03` validates two accepted zero states plus the preserved
A12-left zero stop in 1.566 s, with zero new frame solves.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/joint-frame-compatibility-completion.py diagnose \
  --case a12-left --gap-scale 0 --floor-mask 1 2 3 4 6 7 \
  --diagnostic-source docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-compatibility-completion/floor-pilot-attempt01 \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-compatibility-completion/floor-diagnostic-attempt01 \
  --preparation docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-compatibility-completion/prepare-attempt03 \
  --wood-reduction docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-port-reduction/attempt01
```

Parent executes this bounded diagnostic in its serialized slot. The failed
floor pilot contributes no accepted fields and cannot be used as a response
cache. Preserve each existing output child and every accepted field.

The parent continuation uses the four accepted `frame-attempt05` fields and
the separately authenticated failed disposition. Nominal gaps precede the
zero-gap sensitivity for each case:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/joint-frame-compatibility-completion.py solve \
  --gap-scale 1 --gap-scale 0 --continue-after-stop \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-compatibility-completion/frame-attempt06 \
  --preparation docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-compatibility-completion/prepare-attempt03 \
  --wood-reduction docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-port-reduction/attempt01 \
  --reuse-response docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-compatibility-completion/frame-attempt05 \
  --reuse-disposition docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-compatibility-completion/floor-pilot-attempt01
```

The producer snapshot for this continuation is
`71e72a935353500b6e3e140a4ac7f042d05226e975cab83493ccbb5136f9a0e1`.
The attempted work is nine fresh states, four accepted-state reuses and one
failed-disposition reuse. Every branch keeps the 60 s solver limit and every
floor search the 256-mask cap. No source is changed during parent execution.

## Finished coupled packet

The saved [comparison](rawlocal/joint-frame-compatibility-completion/frame-attempt06/comparison.json)
has SHA-256 `b93b4290a1818c43402b88304101cd188130ff871511754eb7f19343f612c50a`;
its [receipt](rawlocal/joint-frame-compatibility-completion/frame-attempt06/receipt.json)
is `e86fcfb6d5a169a318bc0013c0211369934017ee0034355a007e30a18ff13368`.
The accepted-only `response.npz` is
`1dfe299c8704e1f25a7a9434075e38865ff8742599b07efc9a1ef1e623892993`.
The exact producer remains at `frame-attempt06/producer.py.snapshot` with the
recorded `71e72a93…` digest. The finished packet independently authenticates
77 source/output bindings and preserves every false release flag.

| Source case | Nominal gap | Zero-gap sensitivity |
| --- | --- | --- |
| A12-rear | Audited equilibrium | Audited equilibrium |
| A12-forward | Audited equilibrium | Audited equilibrium |
| A12-left | Audited equilibrium | STOP: no audited floor branch |
| K12-right | Audited equilibrium | STOP: no audited floor branch |
| K12-rear | Audited equilibrium | Audited equilibrium |
| A1-rear | Audited equilibrium | Audited equilibrium |
| Gravity plus proportional accessory only | Audited equilibrium | Audited equilibrium |

Four previously accepted states are reused with all five force/motion/rigid/
shaft/bearing arrays byte-identical. Eight fresh states each pass after one
conic branch. The prior A12-left zero stop is reused without a force field.
The new K12-right zero search takes 268.262 s and exhausts 256 masks:
104 solved, 151 primal-infeasible and one almost-solved. Among solved masks,
98 fail the spring/released-positive-motion gates, 76 fail positive bearing
normal and 28 exceed the contact-motion domain; counts overlap. Six fail only
positive bearing normal. Its first such mask `[0,2,3,5,6,7]` holds footprint 0
with normal `1.45754e-8 N` and opening `-0.0291362 mm`, while the spring-law
residual remains `0.02080 N`. Removing that footprint in the initial mask
produces released positive motion `0.0104253 mm`. No floor-admissible mask
fails only a nonfloor law. Rejected tangent arrays were not saved for this
case, so the A12-left diagnostic's shear value is not transferred. Both stops
remain method dispositions, with no claim that physical equilibrium is absent.

Across accepted states, maximum timber force/moment residuals are
`1.876e-12 N` and `2.387e-9 Nmm`; spring residual is `0.032063 N` against
0.1 N, and compatibility residual is `1.421e-14 mm`. The changed retained-port
force peaks at **337.637 N** in A12-left nominal. Fresh downstream demand
comparisons are required for these saved fields. The largest sampled
same-state smooth-shaft proxy is `123.485 MPa`, with declared 92 ksi and 45 ksi
yield sensitivities 0.19467 and 0.39800. These values do not accept bolt threads,
catalog hardware or complete joints, and do not erase other reference exceedances.

The cached-only [final audit](rawlocal/joint-frame-compatibility-completion/final-audit-attempt01/audit.json)
checks fourteen distinct dispositions, twelve accepted states, sixty saved
response arrays and zero rejected-force exports. Its 84 combined bindings,
cache byte comparison and nullspace decomposition take **0.952 s** with no
frame or native solve. The audit is
`4e013c3c61addb63a7f0f3bc9940511ea19ec47f53a2984d303618d0a0ce9946`;
its receipt is `ccae59c35f7f038d40571867e1dd1ae7d21b43d17a02aaf5580ee4836cd15c4c`.

At the recorded 1e-8 mm activity threshold, A12-rear/forward/left and
K12-right/rear nominal have rank 334 of 344: ten active-map freedoms comprise six independent
timber projections and four metal-only modes. A1-rear and gravity-only nominal
have rank 328: eight timber projections and eight metal-only modes. Timber
participation is confined to the four center cleats and the unloaded knee
spine/inner block on one or both sides. All accepted zero-gap states have rank
344. Thus nominal active-map freedoms include timber participation; their extent, motion
envelopes and second-order stability are not established by equilibrium or this
rank decomposition. No earlier 300-coordinate bounded-seating certificate is
transferred to the current 344-coordinate system.

Completed preparation, reduction, accepted fields, failed floor traces and the
final audit remain active evidence. Earlier interrupted and failed numerical
attempts and coupon-only checks are closed method records that may be archived
only after checking consumers through the repository archive workflow. No raw
attempt has been pruned or substituted here.

## Screw-law source refinement

The panel consumer checks all 198 scalar components of the 66 original Hillman
axes against their original laws, with residual less than 1e-4 N. The source
mapping is correct; `frame-attempt06` has two actual failures:

| State | Screw / original raw row | Actual force | Original-law force | Residual |
| --- | --- | --- | --- | --- |
| A1-rear nominal | `kicker_header_right_2`, row 1444 | 0.04656225 N | 0.04635525 N | 0.0002069933 N |
| K12-rear zero | `round_panel_upper_left_rim_1`, row 1486 | 0.003052547 N | 0 N at -2.2801984e-5 mm | 0.003052547 N |

All ten other accepted states already satisfy this gate; their maximum is
2.02456e-5 N. `--refine-state` excludes exactly the selected old fields from
accepted-state reuse. Each refinement solves one branch at its receipt-bound
original floor mask, using the unchanged geometry, stiffnesses, loads and
physical audits. It adds the stricter screw-law gate and screw axial-force gate
to every exported accepted state. The other ten fields and both floor-stop
dispositions are reused. A guard prevents any undeclared new-state solve;
there is no all-fourteen replay, force clipping or lowered criterion.

The pinned Clarabel settings source cited above documents the absolute/relative
gap and primal/dual feasibility tolerances and iterative linear refinement.
The initial refinement settings were gap absolute 1e-11, gap relative 1e-14,
feasibility 1e-13, and iterative refinement absolute/relative 1e-14 with at most
twenty refinement iterations. `frame-attempt07` preserves both resulting
`AlmostSolved` stops: A1-rear nominal has primal/dual residuals about
9.56e-12/7.81e-13 and gap 7e-10; K12-rear zero has residuals about
9.61e-16/1.66e-13 and gap 1.5e-10. Neither is accepted, and no physical failure
is inferred from a solver stopping tolerance.

The revised profile keeps the original feasibility tolerance 1e-10 and selects
gap absolute 1e-9 and relative 1e-13, retaining iterative refinement. Every
physical and screw gate, 150 interior-point iterations, 60 s branch limit,
exact force scaling and single thread remains. `AlmostSolved` still receives
no accepted-state status. Finite rejected trials now save separate diagnostic
force/motion/rigid arrays and their physical/screw-law audit; these arrays never
enter the accepted response or downstream actions. A forced one-iteration
`MaxIterations` coupon verifies this preservation path.

Tiny circular and near-open unilateral known answers pass before the parent
run. The near-open oracle has analytic opening -2.28e-5 mm and expected zero
force; its law residual is 1.09603e-8 N. Circular 3/4 N forces reproduce the
analytic motions within 3e-14 mm. All existing method coupons and Ruff pass.
The cached-only `reuse-check-attempt04` qualifies aggregate reuse of eight
unaffected states, including both gravity-only states, plus both failed floor
dispositions in 2.021 s, with no new frame solve.

The preserved `frame-attempt07` producer digest is
`987ae35db01637d1f37154378a2a613b43f4fbc86d081e8e65b796c2efc29001`.
The completed `frame-attempt08` producer digest is
`9a20b35532ee9357c75c8d466f5f40aba003947291f7f5982e19c00a459dd63a`.
The revised circular and near-open coupons pass; the latter's residual is
1.08838e-6 N against the unchanged 1e-4 N gate.
Parent executed the following command in its serialized slot:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/joint-frame-compatibility-completion.py solve \
  --gap-scale 1 --gap-scale 0 --continue-after-stop \
  --refine-state a1-rear_gap --refine-state k12-rear_zero \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-compatibility-completion/frame-attempt08 \
  --preparation docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-compatibility-completion/prepare-attempt03 \
  --wood-reduction docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-port-reduction/attempt01 \
  --reuse-response docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-compatibility-completion/frame-attempt06 \
  --reuse-disposition docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-compatibility-completion/frame-attempt06
```

The finished [refined comparison](rawlocal/joint-frame-compatibility-completion/frame-attempt08/comparison.json)
is `57f7c0894ffc0fef48ce07cf796f80efacc59e54edd2e2e7a6c2b16ed0ddafc8`;
its [receipt](rawlocal/joint-frame-compatibility-completion/frame-attempt08/receipt.json)
is `74930ca8ace4a79cbf9165f570bd2bb7785faba631324a83c0728f673e27ac2d`, and
accepted-only response is `45bdb37df6f60cb188f5b59218b3004b72f3b8d4139d9c419b64d8752c9e2bd6`.
Both refinements return `Solved`, retain their exact source floor masks, and
pass every original physical gate plus the stricter screw gates:

| Refined state | Maximum screw-law residual | Maximum changed force | Active ranks at recorded thresholds |
| --- | --- | --- | --- |
| K12-rear zero | 6.86623e-6 N | 0.02384815 N | 344 / 344 / 344 |
| A1-rear nominal | 2.78114e-6 N | 0.0001699824 N | 328 / 328 / 328 |

The independent saved-field
[audit](rawlocal/joint-frame-compatibility-completion/refinement-audit-attempt01/audit.json)
recomputes motions from the bound H/D/e operators, every physical/screw-law
audit and beam equilibrium. It verifies all five arrays of each of the ten
unchanged states byte for byte, fourteen distinct dispositions, twelve accepted
states, sixty accepted response arrays, both original exhaustive floor traces
and zero rejected-force exports. It authenticates 84 bindings in **0.673 s**
with no frame or native solve. Audit SHA-256 is
`39bd3b087153a4bf1d537fdb14c94bc3774d36b4e16d20010d750c644e4da9ce`;
receipt is `c89d6f37fa6b2c92a34963dece205c80f7ee67df964801388cd4e166ea9ad669`.
The new fields are ready for downstream demand consumers. The two zero-gap
floor stops, nominal timber participation in active-map freedoms, reference
exceedances and every false physical-release flag remain separate unresolved
acceptance limits.
