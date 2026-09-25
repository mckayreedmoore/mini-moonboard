# Current wood-joint material scenarios

Status: conditional elastic-input proposal for the owner-reviewed
`led-clearance-2x6-runner-seated-blocks-v1` geometry, September 24, 2026.
The source checkpoint is `b1e8707d` as reported with the owner review. This
document defines diagnostic material cases for the current 24-block, seven-
pattern, 92-candidate-bolt model. It does not qualify stock or hardware, define
failure resistance, or accept a joint.

## Timber elastic scenario

Reuse the nine-constant Douglas-fir diagnostic law already defined in
[`orthotropic-material-scenario.md`](orthotropic-material-scenario.md). Its
longitudinal input is the 2024 NDS Supplement's DF-L No. 2 dimension-lumber
`E = 1.6 × 10^6 psi`, rounded to `E_L = 11,032 MPa`. The transverse and shear
ratios come from the USDA Forest Products Laboratory Douglas-fir clear-wood
averages near 12% moisture. This combines a graded-lumber modulus with species-
average clear-wood ratios as a declared model scenario; it is not a measured,
grade-specific orthotropic property set.

| Material constant | Proposed value |
| --- | ---: |
| `E_L, E_R, E_T` | `11,032, 750.176, 551.6 MPa` |
| `G_LR, G_LT, G_RT` | `706.048, 860.496, 77.224 MPa` |
| `ν_LR, ν_LT, ν_RT` | `0.292, 0.449, 0.390` |

For the symmetric elastic law, derive the reciprocal ratios from
`ν_ji = ν_ij E_j/E_i`: `ν_RL = 0.019856`, `ν_TL = 0.02245`, and
`ν_TR = 0.2867647059`. The FPL table's independently averaged reciprocal values
do not satisfy that relation exactly. The proposed solver card uses the three
independent Poisson ratios above and derives the other three; it does not enter
all six averages as if they were a reciprocal elastic tensor. The existing
helper checks the full compliance matrix for symmetry and positive definiteness
and rechecks the serialized values.

`L`, `R`, and `T` in this scenario always mean longitudinal, radial, and
tangential **material** axes. `X`, `T`, and `N` in the candidate geometry are
source-frame coordinate names. Where stock length follows source `N`, the
proposed mapping is `L_material = N_source`; source `T` is not thereby the
material tangential axis.

## Proposed grain vectors for the seven current patterns

The table maps the current geometric patterns to a longitudinal axis for
diagnostic cases. It combines the current stock review with the preserved
source-frame convention. Vectors are unit directions in global XYZ; the sign
of a wood material axis is immaterial, so `±` denotes the same longitudinal
axis. For patterns with no current stock-orientation declaration, the vector
is an explicit analysis choice based on the proposed blank dimensions and
placement. It is not a statement about delivered boards.

| Current pattern | Count | Current proposed blank, mm | Proposed `L_material` / grain direction | Basis and status |
| --- | ---: | --- | --- | --- |
| Common main-member pattern | 15 | `88.9 × 88.9 × 119.7` | `+N_source`; common axis `±(0, −0.766044, 0.642788)` | Stock review assigns grain to source-local `N`. The global axis follows the pinned WJ04 source frame and the recorded proper-rotation matches for this shared pattern. |
| Center-post cleats | 2 | `88.9 × 88.9 × 128.9` | `+Z = (0, 0, 1)` | Vertical stock length in the stock review. |
| Central principal/header cleat, left pattern | 1 | `83.9 × 139.7 × 134.7` | `+Z = (0, 0, 1)` | Plumb block; vertical stock length is the proposed manufacturing direction. Conditional analysis choice. |
| Central principal/header cleat, right pattern | 1 | `83.9 × 139.7 × 134.7` | `+Z = (0, 0, 1)` | Same plumb stock direction; handed geometry remains a separate pattern. Conditional analysis choice. |
| Outer-rim inner-frame blocks | 2 | `88.9 × 133.35 × 139.0` | `+Z = (0, 0, 1)` | Proposed from the 139.0 mm length and vertical placement. The current stock review does not explicitly assign their grain; retain this as a named scenario. |
| Exterior runner-seated spines | 2 | `38.1 × 139.7 × 276.3` | `+Z = (0, 0, 1)` | The 2×6 blank's long dimension follows global Z. This is a conditional stock-layout proposal; the current revision's geometry checks do not establish grain or stock. |
| Shortened upper G7 pattern | 1 | `88.9 × 88.9 × 86.9` | `+N_source`; `±(0, −0.766044, 0.642788)` | Same 4×4 crosscut orientation as the full-stock G7 source frame, with a shorter proposed grain length. Inherited grain proposal, not an observed board. |

The pattern counts total 24. The explicit `+Z` choices for the plumb central
blocks and the two exterior spines are suitable for conditional geometry
screens now. The inner-frame `+Z` choice is less directly documented and must
remain identified as a scenario input. A source-bound model freeze should still
record each of the 24 finished body IDs, its local `X/T/N` unit vectors, and its
selected grain vector. Pattern labels alone do not provide the per-body
orientation records required by CalculiX.

### Unknown radial/tangential orientation

The long-grain vector does not identify growth-ring orientation in a sawn
board. For each physical block, retain two orthonormal transverse assignments:

- For the sloped `+N_source` pattern, use source axes
  `X = (1,0,0)`, `T = (0, cos 50°, sin 50°)`, and
  `N = (0, −sin 50°, cos 50°)`. Case A assigns material `R = X` and
  `T_material = +T_source`; Case B assigns material `R = +T_source` and
  `T_material = −X`.
- For the vertical `+Z` pattern, use the proposed blank frame
  `X = (1,0,0)`, `Y = (0,1,0)`, `Z = (0,0,1)`. Case A assigns
  `R = X`, `T_material = Y`; Case B assigns `R = Y`, `T_material = −X`.

These are two uniform material-frame choices for sensitivity work, not observed
ring locations or guaranteed bounds. The physical stock pieces may have
different ring orientations, including within one geometric pattern. Preserve
per-body assignments in the frozen input; if response depends on the R/T
choice, add the relevant individual-body swaps before interpreting that
response. `material_orientation_cases()` in
[`fea/wood_joint_patch_materials.py`](../../fea/wood_joint_patch_materials.py)
constructs and validates both right-handed assignments from each source frame.

## Steel elastic scenario

Use the existing generic isotropic diagnostic reference for any modeled steel
bolt, washer, or nut body: `E = 200,000 MPa`, `ν = 0.30`, with derived
`G = 76,923.0769 MPa`. Its full declared numerical sensitivity grid is
`E = 180,000, 200,000, 220,000 MPa` crossed with `ν = 0.25, 0.30, 0.35`.
These nine cases are analyst-selected perturbations around the reference, not
material bounds, test variation, or tolerances.

The current model records 92 candidate bolt axes and 460 installed component
roles. The older steel helper and
[`steel-elastic-material-scenario.md`](steel-elastic-material-scenario.md)
are scoped to one WJ04 profile with eight continuous bolts, sixteen washers,
and eight nuts. Their elastic numbers and sensitivity values can be reused as
proposal values; their 32-body scope and hardware identity cannot. Bind the
current candidate as 92 physical bolts, with their actual head/shaft assembly,
two washers, and nut represented consistently. Assign any of the twelve
preserved starting frame-bolt stacks only if they enter the frozen mechanics
model, and record their material mapping separately.

The reference values follow ANSI/AISC 360-22's steel elastic modulus and a
published AISC finite-element study's `ν = 0.30`. They do not identify the
candidate fasteners' alloy, grade, heat treatment, yield strength, plastic
response, preload, or delivered properties. Keep steel elastic response
separate from fastener resistance and connection acceptance.

## What is ready and what the current input still needs

The numerical timber law, reciprocal-Poisson construction, positive-definite
compliance check, two transverse-frame transformations, and CalculiX card
rendering are implemented in the existing timber helper. Its lightweight
contract tests exercise the values, both ring assignments, and the emitted
`*ELASTIC, TYPE=ENGINEERING CONSTANTS` and `*ORIENTATION` data. The steel helper
likewise defines the isotropic baseline, nine sensitivity cases, and its
`*ELASTIC, TYPE=ISO` renderer. The local CalculiX 2.21 manual pinned by these
helpers is `fea/generated/connection/ccx_2.21.pdf`, SHA-256
`16b6bab5a3f1a40a21fff62379f95c804a58d93758ab2e9a489b18d911dc20c8`.

The exact current-model material assignment is not yet source-bound. The
current geometry inventory needs one row per wood body containing its body ID,
geometry/source hash, right-handed global `X/T/N` frame, grain-axis name and
vector, and the selected R/T case. It also needs an explicit current steel-body
map; the WJ04 32-body helper record is not that map. Those rows are the exact
missing inputs for a frozen current-model deck. They are data-binding work, not
a request for another owner approval. The conditional `L=+Z` proposal for the
plumb central blocks can be used in that screen as directed.

The DF-L No. 2 table modulus applies only when the actual product is identified
as that species group and grade. An uninspected blank, nominal dimension, or
retail label is not a grade mark or property measurement. The model has no
measured local `E`, moisture, density, or ring orientation for these pieces.
FPL elastic ratios are clear-wood species averages, not DF-L No. 2 acceptance
limits, lot guarantees, lower bounds, or statistical intervals. Before making
a stock-specific claim, the record would need the delivered species/grade
identity and relevant stock observations; those facts cannot be inferred from
these elastic scenarios.

The [ordinary-joint response method](ordinary-joint-response-method.md)
describes a conditional WJ16 five-body, eight-bolt local patch. It does not
bind or qualify this revised WJ24 24-block geometry. Current loads, complete
joint response, contact and bolt details, and the applicable resistance
methods remain candidate-specific work. Linear elastic material inputs provide
none of those missing resistance properties.

## Primary references

- American Wood Council, [2024 NDS Supplement](https://awc.org/resources/2024-nds-supplement/), Table 4A, sawn lumber design values.
- USDA Forest Products Laboratory, [Wood Handbook, Chapter 5: Mechanical Properties of Wood](https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr282/chapter_05_fpl_gtr282.pdf), Tables 5–1 and 5–2. Table 5–1 gives Douglas-fir clear-wood elastic ratios; the chapter describes their variation and the reciprocity relation for Poisson ratios.
- American Institute of Steel Construction, [ANSI/AISC 360-22](https://www.aisc.org/aisc/publications/current-standards/aisc-360/), Table B4.1a, steel modulus of elasticity; Mashayekh and Uang, [AISC Engineering Journal study](https://ej.aisc.org/index.php/engj/article/download/1127/1126/1126), typical finite-element steel values.
- CalculiX 2.21 Reference Manual, local pinned copy at `fea/generated/connection/ccx_2.21.pdf`, sections 7.46 (`*ELASTIC`) and 7.102 (`*ORIENTATION`).
