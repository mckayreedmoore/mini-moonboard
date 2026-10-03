# Teranishi 2021 washer-embedment benchmark inputs

The owner's research/status relay supplied three paired experiment/FEA rows.
Primary verified the supplied PDF's SHA-256 and visually checked Tables 2–4
on PDF pages 4–5. [Teranishi et al. (2021)](https://link.springer.com/article/10.1186/s10086-021-01973-9)
provides numerical targets for its own square-washer/Japanese-cedar setup.
These are source records for possible method validation, not a candidate
solver result or selected design inputs.

The local PDF is
`/tmp/mini-moonboard-online-inputs-2026-10-01/teranishi-2021.pdf`, SHA-256
`a68a303250ab4ad43576eed7b3f60f35d98335da5b3d7ca5adb060779e08ad6f`.
The source DOI is `10.1186/s10086-021-01973-9`. Raw PDF/page renders stay
local. The independently browsed publisher article identifies the same
geometry, loading, material and output-definition context.

## Paired response targets

The [CSV](teranishi-2021-benchmarks.csv) preserves experimental and numerical
columns separately. Initial stiffness is in kN/mm; the reported assembly
yield load is in kN. No tolerance or error correction is adopted.

| Paper case | Square side, mm | Thickness, mm | Experimental K | FEA K | Experimental Py | FEA Py |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| S40T2.3 | 40 | 2.3 | 11.78 | 9.36 | 4.75 | 5.94 |
| S40T6 | 40 | 6.0 | 15.22 | 12.16 | 5.98 | 7.11 |
| S80T2.3 | 80 | 2.3 | 15.08 | 11.23 | 5.57 | 6.62 |

The paper fits the initial straight segment by least squares and defines Py
from the intersection of two fitted straight segments. Py is an assembly
load–embedment definition, not first metal yield, an ultimate resistance, or
a design capacity. Experimental curves were shifted along the displacement
axis to remove initial apparatus seating slip. Reproduction needs consistent
displacement references and fitting intervals; the three scalar pairs do not
provide a full curve or prescribe a regression pass band. The flexible/thick
washers exercise different combinations of timber indentation and washer
deformation.

## Printed material and setup inputs

Table 2 uses SS400 steel for the washer and bolt: E=205000 MPa, ν=0.30,
yield stress=235 MPa, with isotropic linear elasticity and perfect von-Mises
plasticity. This value does not transfer to the candidate's `25NWUS` washer.

Table 3 prints the following Japanese-cedar inputs. Elastic and yield values
are MPa; the Poisson entries are dimensionless. L/R/T mean
longitudinal/radial/tangential. These are the table's printed constants, not
an adopted reciprocal compliance matrix or DF-L material values.

| Property group | L or LT | R or LR | T or RT |
| --- | ---: | ---: | ---: |
| Young's modulus, EL/ER/ET | 1386 | 126 | 63 |
| Shear modulus, GLT/GLR/GRT | 70.5 | 83.0 | 4.15 |
| Normal yield, σL/σR/σT | 71.4 | 2.50 | 2.50 |
| Shear yield, σLT/σLR/σRT | 5.20 | 5.20 | 5.20 |

The printed Poisson pairs are
`νLT=0.58, νTL=0.0173; νLR=0.405, νRL=0.0289; νRT=0.901, νTR=0.378`.
Do not silently choose or average redundant constants when translating this
table to a solver. Establish its index conventions, the selected independent
constants, elastic reciprocity/positive definiteness and Hill-yield mapping
in a small pinned-version method fixture before a reproduced assembly run.
No consistent tensor or solver material card is approved by this transcript.

The wood dimensions are L/R/T=`130/29/99 mm`, with a 13 mm wood bore and
loading along R. The study fixes the wood bottom in every direction and uses
a quarter-symmetry model with displacement normal to each symmetry plane
restrained. Its C3D20 model has surface contact at bolt/washer and
washer/wood, with reported friction coefficients 0.4 and 0.3 respectively.
It uses augmented-Lagrangian contact and reports a penalty input of
205000 MPa; that number is not a transferable penalty setting for a different
solver, enforcement convention or mesh.

Complete reconstruction still needs finite washer-hole and bearing-part
geometry, edge profiles, loading/displacement definitions, tensor/yield
conventions, contact enforcement and mesh convergence. Those are method
inputs, not new physical-test, receipt or fabrication prerequisites. The
[source-method review](source-method-review.md) and
[independent review](independent-review.md) retain the candidate's separate
partial seat and unqualified ordinary-washer material boundary. Existing
signed candidate outer-seat action joins supply later conditional scenarios;
these benchmarks neither create another demand solve nor a criterion pass.
