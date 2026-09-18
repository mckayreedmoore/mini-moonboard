# Conditional panel-screw lateral and combined-load reference

The current SPAX XFT08P-2000 screw has a calculated **52.983 lbf (235.680 N)**
single-fastener lateral reference under the inputs below. This fills the missing
DF-L/other-grade-plywood lateral calculation without reassigning the report's
SPF test table. It is **not an adjusted allowable load or a frame qualification**.
Current screw demands, installation adjustments and head-capacity applicability
remain unresolved.

## Inputs and method

[SPAX TER 2010-02, Table 2](https://www.drjcertification.org/report/download/1936)
provides the screw dimensions and bending yield strength. Its Section 6.3 permits
NDS dowel design. This calculation uses [AWC TR12](https://web-media.awc.org/wp-content/uploads/2021/12/17210714/AWC-TR12-1510.pdf),
Table 1-1 and Appendix A, and [NDS 2018](https://plib.org/wp-content/uploads/2020/09/AWC-NDS2018.pdf),
Tables 12.3.1B/12.3.3B and Sections 12.3.5–12.3.7. This identifies the edition
actually inspected; equivalence to the project's other 2024 references has not
been established by this calculation.

| Input | Value / basis |
| --- | --- |
| Receiver bearing | DF-L, G=0.50; Fe=4650 psi |
| Plywood bearing | Other grades, unknown ply species; G=0.42; Fe=3350 psi |
| Effective dowel diameter | 0.100-inch thread root throughout, including the larger shank region |
| Bending yield strength | 187,000 psi, evaluated at the root diameter |
| Plastic bending moment | Fyb × Dr³ / 6 = 31.1667 lbf·in |
| Main bearing length | 2 − 23/32 − 0.163 = 1.11825 inches |
| Side bearing length | 23/32 − 0.320/2 = 0.55875 inches |
| Reduction term | Rd=2.2 for all six modes |
| Interface | One shear plane; faces seated, zero gap |

The main-length deduction uses the permitted tapered-tip approximation E=2D,
with the larger major diameter to reduce bearing length further. This lateral
deduction does **not** change TER's withdrawal convention, which includes the
tip. The side-length deduction excludes the entire ideal 90-degree head cone
to its apex: a conservative modeling choice, not a prescribed countersink depth.
These simplifications give no extra capacity credit for the larger shank or head.

Calculated mode references in lbf are Im=236.357, Is=85.082, II=74.354,
IIIm=85.340, **IIIs=52.983**, IV=70.820. No fastener-count multiplier is applied.
The conservative plywood bearing assignment avoids needing the internal veneer
species for this lateral calculation. It does not establish the separate
G≥0.50 condition for TER's 212 lbf plywood head pull-through reference.

## Combined wood loading

With tensile withdrawal demand T, lateral demand V, and resultant R=hypot(T,V),
NDS 2018 Equation 12.4-1 becomes:

`wood interaction ratio = (V²/Z + T²/W) / R`

Here W and Z are **total adjusted force references**, not W per inch of thread.
At zero load the ratio is zero. Head pull-through is checked separately as T/H,
using an applicable adjusted head reference H. The calculator requires H to be
provided; it does not silently adopt the conditional 943.023 N value.
Compression/contact is outside this tension-only calculation.

TER gives isolated steel tension/shear references, but those two separate
numbers do not establish combined steel resistance. The output leaves that
gate unresolved. No result validates load sharing, prying, splitting, cyclic
behavior, net-panel strength or the physical installation.

## Reproduction and next use

[Calculator](../fea/round_structural_screw_reference.py) ·
[Saved result](../fea/results/round-structural-screw-reference-v1.json) ·
[Tests](../tests/test_round_structural_screw_reference.py)

```sh
uv run python -m fea.round_structural_screw_reference --output /tmp/screw-reference.json
uv run pytest -q tests/test_round_structural_screw_reference.py
```

Use a fresh output path. The calculator authenticates the current geometry audit,
checks all 56 nominal penetration lengths, and records source hashes. Tests cover
an independent mode-IV equation, pure and mixed loading, missing head resistance
and invalid demands. Next supply supported current screw demands, applicable
adjustments and a head/steel resistance basis. The geometry and hardware schedule
are unchanged by this reference calculation.
