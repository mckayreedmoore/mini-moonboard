# PB02 rear-clear developmental evidence

This compact package records the current PB02 geometry after raising the rear
cleat 5 mm clear of the floor. It is source-bound analysis evidence, not a
structural approval or a release to purchase, drill, fabricate, or build.

## Scope

- Candidate: `pb02-kerf-right-native-development-only`.
- Geometry fingerprint:
  `4ef3ff0376b4c49142c8a1bc347270da024852e4554cfc4e549b6cafab63dccb`.
- Contact partition: 8x8, with fingerprint
  `e9cb8ea7a1f197728ed3f02e99b27b9b3445446b989a167474e9d6da674c77c4`.
- Mean face-contact stiffness: 1,000 N/mm per canonical interface.
- Bolt axial stiffness: 1,000 N/mm; bolt lateral stiffness:
  3,086.7464105714 N/mm.
- Floor-contact stiffness: 10,000 N/mm. This is a conditional developmental
  input, not a measured or qualified floor property.
- Applied vertical force in every case: -2,224.11080763025 N, plus the stated
  300 N horizontal case force and modeled self-weight.

The `six-case` directory retains all six accepted reports and each report's
final input, DAT, FRD, and 12D files. The six cases are `a12-forward`,
`a12-rear`, `a12-left`, `k12-right`, `k12-rear`, and `a1-rear`. They converged
in 12, 14, 14, 14, 14, and 10 recorded cycles, respectively. Maximum panel
displacements are 13.6140, 17.0472, 14.7127, 13.8285, 16.4463, and 8.59576 mm.

The `refinement` directory retains A12-forward 2x2, 4x4, and 8x8 grids plus
8x8 0.5x and 2x face-stiffness sensitivities. From 4x4 to 8x8, maximum force,
moment, bolt-force, and panel-displacement changes are 3.0081%, 5.6164%,
0.8192%, and 0.000285%. Active area and peak cell-average pressure still
change 8.5557% and 22.8987%, so local pressure is not qualified. Across the
0.5x/1x/2x range, maximum interface-force and moment ratios are 2.17094 and
2.39203; the governing bolt-force ratio is 1.13920.

## Compact-retention boundary

The package has one shared 278-file source snapshot closure. It keeps the
accepted reports and final-cycle solver artifacts needed by the authenticators,
but omits rejected attempts and nonfinal cycle directories from the much larger
working results. Therefore it does not satisfy every full raw-artifact manifest
embedded in a report. Run:

```text
uv run python -m scripts.simple_center_pb02_six_case_evidence
uv run python -m scripts.simple_center_pb02_refinement_decision
```

Those checks authenticate the retained reports, exact load vectors, model and
scope identities, common source closure, and final-cycle files. Numerical
acceptance does not qualify the modeled demands, the assumed floor stiffness,
hardware, timber resistance, washers, local crossed-bore behavior, or the
complete joint.
