# Both corrected top corners in the working frame

The engineering question is whether the isolated corner correction still has
favorable component references when both corners take up bolt clearance in
the same frame. The earlier right-only comparison did not answer that question.
This calculation reuses the corrected physical operators, recorded six static
loads and all 66 conditional Hillman paths. It changes no reviewed CAD or
authority file and makes no hardware selection.

## Current all-two-receiver clearance replay

`two-receiver-frame-attempt03/` includes the modeled radial clearance of all
88 independent candidate bolts. The four continuous candidate bolts and
twelve retained bolts remain at zero clearance. Geometry, physical operators,
loads and all 66 conditional Hillman paths are unchanged. Six nominal states
meet equilibrium, connector and floor laws with finite fixed-force seating
bounds. Their rank296/297 does not establish a unique pose or strict tangent
stability; these component calculations use the saved simultaneous forces.

The fresh 48-state component calculation peaks at **0.726770 left / 0.813787
right** under the conditional 92 ksi scenario. Concurrent steel-allowance
comparisons are **0.735599 / 0.825272**. Maximum finished tangent-path ratio is
0.161656 and washer wood-pressure ratio is 0.788727. The declared washer strip
stress reaches **198.153 MPa**; actual washer-metal resistance remains unknown.
Neither corner requires larger bolts from these comparisons. The panel-screw
reference deficit remains explicit in the [panel worksheet](panel-attachment/README.md).

Current local outputs: `corner-component-attempt05/component-results.json`
SHA-256 `1e163479d8ed80a353a133bd234fe5e4b069470756f42c922051aef512d73648`;
`steel-interaction.json`
`21c4ef9068f27542f23436d186ccc6ef1ae001e64e942192748919815763bd3b`.
Use `two-receiver-frame-attempt03/` with the component/steel commands below.
Earlier movement maxima are preserved representative results of their own
source frames; they are not motion envelopes for this bounded variant.

## Preserved six-joint integration: four outer corners and left service cleats

The parent has included the two bottom outer corners in addition to both top
corners and the upper/lower left outer service cleats. All 24 bolts receive
modeled clearance together. The physical operators, loads and 66 conditional
Hillman paths are unchanged. All twelve zero-gap/modeled-gap states satisfy
the declared frame laws, floor branches and rank gates.

| Joint | Maximum bolt shear / tension | Maximum local movement | Maximum local rotation |
| --- | ---: | ---: | ---: |
| Top outer left | 936.601 / 573.266 N | 2.3480 mm | 0.8120° |
| Top outer right | 1,067.255 / 656.554 N | 2.3252 mm | 0.9890° |
| Left outer upper service | 4.922 / 15.961 N | 0.5938 mm | 0.1558° |
| Left outer lower service | 4.968 / 13.942 N | 0.7561 mm | 0.1564° |
| Bottom outer left | 251.337 / 186.370 N | 2.4501 mm | 0.2522° |
| Bottom outer right | 4.893 / 15.850 N | 0.1371 mm | 0.0940° |

These maxima are not simultaneous. Maximum fitted body translation is
6.5381 mm. Local interface fits are not complete member/panel deflections
or adopted motion limits. The [bottom-corner calculation](bottom-corner-checks.md)
uses the same source and retains both existing bottom cleats and bolt diameters
within the conditional working model.

Updated 48 same-state top-corner component references peak at **0.7077 left /
0.8037 right** under the conditional Grade 5 scenario. Concurrent steel-allowance
scenarios peak at **0.7164 / 0.8150**. Finished tangent-path and washer wood-pressure
ratios peak at 0.16055 and 0.71321; contact-cell mean and host characteristic
splitting comparisons peak at 0.08987 and 0.15050. The declared washer strip
stress peaks at 179.179 MPa. Complete resistance, actual washer transfer,
operation and motion compatibility remain open; no stronger hardware is selected.

Current local evidence bindings:

- `all-outer-corner-frame-attempt01/comparison.json`: SHA-256
  `ec69b49c821a56fdde76d94148405f9f743e4f72add17c89d35af512be76f6a3`.
- Its `response.npz`: SHA-256
  `aa70480aa18c33bb1cbd7d3a53ff582a0c7a90c93487f92721619474ec251901`.
- `corner-component-attempt04/component-results.json`: SHA-256
  `19d17f5740cb4f039c3fd506f55525ab6a7002273a595f8b540c320a49672dce`.
- Its `steel-interaction.json`: SHA-256
  `d9340a10b98bc56f73de7c5143bf173163d70c575645b58768721039d3757a2c`.

The earlier two- and four-joint calculations, receipts, failures and exact
producer snapshots remain preserved. The six-joint frame is reproduced by
adding `--service-joints --bottom-corners` to the frame command below, with a
fresh output path. Use that frame path for component and steel calculations.
The unchanged historical two-corner scenario below retains its original scope.

## Coupled frame result

[both_corner_frame.py](both_corner_frame.py) extends the existing pairwise
circular-gap equations to all eight top-corner bolts. The four side bolts
have 1.0625 mm relative clearance; the four rail bolts have 1.15 mm. These are
CAD bore/shaft scenarios, not delivered fit or drilling instructions. All other
bolted joints remain at zero gap. Floor bearing and no-slip tangent branches
are allowed to change during each static calculation.

All twelve states, six zero-gap and six modeled-gap, meet the existing force,
moment, spring-law, unilateral and floor checks. Force-bearing rigid rank is
300 throughout. Zero-gap forces differ from the saved quadratic-program
response by at most 0.00719 N. The circular-gap residual is checked against the
raw frame response after the optimization seed; a failed seed termination
message alone is not used as success or failure of the final equations.

| Both-corner modeled-gap result | Left top outer corner | Right top outer corner |
| --- | ---: | ---: |
| Maximum bolt shear | 927.648 N | 1,061.463 N |
| Maximum bolt tension | 566.741 N | 653.712 N |
| Maximum local rail/side movement | 2.3447 mm | 2.3227 mm |
| Maximum local rail/side rotation | 0.8108° | 0.9852° |
| Maximum local projection-fit residual | 0.04698 mm | 0.05348 mm |

Peaks are not necessarily simultaneous. Maximum fitted body translation is
6.5017 mm. Local interface fits and body translations are different quantities;
neither is a complete deformed-surface clearance check or an adopted motion
limit. No motion acceptance is inferred from the service worker's different
joint or provisional targets.

## Same-state component results

[corner_checks.py](corner_checks.py) consumes the six modeled-gap responses.
It joins 48 simultaneous bolt states, 16 grain paths with 32 exact STEP tangent
shear planes, 16 exact washer-seat envelopes, 30 complete body balances,
24 host splitting references and 384 contact-cell pressures.

The conditional material scenario is dry, normal-duration DF-L No. 2 and
Grade 5 bolt tensile-yield input Fyb = 92 ksi on both side and rail bolts.
The steel basis remains conditional; neither a product test nor delivered
material is inferred. Each state keeps its signed force components and axial
tie demand. The quarter-inch rail component calculation applies Cg = 0.992477
and Cdelta = 0.975253; side bolts retain the declared singleton-row component
scenario. Full oblique group interaction is not inferred from those factors.
The preserved zero-gap right-corner individual reference is 1.1593. The
favorable modeled-gap results therefore do not establish Grade 5 adequacy
across unspecified or tighter delivered fits; they support continued work on
the declared fit scenario without selecting stronger bolts.

| Component comparison | Left corner maximum | Right corner maximum |
| --- | ---: | ---: |
| Lateral / adjusted conditional individual reference | 0.7012 | 0.7992 |
| Parallel component / finished tangent-path reference | 0.1402 | 0.1596 |
| Washer mean wood pressure / Fc perpendicular | 0.6156 | 0.7101 |

All sixteen maximum washer envelopes have full modeled wood support. Maximum
contact-cell mean pressure is 0.38163 MPa, or 0.08856 of the conditional wood
bearing reference. This is a cell mean, not a bound on local edge pressure.
The largest complete host-cut demand / smaller EN 1995-1-1 Eq. 8.4
characteristic reference is 0.14964; characteristic-to-design conversion and
the three-dimensional splitting applicability remain explicit open checks.
Some host cuts intersect other distributed contact footprints and therefore
retain the point-action accounting limitation in their records.

Maximum axial stress / conditional bolt proof stress is 0.05437. The largest
direct axial-plus-shank-shear von Mises proxy is 43.101 MPa. These proxies omit
bolt bending; the separate lateral yield calculation includes dowel bending.
They do not establish combined steel resistance by themselves.

The subsequent [same-state steel allowance calculation](steel_interaction.py)
reserves uniform axial stress and an assumed parabolic circular-shank shear
maximum before recomputing the existing lateral bending reference. Its
remaining nominal yield allowance is
`sqrt(Fy² - 3*(4V/(3A_shank))²) - T/A_thread`.
Across all 48 simultaneous states, resulting adjusted lateral-reference
ratios peak at **0.7098 left and 0.8104 right**. This provides a concurrent-load
mechanics scenario instead of comparing unrelated envelope peaks. It remains
an assumed steel stress field, not a prescribed NDS interaction equation or
qualification of actual thread transitions, bearing zones or head/nut behavior.
The source-bound result is retained as
`corner-component-attempt02/steel-interaction.json`.

The declared uniform-annulus/radial-strip washer model requires up to
178.403 MPa bending stress at the catalog minimum thickness, using declared
10 mm rail and 12 mm side head/nut bearing circles. Actual bearing footprints
and an applicable washer-metal resistance basis remain missing. Bolt grade
supplies no washer yield property. This remaining check is specific to washer
transfer; it is not a reason to select stronger bolts from the present results.

## Source bindings and reproduction

Frozen local outputs, retained under the repository's ignored-evidence policy:

- `both-corner-frame-attempt01/comparison.json`: SHA-256
  `044d914af001b9d0e9f2895b4ddc95498b8f3cdf70d96a035bb7d274467a256d`.
- `both-corner-frame-attempt01/response.npz`: SHA-256
  `af5567aeef00df674bd8cfa1400e093174c0427bd9629f8afd9b15657df8451e`.
- `corner-component-attempt02/component-results.json`: SHA-256
  `cb0a0485b7fe088d5aee8b425677e0763b6d863456f265a7bb1ee1c2a15a93b0`.

Each report binds its inputs; exact producers remain beside their outputs.
The first component attempt completed arithmetic but stopped while serializing
a relative CLI path against the absolute repository root. Its failure record
and producer are preserved in `corner-component-attempt01/`; no engineering
result is claimed from that failed publication. The corrected producer resolves
paths before creating source bindings and uses a fresh output directory.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /usr/bin/timeout --signal=KILL 120s \
  uv run --offline --no-project --python 3.12 \
  --with numpy==2.2.6 --with scipy==1.15.3 --with osqp==1.0.4 \
  python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/both_corner_frame.py \
  --output /tmp/FRESH-BOTH-CORNER-OUTPUT
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /usr/bin/timeout --signal=KILL 120s \
  .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/corner_checks.py \
  --frame docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/corner-frame-attempt01 \
  --clearance docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/both-corner-frame-attempt01 \
  --output /tmp/FRESH-CORNER-COMPONENT-OUTPUT
```

The recorded component environment is NumPy 2.5.2, SciPy 1.18.1,
CadQuery 2.8.0 and cadquery-ocp 7.9.3.1.1. Source pin serialization requires
retained inputs under the repository; the output directory may be external.

Continue with complete wood/group and combined steel/washer transfer,
functional motion and assembly/removal, then the other joints and members.
The panel load-slip and resistance assumptions remain conditional. The
original native A12 STOP and missing native authentication remain preserved.
No software tests, native run or review round were performed for this packet.
All 47 formal criteria remain pending and every physical release flag is false.
