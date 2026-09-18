# Horizontal service frame stiffness diagnostic

Ten frame/panel diagnostic cases completed equilibrium, MPC and unilateral
bearing checks. Panels provide measurable stiffness in the controlled comparison:
maximum timber displacement fell **37.5%**, from 21.390 to 13.367 mm, when passive
panels were attached under exactly the same discrete framing loads. Applied-load
work fell **36.4%**. This establishes a stiffness contribution within this model;
it does not qualify the structure or its connections for construction.

Loads include doubled 250 lb or 300 lb vertical force, an adverse 300 N horizontal
force and the couple from a 100 mm offset from the front panel surface. Self-weight
uses an assumed density of 600 kg/m³; holds and hardware mass are omitted.
C10 is in the upper left wide bay; F10 is near the center split. C6 and C7 lie
on opposite sides of the horizontal panel seam.

## Completed diagnostic matrix

The table gives maximum displacement anywhere in the indicated domain, not just
at the loaded hold. All rows passed numerical and compression-only contact checks.
No displacement acceptance limit or connection resistance acceptance is assigned.

| Case | Assumed connector stiffness, N/mm | Maximum panel displacement, mm | Maximum timber displacement, mm | Maximum connector resultant, N |
| --- | ---: | ---: | ---: | ---: |
| C10, doubled 250 lb reference | 1000 | 16.273 | 13.299 | 736.2 |
| C10, more flexible connections | 100 | 39.352 | 38.732 | 596.1 |
| C10, stiffer connections | 10000 | 11.769 | 8.090 | 1504.2 |
| C10, doubled 300 lb | 1000 | 18.815 | 15.247 | 850.8 |
| F10, doubled 250 lb | 1000 | 21.811 | 19.918 | 1110.7 |
| C6, doubled 250 lb | 1000 | 14.030 | 11.019 | 1042.8 |
| C7, doubled 250 lb | 1000 | 10.427 | 10.282 | 964.2 |
| Frame-only C10 control | 1000 | No panels | 21.390 | 1028.5 |
| Passive-panel C10 control | 1000 | 13.771 | 13.367 | 739.5 |
| C10, refined member/panel mesh | 1000 | 16.285 | 13.303 | 736.2 |

The two control rows use identical verified force vectors and locations on the
framing. Their work ratio is 0.635761 and timber-displacement ratio is 0.624928.
They deliberately isolate passive panel stiffness. They are a different loading
experiment from applying the physical resultant through a panel patch, so their
absolute displacements must not be substituted for the coupled-panel cases.

Refining the member/panel mesh from 100/80 mm to 75/50 mm changed the reference
maximum panel displacement by 0.0741% and applied-load work by 0.4250%. The largest
change in an individual connector resultant was 0.536 N. These observations are
limited to this C10 refinement pair; they do not establish local stress convergence
or refinement of every other load and stiffness case. The refined maximum panel
normal stress changed 7.74%; see the separate [stress interpretation](horizontal-frame-stress.md)
for directional components and their refinement limits.

The initial bilateral model was rejected because four outer bearings carried
approximately 197–450 N of tension. The revised calculation removes tensile
bearing springs and reactivates pairs that penetrate. The reference settled in
three iterations; final cases required two or three. Every intermediate deck,
output and rejected contact state is retained.

The eccentric member coupon differed from the analytical displacement by 1.695%
and balanced support moments. It validates transfer of an offset force in the
native member interpolation, not the complete frame model.

Working evidence is in `fea/generated/horizontal-frame-batch-v2`, including its
`summary.json`, per-case reports, raw iterations and source snapshots. The earlier
`horizontal-frame-batch-v1` and standalone trials are historical diagnostics.
Published archive links will identify the final retained evidence. No new solver
execution is needed to replay recorded equilibrium, connector forces or stresses.

Run `uv run python -m fea.horizontal_frame_batch --output <new-directory>` to
repeat the ten cases after freezing sources. Each case permits twelve contact
iterations, each native invocation limited to 180 seconds. Repeated contact sets
stop with nonconvergence. Ratios are withheld if either control fails its checks.

## Hold-load footprint sensitivity

An additional C10 run with an assumed 80 ×80 mm footprint retained the exact
force and 100 mm standoff couple from the 20 ×20 mm reference. Numerical and
compression-only contact checks passed. Maximum panel displacement changed from
16.2731 to 16.2142 mm (−0.362%); governing connector force stayed approximately
736.166 N. In contrast, upper-left panel geometric-Y normal stress fell from
24.3239 to 12.0723 MPa, and Y/normal shear from 13.1381 to 1.5750 MPa.

This demonstrates strong local load-introduction sensitivity. It does not verify
an 80 mm physical hold seat, prove panel strength or justify thicker plywood.
The changed patch also changes local mesh divisions. See the [stress comparison](horizontal-frame-stress.md#completed-load-patch-sensitivity)
for complete quantities and limits. Raw working evidence is retained in
`fea/generated/horizontal-coupled-c10-patch80-v1`.

## Modeling limits and next decisions

Every member is independent and receives the current CAD connection stations.
Six screw springs connect each ideal rigid commercial angle; finite three-axis
springs represent panel screws and leg bolts. Independent shell panels can
transfer stiffness only through those screws. There are no implicit seam ties.

Feet have fully clamped cross sections. This is stronger restraint than an
unanchored floor and does not establish floor slip, uplift, stability or safety.
Contact is frictionless normal bearing with a 1,000,000 N/mm compression penalty;
it is checked by opening/removing and closing/reactivating individual springs.
Its local pressure distribution is not resolved.

Timber stiffness uses a verified retained rear rectangle derived from current
raw wood and service grooves. Applying that reduced section uniformly,
extrapolating end-bevel stiffness and omitting fastener bores are approximations,
not proven bounds. Member weight is concentrated at its raw centroid. Panels are
undrilled isotropic shells; consistent surface integration distributes panel
weight and applied vector traction. A separate zero-resultant nodal couple
represents the hold offset. Actual hold-seat traction is not modeled.

Both timber and plywood use hypothetical isotropic E = 7000 MPa and ν = 0.3.
Plywood directional properties, timber species/grade, connection stiffness,
fastener resistance, bearing distribution and floor behavior remain unresolved.
Integration-point stresses are diagnostic tensors with locations, not qualified
allowable-stress ratios. Local stress peaks and connector forces need their own
refinement assessment.

The next priorities are concrete:

1. Establish connection stiffness and resistance using the actual chosen fasteners,
   receivers and installation. Connection sensitivity changed C10 displacement
   from 39.352 to 11.769 mm. Stiffer assumptions also increased the largest panel
   screw resultant to 1504.2 N; reduced movement does not imply a stronger joint.
2. Check the center-split load path and panel attachment pattern. F10 produced
   more displacement than C10 at the same assumed stiffness, so evaluating only
   the wide bay would miss a relevant case. Its largest connector resultant,
   1110.7 N, occurs at an upper-left panel screw.
3. Replace hypothetical isotropic material properties with selected timber
   species/grade and directional plywood data, then check member and connection
   resistance using the recorded forces and stress locations. The present local
   stress results are diagnostic, and none passes an allowable-strength criterion.
4. Resolve unanchored floor contact, slip, uplift and stability separately. Clamped
   feet cannot answer those questions.

Retain the present layout as a development candidate while resolving those
specific blockers. Panels deserve stiffness credit; they do not remove the need
to qualify fasteners, members and supports. These results do not justify a blanket
lumber increase or establish a full-board load envelope.

Nodal output is rounded by the native solver. The MPC audit retains the raw
printed residual and computes each equation's rounding interval from the actual
decimal/exponent precision of its displacement tokens, weighted by the equation
coefficients. Acceptance requires that interval to intersect the declared
±0.00001 mm tolerance; it does not claim unavailable unprinted precision. A
regression deliberately exceeds the interval plus tolerance and must fail.

## Retained evidence and replay

The [ten-case batch archive](../fea/results/horizontal-frame-batch-v2.tar.xz)
and [80 mm patch archive](../fea/results/horizontal-coupled-c10-patch80-v1.tar.xz)
retain complete case directories, including intermediate contact cycles, raw
native files and source snapshots. Archive contents start directly with each
source directory's contents. The batch also retains `batch-source.py`, whose
hash must match the saved summary. The [archive index](../fea/results/horizontal-evidence-index-v1.json)
records compressed-file sizes, SHA-256 identities and replay report hashes.
Fresh extraction and replay passed for all ten batch cases and the separate
80 mm case. [Batch replay](../fea/results/horizontal-frame-batch-v2-replay.json)
and [patch replay](../fea/results/horizontal-coupled-c10-patch80-v1-replay.json)
remain numerical evidence, not structural qualification.

After extracting each archive into a separate directory, replay without CAD or
a solver:

```sh
uv run python -m fea.horizontal_frame_evidence /path/to/extracted-batch \
  --output /tmp/batch-replay.json
uv run python -m fea.horizontal_frame_evidence /path/to/extracted-patch80 \
  --output /tmp/patch-replay.json
uv run pytest tests/test_horizontal_frame_evidence.py -q
```

The replay checks every hash-covered native artifact and historical source
snapshot, including four runtime JSON references. It verifies cycle-to-parent
hash agreement, recomputes final force/moment/MPC/contact diagnostics and all
integration-point stress summaries, then reconstructs the ten-case summary and
matched-load ratios. It records the current replay code hashes; successful replay
does not claim that historical CAD snapshots equal a newer design. Routine tests
exercise tampering and missing-evidence rejection without repeatedly decompressing
large solver archives. Full archive replay is a separate publication check.
