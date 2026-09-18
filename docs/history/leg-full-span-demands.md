# Full prismatic-span leg demands

This reporting-only extension scans the actual archived interpolation-node
loads, including the bolt-loaded region that the clear-strip screen excludes.
It leaves all native, CAD and earlier diagnostic sources unchanged.

```sh
uv run python -m fea.leg_full_span_demands fea/results/spread-leg-response/2x6-e300-m40-E7000.tar.gz
uv run pytest -q tests/test_leg_full_span_demands.py
```

For each spring stiffness and climber weight, independent maxima retain their
own governing case, side, cut station and complete simultaneous section wrench.
The report includes axial compression/tension, both shear and bending axes,
torsion, combined biaxial gross-section normal stress extrema, and separate
rectangular-section shear stresses excluding torsion. Do not combine different
peak witnesses into a fictitious simultaneous load.

Both sides of each nodal load station are evaluated. Between these stations,
axial/shear resultants are constant and bending moments are affine, so these
cuts bound the reported first-order gross-section measures. Negative quadratic
interpolation weights are retained. Nodal and virtual-point wrenches are checked
for equivalence below the group before scanning.

This closes a demand-recovery omission, **not a strength or buckling gate**.
The lowest cut is above the entire floor bevel. Net sections, local bolt bearing,
torsional shear, actual restraints, combined member resistance and compliant
floor contact remain unassessed. The archived isotropic, fixed-floor model has
uncalibrated springs and no gravity; its nodal load spread is not physical
bolt-hole bearing. No interaction ratio, load rating or qualification is added.

## Compact versus extended 2×6 evidence

Both native archives now pass all 27 basis checks, with 648 prescribed linear
load combinations each. The compact archive is
[2×6, zero extension](../fea/results/spread-leg-response/2x6-e0-m40-E7000.tar.gz).
Saved full-span reports cover [zero extension](../fea/results/leg-full-span-demands/2x6-e0.json)
and [+300 mm extension](../fea/results/leg-full-span-demands/2x6-e300.json).
The reports preserve all four climber weights and governing witnesses.

For the 250 lb case family, the conditional comparison is:

| Spring stiffness, N/mm | Extension, mm | Peak loaded-hold displacement, mm | Peak bolt lateral demand, N | Peak bolt axial magnitude, N | Peak gross compressive normal stress, MPa |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 0 | 6.619 | 308.63 | 18.20 | 1.717 |
| 100 | 300 | 6.180 | 314.01 | 17.80 | 1.279 |
| 1,000 | 0 | 2.905 | 605.33 | 97.62 | 1.411 |
| 1,000 | 300 | 2.690 | 568.11 | 83.19 | 1.320 |
| 10,000 | 0 | 2.080 | 832.88 | 172.85 | 1.689 |
| 10,000 | 300 | 1.993 | 803.75 | 138.56 | 1.639 |

Columns are independent maxima, not a simultaneous joint load. The gross
normal stress includes simultaneous axial force and biaxial bending at its own
governing section, but no hole deductions or strength comparison. Displacement
and bolt-demand columns use `fea.lumber_leg_summary.summarize` on the same
archives. Values are conditional on the spring and fixed-floor assumptions;
the long-bolt viewer does not calibrate these spring constants.

For compact legs at 250 lb, the 100 N/mm case governs near the lowest full-width
cut (18.821 mm from the foot datum); the 1,000 and 10,000 N/mm cases govern
inside the loaded region (1,562.603 mm from that datum). This is why the
clear-strip check alone was insufficient even for gross first-order demands.

The compact footprint increases deflection in these comparisons, with changes
also sensitive to the unknown connector stiffness. These results support
continuing the compact candidate investigation, not declaring it adequate or
requiring a larger leg. Complete connection resistance, physical restraints and
unanchored contact remain the deciding gaps.
