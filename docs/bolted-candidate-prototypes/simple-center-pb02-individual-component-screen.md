# PB02 upright/link individual-component screen

The [screen](../../scripts/simple_center_pb02_individual_component_screen.py)
authenticates the retained `a12-forward` report before using either bolt force.
It pins the report SHA-256, candidate, numerical acceptance, model identity,
diagnostic-scope fingerprint, force owners/axes/source rows, and active geometry
fingerprint `06f0cd1a…d61387`. The report is numerically accepted but explicitly
does **not** qualify actual joint demands.

A later face audit found one active canonical spring outside the true
principal/cleat overlap and no tributary-area basis for the four equal face
springs. These ratios are retained as pre-contact-cell-correction sensitivity,
not current demand evidence, and require recomputation after the model rerun.

## Conditional result

The calculation uses the 2024 NDS with current errata, dry unincised DF-L No. 2,
`G = 0.50`, `Fyb = 45 ksi`, fully threaded 0.189/0.180-in root sensitivities,
zero face gap, and actual member bearing lengths. `CD`, `CM`, `Ct`, `Cdi`,
`Ctn`, `CΔ`, and `Cg` are each 1.0. Each interface has one fastener (`n = 1`),
so the two orthogonal bolts are not treated as one row or group.

| Connection | Axial / lateral demand | Member angles to grain | 0.189-in reference / ratio | 0.180-in reference / ratio |
|---|---:|---:|---:|---:|
| principal–upright cleat | 20.08 / 32.50 N | 38.46° / 78.46° | 455.89 N / 0.0713 | 429.68 N / 0.0756 |
| upright cleat–rear cleat | 0 / 18.49 N | 47.90° / 47.90° | 490.04 N / 0.0377 | 461.87 N / 0.0400 |

Mode IV governs all four sensitivities. The machine-readable output retains all
six mode values, both bearing values, root bending moments, reduction terms,
and adjustment factors. These are conditional one-bolt lateral-yield references,
not complete connection capacities.

## Directional placement finding

For the inclined principal, the solved force points toward the 129.685-mm
transverse edge; that is the loaded edge and exceeds the 4D = 25.4-mm marker.
The 10.015-mm edge is unloaded in this case and exceeds 1.5D = 9.525 mm by only
**0.490 mm** before fabrication tolerance. A transverse force reversal would
make that edge loaded and fail the 4D marker. The recorded 85.072/2421.095-mm
grain-end distances and every cleat end/edge distance pass their nominal
direction-dependent markers for this one force vector.

The link bolt has zero tensile washer demand in this case; this does not qualify
its washer. The upright bolt has 20.08 N tensile washer demand, but no washer
resistance is calculated.

Local crossed-bore splitting and nearby-hole interaction, combined net-section
mechanics, washer metal, bolt/nut/thread resistance, preload, prying, exact
hardware, contact-pressure distribution, tolerances, and the other five load
cases remain unqualified. This is not a rating, drilling, fabrication, or
construction release.

Reproduce with:

```text
.venv/bin/python -m scripts.simple_center_pb02_individual_component_screen
.venv/bin/pytest -q tests/test_simple_center_pb02_individual_component_screen.py
```
