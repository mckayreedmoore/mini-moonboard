# Kicker edge bearing does not eliminate prying

**Under the unchanged conditional screw/head references, 11 of 45 sampled
cases per kicker cannot satisfy pitch equilibrium even with generous bottom-edge
bearing credit.** This is a fixed-reference point-force model, not an upper bound
on physical capacity or a climbing rating. The unresolved countersunk-head
applicability in the [head review](round-structural-head-calculation.md) remains.

The [calculator](../fea/round_structural_kicker_prying.py) and
[saved report](../fea/results/round-structural-kicker-prying-v1.json) test the
specific proposed simplification: support the kicker bottom edge on a rigid
floor instead of making its four screws carry all downward load. That changes
the prior [screw-only force screen](round-structural-panel-equilibrium.md), but
an outward hold projection still produces a moment that must enter the panel,
fasteners, backing and floor through real forces.

## Explicit geometry, loads and reactions

Use local outward Y measured from the plywood back, Z upward from the floor.
Panel thickness is 18.25625 mm, screw heights are 60/60/140/140 mm, and the hold
row is 150 mm above the floor. The current source-authenticated mass inventory
gives each drilled kicker 29.4110 N dead weight at Y = 9.127741 mm, using assumed
600 kg/m³ density. This differs slightly from the gross-panel reference in the
[axial compression calculation](round-structural-kicker-bearing.md).

The calculation considers 1200 N downward as a diagnostic, and the inherited
250/300 lb ×1/×2 sensitivities, with 0/50/100 mm outward standoff and −300/0/+300 N
normal force at the hold row. Positive normal force pulls away from the backing.
Each full resultant is applied to one independent kicker. These are project
comparisons, not adopted dynamic design requirements. Hold/accessory weight,
simultaneous hand/foot forces and the actual hold geometry remain separate.

Let T be each screw's inward tensile force, S its signed upward shear force,
and q the depth where that shear acts, anywhere between back and front faces.
Backing reactions B push outward at nonnegative heights. Floor reaction R is
upward only and acts within the panel thickness. No backing or floor friction,
seam transfer or independent screw-head/shank couple is credited.

For downward live load D, outward force P at height h, standoff e, panel dead
weight d at depth y_d and thickness t, equilibrium requires:

```text
sum(S) + R = D + d
sum(T) - sum(B) = P
sum(z*T + q*S) - sum(z_backing*B) + y_floor*R
    = D*(t+e) + P*h + d*y_d
```

Thus the moment is never balanced by an unspecified reaction couple.

## Necessary bound allowing favorable floor and screw reactions

The most favorable floor depth is at the front edge, because R cannot be
negative. Rearward downward screw shear can provide an additional couple
through the panel thickness; simply discarding it would falsely strengthen a
failure claim. With each screw's maximum lateral magnitude Vmax, equilibrium
necessarily implies:

```text
Q = D*e + P*h - d*(t-y_d)
Q <= sum(z*T) + t*sum(max(-S, 0))
Q <= 400*H + 4*t*Vmax
```

H = 304.125 N is the current conditional tensile reference, below the withdrawal
reference; Vmax = 252.354 N comes from maximizing the existing combined-load
equation. Allowing both maxima independently is deliberately generous. They
need not be attainable simultaneously. Current upper products are
121649.819 N·mm from tension and 18428.182 N·mm from vertical shear couples.

The required total tension in the two top screws is at least
`max(0, (Q − 120*H − 4*t*Vmax)/140)`. No equal sharing is assumed. If this exceeds
their conditional sum 2H = 608.249 N, no distribution inside this relaxed model
can work. Normal contact, moment and compatibility restrictions can only narrow
the same model's feasible states.

Panel dead weight can stabilize this edge-bearing moment model. It therefore
cannot be omitted on the claim that omission is always conservative. The
calculation retains the actual modeled centroid and clearly assumed density.

## Results and constructive comparisons

Both current kickers have identical relevant scalar profiles; the report
authenticates both before aggregating their 45 cases. Eleven exceed the generous
necessary bound. Examples with +300 N outward load are:

| Downward case | Standoff | Required top-row tension lower bound | Top-row reference sum |
| --- | ---: | ---: | ---: |
| 1200 N diagnostic | 100 mm | 784.346 N | 608.249 N |
| 250 lb ×2 | 50 mm | 721.528 N | 608.249 N |
| 250 lb ×2 | 100 mm | 1515.853 N | 608.249 N |

A separate restricted linear program constructs two-dimensional witnesses for
22 cases. It sets all vertical screw shear to zero, puts the floor reaction at
mid-thickness, and permits backing reactions at heights 25 and 200 mm. These
heights lie within the post/header backing ranges, but their X locations,
pressure patches and local resistance are not evaluated. Actual summed force
and pitch residuals are checked. This avoids using the bound's ideal front-edge
floor resultant as a proposed contact detail.

The remaining 12 cases have neither a necessary-condition failure nor a witness
in that restricted submodel. Failure of the restricted linear program is not
proof of general infeasibility. Conversely, a two-dimensional witness supplies
no three-dimensional equilibrium, panel stiffness, contact compatibility,
compression/bending/buckling, hold/T-nut transfer or strength acceptance.

## Engineering decision

Bottom-edge support is a possible vertical load path, subject to the separate
axial/local-contact checks. It does not by itself close kicker attachment
qualification. The current conditional reference/load/support combination needs
resolution: a defensible applicable resistance and load basis or a specifically
checked attachment/support revision that also carries prying. No new fastener,
washer, hold limit or floor-support instruction is selected by this calculation.

```sh
uv run python -m fea.round_structural_kicker_prying --output /tmp/kicker-prying.json
uv run pytest -q tests/test_round_structural_kicker_prying.py
```

Use a fresh output path. Tests recover the original moment equation from each
example witness, check randomly constructed equilibrated point-force states,
retain the distinction between restricted infeasibility and the necessary
bound, and verify saved source identities. **The build remains unreleased.**
