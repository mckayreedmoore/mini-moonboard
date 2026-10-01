# A1-rear case-bound corner demand export

This packet projects the authenticated `a1-rear` selected-floor response into
the existing BG001/BG003/BG045 left-outer-corner contract. It uses only the
exact A1 response and its case context, six-case load/wrench register, pinned
711 response audit, and parent all-body audit. It does not transfer a12 forces
or masks and does not use the generic `df1ed…` response gate. The diagnostic
floor screen is recorded as rejected context; none of its forces or states
seed the report.

`projection-freeze.json` was created before projection and pins 76 source
files, including the selected model, input deck, native DAT and response,
external case context and register, parser/audit proofs, corner contract and
map, unchanged legacy projection source, and its conditional evidence. The
report records the exact model, deck, DAT, response and context hashes.

The seven response increments each contain all 338 mapped interfaces and 232
contact rows, including signed force vectors, owner-datum wrenches, contacts,
and onward transfers. The primary groups retain six physical bolts, eight
separate lateral-plane actions, six outer-seat ties, 12 washer seats, and
five-body equilibrium records. BG001, BG003 and BG045 each retain two bolts
and two ties; their lateral-plane counts are 2, 4 and 2. Twelve original
LEG/FLOOR-RUNNER arrangements remain identified separately from 92 new axes.
Eight retained interface rows fall within this five-body projection; this
does not reduce the retained arrangement inventory from twelve.

Floor counts distinguish the full audited response from its corner subset.
Across all 100 normal cells, this A1 branch has 46 selected bearing cells and
54 inactive separated cells per increment, with 92 exact tangent-reaction
rows and 108 inactive zero-action rows. The corner map contains four floor
contacts incident to its five bodies; two are selected bearing and two are
released in this response. The report preserves the complete response cell
and tangent-row IDs. These conditional support states establish no floor
friction, anchorage or physical floor capacity.

The report is numerical demand input for conditional joint checks on this
exact A1 response. It does not establish joint resistance, a group capacity,
design qualification, a complete-joint acceptance, fabrication approval or
climbing release. Existing resistance evidence is included as a reference;
no resistance method or evidence source was changed or reopened here. Parent
owns final validation and terminal assessment.

The unchanged legacy mapper iterates floor-tangent connection names from a
set before summing five-body resultants. Fresh-process runs showed last-bit
variation only in
`increments[*].corner_five_body_balance.base_post_outer_left.interface_action_wrench`
and its `combined_residual_wrench`. The new wrapper sorts the mapped rows by
`source_connection_name` before calling the same pinned `member_balance`
helper. This fixes summation order; it does not round or alter per-interface
force vectors, response gates, model inputs, or the legacy exporter.

Reproduce and verify from the repository root:

```sh
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-a1-rear-case-bound-export-attempt01/project_a1_corner.py --write
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-a1-rear-case-bound-export-attempt01/project_a1_corner.py --verify
```

`--verify` checks every frozen source, reauthenticates the A1 context and 711
response gates, checks the independent parent 50-body audit, and compares a
fresh seven-increment projection with `corner-demand-report.json`.
