# Knee bridge common displacement compatibility

**Status: finite reconciliation complete; all six cases conflict with the
declared common affine-pose hypothesis.** This rejects combining these specific
saved local solutions and total connector motions as one affine receiver
state. It does not establish physical assembly failure. The bounded question
is whether the four specific saved continuous
shaft states and the saved simultaneous knee connector motions admit one common
first order affine pose per receiver in each of the six nominal cases. The new
internal v pairs also need a passive law and an elastic seat displacement field;
their static allocation does not supply either.

[knee-bridge-common-compatibility.py](knee-bridge-common-compatibility.py) owns
only this new leaf and fresh immediate children of
`rawlocal/knee-bridge-common-compatibility/`. The selected candidate, all existing
source files, previous attempts, frame/CAD/native workflows and other agents'
work remain separate authorities. Parent owns execution, final validation,
global stability and permanent integration. Normal anchorage belongs to the
splitting peer and is outside this adapter.

## Frozen API and preparation record

Importing the module reads no evidence and imports no numerical library.

| API | Work performed | Return value |
| --- | --- | --- |
| `prepare(output: Path)` | Authenticate sources, bind immutable states and modified geometry, inspect saved array headers and installed dependency versions | JSON object also written as `report.json` |
| `build(output: Path)` | Repeat authentication; run two small new method references, then one feasibility LP per nominal case | Same report schema with per-case constraints, diagnostics and certificates |

The APIs accept only a fresh immediate child of the owned raw directory.
Neither API falls back to other loads, geometry, laws or historical mechanical
states. The parent executed `build` in the preserved fresh `attempt01` child.

### Completed finite result

Attempt01 returned
`COMPLETE_FINITE_RECONCILIATION_WITH_COMMON_POSE_CONFLICT_AND_MISSING_PASSIVE_FIELDS`.
Both new known-answer references and the saved-D coordinate checks passed.
All 135 source pins and three output hashes matched independently afterward.
Each of the six minimax LPs returned matching primal and dual bounds:

| Nominal case | Minimum maximum scaled kinematic residual (mm) |
| --- | ---: |
| A12 rear | 5.022769 |
| A12 forward | 5.856550 |
| A12 left | 5.478945 |
| K12 right | 5.370102 |
| K12 rear | 4.956824 |
| A1 rear | 1.499667 |

The residual combines translations and slopes scaled by the actual 215.9 mm
grip. It is not a predicted frame deflection or an adopted serviceability
limit. Every case has nine duplicate-row conflict certificates. In particular,
the two independent shafts prescribe different rotations for the same receiver.
Their source local equilibria remain unchanged and valid within their own
isolated hypotheses.

| Finite artifact | SHA-256 |
| --- | --- |
| `attempt01/report.json` | `05741edf258ad5608d8db7414e7b2e52426ac01d6aa6e17c2bf1f06e79f28f7f` |
| `attempt01/receipt.json` | `500091d3e6d2054be4603e0a75293d072b289e12d6468189ef577f2409790833` |
| `attempt01/producer.py.snapshot` | `cb6e607cb5b61225e5c1a513aadfd45a58a4d6d5b2dbc17aa4caf58d267a7485` |

The required next reconciliation is a common elastic receiver/seat field with
an explicit passive law and unloaded reference for the four internal v ties.
Changing hardware is not justified by this kinematic diagnostic alone. The
finite result does not search alternate contact equilibria or elastic fields.

The final preparation command executed after the parent restored the corrupted
washer receipt was:

```sh
.venv/bin/python -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-bridge-common-compatibility.py \
  --prepare \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-common-compatibility/prepare-attempt02
```

It returned `PREPARED_BOUNDED_RUN_WITH_EXPLICIT_PASSIVE_FIELD_GAPS`, authenticated
135 source pins before and after, and made no numerical calls. Python AST
parsing and Ruff passed. No software tests, new coupons, contact solves,
frame/native solves, CAD builds or reviews ran.

| Owned artifact | SHA-256 |
| --- | --- |
| Current producer | `cb6e607cb5b61225e5c1a513aadfd45a58a4d6d5b2dbc17aa4caf58d267a7485` |
| `prepare-attempt02/producer.py.snapshot` | `cb6e607cb5b61225e5c1a513aadfd45a58a4d6d5b2dbc17aa4caf58d267a7485` |
| `prepare-attempt02/report.json` | `77e4a92ce5fc234e9381e014fc0810d4a79e665448ed88d5848844b4191e6c1c` |
| `prepare-attempt02/receipt.json` | `fdc08d395129eb32ba948413185f7690f9fea4ac6b02cf37fb37639b4b00914d` |
| `prepare-attempt01/producer.py.snapshot` | `9047a8f6414af92df5ba7b478760adc9498872be8251d003fe9d96c1cf993d6d` |
| `prepare-attempt01/report.json` | `65345bddc1042d30397b14b22e326d2c3b276589393c8ea9d39d3ab7a0da5cf0` |
| `prepare-attempt01/receipt.json` | `b0c2b31b4f38d094db3fbe8648cc51ad603ea5aea98535922a86fe86d460c77b` |

The current producer adds preservation of completed cases and an active phase
when a later numerical case stops. The preparation API and consumed inputs are
unchanged by that final edit. Attempt02 authenticates this final producer; the
earlier preparation snapshot and receipt remain preserved.

### Integrity interruption and restoration

The parent reported that
`rawlocal/knee-bridge-washer/attempt02/receipt.json` became invalid JSON. Its
expected original hash is
`041067657335395f4b1723a237e11574a0ed0b3efcba4e95f32e25db77d3630f`.
This receipt is absent from all 135 preparation pins. No command or patch in
this task read, hashed, wrote or redirected to that file; listing its filename
did not consume its bytes. This task has no original copy of that receipt.

No frozen inputs were consumed between the alert and the parent's restoration
notice. The parent then restored the exact original from a verified archive and
reported that the scalar and stability packets' pins and outputs match. Bad
bytes remain at
`/tmp/mini-moonboard-washer-receipt-corruption-preserved-1791047411.bin` under
parent ownership. Final preparation resumed afterward and authenticated this
adapter's unchanged 135 pins. No washer pin or source was changed by this task.

The parent executed the finite call:

```python
report = module.build(
    module.RAW / "attempt01"
)
```

The equivalent CLI omits `--prepare`. A finite conclusion with explicit
conflicts or missing fields returns exit 0; source/API, method-reference or LP
certificate failures return `STOP` and exit 2. Completed earlier cases are
retained if a later case stops. Completion of the bounded arithmetic never
means full numerical model qualification.

## Consumed authority and pins

All paths in this table are relative to this packet. Full source bindings,
including the 24 immutable state hashes, are in the preparation report and
receipt. The existing adapter's `sources`, `reuse_nominal`, `bind` and
`authenticate` functions are reused directly. Its `build`, `backend`, `solve`
and placement APIs are never called.

| Input | SHA-256 |
| --- | --- |
| `knee-bridge-continuous-shafts.py` | `c5e45ddc8c92094879fbfdaacb7ef66f3eb06b7843eb5728c25cbae32c259e27` |
| `rawlocal/knee-bridge-continuous-shafts/attempt02/suite.json` | `ec3b5bbc6d2c80c38bfcbe5877a4ea9ca6ac89f926f5f22fa799bfb9c76a701f` |
| Its `receipt.json` | `5496190db02ec1ed8fca6ced59f7538526503ab6735f946e651394ab225d1ffa` |
| Immutable attempt01 `receipt.json` | `1eba7e7047210366afe53e78d8dc6492281280ac0be6119a11e21383ea778e69` |
| Immutable attempt01 `fresh-inputs.json` | `19f292683521bbc4f4def787fffcaaf686a266631f87fc54a14d888b6920a28b` |
| `rawlocal/knee-bridge-frame/attempt02/response/comparison.json` | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` |
| Its `response.npz` | `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` |
| `rawlocal/knee-bridge-gravity/attempt01/operator-assessment.json` | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| `rawlocal/knee-bridge-integration/attempt02/manifest.json` | `1744bb616354159c06694e99fb239251578dba3a6e860da5391dae19b5d7026c` |
| `rawlocal/knee-bridge-geometry/attempt01/manifest.json` | `254dd58d2f311553b32637b01b85b8bacbc0b474acfee667597333c501afe147` |
| Modified left spine STEP | `534ec2db81bbedfddba6cdf92c8703112231e970eff9b10e6a11fd11ce134645` |
| Modified right spine STEP | `847e644efdb36156a74dee1641e52a18cf17d301f03f59d2fa0bb68cd7d2b273` |
| `rawlocal/knee-bridge-joint-replay/attempt01/checks.json` | `71980f983dd3466d02eb6c5f838186de4b77dc2ebe04653f66cf3f3598fbe891` |
| Its `allocations.jsonl` | `5428cf793ba59c0ca1d75dbfedb62036518f29d31cefe63101df9b3d0a5bdb17` |
| `rawlocal/knee-spine-reinforcement/attempt01/checks.json`, geometry only | `c9360e7ca4ab167a5cbc505373b2bd1342aa6a830f72a26113da9f7c4a8ad778` |

The runtime is **Python 3.12.3 / NumPy 2.5.2 / SciPy 1.18.1**. Repository
`uv.lock` is pinned to
`5ea7a77ddb3072bfe1c2ba131e34b293a0103f931eb9b911e9eb248ccb6d84d3`.
Installed SciPy's `optimize/_linprog_highs.py` documents the selected options
and `ineqlin.marginals` sign convention; that source was inspected before the
integrity alert. The chosen API uses `method="highs"`, free pose coordinates,
zero gauge bounds, an explicit nonnegative slack, 1e-9 primal/dual feasibility
tolerances, 1,000 maximum iterations and five seconds per case. It checks the
primal residual, marginal signs, free-coordinate stationarity, dual norm and
duality gap before interpreting the result. Solver failure stops the case.

The live loads remain the fresh 250 lb climber × 2, signed 300 N horizontal
force, 100 mm lever, 225.19791414318078 kg modeled mass and
1.1110134616260479 dead factor. Geometry-only historical definitions supply no
old load or acceptance. The global inventory remains **104 bolt axes / 66
Hillman axes**; the unadopted proposal has **108 bolt axes**, comprising the
104 global axes plus four internal same-body v axes with no operator row.

## Smallest finite reconciliation

The cases are `a12-rear`, `a12-forward`, `a12-left`, `k12-right`, `k12-rear` and
`a1-rear`, all at saved nominal `gap_scale=1.0`. Only those six simultaneous
states are evaluated. The source zero-gap responses are not additional cases.

The four existing axes are `knee_outer_left_side_1/2` and
`knee_outer_right_side_1/2`. Each retained shaft spans the ordered spine,
`base_side` and inner frame block. Its 6.35 mm smooth diameter, 7.5 mm circular
bores, 0.575 mm radial clearance, three bearing lengths of 38.1/88.9/88.9 mm
and 215.9 mm wood grip stay unchanged. The local contact definitions remain
**Kwood=20 MPa/mm, Khead=10,000 MPa/mm, Ebolt=200,000 MPa** and their original
annular profiles. Every accepted iterate, signed receiver force and moment,
contact field, source boundary and state hash remains immutable.

One pose `(t, theta)` is assigned to each of six receivers. At reference point
`p`, displacement is `u(p)=t+theta cross (p-o)`. A common side datum `o` is used
for all three receivers on that side. Rotations are stored as `1000*theta`.
The two `base_side` poses are set to zero solely to remove the six rigid gauge
coordinates on each disconnected side. These bounds supply no physical floor
restraint or new attachment.

Each shaft supplies nine equations:

1. Two transverse translations and two transverse slopes of the spine relative
   to the middle receiver at that shaft's own datum.
2. The same four relative coordinates for the inner frame block.
3. The signed outer-seat opening from the saved normal-transfer field, evaluated
   at the actual head and nut seats.

The resulting **36 local equations** use the immutable 112-coordinate accepted
iterates. Slopes are converted using each actual saved grip, then scaled by
215.9 mm for the kinematic residual. Axial translation of the middle receiver
and shaft-axis rotation remain free where the retained model supplies no law.
The signed opening is preserved even when annular partial-contact closure
makes its datum value negative; it is never replaced with `T/k` or clipped.
All 24 saved local tensions are positive. A future zero-T local state would
stop with the exact missing unilateral slack contract rather than imposing a
spurious equality at zero opening.

The saved **36 knee port coordinates** add 36 equations to the same poses.
These include 16 lateral components, 16 face-contact coordinates and four
physical outer ties. q indexing is the retained nonfloor row order: the first
1,588 entries of q1612, followed by 24 floor means. A raw row number is joined
through the explicit prefix map. rigid300 is checked separately and used only
as a rigid-component diagnostic.

Port motion uses the source operator sign:
`q = direction dot (u_second-u_first)`. Before interpreting any fit, the finite
run checks that point-motion rows, body datums and `1000*theta` scaling recover
the saved D rows. Total q is not replaced by rigid300, and independent port
fits are not averaged into a claimed common pose.

For each case the LP minimizes `r` subject to every row of
`abs(A*x-b) <= r`. There are **72 equations, 36 pose coordinates, 12 gauge
coordinates and one nonnegative slack**, with no modified load, stiffness,
gap or weighting search. The 1e-5 mm motion resolution comes from the pinned
`simple_frame.py`; its use with a 215.9 mm scaled slope is an explicit
diagnostic convention, not a new adopted strength or joint criterion.

The report preserves every coefficient, target and residual, the best pose,
dual weights and lower bound. Repeated identical rotation rows also give an
interpretable conflict certificate: their different targets require a minimum
maximum error of half the target difference. The fitted compromise is always
marked as a diagnostic rather than a new contact equilibrium.

## Internal v pairs: explicit missing passive law

The two v bolts per spine are canonical `proposed_v_bridge_1/2`, at the saved
100/250 mm grain stations, spanning approximately 139.7 mm on each single
spine. The fresh replay's 24 static tensions and 48 end-seat forces remain
unchanged. They have zero whole-body rigid wrench but can do internal work
through strain. Zero rigid wrench does not establish displacement compatibility.

The existing LP allocation selects T to satisfy a finite pressure construction
and its declared reference comparisons. It does not define T as a function of
seat displacement, unloaded bolt length, installation gap or strain. Neither
the global q vector nor rigid300 includes the new v seats' elastic motions.
Consequently these pairs are reported as
`MISSING_LAW_AND_COMMON_ELASTIC_SEAT_FIELD`, including zero-T allocations.

The adapter documents one **unadopted P0 passive hypothesis** solely to expose
the missing condition: straight concentric smooth 6.35 mm steel, E200000,
identical rigid annuli, K10000 head contact, K20 wood contact, zero relative
tilt, zero installation gap/preload and an unloaded reference equal to the
original seat separation. With full annular areas `Ah` and `Aw`, it requires:

```text
opening(T) = T*L/(E*Asteel) + 2*T/(Khead*Ah) + 2*T/(Kwood*Aw)
```

This is positive for positive T. One rigid body's first order normal separation
change between collinear seats is exactly zero, since
`n dot [theta cross (L*n)] = 0`. Under P0, the saved positive tensions therefore
require an elastic seat extension that a single rigid spine pose cannot supply.
The finite report can calculate this required extension without adopting P0,
inventing a stiffness, tuning T or pretending the existing static allocation
is an elastic solution. A different passive model needs explicit supporting
definitions. Arbitrary free seat motions would not qualify the common body.

## Known answers, readiness and interpretation

The existing contact and beam checks are reused within their original scope:

| Saved reference | Evidence and applicability |
| --- | --- |
| `rawlocal/knee-compatible/coupon-attempt01/coupon.json`, hash `c76aacdd80d42adc6ae7a080ea3ae3ab4b614cb1dcce2709a429e764a11fa1cd` | All 24 arithmetic records matched: beam energy/fields, circular-bore force/moment recovery, common rigid gauge invariance, zero-tilt axial opening, annular tractions and rotational virtual-work scaling. These support the retained local laws, not common receiver poses. |
| `rawlocal/knee-contact-entry/coupon-attempt01/coupon.json`, hash `3301215eaef7b83ec4ac1d940615f44e2004e112029f1d3c64b99a6f8a84f3b1` | Three analytical circular-clearance contact responses matched. No contact solver is rerun in this reconciliation. |

Two new engineering references were executed in the parent's finite run:
a point-motion row with known rotation/datum displacement of -0.98 mm, and
identical scalar rows with targets 0/2 mm whose minimax error is exactly 1 mm.
They passed and gate the new coordinate adapter and feasibility/certificate
method. They are engineering references, not software test suites.

The final preparation established the bounded source/API layout and pinned
runtime after the integrity interruption. The parent subsequently completed
the two new method references, saved-D check and six finite LPs.
The full passive common-state question is not ready for a positive conclusion
because the two named fields are missing.

The finite outcome is an affine-pose conflict plus explicit missing
elastic/passive fields. A conflict rejects embedding of these
particular frozen local states and total port motions into the declared affine
receiver hypothesis. It does not prove failure of an elastic timber assembly,
rule out every alternate contact equilibrium at the same loads or transfer a
historical capacity. A small residual would supply only a kinematic diagnostic;
it would still leave internal passive response and the common elastic field
unqualified. All full-joint, hardware, changed-hole-stiffness, global-stability,
proposal-adoption and physical-release flags stay false.

The source, this MD and the ignored preparation child stay active. Immutable
attempt01 shaft states and the completed attempt02 continuation are required
inputs. No artifact is proposed for pruning or archival. No staging or commit
was performed.
