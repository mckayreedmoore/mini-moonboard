# Revised-viewer outer/top eight: integrated collision probe

This is a bounded diagnostic of the **revised barrel viewer assembly**, built by
`scripts.export_owner_barrel_scene.build_viewer_assembly()`. It is not the
default producer, a wood-cut model, a hardware selection, or a drilling plan.
The probe owns no scene or producer changes. Run it with:

`uv run python -m scripts.owner_barrel_revised_outer_top_probe`

The JSON reports both rows at each of the eight outer/top stations. For every
row it includes the barrel and bolt shaft, washer, head, machine/barrel bores,
straight bolt/barrel tool envelopes, and—at the four recessed outer-header
bolts—the counterbore. The viewer supplies the four header heads and washers.
The other twelve outer/top heads and washers are **supplemental provisional
envelopes**, not installed viewer parts or selected retail hardware. Other
families are screened with their current viewer stacks plus similarly flagged
supplemental heads/washers where absent.

For each outer/top station, the script records 3D intersection volumes over
1 mm³ against the fixed protected inventory (T-nuts, provisional 50.8 mm
hold-hole/rear-bolt projections, lights, wires, all 66 panel/kicker screw axes,
and 12 original frame-bolt axes), unrelated uncut wood, neighboring stations
within the outer/top family, and all other barrel families. Neighbor screens
cover physical–physical, path–physical, physical–path, and path–path pairs.
Intended own-station hardware/bores and own host wood are excluded from those
neighbor/unrelated-wood comparisons; intersections are diagnostic volumes, not
automatic failures or approvals. Wire bends, real hold-bolt lengths, bit
diameters, hardware tolerances, insertion sweeps, and structural resistance
are not established.

The outer-header bolt driver is **blocked by the installed side rim**. For
each of its four rows the report keeps that installed-state intersection and
separately screens unrelated wood with that one rim omitted. The second state
is conditional on an unverified rim-removal and handling sequence. It does not
establish access, safe support, or repeatable demounting. Neither state may be
reported as a release or an approved fit.

In the current revised-viewer run, there are four unrelated-wood intersections,
all from the four outer-header driver envelopes against the installed rims.
Each intersection is about 12,252.211 mm³. The fixed protected inventory and
same-family/cross-family neighbor screens report no intersections above the
1 mm³ threshold. That is a result for these *nominal* finite envelopes, not a
pass: the delivered parts, continuous insertion/removal paths, and wood left
after drilling remain unverified.

All stations remain `REVISE`; layout, drilling, fabrication, and structural
release flags remain false. The nominal 11 mm × 4 mm head, 25.4 mm washer,
1.651 mm washer thickness, 20 mm × 40 mm straight driver, bore, counterbore,
and Hillman 880543 cross-dowel dimensions are only collision envelopes.
