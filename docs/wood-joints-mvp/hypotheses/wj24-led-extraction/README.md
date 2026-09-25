# Individual LED axial extraction diagnostic

The parent tested all 132 retained LED cylinder envelopes against 842 stationary
finished-wood, candidate-hardware, fixed-screw, frame-bolt and T-nut shapes in
the complete WJ24 layout. Each original cylinder was independently reconstructed
with zero measured symmetric difference and assigned to the same owning panel
as the earlier harness topology report. The continuous swept cylinder withdraws
each LED rearward until its front end is 1 mm behind the panel rear. The 1 mm
is an explicit scenario, not a delivered tolerance or tested release action.

The required translation is 19.25625 mm. G7 intersects
`wj04_lower_full_stock_cleat` by 319.657955 mm³ along that sweep. The other 131
LED sweeps have no positive-volume obstacle hits above 1e-5 mm³. The original
installed G7 light remains clear; static fit does not establish extraction.

This does not prove or disprove a different supported staging sequence.
Wires, slack, flexibility, connector feeding, neighboring lights, bulb latches
and provisional hold-bolt projections are excluded from this bounded operation.
Those exclusions prevent treating the result as a complete transport pass.
The continuous harness still crosses panel boundaries as recorded in the
[earlier topology investigation](../wj18-panel-harness-topology/README.md).

Execution took 2.908887 seconds inside the retained parent CAD session.
The [report](geometry.json), producer snapshot and execution record bind the
full-layout composition, prior topology and geometry sources. No native solve,
physical removal, assembly acceptance or release is claimed.
