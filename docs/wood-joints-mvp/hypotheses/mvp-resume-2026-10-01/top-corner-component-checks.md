# Both corrected top corners in the working frame

The engineering question is whether the isolated corner correction still has
favorable component references when both corners take up bolt clearance in
the same frame. The earlier right-only comparison did not answer that question.
This calculation reuses the corrected physical operators, recorded six static
loads and all 66 conditional Hillman paths. It changes no reviewed CAD or
authority file and makes no hardware selection.

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
