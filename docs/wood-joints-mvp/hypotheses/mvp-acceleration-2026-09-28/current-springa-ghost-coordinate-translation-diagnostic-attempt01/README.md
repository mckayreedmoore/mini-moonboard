# SPRINGA ghost-coordinate translation diagnostic — attempt01

This read-only packet tests the emitted coordinates for A12-rear element 3690,
the row that the parent KKT assessment identifies as reduced force-vector
position 1586. It does not modify a model, source file, freeze, or geometry and
does not launch CalculiX.

## Pinned source path and input

The local CCX 2.23 source archive is
`/tmp/ccx_2.23.src.tar.bz2`, SHA-256
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.
The audit verifies archive members before using their source semantics:

- `springforc_n2f.f`, SHA-256
  `706d066ef4b951c6382b754094bc576d98865b86f6272da535b588c7e7282d60`:
  lines 50–57 form static current positions as `pl=xl+vl`; lines 71–96 compute
  `dd0` from `xl`, `dd` from `pl`, set `val=dd-dd0`, and call the spring-law
  evaluator.
- `calcspringforc.f`, SHA-256
  `67d945c054f9e0584432a0f4aef5bd6d3373688530ceaafe4c96796c72b975aa`:
  lines 47–80 interpolate the nonlinear force table using that `val`.
- `materialdata_sp.f`, SHA-256
  `b1089a3d57be2e5477cc9351866513333453bcb050617a408a7b3ff491c083a5`:
  lines 37–40 describe the internal curve as displacement/force.

The exact source input pins are recorded in `known-answer.json` and enforced by
`audit.py`: the selected case's `model.inp`, `model.json`, final `model.dat`,
and serialized `response.json`. The deck binds SPR1787 / element 3690 to ghost
nodes 21300 and 21301. Its emitted coordinates are:

| Node | Emitted coordinate (mm) |
| --- | --- |
| 21300 | `(-134.5, 643.62182968176, 1192.0483260447)` |
| 21301 | `(-134.5, 579.34306873736, 1115.4438817125)` |

The parsed relative vector is `(0, -64.2787609444, -76.60444433220005)` mm and
its actual emitted length is `99.9999999999623` mm. The deck's nonlinear
SPRING table has zero force at zero elongation and a positive-branch tangent
of `3975.8157915 N/mm`. CCX's `dd0` is the norm of these actual parsed endpoint
coordinates. The approximately `3.77e-11 mm` difference from nominal 100 mm is
therefore not an initial spring extension and receives no force “correction”:
the same emitted span is the `dd0` datum subtracted from `dd`.

The emitted MPCs keep node 21300 DOF 1 at zero and set its DOFs 2 and 3 to
`0.64278760944401 * (u_18269,1 - u_18268,1)` and
`0.76604444332249 * (u_18269,1 - u_18268,1)`; node 21301 is fixed. This is a
scalar projected motion carried by a ghost endpoint. The common translation
does not alter those equations or their coefficients.

## Bounded arithmetic result

The final `.dat` displacement tokens for this pair are
`u_21300=(0, 5.874957e-7, 7.001501e-7) mm` and `u_21301=(0,0,0) mm`. The
oracle applies the pinned source's operation order to those unchanged emitted
coordinates and displacements. It then repeats only the arithmetic after a
common translation that moves node 21300 to the origin and preserves the
parsed binary64 relative vector exactly. The translated vector is serialized
at 17 significant digits for a round-trip check; no production deck is made.

| Calculation on the final printed displacement | Elongation (mm) | Table force (N) |
| --- | ---: | ---: |
| Original emitted coordinates, `norm((x2+u2)-(x1+u1))-norm(x2-x1)` | `9.139811254499364e-7` | `0.0036338205916957023` |
| Common-shifted pair near origin, same relative vector and `u` | `9.139810401848081e-7` | `0.003633820252697259` |
| Decimal high-precision result from the exact deck and printed `.dat` tokens | `9.139810501583170e-7` | `0.003633820292350096` |

For these printed tokens, the finite-coordinate operation order changes the
computed force by `-3.3899844e-10 N` (`-8.5265128e-14 mm`). The response record
places the native endpoint RF at `0.003633820631903696 N`, with radius
`7.0441603e-10 N`; both calculated values lie inside that interval. The
direct emitted-coordinate calculation is closer to that RF center for these
rounded displacement tokens. The response record's geometric/table value is
`0.0036338202526972614 N`; this arithmetic comparison does not imply that the
postprocessor and CCX execute identical floating-point paths.

This is a small, measurable-in-binary64 effect, but it is not a plausible
explanation for the failed row-1586 KKT comparison: its direct free-force
minimum differs from the native RF center by about `9.06e-8 N`, roughly 267
times the calculated translation effect. The parent assessment separately
reports 25 force-interval failures; this one-row arithmetic check does not
identify or explain the other rows. It also does not establish that a common
translation would improve native-to-reduced agreement. The final `.dat`
displacements are rounded, and the native RF interval radius is larger than
the calculated shift.

**Readiness decision:** the source confirms a coordinate-dependent binary64
rounding path at this emitted coordinate scale (largest absolute coordinate
about 1192 mm). A translation-only native coupon is not justified as the next
RF-versus-reduced force-reproduction remedy under the currently available
endpoint-force precision: both outcomes fall within the existing RF interval,
and the effect is much smaller than the row's reduced-force miss. The existing
two-body 100 mm relative-coordinate SPRINGA coupon remains the native method
evidence for nested-MPC force transfer; this diagnostic does not extend its
acceptance or change its inputs. The known-answer script is useful to retain
the numerical bound and coordinate values for any later explicitly scoped
coupon decision.

If a later coupon is authorized for a different question, its ghost-only
coordinate change would be separate and explicit: node 21300 to `(0,0,0)`;
node 21301 to `(0,-64.278760944400005,-76.604444332200046)` mm. The common
translation vector is `(134.5,-643.62182968176,-1192.0483260447)` mm. Preserve
the parsed relative vector at 17 significant digits and keep all MPC
coefficients, solid nodes, bodies, and 92 physical axes fixed. This proposal
is mathematical only; it is not a modified or frozen case.

## Reproduction and limits

Run the standard-library audit from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-ghost-coordinate-translation-diagnostic-attempt01/audit.py --verify
```

It checks the local source archive and case hashes, parses the selected deck
row/table and final printed displacements, computes direct/translated/decimal
answers, and verifies them against `known-answer.json`. It performs no solver
execution. Its displacement vectors come from the printed `.dat` tokens, not
the unavailable full-precision converged state, so the arithmetic delta is an
order-of-magnitude diagnostic rather than a reconstruction of native internal
state. It does not diagnose MPC projection precision, determine the causes of
the 25 force misses, or establish any physical/design acceptance.
