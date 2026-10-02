# Current lower-left outer service bolt references

[service_joint_checks.py](service_joint_checks.py) joins the four bolts on
`left_service_outer_lower_cleat` to all six nominal-gap states from the
preserved `all-outer-corner-frame-attempt01/`. This fills the deliberate
four-axis omission in the general remaining-joint screen. It does not replay
or replace the service worker's 84 historical states.

There are **24 signed simultaneous records**. Six have nonzero lateral
resultants. The other eighteen retain their signed axial ties and numerical
zero lateral vectors; load direction and lateral reference fields remain
null. A zero direction is not a physical strength failure.

The governing individual reference is K12-rear, `lower_side_1`:

| Same-state quantity | Value |
| --- | ---: |
| Force on cleat, global X/Y/Z | `(0, -3.778194, +3.090856)` N |
| Lateral resultant | 4.881408 N |
| Simultaneous outer tie | 1.686482 N |
| Side/cleat bearing lengths | 88.9 / 88.9 mm |
| Side/cleat load-to-grain angles | 89.285828 / 0.714172 degrees |
| Unadjusted 45 ksi reference / ratio | 600.990 N / 0.0081223 |
| Unadjusted conditional 92 ksi reference / ratio | 859.320 N / 0.0056805 |
| Unadjusted 106 ksi sensitivity / ratio | 922.388 N / 0.0052921 |

These reuse the existing six-mode quarter-inch smooth-shank DF-L SG0.50
arithmetic, including diameter-specific bearing and load-angle reduction.
They are individual lateral comparisons before remaining group/end-use
adjustments, splitting, simultaneous steel interaction and washer transfer.
The steel scenarios do not authenticate delivered hardware. Their favorable
values support retaining the current bolts for this working comparison;
complete joint, operation and physical acceptance remain false.

Current frozen result: `service-joint-current-attempt02/result.json`, SHA-256
`7e5b7aa9e175d7eb1bc324cd4a9d9a2ba688ce7521542c738ad98fd289c6e18f`.
It binds the current frame, raw operators/row identities, unchanged geometry
and reused method. Attempt01 stopped because its first producer lacked a
zero-lateral-direction branch; that source/failure is retained. No geometry,
authority, native solve, software test, review loop or hardware change occurs.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/service_joint_checks.py \
  --output /tmp/FRESH-SERVICE-JOINT-COMPARISON
```
