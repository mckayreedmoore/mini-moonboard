# Aligned first-knot cleat momentum comparison — K=100000 vs K=10000

This compares the immutable baseline and child outputs at the same first
accepted physical time, `t=0.001 s`. Each has one accepted `0.001 s`
increment from zero initial velocity. The baseline took 25
iterations and the child 26; iteration count is only an
operational observation. The frozen penalty-comparison contract is pinned in
`report.json`.

The frozen input artifacts retain the same mesh, material, actuator, complete
pilot deck, and nut-coupling files. The contact fragments differ only at the
linear surface-behavior scalar: `100000` versus
`10000 N/mm³`. This is a numerical enforcement
sensitivity, not physical contact stiffness. Both decks apply an exact
`100 N` reference resultant per cleat side, with the same
first-knot ramp factor `0.000298` and impulse
`1.49e-05 N·s` along N.

The W00 cleat has 5,157 C3D10 elements and 9,369
owned nodes. One untransformed CalculiX 2.21 four-point consistent mass
operator was built from the pinned shared mesh and used for both complete
`DISP`/`VELO` states. Its total mass is `0.558187221259 kg`.

| Cleat quantity | K=100000 | K=10000 | Child minus baseline |
| --- | ---: | ---: | ---: |
| COM displacement X (mm) | -4.4856233671e-07 | 8.39586005763e-08 | +5.32520937286e-07 |
| COM displacement Y (mm) | -1.01727152626e-05 | -1.01815597138e-05 | -8.84445117795e-09 |
| COM displacement Z (mm) | 8.64052952338e-06 | 8.62998799236e-06 | -1.05415310219e-08 |
| Momentum X (N·s) | -5.00763097342e-07 | 9.37291807725e-08 | +5.94492278114e-07 |
| Momentum Y (N·s) | -1.13565590629e-05 | -1.13664338261e-05 | -9.87476319966e-09 |
| Momentum Z (N·s) | 9.64606528876e-06 | 9.63429704217e-06 | -1.17682465934e-08 |

The signed complete-vector momentum difference has infinity norm
`5.94492278114e-07 N·s`, or `5.2348%` of the baseline infinity
norm using the contract's `1e-9 N·s` denominator floor. The declared 10%
screen is `BELOW_DECLARED_CHANGE_FLAG`. The COM
displacement difference has infinity norm `5.32520937286e-07 mm` and is
reported descriptively; the contract does not set a separate COM-summary
flag. Neither metric determines a design response or selects a penalty.

Both complete FRD fields contain 116,162 physical-node records. The
consistent-mass COM and momentum calculations use the same element ownership
and the same mass blocks, not equal-node averaging. `report.json` contains
input, snapshot, contract, operator, and helper hashes together with signed
vectors, impulse residuals, and exact comparison arithmetic. No native solve,
CAD operation, principal-block fit, or whole-patch integration was run here.
