# Current attachment topology — attempt01

This source-only index crosswalks the owner-reviewed revision
`led-clearance-2x6-runner-seated-blocks-v1` to exact member STEP files,
candidate bolt axes, retained frame-bolt axes, panel screws, and pair-level
contact records. It preserves the separate selected candidate
`compact-floor-flush-development`.

The index covers 24 former duties, 50 members (20 timber, six panels, 24
candidate blocks), 92 unique candidate bolt axes, 12 retained frame bolts,
and 66 panel screws. It records 104 candidate-axis references across duty
rows because each exterior six-axis chain is listed under two former duties;
the shared chain IDs prevent double counting. The source graph has 1,225
member pairs, including 115 finite planar contacts, six zero-area or
unresolved tangencies, and 1,104 separated pairs. Of those, 1,078 separated
pairs were excluded by disjoint AABBs without exact BRep evaluation.

`pair:<member-id>|<member-id>` is a derived join key with member IDs sorted
lexicographically. The source graph has no native pair IDs. Each duty row
references exact STEP hashes and pair IDs. Retained-bolt and panel-screw
links on a duty row mean only that the duty shares a member or receiver; they
do not claim a station-local connection.

## Verification

From the repository root:

```sh
script=docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/\
current-attachment-topology-attempt01/produce.py
python3 "$script" --verify
```

`--write` deterministically regenerates `attachment-topology.json` from the
pinned source records. The verifier checks the crosswalk counts, source
identities, member/STEP coverage, axis/receiver coverage, and every referenced
contact pair. It reads existing JSON and Markdown records only; it does not
replay geometry.

## Limits

The contact graph is pair-level and is not a solver surface map. It contains no
face IDs, normals, or patch coordinates. This index supplies no contact law,
active attachment mechanics, fastener engagement, solver mapping, current
demand, or duty acceptance. Finite geometric contact does not establish force
transfer or capacity. Step 3 remains open.

Bundle SHA-256: `d9d8feefea4df6ad2895a25292e164851c4d776ae6606c12956b639fb161e3fc`.
STEP-set SHA-256: `590e3d8ffc6a013ad10436def028b54b3c855688398c4bf9b30c460800fc987c`.
Index SHA-256: `175748c8ade586bfd57c93da41b3c31537de464301ddddfddca69e633f200a54`.
