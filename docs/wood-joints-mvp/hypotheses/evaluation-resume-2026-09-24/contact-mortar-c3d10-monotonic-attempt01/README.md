# C3D10 monotonic compression discriminator

## Status and scope

Prepared for parent review. CalculiX has not been launched for this packet.
It derives two small compression decks from the pinned prior coupon. The
fixture is a method discriminator, not a joint model or mechanical acceptance.

The earlier three-step coupon passed with matched surface-to-surface penalty
contact and failed with MORTAR: MORTAR carried about 40 N while the interface
was still geometrically open after the initial opening step, then peaked near
448 N against the 399.52 N nonlinear continuum reference. This pair removes
that prior open/reversal history. Both decks start at touching contact and
monotonically prescribe the upper face from `U3=0` to `U3=-0.005 mm` in one
`*STEP,NLGEOM` step. They differ only in the contact-pair `TYPE` value.

A MORTAR pass would show that the previous failure does not recur on direct
monotonic compression, consistent with dependence on the earlier loading
history. A MORTAR failure here would show that the issue is not limited to that
history. Either result leaves opening, reopening, and joint behavior
unvalidated.

## Pinned fixture and solver

The mesh, material, contact law, supports, output requests, and solver pins
are inherited from the prior
[`contact-mortar-c3d10-known-answer-attempt01`](../contact-mortar-c3d10-known-answer-attempt01/README.md)
packet.
The two 2 mm elastic C3D10 blocks use `E=100000 N/mm2`, `nu=0`, contact area
`4 mm2`, and a frictionless linear pressure-overclosure slope
`K=100000 N/mm3`. The bottom face is fixed in `U3`; minimal corner constraints
remove rigid lateral modes without constraining slave contact nodes.

The decks use the unpatched CalculiX 2.23 image
`sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38`
and binary SHA-256
`c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863`.
The prior expected record pins the source archive and the member hashes used
for C3D10 MORTAR routing, contact-law mapping, field output, and the source
iteration guard. No patched or instrumented executable is used.

The single requested schedule is:

```text
*STEP,NLGEOM,INC=100
*STATIC
0.1,1.0,1e-8,0.1
TOP,3,3,-0.005000
```

The input requests minimum increment `1e-8`; the pinned solver raises its
effective `*STATIC` minimum to `1e-6`. The declared initial and maximum
increments are `0.1`; parent verification must inspect the actual accepted
schedule and convergence trace. Each increment requests all-node `U,RF` and
contact `CDIS,CSTR` output.

## Frozen known-answer gates

The acceptance oracle and tolerances are inherited unchanged from the prior
coupon. For the linear series-compliance reference,

```text
C = Lupper/E + Llower/E + 1/K = 5e-5 mm3/N
F = (0.005*t / C) * A = 400*t N,  t in [0,1]
```

At step-relative time `t`, `TOP RF3` should be `-400*t N` and the bottom
support should balance it. Both blocks shorten uniformly by `0.002*t mm`; the
upper and lower interface averages are `-0.003*t mm` and `-0.002*t mm`, so
the geometric interface gap is `-0.001*t mm`. The top displacement is
`-0.005*t mm`. These profiles, reaction closure, endpoint force and endpoint
pressure compliance use the prior predeclared gates: force error at most
`1% + 0.001 N`, displacement/profile/interface-gap/face-warp error at most
`1e-5 mm`, and pressure-compliance error at most `1% + 1e-10 mm3/N`.

The linear oracle is approximate for `NLGEOM`. The source-derived uniform
St Venant-Kirchhoff endpoint estimate is `399.519872 N`, `0.120032%` below
the 400 N linear answer. This is explanatory only; acceptance continues to
use the frozen linear oracle and existing tolerances.

Every captured MORTAR iteration must be at or below the source-derived
`ndiverg=14`, since pinned 2.23 `stressmortar.c` clears the active-set flag
above that threshold. The accepted `.sta` iteration must equal the last `.cvg`
iteration for that increment. FRD `COPEN` and `CPRESS` remain finite-field
availability/coverage diagnostics; their MORTAR values are weighted or
transformed, so they are not pointwise law or force gates.

## Records and next action

`prepare.py` verifies the original input and expected-record hashes plus the
pinned source-archive hash, then slices off the original three-step tail and
adds one compression step. It asserts that the resulting decks differ only
at the contact `TYPE` value. `expected.json` retains the prior analytical
gates and records the one-step schedule and its discrimination limit.

The parent owns static review, immutable input freeze, bounded serialized
execution, and result audit. Do not run either deck before that review and
freeze. No large joint analysis is part of this packet.
