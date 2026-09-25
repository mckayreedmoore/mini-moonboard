# Elastic material scenario for local diagnostics

Status: implementation input proposal, 2026-09-24; no material model or native
response is accepted. This completes the nine-constant definition missing from
the [response-method proposal](ordinary-joint-response-method.md). It does not
supply strength, embedment, splitting, or measured stock properties.

The USDA [2021 Wood Handbook, Chapter 5](https://research.fs.usda.gov/download/treesearch/62244.pdf),
Tables 5–1 and 5–2 on printed pages 5–2 and 5–3, supplies Douglas-fir elastic
ratios and Poisson data near 12% moisture. The first Poisson subscript names
the stress direction; the second names transverse strain. The text explains
that the independently measured averages need not satisfy exact reciprocity.
The parent inspected the rendered Table 5–2. Retrieved PDF SHA-256:
`724c99666ad364c4bd13022b5b1db09bb391166eace37bd920fee1f8d2d23204`.

For the declared `E_L = 11032 MPa` scenario, use these nine independent
constants, with material axes L, R, T distinct from CAD axis names:

| Constant | Proposed value |
|---|---:|
| E_L, E_R, E_T | 11032, 750.176, 551.6 MPa |
| G_LR, G_LT, G_RT | 706.048, 860.496, 77.224 MPa |
| ν_LR, ν_LT, ν_RT | 0.292, 0.449, 0.390 |

For a reciprocal elastic scenario derive the remaining ratios from
`ν_ji = ν_ij E_j/E_i`: ν_RL = 0.019856, ν_TL = 0.02245, and
ν_TR = 0.286764705882353. These are derived model values. They differ from
the table's independent averages (0.036, 0.029, 0.374); do not silently enter
all six measured ratios into a supposedly symmetric elastic law.

The parent formed the normal compliance block with `S_ii = 1/E_i` and
`S_ij = S_ji = -ν_ij/E_i`. Its eigenvalues are approximately
`8.83057e-5`, `1.00253e-3`, and `2.14574e-3` MPa⁻¹. All are positive,
as are the three engineering-shear compliances. This checks mathematical
admissibility, not physical calibration. The numerical adapter must preserve
the solver's component order and engineering-shear convention and repeat
that check on the values actually written to its deck.

Use explicit source grain vectors. Unknown ring orientation requires R/T
orientation scenarios; swap the full material frame consistently, including
shear and Poisson coupling. Scenario sensitivity is not a statistical material
bound. Keep results pending if plausible property or orientation choices
change the governing disposition.
