# Current insert member and structural-connection demands

The [authenticated three-case result](../fea/results/round-insert-member-connections-v1.json)
uses only the completed F10, C6 and C10 contact runs in
`fea/generated/round-insert-frame-v3`. It does not qualify the assembly.
The failed 10,000 N/mm case and other sensitivity cases are outside this report.
No historical screw-design force is transferred into these calculations.

## Current check status (2026-09-12)

| Check | Case coverage | Result | Evidence summary |
| --- | --- | --- | --- |
| Member and connection assessment execution | F10, C6, C10 | **PASS** | Three native cases replayed from authenticated reports with fixed node-to-member ownership and seating-force reconciliation. |
| Angles processed per case | 24 | **PASS** | 24 angle recoveries per case, and whole-angle imbalance checks are within the runner limit (0.0166 N, 0.708 N·mm max). |
| Full directional strength mapping | 24 | **NOT PASSED** | 22 brackets each case still have `unassessed_reason`; only `clip_angle_base_left/right` are mapped to ML24Z bearing-installation directional components. |
| A34/ML24Z missing-direction check | 6 outer-angle states | **NOT PASSED** | F2 (uplift) remains unlisted for ML24Z bearing installation; five-to-six of the six outer states per current runs still include upward demands (`~-72 to +261 N`). |
| Moment resistance for outer-angle pair | 24 outer-angle wrenches | **NOT PASSED** | Parallel couples are reported (`~1,875–10,086 N·mm`) with no tested moment resistance in ML24Z tables. |
| Leg-bolt lateral demand | 8/hold, 3 holds | **PROVISIONAL** | Max lateral ratios are 0.710, 0.499, 0.917 (F10/C6/C10) from `lateral_demand_reference_ratio`; axial resistance, washer bearing, group action and splitting are still unqualified. |
| Round-bore nominal cut demand | 32 sections/hold | **PASS (diagnostic only)** | Each case carries 32 cuts with reported axial/shear/moment/nominal stress values; no hole-concentration, edge splitting, torsion, instability, or transfer resistance check is yet complete. |

Overall member/joint qualification remains false because several required directional and failure-mode mappings are unresolved, and connection capacity checks are not complete.


Each input has 906 seating-contact records and assumed 1,000 N/mm panel
attachment stiffness. Authentication reproduces the native deck, checks source
and output hashes, and replays corrected expanded-S8 opposite-surface force
recovery, contact/MPC checks and raw member stresses. Seating forces enter the
wood free bodies at their recorded physical points exactly once. This assessment
runs no additional solver. The method, conditional bolt properties and isolated
bore-section definitions are documented in the
[member assessment](round-member-connections.md); its older force-recovery
warning applies to the historical result, while this report uses the corrected
current native recovery.

| Hold | Worst bolt lateral demand / conditional reference (N) | Ratio | Left / right base uplift demand (N) | Largest isolated-bore nominal normal magnitude (MPa) |
| --- | ---: | ---: | ---: | --- |
| F10 | 559.253 / 787.799 | 0.710 | +259.981 / +260.829 | 1.316 (bore_base_principal_center_left_060) |
| C6 | 411.376 / 824.951 | 0.499 | -72.174 / +56.280 | 3.540 (bore_base_rail_service_lower_left_030) |
| C10 | 726.426 / 793.283 | 0.916 | +161.239 / +101.343 | 0.754 (bore_base_rail_service_upper_left_017) |

Five of the six outer-angle states require an uplift direction absent from the
ML24Z bearing-installation table. Independent parallel couples range from
1,875 to 9,485 N·mm; changing the force reference point cannot remove them.
The catalog's general simultaneous-force unity equation requires an applicable
allowable for every participating direction and does not supply a missing
uplift or free-moment resistance. The [A34 remedy study](round-base-angle-remedy.md)
provides a bounded replacement option and the exact remaining manufacturer question.

The controlling bolt is C10 left bolt 4. Its 0.916 lateral ratio is conditional
on the stated DF-L/steel/dowel assumptions; group behavior and bolt axial
resistance are not established. Maximum absolute bolt-axis demands are 279.850,
234.925 and 216.536 N for F10, C6 and C10 respectively. The JSON preserves every
bracket-flange wrench, individual SDS demand and bore-cut axial/shear/bending/
torsional demand. Neither nominal plane-section stresses nor retained-prism
native stresses establish local bore-edge, splitting, torsional or stability
resistance. Clamped feet, isotropic timber and assumed attachment stiffness
also remain model limitations. Member and structural-connection strength flags
therefore remain false.

Reproduce without running the solver:

```sh
uv run python -m fea.round_member_connection_assessment \
  --native-run fea/generated/round-insert-frame-v3/f10-contact \
  --native-run fea/generated/round-insert-frame-v3/c6-contact \
  --native-run fea/generated/round-insert-frame-v3/c10-contact \
  --output /tmp/round-insert-member-connections.json
```
