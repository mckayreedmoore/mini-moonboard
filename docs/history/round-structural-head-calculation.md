# Conditional plywood head pull-through reference

The current circular SPAX XFT08P-2000 head has a calculated **68.370 lbf
(304.125 N)** plywood pull-through reference with deliberately reduced panel
thickness. This supplies an analytical fallback candidate for the unknown-ply-species
Roseburg plywood. **Actual head-geometry applicability remains unresolved**;
this is not an adjusted allowable or an attachment release.

## Published method and applicability

[NDS 2018](https://plib.org/wp-content/uploads/2020/09/AWC-NDS2018.pdf#page=94),
Section 12.2.5 and Table 12.2F, provide Equation 12.2-6a:

`WH = 690 × pi × DH × G² × tns`, for `tns <= 2.5 × DH` (inches, lbf).

The table covers head diameters 0.234–0.500 inch and net thicknesses
0.3125–1.5 inches; this calculation stays inside both ranges. Table 12.2F
footnote 2 directs panel specific gravity to Table 12.3.3B, whose other-grade
plywood default is **G = 0.42** when ply species are unknown. This does not
establish G ≥ 0.50 for the separate SPAX TER 212 lbf result. For ASD,
Table 11.3.1 lists load-duration, wet-service and temperature adjustments for
head pull-through. End-use factors remain to be established; no impact increase
is adopted. The inspected edition is 2018; consistency with the project's
2024 provisions remains open.

The [SPAX family drawing](https://dxf82wtg340bb.cloudfront.net/resources/8-Flat-Head-Unidrive-and-T-Star-Plus-2D-11-5-21.pdf)
was visually inspected: circular 0.320-inch head, 90-degree countersunk profile,
0.115-inch shank. These match the [recorded product geometry](round-panel-countersink-reference.json).
Here circular describes the perimeter, not a domed head profile.

The [AWC underlying research](https://web-media.awc.org/wp-content/uploads/2021/12/17210650/2018-nds-head-pull-through-paper.pdf#page=2)
includes flathead screws countersunk flush in wood and plywood. Its modeling
deducted one-third of countersunk head depth; it deducted full counterbore depth
for recessed bolts/washers. Thus a countersunk screw is not excluded merely
because its top is flat. This supports the general equation's use as a
conditional reference, without asserting that the tested screws were this SPAX
product. The study assigns equivalent panel gravity; the calculation instead
uses the lower NDS default. No extra shank-friction resistance is added.

There is relevant counterevidence: [Simpson's C-F-2025TECHSUP, page 20](https://www.buildsite.com/pdf/simpsonstrongtie/Simpson-Strong-Tie-Fastening-Systems-Technical-Guide-2895928.pdf#page=20)
describes a flat wood-bearing surface as an NDS-function assumption and reports
lower pull-through performance for its angled-underhead flathead screws in
dimensional lumber. It applies factors of 0.8 for DF-L/SP and 0.6 for SPF/HF.
Those are Simpson product/material factors, not transferable SPAX plywood
resistances. This does not erase AWC's countersunk-screw data, but it prevents
claiming that a circular perimeter alone settles actual head applicability.
The smaller thickness input below produces a smaller equation reference;
it does **not prove a lower bound on this SPAX countersunk plywood seat**.
An applicable product basis or supported geometry assessment remains necessary.

## Thickness choice and installation limits

The [2018 commentary, C12.2.5](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf#page=66)
describes full side-member thickness for flush heads and thickness below the
hole for counterbored heads. Its flush convention would give **391.212 N** for
nominal 23/32-inch plywood. Here the calculation excludes the entire ideal
90-degree cone to its apex: 0.320/2 = 0.160 inch, leaving **0.55875 inch**.
That exceeds both the nominal cone-to-shank depth (0.1025 inch) and the research
paper's fractional deduction, reducing the equation's result further. This
is a discretionary calculation reduction, not an NDS-required deduction,
measured head profile or machining depth instruction.

A supported flush seat in intact plywood remains an installation assumption.
Nominal cone arithmetic does not qualify overdriven heads, veneer damage,
oversized seats, defects or thinner delivered panels. Actual seat preparation
and dimensions must support the adopted reference before release.

## Reproduction and remaining checks

[Calculator](../fea/round_structural_head_reference.py) ·
[Saved result](../fea/results/round-structural-head-reference-v1.json) ·
[Tests](../tests/test_round_structural_head_reference.py)

```sh
uv run python -m fea.round_structural_head_reference --output /tmp/head-reference.json
uv run pytest -q tests/test_round_structural_head_reference.py
```

Use a fresh output path. The calculator reuses current-product, all-56-attachment
and geometry-source authentication from the existing screw calculator, then
records its own provenance. Tests check published table landmarks, thickness
saturation, range rejection and stale-source rejection.

Supply an explicitly adjusted head reference to the existing
[wood interaction check](round-structural-screw-calculation.md); this calculator
does not silently change that required argument. Current tensile/lateral demands,
panel contact, combined steel action and all other frame/panel gates remain open.
