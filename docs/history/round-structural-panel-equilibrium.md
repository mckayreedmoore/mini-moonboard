# Conditional panel force-equilibrium screen

The current four-screw kicker connection cannot balance a downward 1200 N
single-panel load under the **unchanged conditional screw references and no
panel-edge bearing or backing friction**. Its optimistic sum of maximum lateral
components is **1009.42 N**. This is a mathematical result for those assumptions,
not an adjusted allowable capacity or a verdict on a kicker supported by floor
bearing. The 1200 N case is a diagnostic, not a newly adopted release criterion.
The inherited 250/300 lb, ×1/×2 downward sensitivity cases also exceed that
conditional kicker bound. No geometry or hardware changes follow automatically.

The [reproducible report](../fea/results/round-structural-panel-equilibrium-v1.json)
contains all six panels, all 142 hold locations and 30 force cases. The
[implementation](../fea/round_structural_panel_equilibrium.py) uses the current
attachment datums and authenticated screw/head references. It does not run FEA.

## Derivation and meaning

The existing [wood interaction calculation](round-structural-screw-calculation.md)
implements [NDS 2018 Equation 12.4-1](https://plib.org/wp-content/uploads/2020/09/AWC-NDS2018.pdf):

```text
(V²/Z + T²/W) / sqrt(V² + T²) <= 1,   0 <= T <= H
```

Here V is the magnitude of one screw's in-plane force and T its tensile force.
Z = 235.680 N and W = 733.601 N are the unadjusted conditional lateral and
withdrawal references. H = 304.125 N is the separate provisional plywood head
reference; its assumptions and limitations remain applicable. The
[head-method review](round-structural-head-calculation.md) retains unresolved
applicability to this countersunk SPAX/plywood installation. Subtracting the
ideal cone depth does not establish a conservative physical head resistance.
None of these values establishes a current adjusted design resistance, and this
conditional mathematical envelope is not an upper bound on actual capacity.

Mixed tension permits V to exceed Z in this equation. Therefore simply comparing
a panel's tangential force with its screw count times Z would not prove
infeasibility. Solve the equality for V² at fixed T:

```text
V²(T) = [Z² - 2ZT²/W + Z sqrt(Z² + 4T²(1-Z/W))] / 2
```

For W > 2Z its unconstrained maximum occurs at

```text
T* = (W/2) sqrt((W-2Z)/(W-Z))
V* = (W/2) sqrt(Z/(W-Z))
```

The head-constrained maximizing tension is min(H,T*). For W <= 2Z,
the maximum is V = Z at T = 0. Current values give T* = 266.195 N,
below H, and V* = **252.354 N**. Tests compare this analytic maximum against
10,001 angular samples of the existing interaction envelope, including a binding
head cap and W <= 2Z cases.

For N independent screws, the triangle inequality requires the magnitude of the
net tangential force to be no greater than N V*. Separately, required net
outward force cannot exceed N min(W,H). These bounds allow each screw its best
possible force state without requiring compatibility or simultaneous attainment.
They assume no equal load sharing. Exceeding either bound proves force equilibrium
impossible only within the specified conditional model. Staying below both does
not provide a feasible reaction distribution or satisfy moments.

## Current panels and support assumptions

| Panel | Holds | Screws | Optimistic tangential sum | Optimistic tensile sum |
| --- | --- | ---: | ---: | ---: |
| Lower left | A–F, rows 1–6 | 12 | 3028.25 N | 3649.49 N |
| Upper left | A–F, rows 7–12 | 12 | 3028.25 N | 3649.49 N |
| Lower right | G–K, rows 1–6 | 12 | 3028.25 N | 3649.49 N |
| Upper right | G–K, rows 7–12 | 12 | 3028.25 N | 3649.49 N |
| Kicker left | Kicker 1–5 | 4 | 1009.42 N | 1216.50 N |
| Kicker right | Kicker 6–10 | 4 | 1009.42 N | 1216.50 N |

For downward force D on a main panel at 40 degrees from vertical, the required
in-plane component is D cos(40°), and the outward component is D sin(40°).
For the vertical kicker those components are D and zero. All reported cases
place the complete load on one panel; adjacent seams remain independent.
The four main panels stay below these loose force-only bounds in the sampled
cases. That is **not** a panel or attachment pass.

The geometry places kicker bottom edges at floor height. The preceding
[round-service floor policy](../fea/round_service_floor.py) explicitly excludes
those edges from floor-support credit because their bearing resistance is
unqualified. This screen retains that assumption. If actual panel-edge floor
bearing is credited and justified, its upward reaction can reduce kicker screw
shear and the screw-only impossibility result no longer applies. No physical
floor test is required by this calculation; an analytical installation/support
detail would need its own resistance basis. Other panel-edge bearing and backing
friction are also excluded. Compression-only normal backing contact is allowed
optimistically; it cannot reduce the required net tensile force.

The follow-up [edge-bearing compression reference](round-structural-kicker-bearing.md)
and [pitch-equilibrium calculation](round-structural-kicker-prying.md) test that
support alternative. Eleven of 45 sampled cases still exceed a generous
conditional prying bound even with floor-bearing credit. Thus removing this
screw-only tangential shortfall would not by itself qualify the kicker.

Panel dead weight is omitted in the report to make the downward-load test
optimistic. The function accepts explicit nonnegative panel dead load; its
projection adds to both required components. This omission cannot rescue an
already failed downward-only case. It does prevent interpreting a nonfailure as
a check of the full load. Hardware and hold mass are likewise omitted.

Hold positions determine panel ownership, not equal screw shares. Hold standoff,
eccentricity, applied torque, screw layout moments, panel bending, contact
compatibility, steel interaction, timber splitting, group behavior and applicable
end-use adjustments remain unresolved. Adding those equilibrium constraints can
only restrict the reaction states for these same fixed references and supports;
changing the reference values or credited support changes the problem.

**Not released for construction or climbing.** This finite result identifies a
specific kicker load-path question before spending time on full-frame numerical
solves; it does not qualify the rest of the frame or the actual floor.
