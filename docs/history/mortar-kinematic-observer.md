# Additive kinematic and force observer packet

`fea/mortar_observer/kinematic_patch.py` applies the unchanged V1 generator to
hash-verified official CalculiX 2.21 sources, then inserts two read-only logging
blocks in `stressmortar.c`. Removing those blocks restores V1 byte-for-byte;
`nonlingeo.c` is exactly its V1 version. This is instrumentation, not solver or
physical-contact qualification. V1 evidence and its reader remain separate.

Run from the repository root, with a destination that does not exist:

```sh
python -m fea.mortar_observer.kinematic_patch OFFICIAL_SOURCE NEW_OUTPUT
```

Standalone use requires unchanged `patch.py` beside `kinematic_patch.py`:
`python kinematic_patch.py OFFICIAL_SOURCE NEW_OUTPUT`. The only outputs are the
two patched C files and `patch_manifest.json`. The manifest binds original source
hashes, V1 and V2 patched hashes, and both generator hashes. Its
`patch_generator_sha256` is an alias for `v2_patch_generator_sha256`. A build must
archive both generator files and bind the resulting executable separately.

## Packet schema and observation phases

All records retain the V1 `MORTAR_OBSERVER ` prefix and `kind`/`call_id` fields.
Integers follow source indexing: physical nodes are one-based; pair, slave slot,
and sparse entry indices are zero-based. Floating-point output uses `%.17g`.
Tangents, bases, multiplier snapshots, convergence context, and acceptance
mapping come from the unchanged V1 packet.

The first block occurs after the slave displacement transformation overwrites
`b2`, before weighted kinematics and before any active-set update. It records:

| Kind | Additional fields |
| --- | --- |
| `KIN_INVENTORY` | `all_node_count`, `physical_count`, `dd_count`, `bd_count`, `slave_count` |
| `KIN_NODE` | `node`, `dd_count`, `bd_count`, `b2[3]`, `vold[3]`, `vini[3]` |
| `KIN_DD`, `KIN_BD` | `node`, `entry`, `row_node`, `slave_slot`, `value` |
| `KIN_GAP` | `pair`, `slot`, `node`, `gap` |

Only physical nodes having a nonempty Dd or Bd column receive `KIN_NODE` records,
in ascending node order. Each node's Dd entries precede its Bd entries, each in
CSC order. The sparse row is a physical node; `slave_slot` is the actual
`islavnodeinv[row_node-1]-1`, not an assumed ordering. Inventory counts cover all
columns, including stored zero coefficients. Gap records cover every slave of
every C tie in source order and capture the original weighted gap.

The second block occurs immediately after the Dd/Bd `cfs` assembly, before the
dynamic branch or constraint redistribution. It records:

| Kind | Additional fields |
| --- | --- |
| `CFS_INVENTORY` | `all_node_count`, `physical_count` |
| `CFS_NODE` | `node`, `force[3]` |
| `CFS_OUTSIDE` | `node`, `force[3]` |
| `CFS_END` | `scanned_nodes`, `physical_count`, `outside_nonzero_count` |

The same coupled physical-node set receives `CFS_NODE`. The block scans every
physical node: any nonzero component outside that set emits `CFS_OUTSIDE`, not
silent omission. Such a record must fail bounded coverage qualification. The
reader must also reject missing, duplicate, reordered, nonfinite, or inconsistent
inventory records. No interpretation of unsupported dynamic cases is implied.

## Bounded reconstruction

For ordinary static MORTAR, assemble the observed scalar coupling matrix A from
Dd and Bd, with inverse-mapped slave rows and physical-node columns. Using the
unchanged V1 frozen bases and post-active-loop multipliers, independently replay:

- `du = A*b2`, `history = A*(vold-vini)`;
- `q = n·du-gap`, `ut = t·(du+history)`;
- `cfs = Aᵀ*postlambda`;
- work conjugacy: `b2·cfs = du·postlambda`.

These checks qualify recorded matrix arithmetic only. They do not independently
validate segmentation, gap construction, physical penetration, friction capacity,
or global/body equilibrium. For physical resultants, the packet's internal force
has applied-contact sign `-cfs`; current physical positions require original mesh
coordinates plus `vold+b2`. Per-foot assignment requires independently checked
mesh membership, and demands require accepted-state/STA matching and independent
ground-brick or whole-body balance, not just internal work conjugacy. Untied floor
validation and later connection design remain separate gates.

## Output budget

The new records per call are `3 + 2P + D + B + S + O`, where P is coupled physical
nodes, D/B are stored sparse entries, S is C-tie slaves, and O is unexpected
nonzero outside nodes. Other zero-force nodes are scanned but not printed. No new
solver arrays are allocated. Measure actual bytes and counts in a bounded run
before extrapolating to a full frame; sparse coefficients can materially increase
the existing V1 log, so the packet alone does not guarantee a 512 MiB archive cap.

Hermetic tests verify source pinning, exact additive preservation, ordering,
coverage guards, standalone CLI provenance, and C fragment syntax/format. They
do not compile or run a solver.
