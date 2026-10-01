# BG045 component sensitivity at the A12 BG001 tie-stiffness point

Status: **source-bound conditional component sensitivity only**. This report
applies the unchanged BG045 resultant-angle Mode IV with `Ceg` and the existing
header washer-seat `Fc_perp` reference to the two BG045 lateral planes and two
outer-seat tie actions in each of seven A12-rear sensitivity increments. It
compares directions and edge flags only with the prior accepted numerical A12
baseline. It does not evaluate the other corner groups.

Reproduce and verify from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-bg045-stiffness-sensitivity-attempt01/produce.py --write
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-bg045-stiffness-sensitivity-attempt01/produce.py --verify
```

The producer binds the sensitivity model, deck, native DAT, freeze, terminal
execution, seven-increment response, parent all-50-body audit and the signed
14-connector comparison. It checks that each response gate is true at every
increment, all fifty physical bodies and global equilibrium pass the parent
audit, and the four BG045 connector actions at each increment match the
baseline/variant vectors in the parent-pinned comparison. The earlier A12
response is also checked against the reviewed BG045 final-increment report.
This report consumes 28 BG045 signed action rows from that 98-row comparison.

## Conditional component results

At load factor 1.0, reducing the two BG001 tie stiffnesses from
4670.0542 N/mm to 2401.7144 N/mm (0.51428×) gives these BG045 component
comparisons:

| BG045 axis | Lateral demand, baseline → sensitivity | Mode IV reference after `Ceg` | Demand/reference, baseline → sensitivity | Header tie, baseline → sensitivity | Header `Fc_perp` ratio, baseline → sensitivity |
|---|---:|---:|---:|---:|---:|
| Axis 1 | 90.1157 → 92.8118 N (+2.992%) | 401.1378 N | 0.22468 → 0.23137 | 119.3430 → 118.0730 N (−1.064%) | 0.12964 → 0.12826 |
| Axis 2 | 24.9462 → 24.4072 N (−2.160%) | 400.4246 N | 0.06230 → 0.06095 | 19.8817 → 19.7075 N (−0.876%) | 0.02160 → 0.02141 |

The seven matched increments preserve the baseline force signs and face flags.
The block-plane ray first meets +X for both axes and the block group resultant
in both runs. A12 axis 1's block +Y component still faces the 20 mm source
envelope edge; the prior screen labels this a conservative component-face
sensitivity because the ray reaches +X first. Header axis 2's isolated −Y
component still faces its 20 mm source-envelope edge. Both are unresolved
conditional detailing questions; the oblique header vector is not treated as
a direct Table 12.5.1C result. See `sensitivity.json` for the signed actions,
angles, references, ratios, component-face states, ray flags and provenance at
all seven increments.

The lateral values are individual-bolt resultant-angle references under the
prior named scenario: 1/4-in smooth full-body bolt, conditional DF-L No. 2
`SG=0.50`, stated block/header bearing lengths, zero gap, `Fyb=45 ksi`, and
`Ceg=0.67` once. They are not group or complete-joint capacities, nor a
combined lateral/axial interaction check. The header axial-seat comparison
reuses the candidate minimum washer annulus and unadjusted `Fc_perp` component
reference from the prior BG045 screen. The washer remains an unselected
dimensional lead and the screen assumes uniform pressure over a fully
supported annulus. No block `Fc_parallel` value is assigned.

The variant's numerical response passes all seven physical gates and the
parent's all-50 body/global audit for this conditional A12 branch. The
parent-terminal record explicitly retains no mechanical acceptance, six-case
envelope or physical stiffness bound. This single stiffness point does not
establish a physical stiffness range or branch uniqueness. No splitting,
net-section, group-capacity, broader corner or whole-joint pass is inherited
from the prior BG045 screen.

The exact report, native and method source hashes are in `sensitivity.json`;
the pinned primary NDS source metadata and the full dependency pins for the
reviewed BG045 method screen are carried forward there as well.
