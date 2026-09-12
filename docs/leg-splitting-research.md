# Supplemental leg-joint splitting assessment

This assessment supplements the NDS bolt and member checks. It does not create
an NDS perpendicular-to-grain tensile design value or a whole-frame rating.

NDS 2024 §3.8.2 directs designers to avoid perpendicular-to-grain tension where
possible and to consider mechanical reinforcement where it cannot be avoided.
The text does not state that every cross-grain bolt force mandates reinforcement.
Passing bolt distances alone nevertheless does not quantify splitting resistance.
See the [AWC chapter 3 source](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf).

For a separate quantitative comparison, Swedish Wood's
[Glulam Handbook, volume 2](https://www.swedishwood.com/siteassets/5-publikationer/pdfer/glulamhandbook2-240508.pdf),
pp. 202–203, reproduces the EC5 §8.1.4 connection-splitting model:

```
F90,Rk = 14 b sqrt(he / (1 - he/h))
F90,Rd = kmod F90,Rk / gammaM
```

Dimensions are millimetres and forces newtons. `he` extends from the loaded
edge to the most distant fastener. The modeled rim is symmetric across its two
bolt rows, so either load direction gives `he = 98.5481 mm`, `h = 139.7 mm`, and
`b = 38.1 mm`. Full through-bolt penetration engages that thickness. No benefit
from additional bolts along the grain is taken.

Choose dry indoor solid timber, `kmod = 0.8` (medium-term), `gammaM = 1.3`.
Volume 2 table 2.4 includes solid timber; volume 3 table 7.2 gives the solid
wood/connection material factor. See [volume 3](https://www.swedishwood.com/siteassets/5-publikationer/pdfer/glulamhandbook3-240508.pdf).
This is deliberately less favorable than using a short-duration or instantaneous
strength factor for a climbing move. Apply an additional 1.5 load multiplier to
the entire existing dead-plus-doubled-climber load envelope, rather than compare
a factored resistance directly with an unfactored service load.

For the zero-imposed-moment axial-transfer case in
`fea/results/leg-only-load-check-v2.json`:

| Quantity | Result |
| --- | ---: |
| Complete rear compression assigned to one leg | 4,071.70 N |
| Rim transverse force, `P sin(55 degrees)` | 3,335.34 N |
| Additional-factored transverse demand | 5,003.01 N |
| Characteristic splitting resistance | 9,756.20 N |
| Reduced design splitting resistance | 6,003.81 N |
| Demand/resistance | 0.8333 |

The demand assigns the entire transverse connection force to one side of the
rim section rather than crediting its division between the two adjacent spans.
Thus the axial-transfer case passes this supplemental splitting comparison.
The permanent-load-only case uses `kmod = 0.6`: the same geometry and 25 kg
equipment allowance give 1,208.77 N rear compression, 1,485.24 N factored
transverse demand, and 4,502.86 N design resistance (ratio 0.330). This case also
passes; it does not inherit the medium-term factor without a variable load.

This scalar calculation does not independently establish the connection's
moment demand. If the final load model introduces an imposed joint moment,
use its individual bolt forces to check the transverse demand and direction;
do not transfer this zero-moment result silently. The source explicitly discusses
this limitation for moment-resisting groups. The result is a supplemental
engineering calculation under stated assumptions, not a claim of code approval.
