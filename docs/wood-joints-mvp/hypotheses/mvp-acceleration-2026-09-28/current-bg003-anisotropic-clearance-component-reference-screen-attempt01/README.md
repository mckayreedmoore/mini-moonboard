# BG003 anisotropic-clearance component-reference screen

This bounded packet uses the eight saved A12-rear BG003 bolt-1 anisotropic-clearance proxies to form conditional comparisons for the saved receiver bearing samples and the paired bolt bending stress. It performs no beam, frame, or native solve. The source is the same full-load `a12-rear` state for `knee_outer_left_side_1`; plane 37 and plane 38 carry the identical 95.96739 N physical outer-seat tension, which is applied once in the signed steel stress calculation.

For wood, each receiver output stores a signed Y/Z line-force vector at its maximum-sampled resultant `p/d` point. The producer divides the force per unit length by the modeled 6.35 mm diameter, computes its angle to the receiver's proposed undirected grain axis, and compares that local sampled pressure with unadjusted NDS-2024 `Feθ` under the conditional DF-L No. 2, `G=0.50`, full-body `D=0.25 in.` scenario. It uses `Fe∥=11200G=5600 psi`, `Fe⊥=6100G^1.45/√D=4465.461 psi` (unrounded formula value), and §12.3.4 Eq. 12.3-11. The `p/d` value is a nominal projected-bore average from a line resultant; the model does not resolve pressure around the bolt circumference. The inner block remains the explicit hypothetical final-section No. 2 / `CFstudy=1.0` case; no grade transfer or delivered species is asserted.

The 32-division saved samples give the following point/reference ratios. Each pressure, angle, and `Feθ` comes from the same receiver's maximum-sampled resultant point in that scenario.

| Density hypothesis (kg/m³) | Gap hypothesis (mm) | Receiver | Acute force-to-grain angle | Sampled `p/d` (MPa) | Conditional `Feθ` (MPa) | Sample / `Feθ` reference |
| ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 350 | 0 | Spine | 36.104° | 8.413 | 35.481 | 0.2371 |
| 350 | 0 | Side | 73.996° | 5.329 | 31.270 | 0.1704 |
| 350 | 0 | Inner block | 0.638° | 0.902 | 38.609 | 0.0234 |
| 350 | 0.575 | Spine | 34.143° | 14.630 | 35.749 | 0.4092 |
| 350 | 0.575 | Side | 80.800° | 6.574 | 30.949 | 0.2124 |
| 350 | 0.575 | Inner block | 0.757° | 3.191 | 38.609 | 0.0827 |
| 550 | 0 | Spine | 35.799° | 8.770 | 35.523 | 0.2469 |
| 550 | 0 | Side | 74.884° | 6.558 | 31.218 | 0.2101 |
| 550 | 0 | Inner block | 0.679° | 1.041 | 38.609 | 0.0270 |
| 550 | 0.575 | Spine | 35.252° | 18.587 | 35.598 | 0.5221 |
| 550 | 0.575 | Side | 80.351° | 8.179 | 30.965 | 0.2641 |
| 550 | 0.575 | Inner block | 0.778° | 4.138 | 38.609 | 0.1072 |

The maximum sampled point/reference ratio is 0.5221 for the spine at 550 kg/m³ and 0.575 mm modeled gap. These are conditional arithmetic comparisons against an NDS embedment reference, not NDS design DCRs, dowel-yield capacities, or joint checks. The line-foundation stiffness and gap are uncalibrated hypotheses. The adapter saves one maximum-sampled resultant point per receiver, not a proven continuous pressure maximum; its prior 16/32 comparison reports 4.27% inner-block pressure change and 1.05% side pressure change in the 550 kg/m³, 0.575 mm scenario. The coupled Y/Z action remains one vector; no plane capacities are summed. The screen makes no `Fc⊥` washer/gross-contact comparison.

For steel, the producer keeps the exact signed middle-cut and sampled-peak `(My,Mz)` vectors. It combines each paired moment norm with the one same-state positive tie tension to calculate the two signed bending-extreme normal stresses on a smooth full 6.35 mm circular section: `T/A + |M|/Z` and `T/A − |M|/Z`. The selected reference is the existing conditional SAE J429 Grade 5 92 ksi machine-test yield value (634.317671 MPa) for the nominal diameter band. At 32 divisions, sampled-peak extreme stresses are:

| Density hypothesis (kg/m³) | Gap hypothesis (mm) | Tension extreme (MPa) | Opposite extreme (MPa) | Maximum absolute stress / 92 ksi |
| ---: | ---: | ---: | ---: | ---: |
| 350 | 0 | +180.698 | −174.638 | 0.2849 |
| 350 | 0.575 | +145.110 | −139.049 | 0.2288 |
| 550 | 0 | +146.481 | −140.421 | 0.2309 |
| 550 | 0.575 | +118.116 | −112.056 | 0.1862 |

The outer-seat tie comes from the two identical signed-demand records and is used once as tension. The selected steel reference is conditional: the hardware packet lists Ro-Brand HC5127 as a catalog/length lead and does not establish exact J429 conformance. The stress screen omits actual thread roots, reduced sections, runout, shear, torsion, preload, fatigue, fracture, steel interaction, and physical contact bounds. No delivered bolt property is asserted.

The raw signed vectors, per-scenario 16/32 records, directional calculations, stress calculations, input hashes, and scope flags are in [`component-reference-screen.json`](component-reference-screen.json). The calculation pins the saved finite result and its transitive source chain, the signed same-state demand register, the existing steel-reference helper, the material inputs, and the cached primary NDS chapter file in [`source-pins.json`](source-pins.json).

Replay the source-pinned arithmetic from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg003-anisotropic-clearance-component-reference-screen-attempt01/produce.py --verify
```

`--verify` is read-only. `--write` regenerates only this packet's `component-reference-screen.json`.
