# Selected-floor five-member corner demand report

`produce.py` consumes the pinned attempt03 selected-floor response and writes a
source-bound numerical demand report for the complete left outer
BG001/BG003/BG045 assembly. It does not launch a solver or read raw DAT force
records. Its output, `corner-demand-report.json`, is bound to the adjacent
model, frozen deck, terminal DAT, execution record, response auditor, parent
serialization record, independent all-body sum audit, and parent terminal
assessment.

The report covers one conditional a12-rear case: ring A, Hillman axial ratio
1, zero bolt gap, zero accessory, and the reviewed 25/75 proposed floor branch.
Seven recorded increments cover the ramp to load factor 1.0. The parent all-body/global sums and
this exporter’s separate five-corner-body force/moment sums pass at each
increment. The report contains all 338 source-owned corner interfaces,
signed actions at source points, member and group wrenches, 232 contact rows,
parallel transfer routes, physical bolt planes/ties, splitting/net-section
inputs, and washer-seat actions. It retains 12 head/nut seat records for the
six physical bolts and keeps all 12 original LEG/FLOOR-RUNNER arrangements
separate; their unchanged resistance checks are not reopened.

The primary groups contain six physical bolts, eight lateral planes, and six
outside-seat ties. BG003 remains two continuous three-member bolts, each with
two separate plane actions. Its conditional double-shear reference may assume
equal outer-plane sharing, so it cannot be applied blindly to unequal signed
plane actions. No plane capacities are summed.

The proposed floor branch remains unqualified for friction, anchorage, or
physical-floor behavior. Its 150 inactive tangent rows are shown with
source-row IDs, isolated-output RF intervals, and no-equation/no-spring
provenance; the four local corner tangent interfaces are explicitly released
with zero action. These mechanics gates establish only a conditional
numerical demand input for this case. They do not establish adjusted
resistance, complete-joint acceptance, material or hardware qualification,
fabrication approval, or climbing release. The other five cases and required
sensitivities remain outstanding.

Run the source-bound export from the repository root with the pinned response:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-native-demand-export-attempt03/produce.py \
  --response docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a12-rear-attempt03/response.json \
  --output docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-native-demand-export-attempt03/corner-demand-report.json
```

The exporter checks the exact response SHA, selected-floor audit gates at the
root and each increment, the complete 150-row inactive mask, all five body
and global response balances, parent serialization and all-body audit pins,
the terminal acceptance record, and independent five-member closure. Any
mismatch writes only blocker names and source evidence, with no response force
rows.
