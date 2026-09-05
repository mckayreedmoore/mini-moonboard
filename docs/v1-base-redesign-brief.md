# V1 unanchored-base redesign brief

> Historical rail-frame brief, superseded by the
> [box-frame load-basis audit](../exports/mini_moonboard_v1_stability_screen.md).
> Mass thresholds and the former evaluator API below do not describe the
> current design. Establish the load envelope before choosing footprint changes.

The present V1 frame is **not** an unanchored build candidate.  This brief is
the input contract for its next geometry; it does not select a base for the
builder.

## Evidence that drives the redesign

The CAD-volume stability screen predicts uplift for both directions of the
1.2 kN top-row face-normal load.  The current 192.5 kg screened frame would
need 458.3 kg total mass if its present centre of mass and its two floor toes
were retained.  The fixed-foot beam screen separately predicts 169–351 mm
top displacement, with both lower legs governing.  See the
[stability result](../exports/mini_moonboard_v1_stability_screen.md) and
[fixed-foot FEA screen](v1-fixed-foot-fea-screen.md).

Adding arbitrary ballast is not a resolution: its mass, position, attachment,
floor bearing, and transport method all change the answer.  A new base must
also make a direct, continuous load path from the board/rails to both feet.

## The minimum proposal to model

Provide these values for one chosen concept:

| Required item | Why it is needed |
| --- | --- |
| Front and rear floor-toe coordinates (mm from the existing V1 datum) | Determines overturning leverage in both directions. |
| Overall width and the cross-bracing/racking scheme | Determines lateral stability; the current two-dimensional screen cannot infer it. |
| Every added member's material, finished section, and mass | Required for stiffness, weight, and connection analysis. |
| Added mass and its three-dimensional centre of mass, if any | A low, attached mass changes both normal-direction reactions. |
| Floor contact material, floor type, and a reviewer-approved friction/bearing basis | Required for sliding and local floor checks. |
| Exact connection path into the rails/legs | Needed for bolt, screw, glue, bearing, and tear-out checks. |

## Immediate pre-CAD screen

`evaluate_unanchored_stability` in
[`mini_moonboard/stability.py`](../mini_moonboard/stability.py) evaluates the
two normal-load reactions from proposed combined mass/centre of mass and front
/ rear floor toes.  It is intentionally reusable before the shape exists in
CadQuery.  Example shape of a call:

```python
evaluate_unanchored_stability(
    mass_kg=..., centre_y_mm=..., front_toe_y_mm=...,
    rear_toe_y_mm=..., load_y_mm=..., load_z_mm=...,
)
```

Both reactions must be non-negative in both cases before the concept advances.
That condition is necessary but not sufficient: the subsequent model still
needs contact/slip, racking, member, connection, panel, and local-floor
analysis.  It is not a ballast-sizing tool or construction authorization.
