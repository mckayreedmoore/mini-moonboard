# Selected-floor five-member corner demand exporter

This input-only packet prepares a source-bound demand report for the left outer
BG001/BG003/BG045 assembly. It consumes one authenticated case model and a
passing `current_springa_selected_floor_physical_response_audit/v1` JSON. It
never launches a solver or parses native DAT force fields. The existing
conditional resistance, washer-seat, splitting/net-section, and NDS-helper
evidence remains reference-only; this exporter computes no adjusted
resistance, interaction, DCR, or complete-joint acceptance.

The primary corner path is six physical bolts, eight lateral shear planes,
and six outside-seat ties. BG003 is two continuous three-member physical
bolts, each with separate planes; plane capacities are never summed. The 92
new block attachment axes replace the former ML24Z/SDS duties. The twelve
original LEG/FLOOR-RUNNER arrangements remain distinct and their unchanged
resistance checks are not reopened.

Run the input-only preflight from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-native-demand-export-attempt02/produce.py
```

The default preflight is blocked. The selected-floor native run completed at
full factor, but its parent terminal assessment rejects the prescribed 23/77
support branch because inactive SPR1215 was not strictly separated with zero
endpoint reaction. No response audit was produced, so `preflight.json` contains
no recovered force rows. A return code of zero and full load factor do not
override that failed compatibility gate.

A future accepted response must match the exact input model file and canonical
record, the adjacent frozen deck and the terminal DAT output hashes, the
successful execution and explicit parent terminal assessment, and final load
factor 1.0. The exporter also requires all seven response gates at the root
and every increment, all five audited body balances and global balance, and an
independent five-body force/moment closure using response rounding intervals.
It checks all 154 inactive tangent zero-action records against the frozen
original-row mask and includes the four corner tangent rows with their source
row IDs, local DOFs, isolated-output RF intervals, and no-equation/no-spring
provenance. Rejected or partial responses produce only exact blockers and no
force rows.

Even a future passing numerical report is conditional input to later joint
checks for this one a12-rear case. It does not qualify the proposed floor
branch, friction, anchorage, materials, hardware, fabrication, or climbing use.
The other five cases and required sensitivity cases remain outstanding.
