# PB01 a12-left hybrid local actions

Run `uv run python -m scripts.simple_pb01_hybrid_local_actions` from the repository root.
It prints JSON to stdout and writes no files. The input is the preserved
`pb01-quarter-contact4-a12left-evidence.tar.gz` final-cycle bundle. It does not
run a solver. The extractor accepts only the frozen archive SHA-256
`fc298a3a481437a5dc9f24c02bc9a234458074c2ffcba6753fe33875f4805546`
and top-level report SHA-256
`c10b2b2d1b979fe82ffc5bca31c60e374650610e4c44245e8e56431c7b0c4918`.
It checks the 260 source snapshots, final-cycle artifact hashes, a12-left quarter
identity, 23 distinct old-proxy stations, two bolts and four contacts on each
PB01 face, contact active state, signed connector pairs, and reported plus
numeric equilibrium. Any failed check raises an error before output.

For every bolt, `force_on_host_xyz_n` is the signed global force on the named
host member; `axial_n` is its dot product with the recorded installation axis.
`lateral_xyz_n` is the remaining signed vector and `lateral_magnitude_n` its
length. Contact force vectors and positive compression are similarly on the
host. The force on the cleat is equal and opposite at each recorded point.
The common PB01 datum is the arithmetic mean of the four bolt points:
`[134.05, 658.241598, 1233.677695]` mm in the model's global coordinates.
Each reported moment is the sum of `(point - datum) × force` in N·mm, using
the right-hand rule. Cleat resultants are the negatives of host resultants
for the **same interface**; the two serial interfaces are not added together
as a free-body balance of the cleat.

Rounded host-side final-cycle resultants about that datum:

| Interface | Force XYZ (N) | Moment XYZ (N·mm) |
| --- | --- | --- |
| Principal/cleat | `[-18.2715, -2.8150, -14.0550]` | `[825.136, -739.433, 132.376]` |
| Rail/cleat | `[18.2710, 2.81464, -1.66442]` | `[-188.966, 1081.259, -132.382]` |

Active contact compression is 5.03925 and 7.24125 N on the principal face,
and 6.42508 and 2.28498 N on the rail face.

This is a local force extractor for one source-authenticated diagnostic run.
The other 23 stations retain ML24Z/SDS proxy topology, and the contact and
bolt spring properties are provisional. It provides **no full V4 demand, no
utilization, and no design verdict**. Numeric equilibrium confirms only this
hybrid solve within the recorded tolerances, not calibrated joint behavior.
