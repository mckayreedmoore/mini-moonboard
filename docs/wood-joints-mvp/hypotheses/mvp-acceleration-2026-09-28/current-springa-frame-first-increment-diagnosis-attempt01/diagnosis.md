# First-increment diagnosis: current SPRINGA frame

## Finding

The first a12-rear run did not accept any increment. Its strongest source-based
explanation is that CalculiX's default residual-growth divergence check requested
the repeated quarter-step cutbacks at iteration 5, followed by the default
cutback limit. This is a high-confidence attribution, not a logged branch trace:
the solver output records `divergence` and the cutback size, but not the
internal reason code. The mechanical reason that Newton's residual followed
this pattern remains unknown.

This is not evidence that the frame or a corner joint physically failed. The
run returned 201 after 51.426 seconds, all six increment attempts ended at
accepted time zero, and the output contains no accepted force response. The
terminal message was `*ERROR: too many cutbacks`; it was not the minimum-step
error.

## Observed pattern

The frozen deck uses `*STEP,NLGEOM,NLGEOM=NO,INC=40` and
`*STATIC` data `0.1,1.0,1.e-6,0.25`. It contains no `*CONTROLS` card, so the
pinned solver defaults apply. The stdout shows five Newton iterations for each
of six attempts. After each fifth iteration, the solver cuts the step to one
quarter of its previous size. Attempt load fractions are 0.1, 0.025, 0.00625,
0.0015625, 0.000390625, and 0.00009765625.

At the first attempt's iterations 3, 4, and 5, the largest residual forces are
1177.551236 N, 2160.829268 N, and 3095.028008 N. Across the six cutbacks,
the same dominant node/DOF sequence recurs and the residuals scale with the
load fraction; the parent pattern extraction reports a maximum spread of
0.00512 N after normalizing by that fraction. Smaller increments therefore
replayed essentially the same iteration path instead of producing an accepted
state. The repeated residual pattern is observable; its underlying mechanical
cause is not identified by these outputs.

## Source-based interpretation

The frozen run used the pinned CalculiX 2.23 binary and image recorded in its
`execution.json`. The exact official 2.23 source archive used for this diagnosis
has SHA-256
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`, matching
the checksum in [`fea/calculix_223/Dockerfile`](../../../../../fea/calculix_223/Dockerfile).
The matching local manual is pinned in [`source-pins.json`](source-pins.json).
The official project page identifies version 2.23 and links the solver source
and manual downloads ([CalculiX official site](https://dhondt.de/)). The
official GitHub source is also linked for online inspection
([repository](https://github.com/Dhondtguido/CalculiX)); the mutable `master`
branch is contextual only, while version-specific claims here use the hashed
2.23 archive.

In `ini_cal.c`, the default time controls are I0=4, IR=8, IP=9, IC=16, IL=10,
IG=4, IS=0, IA=5 and DF=0.25. The manual's *CONTROLS section (7.24, printed
pages 442–445) defines those controls and their input order. `controlss.f`
confirms that the first TIME INCREMENTATION data line reads eight integer
values, with real controls on the next line.

In `checkconvergence.c`, the I0 gate activates the residual-divergence
check. That check requests divergence when the current peak residual exceeds
the preceding two and also exceeds the selected residual threshold. The
iteration 3→4→5 residuals above are strictly increasing, while iteration 5 is
at or after default I0=4; this is consistent with the observed cutback after
iteration 5. The default IR=8 is the iteration from which the solver estimates
the remaining iterations to convergence, and default IC=16 bounds the iteration
forecast. Thus five iterations are not a configured five-iteration maximum.
`checkdivergence.c` counts each retry and stops when the cutback count exceeds
IA; default IA=5 is consistent with six failed attempts before the terminal
error. The exact cutback factor DF=0.25 matches the stdout sequence.

The zero-side SPRINGA tangent is not the leading explanation. The frame table
law is `k*max(q,0)` with a zero-force knot at q=0 followed by its positive
branch. In the pinned `ident.f`, an exact knot selects the last table abscissa
not greater than q. `calcspringforc.f` then uses the secant to the next point
for an interior knot. Therefore q=0 selects the positive-side slope k for this
table. This rules out a zero initial tangent for the encoded table convention;
it does not prove that every element remained on that branch during the failed
iterations.

The pinned 2.23 source also documents line search in `nonlingeo.c` as limited
to static surface-to-surface penalty contact. It is not a supported generic
SPRINGA remedy for this model, so this diagnosis does not recommend a line-search
control change.

## Bounded method diagnostic

The parent prepared and launched a separate, source-bound controls attempt.
Its exact inputs and output files are identified in
[`source-pins.json`](source-pins.json). The change was limited to the documented
time-incrementation control card and its diagnostic scope record; the parent
input review records the physical deck as unchanged. The attempt returned 0 in
45.06 seconds with no cutbacks: its first increment converged in 13 iterations,
the next six accepted increments each took two iterations, and the complete
static step reached time 1.0. This supports the inference that the default
early residual-growth/cutback policy was premature for this case. Since I0,
IR, IC, and IA changed together, the run does not isolate a single control as
the cause, and it does not reveal why the early residuals grew.

Native output provenance is recorded by hash: `model.dat`
`10b08e7fcfca13cc0c68916634c525b66549d4e033e3d657c83f11bddfac1f8d`, `model.frd`
`e79783f238592d7b8321d528e617a899adad999b8803a16f30852750bcfdcfdf`,
`native.stdout`
`37ba5432f6abc468e939d0f8cfb40d19a2f6044b17a113c6e4beb8f248fa60f5`, and
`model.sta`
`aa4826cc59e3dcf39b32c53361b58059d4d68a6563c3a80b8baf54b439089067`.
The parent response audit was still running when this method result was
reported. These files establish a completed numerical step only; until the
response audit passes the required law, MPC, floor-normal, per-body, global,
and rounding-interval gates, no output force is a usable corner demand.

The diagnostic card is:

```text
*STEP,NLGEOM,NLGEOM=NO,INC=40
*CONTROLS,PARAMETERS=TIME INCREMENTATION
40,40,9,40,10,4,0,0
0.25,0.5,0.75,0.85,,,1.5
*STATIC
0.1,1.0,1.e-6,0.25
```

The first row sets I0=40, IR=40, IP=9, IC=40, IL=10, IG=4, IS=0, and IA=0.
The second row preserves DF=0.25, DC=0.5, DB=0.75, DA=0.85, leaves DS and DH
at their unchanged defaults, and preserves DD=1.5. No FIELD control card is
introduced, so its convergence criteria remain unchanged. With IA=0, any
cutback request terminates that diagnostic attempt instead of silently
launching smaller retries. If the solver reaches a converged increment, its
response still must pass the existing serialized MPC, spring-law, floor-normal,
individual-body, global-balance, and rounding-interval checks before any force
can be used. Solver convergence alone does not qualify a joint or establish a
corner demand.

## Scope and limits

The analysis is limited to the pinned solver's control path and the first failed
increment, together with the one parent-owned controlled method follow-up. It
does not establish why the original residuals grew, validate all SPRINGA
branches during Newton iteration, establish that a response audit passed,
reopen any joint resistance, or qualify the frame. No native launch was
performed as part of this diagnosis packet; the separate follow-up was
parent-owned.

Primary references: [official CalculiX 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf),
[official CalculiX site and downloads](https://dhondt.de/), and the
[official upstream source repository](https://github.com/Dhondtguido/CalculiX).
