# Continuous knee bolts: straight-shaft placement at saved poses

## Result and next decision

Explicit placement lines were found for **all 96 geometry scenarios**: four
continuous knee bolts, six cases, zero/nominal source gaps and two motion
representations. Each line uses one 6.35 mm shaft through all three saved
7.50 mm bores, giving 0.575 mm nominal radial clearance per receiver. The
ordered bearing lengths remain 38.1 / 88.9 / 88.9 mm.

For the local fits of total connector motion, the smallest conservative
placement margin is **0.435309 mm**, at A12-left nominal, L1. Maximum shaft
centerline error is 0.139689 mm there. The largest scalar projection error
in the local motion fits is **0.006500 mm** across all states. That error is
reported separately; it is not a bound on unobserved bore deformation.

The rigid-only representation has a much smaller minimum margin,
**0.000453 mm**, at K12-right zero-gap, R1. This does not establish fabrication
tolerance. It omits the elastic motion that is present in the total connector
records and cannot replace their relative-motion result.

| Nominal source case | Maximum clearance fraction, rigid component | Maximum clearance fraction, total-motion fit | Minimum margin, total-motion fit (mm) |
| --- | ---: | ---: | ---: |
| A12-rear | 0.935352 | 0.175878 | 0.473870 |
| A12-forward | 0.890057 | 0.214856 | 0.451458 |
| A12-left | 0.983770 | 0.242940 | 0.435309 |
| K12-right | 0.970147 | 0.238627 | 0.437790 |
| K12-rear | 0.920419 | 0.171916 | 0.476149 |
| A1-rear | 0.351794 | 0.041173 | 0.551326 |

Fractions include the conservative tilted-cylinder radius allowance. Rows
take their maximum or minimum across four bolts; these are geometric witness
summaries, not simultaneous force interactions or motion envelopes.

**No geometric need to enlarge these bores follows from this calculation.**
The next mechanics question is which bore-wall contacts carry the saved
receiver wrenches as the shaft translates, rotates and bends. The placement
lines themselves are free of bearing contact. They therefore do not reproduce
the loaded [static bearing fields](knee-bearing-checks.md), select a contact
branch or establish compatibility of the frame's current force allocation.
All four continuous bolts retain zero modeled clearance in the source frame.

## Small placement model

The first representation uses returned rigid translations and rotations,
referred to the middle member. The second fits each outer/middle interface's
eight scalar total-motion records to six relative pose coordinates at each
bolt's head-seat datum. All fits have rank six. This supplies 96 common-datum
fit records for 48 distinct interface/state combinations. It includes the
saved connector elastic contribution through those records, but does not
reconstruct elastic displacement along the complete bore surfaces.

Each straight receiver axis is moved by the frame's first-order pose rule,
`p' = p + t + rotation × (p − datum)`. A direct least-squares line through the
six receiver endpoints supplies a candidate common shaft. Its intersection
with each receiver's own normal plane is checked at both ends. If `c` is the
absolute cosine between shaft and bore axes, the tilted shaft section lies
inside a circle of radius `3.175/c` mm. The reported sufficient margin is:

```text
bore radius − 3.175/c − shaft-center offset in the bore plane
```

That enclosing-circle check is conservative for the elliptical shaft section.
Offset along each straight bore varies linearly; the endpoint norm bounds the
complete segment. There is no contact stiffness, friction, preload, beam
solve, new bore occupancy or hardware change in this calculation.

The initial least-squares construction found 95 of 96 witnesses. At A12-left
zero-gap L1, rigid-only, it missed one endpoint by 0.003061 mm. A single direct
line shift of `[0, −0.056778, +0.048451]` mm then produced positive margins at
all six endpoints, with minimum 0.071580 mm. Every endpoint was recalculated.
This is a different mathematical placement of the same shaft, not a change to
the reviewed wood or bolt stations. No optimizer or exhaustive infeasibility
claim was needed. The initial packet remains preserved.

## Sources and reproduction

[knee_bore_source.py](knee_bore_source.py) binds the four ordered stacks to the
existing three-member screen and model-input clearance records. The underhead
interval starts at 1.651 mm; endpoint construction starts at the saved wood
head seat, so this offset is not counted twice. Its source STEP identifiers
are retained as saved geometry evidence; no new CAD query was performed.

[knee_bore_fit.py](knee_bore_fit.py) consumes the unchanged
`two-receiver-frame-attempt03/` comparison and response, model, row identities
and existing force-state contract. The nominal saved positions remain
representative, bounded and nonunique. This calculation supplies no bound
over all other permitted seating positions and no physical inspection.

Ignored/local output `knee-bore-fit-attempt02/fit.json` has SHA-256
`eaf1b47163978c9e928cc2d6c973d0f420de8ed490f9657989f30f7f723d2a6b`.
All ten consumed source bindings match. The exact producer is preserved in
the output directory. Initial `knee-bore-fit-attempt01/fit.json` remains
unchanged, SHA-256
`d6819bccce31bfac44e8bc22564bb36abf9cb639ba92669df541505ce50d3d27`.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/knee_bore_fit.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/knee-bore-fit-attempt03
```

Use a fresh output directory. Ruff passes. No software tests, review loop,
frame/native solve, delivered-hardware assumption change or physical work was
performed. Loaded bearing compatibility, common-bolt clearance integration,
actual thread sections and complete joint resistance remain open. The panel
attachment deficit and top-rail proxy exception remain. All 47 criteria stay
pending, all eight release flags stay false, and Actual/Disposition cells
remain blank.
