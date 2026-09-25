# Current modeled mass centers

The parent read the existing owner-reviewed CAD objects on September 25, 2026.
No CAD rebuild, geometry edit, mesh, or native solve was performed for this
export. The in-memory review report matched the frozen owner report, the
revision IDs matched, and all 778 row volumes and masses reconciled with the
frozen weight inventory. The input file hashes are embedded in
[`mass-centroids.json`](mass-centroids.json).

The modeled 224.420776668 kg has global mass center
**(−1.644537, 697.857581, 1033.609057) mm**. With global downward gravity
9.80665 m/s², its resultant is **(0, 0, −2200.816010) N** and its moment
about the global origin is **(−1535856.136568, −3619.323689, 0) N mm**.
These are mass accounting quantities, not support reactions or a stability
result. The additional 25 kg equipment allowance is excluded from this center;
its placement scenarios remain separate in the
[dead-load map](../../../current-frame-dead-load-map.md).

The 778 entries comprise six panels, 20 timber members, 24 blocks, 460
candidate bolt-stack roles, 60 retained frame-bolt roles, 66 screw envelopes,
and 142 T-nuts. All 66 screw rows use the same cylindrical axis-envelope
fallback as the original weight producer; they are not detailed solids of
purchased Hillman screws. The current shapes already contain the eight
owner-directed moves. Their centers were checked against the recorded new
axis start plus half the 63.5 mm modeled length, so no translation was applied
twice. All density and dimensional assumptions of the weight estimate remain.

The producer is [`export.py`](export.py), SHA-256
`8da82299d3b2b2b426bdace5c129a412672cacaaafba14c821fff35bcd9a2441`.
The result SHA-256 is
`4c107b76d42d2a6f49b81c4857ba20bb236920932a7c34392c63e70d0882099a`.
The parent executed `export_mass_centroids` against `g24_outer_2x6`,
`source_parts`, and `frozen_review_report` in the existing CAD process. The
function writes a new destination only, refusing an existing result file.
The first invocation stopped before writing because source screw display
bodies were absent; the corrected producer explicitly retains the original
inventory's envelope fallback.

These centers permit explicit gravity placement in a reduced model. Each
row still needs a named load-transfer owner in that model, and equipment
placement sensitivity remains necessary. No joint, complete-frame, floor,
fabrication, or climbing acceptance follows from this export.
