# Lower-left outer service bolt references

[service_joint_checks.py](service_joint_checks.py) joins the four bolts on
`left_service_outer_lower_cleat` to the selected saved comparison's nominal
force states. It fills the deliberate four-axis omission in the general
remaining-joint screen. It does not replay or replace the service worker's 84
historical states. Optional `--clearance` selects a comparison directory or
`comparison.json`; default remains `all-outer-corner-frame-attempt01/`.

## Selected source and current same-state forces

Current calculation uses `two-receiver-frame-attempt03/comparison.json`,
SHA-256
`0ff0dfc00c112a906910641141fd242f4a58295aa3324ca569132a3fa2d388a5`, and its
`response.npz`, SHA-256
`774c3bbddf8061f6b9d1cfdd5f22efbeb1025bd57431a249912ae8e60a731f52`. All six
nominal states pass the helper's bounded finite fixed-force seating checks.
Their response ranks are 296 for A12-rear, A12-forward, K12-rear and A1-rear;
297 for A12-left and K12-right. These are bounded seating states: they do not
establish a unique pose, strict tangent stability or complete joint
acceptance.

The report contains **24 signed simultaneous records**. Six have nonzero
lateral resultants; the other eighteen retain signed axial ties and numerical
zero lateral vectors, with undefined direction and reference fields left
null. The table shows each case's governing same-state `lower_side_2` record:

| Nominal case | Force on cleat, global X/Y/Z (N) | Shear (N) | Same-state tie (N) | 92 ksi reference ratio |
| --- | ---: | ---: | ---: | ---: |
| A12-rear | `(0, -2.068309, +5.128618)` | 5.529975 | 3.521600 | 0.00604395 |
| A12-forward | `(0, -2.262325, +4.897399)` | 5.394686 | 6.281455 | 0.00593564 |
| A12-left | `(0, -2.233251, +4.932048)` | 5.414103 | 4.037265 | 0.00595093 |
| K12-right | `(0, -2.696729, +4.379697)` | 5.143354 | 9.989272 | 0.00575006 |
| K12-rear | `(0, -2.645394, +4.440875)` | 5.169089 | 3.246443 | 0.00576758 |
| A1-rear | `(0, -0.810774, +6.627290)` | 6.676700 | 7.285533 | 0.00703804 |

Governing individual reference is A1-rear, `lower_side_2`:

| Same-state quantity | Value |
| --- | ---: |
| Force on cleat, global X/Y/Z | `(0, -0.810774, +6.627290)` N |
| Lateral resultant | 6.676700 N |
| Simultaneous outer tie | 7.285533 N |
| Side/cleat bearing lengths | 88.9 / 88.9 mm |
| Side/cleat load-to-grain angles | 46.974832 / 43.025168 degrees |
| Unadjusted 45 ksi reference / ratio | 663.472 N / 0.0100633 |
| Unadjusted conditional 92 ksi reference / ratio | 948.659 N / 0.00703804 |
| Unadjusted 106 ksi sensitivity / ratio | 1018.284 N / 0.00655681 |

These reuse existing six-mode quarter-inch smooth-shank DF-L SG0.50
arithmetic, including diameter-specific bearing and load-angle reduction.
They are individual lateral comparisons before remaining group/end-use
adjustments, splitting, simultaneous steel interaction and washer transfer.
Steel scenarios do not authenticate delivered hardware. Complete joint,
operation and physical acceptance remain false.

## Preserved historical result

The previous `service-joint-current-attempt02/result.json`, SHA-256
`7e5b7aa9e175d7eb1bc324cd4a9d9a2ba688ce7521542c738ad98fd289c6e18f`, used
the preserved `all-outer-corner-frame-attempt01/` source. Its historical
six-joint governing record was K12-rear, `lower_side_1`: force
`(0, -3.778194, +3.090856)` N, shear 4.881408 N, simultaneous tie 1.686482 N,
92 ksi reference 859.320 N and ratio 0.0056805. Those values describe that
earlier source and are not the attempt03 forces.

## Current result and limits

Current result:
`service-joint-current-attempt03/result.json`, SHA-256
`474508d76914cfb0e6ec32b43bef648f518f2b44c0c074aedafe62675abc2612`. It has
24 records and 127 source bindings, including the comparison, response,
producer and `frame_state_contract.py`. Helper SHA-256 is
`22e1f8b864c03469701010fc856a815b3604a4efde2748531e36d284050266e5`.
Attempt01's zero-lateral-direction failure and attempt02 result remain
preserved. Geometry, authority and hardware are unchanged; no native solve,
software test or review loop was run.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/service_joint_checks.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/service-joint-current-attempt03 \
  --clearance docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/two-receiver-frame-attempt03
```
