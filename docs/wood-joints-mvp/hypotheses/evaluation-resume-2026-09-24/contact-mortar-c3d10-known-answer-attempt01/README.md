# C3D10 mortar compression coupon

## Status and scope

This packet is prepared for parent review. It has not launched CalculiX.
Native execution remains unauthorized until the parent reviews and freezes
these inputs. The coupon checks one static contact method on two small elastic
blocks; it is not a joint model, a strength check, or acceptance of a full
wood-joint analysis.

The packet contains two separate decks:

- `input/mortar_c3d10.inp` uses one `TYPE=MORTAR` contact pair.
- `input/penalty_c3d10.inp` uses one `TYPE=SURFACE TO SURFACE` pair with the
  same linear pressure-overclosure slope. It is a method comparison only.

Each deck has one contact type. The decks differ only in the `TYPE` value on
the contact-pair card; the mortar and penalty formulations are never mixed in
one input file.

## Pinned source and fixture

The intended toolchain is the unpatched CalculiX 2.23 executable from image
`sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38`.
The executable path is `/usr/local/bin/ccx-upstream-2.23` and its SHA-256 is
`c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863`.
No patched or instrumented executable is part of this fixture.

The primary reference is the [CalculiX 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf),
p. 248–249, §6.7.8, and p. 438–439, §7.22. The manual limits MORTAR to static
analysis, disallows mixing mortar and penalty contact in one deck, and requires
element-face surfaces for quadratic contact elements. The manual also cautions
against extra slave-edge MPCs. The decks use no `*FRICTION` card and add no
constraint to a slave contact node.

The exact 2.23 source archive and member hashes are in `expected.json`.
`contactpairs.f` maps `TYPE=MORTAR` to mortar mode 2 and
`TYPE=SURFACE TO SURFACE` to mode 1. `surfacebehaviors.f` and
`getcontactparams.f` parse a linear slope `K` and map it to mortar compliance
`1/K`; here `K=100000 N/mm3`. `getnumberofnodes.f` identifies C3D10 as a
10-node tetrahedron with six-node faces, while `slavintmortar.f` dispatches
those faces to `shape6tri`.

The source also controls acceptance. `stressmortar.c:138` initializes
`ndiverg=14`, line 210 may raise it using active slave nodes and contact-pair
count, and line 752 clears the convergence flag when the iteration exceeds
that limit. This fixture has at most nine unique slave-face nodes and one
contact pair, so the source-derived limit remains 14. Reject the method check
if any captured mortar iteration exceeds 14; the accepted `.sta` rows must
finish at or below that limit.

The two 2 mm cubes reuse the frozen C3D10 geometry from
`contact-output-known-answer-attempt01/baseline/coupon.inp`, scaled by 0.02.
That source deck SHA-256 is
`059c07fb59b500e78578413d0d9538076cabacda7154b035baeee334fdc40404`.
Static preparation checks all 12 tetrahedron Jacobians, straight midside
nodes, element-face ownership and outward orientation, matching six-node
contact faces, and the 4 mm2 contact area. The upper slave faces are elements
1 and 2, S1; the lower master faces are elements 11 and 12, S3.

Each body has `E=100000 N/mm2` and `ν=0`. The lower bottom face has `U3=0`.
One corner on each body's non-contact end fixes `U1,U2`; a second corner on
the +x edge fixes `U2` to remove lateral rigid motion and rotation. These are
minimal fixture anchors, not joint supports. Every node's `U,RF` is requested
in both `.dat` and `.frd`; the contact request is `CDIS,CSTR` on every
increment.

## Load history and analytic reference

Each deck has three `*STEP,NLGEOM` steps with a `*STATIC` procedure, a nominal
ten increments per step, and maximum increment 0.1:

1. Open: prescribe the upper top face to `U3=+0.001 mm`.
2. Compress: prescribe it to `U3=-0.005 mm`.
3. Reopen: prescribe it to `U3=+0.001 mm` again.

The initial interface is touching at `z=0`; it is opened by prescribed motion,
not by an adjustment. No external pressure or point force is applied. Under
the linear series-compliance reference,

```text
C = Lupper/E + Llower/E + 1/K
  = 2/100000 + 2/100000 + 1/100000
  = 0.00005 mm3/N
```

At the compression endpoint, `δ=0.005 mm` gives `p=δ/C=100 N/mm2` and
`F=pA=400 N`. The expected CalculiX reaction convention is top `RF3=-400 N`
and bottom `RF3=+400 N`, matching the sign in the existing CalculiX 2.23
coupon output. Expected body shortenings are 0.002 mm each and expected
contact overclosure is 0.001 mm. The upper interface average displacement is
`-0.003 mm`; the lower interface average is `-0.002 mm`.

At that compression endpoint, compute recovered pressure compliance as
`C_pressure = A * abs(top U3) / abs(sum(top RF3))`. Compare with
`0.00005 mm3/N` under the additive bound
`abs(C_measured - C_analytic) <= 0.01 * C_analytic + 1e-10 mm3/N`.
The force bound is `abs(F_measured - F_analytic) <= 0.01 * F_analytic +
0.001 N`. Do not compute compliance from open-state zero-force outputs.

At open and reopened endpoints, the geometric clearance is 0.001 mm and both
support reaction resultants should be zero. `expected.json` records the
all-node displacement profile through every increment, force closure,
tangential displacement, face warp, and tolerances. The linear series oracle
is an approximation for the `NLGEOM` deck at about 0.1% axial strain; the
predeclared 1% force/compliance and `1e-5 mm` displacement tolerances cover
that small finite-geometry difference.

The source writes MORTAR `CDIS,CSTR` through the FRD contact fields. However,
its gap is a weighted dual quantity and its contact stress is transformed
before FRD recovery. Treat `COPEN` and `CPRESS` as field availability,
coverage, and diagnostic sign summaries only. Do not infer force by naively
integrating the nodal field, require pointwise `CPRESS=K*(-COPEN)`, or use
field sign variation as a hard failure. Use all-node displacement geometry
and support reactions for the hard analytical checks.

## Records and next action

`prepare.py` verifies the frozen reference deck, pinned 2.23 source archive,
source-member hashes, and local manual hash. It creates both inputs,
`expected.json`, and `readiness.json`; it refuses to regenerate after
`input-freeze.json`, `execution.json`, or `output/` exists. The prepared
input hashes and geometry checks are recorded in `readiness.json`.

The parent owns the reviewed input freeze and serial bounded execution using
the unpatched image. Expected case names are `mortar_c3d10` and
`penalty_c3d10`; the parent runner records `.dat`, `.cvg`, `.sta`, `.frd`,
`.log`, stdout, stderr, and execution JSON under `output/<case>/`. Before
accepting the MORTAR run, check all captured `.cvg` iterations against the
source-derived limit of 14 and require accepted `.sta` increments to match
their final `.cvg` iteration rows. No large joint solve is part of this packet.
