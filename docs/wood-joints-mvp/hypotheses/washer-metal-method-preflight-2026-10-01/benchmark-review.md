# Independent review: Teranishi 2021 benchmark inputs

**Reviewed:** 2026-10-01. **Scope:** independent transcription and method
boundary review of the proposed benchmark inputs, using the primary article
PDF rather than the owner-authored input note. No model or scenario was run.

## Source and transcription

The locally inspected PDF SHA-256 is
`a68a303250ab4ad43576eed7b3f60f35d98335da5b3d7ca5adb060779e08ad6f`, matching
the reported source file. I visually checked PDF pages 4–5, including Tables
2–4, and checked the article text for the setup and output definitions. The
three proposed Table 4 rows are transcribed correctly:

| Case | Experimental K | FEA K | Experimental Py | FEA Py |
| --- | ---: | ---: | ---: | ---: |
| S40T2.3 | 11.78 | 9.36 | 4.75 | 5.94 |
| S40T6 | 15.22 | 12.16 | 5.98 | 7.11 |
| S80T2.3 | 15.08 | 11.23 | 5.57 | 6.62 |

K is in kN/mm and Py in kN. The article defines K from the initial straight
portion using least squares and Py as the intersection of the first and second
straight portions. It states that the experimental curves were shifted along
the displacement axis to remove initial seating clearance between the nut and
steel test jig. These are assembly load–embedment targets; Py is not the
washer steel's first-yield load or a design resistance.

Table 2 is transcribed correctly for the modeled bolt and washer: `E =
205,000 MPa`, `ν = 0.3`, and `σy = 235 MPa`. The article describes isotropic
linear elasticity, von-Mises yielding, and perfect elastoplasticity for both
steel parts. These are SS400 study inputs and do not identify the candidate
25NWUS material.

Table 3's printed Japanese-cedar values also match the input note:

- `EL/ER/ET = 1386/126/63 MPa`;
- `GLT/GLR/GRT = 70.5/83.0/4.15 MPa`;
- `νLT/νTL = 0.58/0.0173`, `νLR/νRL = 0.405/0.0289`, and
  `νRT/νTR = 0.901/0.378`;
- normal yield `σL/σR/σT = 71.4/2.50/2.50 MPa`, and shear yield
  `σLT/σLR/σRT = 5.20/5.20/5.20 MPa`.

The table's explanatory text also gives `EL:ER:ET = 22:2:1`,
`GLR:GLT:GRT = 20:17:1`, and `EL:GLR = 16.7:1:1`; the printed values agree
within rounding.

## Tensor and applicability boundary

The paired Poisson values are not mutually reciprocal under the conventional
orthotropic engineering-constant relation `νij/Ei = νji/Ej`, with `νij`
defined as transverse strain in `j` under uniaxial stress in `i`. The printed
pairs give:

- L–T: `0.58/1386 = 4.185×10⁻⁴`, versus `0.0173/63 = 2.746×10⁻⁴`;
- L–R: `0.405/1386 = 2.922×10⁻⁴`, versus `0.0289/126 = 2.294×10⁻⁴`;
- R–T: `0.901/126 = 7.151×10⁻³`, versus `0.378/63 = 6.000×10⁻³`.

The discrepancies exceed rounding. Thus the six printed ratios, alongside
the three Young's moduli, do not directly define one symmetric orthotropic
compliance tensor. The public article reports all six ratios but does not
explain which independent reciprocal values were entered in Abaqus/CAE or how
the remaining values were reconciled. The benchmark input note correctly
withholds a solver material card and calls for a small pinned-version check
of index conventions, reciprocal constants, elastic positive definiteness,
and Hill-yield mapping. Reconstructing all table entries as independent
constants would not be a valid elastic tensor.

The source setup is a distinct coupon: square washer side lengths 40, 60, or
80 mm and thicknesses 2.3, 4.5, or 6.0 mm; Japanese cedar block dimensions
`L/R/T = 130/29/99 mm`; a 13 mm **wood bore**; and loading along R. The FEA uses
a quarter-symmetry C3D20 model, fixes the wood bottom in all directions, and
restrains displacement normal to its symmetry planes. It applies
surface-to-surface contact at bolt/washer and washer/wood interfaces, with
friction coefficients 0.4 and 0.3 respectively, using augmented Lagrangian
contact and a reported 205,000 MPa penalty input. That penalty value is a
source-study setting, not a transferable value for another solver or contact
formulation. The 13 mm wood bore does not specify the washer hole or the
finite nut/washer bearing land; those remain needed to reconstruct exact
contact geometry.

The source material constants, contact coefficients, boundary conditions,
and target curves are useful inputs for a reproduction of this study only.
They do not transfer to DF-L No. 2 wood, an ordinary low-carbon washer, a
delivered bolt, the WJ24 geometry, or a design/capacity claim. If used for
method validation, keep measured and FEA K/Py results distinct, preserve the
paper's curve-fitting and displacement-reference definitions, and report any
chosen reciprocal tensor as an explicit reconstruction assumption rather
than a source-reported fact.

## Reviewed artifacts and disposition

The primary article PDF was independently checked against the three selected
response rows, steel properties, wood table entries, and published setup. The
owner-authored packet hashes currently read:

- `benchmark-inputs.md`:
  `2d484a4eb04faa9b1f30752e9536474c15f2060d7c15696fdc3f7f190ff5d9da`
- `teranishi-2021-benchmarks.csv`:
  `3034e5e4d9cab165f3758e660defba87611e889deb0f81993e58591a1f838040`

No transcription error was found in the sampled rows or printed properties.
The substantive reproduction blocker is the unreported reciprocal-Poisson
mapping, not a discrepancy in the three response rows. Any reproduced
benchmark should document its internally consistent tensor and the limits
that follow from that reconstruction. This does not make publication
reproduction a prerequisite for a separately declared conditional scenario.
