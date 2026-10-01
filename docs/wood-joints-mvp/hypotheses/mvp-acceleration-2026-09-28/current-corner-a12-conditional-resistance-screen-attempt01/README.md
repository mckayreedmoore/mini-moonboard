# Current a12-rear conditional corner resistance screen

This packet compares the accepted, source-bound a12-rear corner demands at
load factor 1.0 with existing conditional reference calculations for BG001,
BG003, BG045, and the six bolt-axis outer-seat ties. It is a comparability
screen only. The numerical response is one case; this packet does not accept
the joints, establish design resistance, qualify the floor, or release
fabrication or climbing.

The screen reads the exact passing corner demand export
`current-corner-native-demand-export-attempt03/corner-demand-report.json`
(SHA256 `812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17`),
which binds response `892dadee…e1274` and model `8a90452d…1cda8`. The report
has seven accepted increments. Its per-increment MPC, SPRINGA, retained
bilateral, floor complementarity, inactive floor tangent, and local corner
balance gates pass. The independently checked 50-body/global balance also
passes at all seven increments. The final full-load increment is used here;
the exported demands increase monotonically across these seven increments.

The reproducible calculation is:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-a12-conditional-resistance-screen-attempt01/screen.py
```

It validates the pinned inputs and existing conditional source screens before
writing `screen.json`. It reads the exported physical plane actions and outer
ties directly. Ratios below are per-axis component/reference screens only;
they are not combined-action DCRs.

| Group | Observed final-load lateral demands | Existing comparison and applicability |
| --- | --- | --- |
| BG001 | Post bolt 1: 301.657 N; bolt 2: 335.061 N. Outer ties: 64.966 N and 18.473 N. | Separate Y-component magnitude / 567.848 N and Z-component magnitude / 796.262 N component ratios are 0.266/0.328 and 0.375/0.325. These use the existing unadjusted individual-bolt references with their stated full-body 1/4-in shank, 38.1 mm bearing, zero gap, SG 0.5, and Fe assumptions. No mixed-axis interaction, axial-bolt check, group capacity, or acceptance is available. The existing Cg/Cdelta rows are conditional reference multipliers, not group resistance, and are not treated as such here. |
| BG003 | Bolt 1 outer planes: 483.948 N and 65.913 N; bolt 2: 239.230 N and 86.983 N. Outer ties: 95.967 N and 43.508 N. | The two outer-plane resultant ratios are 7.342 and 2.750; their action-vector angles are 37.97° and 119.35°. Existing three-member double-shear cases assume equal, same-direction outer actions, so they do not match these observed splits. No capacity ratio is calculated and the two plane or bolt capacities are not summed. |
| BG045 | Header lateral planes: 90.116 N and 24.946 N. Outer ties: 119.343 N and 19.882 N. | Separate X/Y component ratios against the existing Ceg-only conditional references are 0.222/0.0369 and 0.0604/0.0151. Comparisons retain the previous conditional main/side, Fe, and Ceg assumptions. No mixed-axis interaction, group resistance, axial resistance, or acceptance is established. |

The 12 outer washer seats use the modeled annular area of 222.726 mm², so
uniform-average pressure is the tie divided by that area. The resulting
pressures range from 0.08294 to 0.53583 MPa. Conditional Fc⊥ force-reference
ratios are 0.06769 and 0.01925 for the base-post seats and 0.12434 and
0.02071 for the base-header seats. Those four ratios apply only to the
existing DF-L No. 2 full-annulus, sound-wood, transverse-to-grain reference.
No block Fc⊥ value is assumed; the BG045 inner-frame-block seats load parallel
to the proposed grain. Full annular support, the washer opening and product,
actual wood condition, contact distribution, and washer bending/spreading
remain unverified, so these are not seat-resistance checks.

The source geometry screen contains net-section areas and uniform-stress
coefficients, but no supported splitting or net-tension resistance method,
signed section action, or wood-strength basis. No splitting, row-shear,
tear-out, or net-section ratio is computed. Whole-body equilibrium is not
used as internal section action; only recovered local bolt-plane actions
appear in this screen. Delivered bolt grade and thread/shank geometry, actual
holes and fit, axial-bolt resistance, spacing/end/edge criteria, adjustment
factors, and complete connection behavior remain open.

Pinned source hashes, exact vectors, component calculations, washer-seat
conversions, and the no-acceptance flags are in `screen.json`. This packet
does not reopen unchanged leg/runner checks or extend the result beyond the
single a12-rear case.
