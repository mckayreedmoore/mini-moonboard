# Conditional floor-stick coupled-load fixture — attempt01

## Result

This fixture adds load-driven state selection to the prescribed-state
arithmetic already recorded in the [feasibility plan](../next-gate-feasibility-plan-2026-09-29.md).
It couples one compression-only normal support to two ideal tangential stick
axes and a sequence of open, bearing, release, and re-engagement loads. The
small analytic selector enumerates the open and bearing normal branches and
requires exactly one admissible branch at every load stage. Tangential stick
is then enabled only for strictly positive normal reaction; zero-reaction
touch is released.

The recorded run of [`verify_fixture.py`](verify_fixture.py) returns
`PASS_LOCAL_ANALYTICAL_FIXTURE` for all eight stages. Each stage has one
admissible normal branch. Maximum vertical equilibrium residual,
tangential equilibrium residual, and bearing slip are all zero at the
fixture's `1e-12` tolerance. At the load threshold `P = 10 N`, the contact is
classified as a zero-reaction released touch. Loading to `20 N` gives
`N = 5 N` and `g = -0.05 mm`; unloading to the threshold releases both normal
and tangential reactions. Re-engagement at `14 N` gives `N = 2 N`, resets the
tangent reference to `(0.25, 0.15) mm`, and preserves zero tangent motion.
The subsequent `(7, 1) N` tangent load produces the exact ideal constraint
reaction `(-2, +2) N`; opening again sets tangent reaction to zero.

## Fixture method

The normal fixture uses the same `100 N/mm` penalty value as the earlier
hand-solvable oracle, with a `100 N/mm` *fixture-only* vertical carrier spring
and `0.10 mm` initial gap. Positive `z` is upward, positive `P` is downward,
and

```text
g = g0 + z
N = kn * max(0, -g)
Rcarrier = -kz * z
N + Rcarrier - P = 0
```

For an open candidate, `N = 0` and equilibrium gives `z = -P/kz`; it is
admissible when `g >= 0`. For a bearing candidate, solve
`z = -(P + kn*g0)/(kn + kz)` and `N = -kn*g`; it is admissible only when
`g < 0` and `N > 0`. The selector checks both candidates directly; it does
not iterate. The threshold is `P = kz*g0 = 10 N`. At the threshold, the
open and penalty equations meet at `g = N = 0`, which this fixture classifies
as released, so no tangent reaction remains active.

The tangent fixture uses two orthogonal `20 N/mm` reference springs. While
`N > 0`, it fixes `u` at the current episode reference and solves `T` from
`H - 20u + T = 0`. While open, it sets `T = 0` and solves `u = H/20`. On
re-engagement, it captures the preceding open displacement before the next
tangent load increment. These reference springs and the vertical carrier
spring are fixture devices only; they are not estimates of floor, frame, or
connection stiffness.

The exact inputs and expected states are in [`fixture.json`](fixture.json);
the observed deterministic output is [`observed.json`](observed.json).
Reproduce from the repository root with:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/conditional-floor-stick-coupled-load-fixture-attempt01/verify_fixture.py
```

The verifier enumerates the two scalar normal branches at each load stage,
checks branch admissibility, applies the tangent rule selected by the normal
reaction, and verifies vertical and tangent force closure. The zero-reaction
threshold is classified as released; the run does not claim a production
near-zero tolerance or hysteresis rule. The complete observed stage record is
the JSON output above.

## Applicability and stop boundary

This is a load-driven, one-cell analytical mechanism check. It adds a distinct
check beyond prescribed gaps and reactions, but it does **not** establish
multi-cell load sharing, rotational coupling, uniqueness of a full-frame
active set, production tolerance behavior near zero reaction, or a native
solver implementation. It supplies no actual floor reaction, friction value,
anchor claim, or capacity. The full floor-support gate remains **BLOCKED**;
the result only supports scoping a later parent decision about an
implementation method. A multi-contact method that has multiple admissible
states, no admissible state, or cycling must stop with the affected support
forces unresolved. This fixture does not qualify that multi-contact method.
No mesh, CalculiX, Code_Aster, or other native solver was run.

## Source pins

| Source | SHA-256 |
|---|---|
| [`AGENTS.md`](../../../../../AGENTS.md) | `672203b929d51d340d39d770e71dd43b019794ea33172bc9f4f7be469fc20536` |
| [Feasibility plan](../next-gate-feasibility-plan-2026-09-29.md) | `1d0162a17071db7e029dc8d893dc41ce3f55ef4991e91f8596923c86d2503812` |
| [Option A/B comparison](../option-ab-method-selection-2026-09-29.md) | `d73dc9b2583c88b64fab4a8e61b1910dfbdb2881cc6dde629b30911a5425c76a` |

The local artifact files are listed in [`SHA256SUMS`](SHA256SUMS).
