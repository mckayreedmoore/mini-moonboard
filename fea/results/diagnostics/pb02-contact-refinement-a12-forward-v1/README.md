# PB02 exact-face A12-forward contact refinement evidence

This compact package preserves five authenticated developmental `a12-forward`
runs for the active Z202/link-Z328.5 PB02 geometry:

- `grid-2x2`: 2x2, 1,000 N/mm, 11 cycles; report SHA-256
  `837523aeebf3f997cc6271fe3f11a7bb19830573d6fbfabc3dbe8b90eb644504`.
- `grid-4x4`: 4x4, 1,000 N/mm, 11 cycles; report SHA-256
  `d1e04abaefbda829125b12cd13392d8567b8ed7c7df89baf1e931f9a0eda7653`.
- `grid-8x8`: 8x8, 1,000 N/mm, 11 cycles; report SHA-256
  `5587450b5760cee02e3b9895301959aa361c6cc644384f6ce35047c4f0de70ef`.
- `density-0p5x`: 8x8, 500 N/mm, 11 cycles; report SHA-256
  `eb1cfe5987b7edfe79102c1f1507ab3302be9e570eff0560e64dab857cd1a6d6`.
- `density-2x`: 8x8, 2,000 N/mm, 13 cycles; report SHA-256
  `a5e24552a90e4d6e27a987e381665bcc489a9021b61769c77fbbd0c5948e3631`.

Every run passes its recorded contact and tension-only active-set checks,
member and global equilibrium checks, MPC audit, positive-work gate, producer
source inventory, partition identity, stiffness inventory, and physical-force
authentication. They remain numerical development evidence, not qualified
joint demands.

## Decision

The machine-readable [comparison](comparison.json) has SHA-256
`9ab404eedd90a5b529862dcd5683b6137099f58d37544f67a32fcad89e93d4f6`.
The 4x4-to-8x8 comparison changes interface-force magnitude by at most 3.287%,
interface-moment magnitude by at most 8.186%, maximum bolt demand by 0.697%,
and panel displacement by 0.000242%. The 8x8 model is therefore retained for
developmental global force and moment demand.

Active contact area changes by as much as 48.195%, and peak cell-average
pressure changes by as much as 21.091%. Neither quantity is locally converged;
the cell-average pressure must not be used as bearing qualification.

Across the 0.5x, 1x, and 2x contact-density runs, the maximum interface force
ratio is 1.738, the maximum interface moment ratio is 5.083, and the governing
bolt combined-force ratio is 1.649. Panel displacement changes by less than
0.018%. The density is not qualified. The 2x case is retained only as the
current bounded same-case component screen while PB02 remains under revision.

## Compact-package scope

Each subdirectory retains its authenticated top-level report, diagnostic scope,
final-cycle input, solver force output, displacement output, and empty 12d
file. The common source-snapshot closure is retained once at package level.
Earlier contact cycles, model pickle files, logs, and other raw artifacts are
omitted, so the compact copy does not satisfy every raw artifact hash recorded
in each report.

No drilling, fabrication, purchasing for construction, construction, or
structural acceptance is released by this package.
