# Isotropic steel elastic diagnostic scenario

Status: proposal-only input for response diagnostics, dated 2026-09-24. No
material model or hardware response is accepted by this definition.

This scenario supplies a generic isotropic elastic reference for the 32
response-only hardware solids in one selected WJ04 hardware profile: eight
continuous bolts, sixteen washers, and eight nuts. Geometry role counts come
from the [hardware profile definition](hypotheses/wj04-mechanics-hardware/README.md).
The same reference card may be applied to those bodies for diagnostic
sensitivity work only. That simplification does not assert that the actual
bolts, washers, and nuts share an alloy, grade, or delivered material property.

## Source-backed reference values

The American Institute of Steel Construction (AISC) [ANSI/AISC 360-22,
Table B4.1a](https://www.aisc.org/aisc/publications/current-standards/aisc-360/)
states the steel modulus of elasticity as 29,000 ksi (200,000 MPa). A primary
published AISC study by Mashayekh and Uang, [“Experimental Evaluation of a
Procedure for SMF Continuity Plate and Weld
Design”](https://ej.aisc.org/index.php/engj/article/download/1127/1126/1126),
reports typical steel finite-element model properties of `E = 29,000 ksi` and
`ν = 0.3`. The paper concerns tested structural-steel moment-connection
specimens; it supports these generic reference inputs, not the identity or
properties of the hardware represented here. Retrieved article PDF
SHA-256: `c31583aaa194f454c50d822db417e9493fd39edf804de10e5d6eecc143c62f36`.

The baseline uses the standard's stated metric modulus and the article's
Poisson ratio:

| Input | Value | Basis |
|---|---:|---|
| Young's modulus, `E` | 200,000 MPa | AISC 360-22, Table B4.1a |
| Poisson ratio, `ν` | 0.30 | AISC Engineering Journal model reference |
| Derived shear modulus, `G = E / (2(1 + ν))` | 76,923.076923 MPa | Computed from the two elastic inputs; not a separate sourced or measured property |

The card is explicitly `TYPE=ISO` and contains only `E` and `ν`; `G` is
reported for audit and is derived, not an independent input. These linear
elastic values do not assign a steel grade or define yield, plasticity, or
resistance.

## Declared numerical sensitivity

Use the following full Cartesian sensitivity grid. The `E` values are the
baseline plus and minus 10%; `ν` uses plus and minus 0.05 absolute around its
baseline. These are analyst-declared numerical perturbations for response
sensitivity. They are not statistical confidence intervals, manufacturing
tolerances, lot-property estimates, or asserted physical material bounds.

| `E` (MPa) | `ν = 0.25` | `ν = 0.30` | `ν = 0.35` |
|---:|---:|---:|---:|
| 180,000 | sensitivity | sensitivity | sensitivity |
| 200,000 | sensitivity | baseline | sensitivity |
| 220,000 | sensitivity | sensitivity | sensitivity |

Each pair is an explicit scenario with its own `scenario_id` and
`scenario_sha256`. The baseline is `steel_elastic_diagnostic_baseline_2026-09-24`.
If any declared sensitivity changes the governing response or disposition,
keep the result pending and investigate the material assignment; do not select
a favorable value as a capacity result.

## Solver card and limits

The local CalculiX 2.21 manual is pinned as
[`fea/generated/connection/ccx_2.21.pdf`](../../fea/generated/connection/ccx_2.21.pdf),
SHA-256 `16b6bab5a3f1a40a21fff62379f95c804a58d93758ab2e9a489b18d911dc20c8`.
Section 7.46, `*ELASTIC`, defines `TYPE=ISO` as the isotropic default and
specifies Young's modulus and Poisson's ratio on the following data line. The
material renderer emits that exact form, in MPa-based units:

```text
*MATERIAL,NAME=STEEL_DIAGNOSTIC
*ELASTIC,TYPE=ISO
200000,0.3
```

The model remains a response-only elastic diagnostic. It does not establish
delivered hardware material, grade, heat treatment, proof or yield strength,
plastic response, bolt preload, washer behavior, connection resistance, or
design qualification. It does not transfer any hardware catalog rating or
test result. No native solve or physical hardware inspection is represented
by this scenario.
