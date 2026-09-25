# Scalar axial MPC fixture

The parent ran the frozen four-element elastic-bar fixture with the pinned
CalculiX 2.21 executable. The [audit](parent-audit.json) verifies the 0.005 mm
extension under 1,000 N, all 32 stress/strain integration points, the nine-node
area-weighted force transfer and whole-fixture force/moment equilibrium.
An independent read of the raw output found no oracle mismatch. Three focused
producer tests passed before execution.

This verifies one numerical axial mean constraint with a finite rigid nut
surrogate and explicit fixture guides. It does not establish physical thread
engagement, radial restraint, actual nut geometry, or current-joint response.
The guides must not be transferred to the board model.

The top bolt-face nodal RF values show the MPC transfer. Reference-node RF is
zero in this output. Whole-fixture equilibrium counts the explicit external
load and bottom support reactions; adding the internal top-face transfer again
would double-count it. The requested minimum increment was automatically
raised from `1e-8` to `1e-6`; the single actual increment reached time 1.0.
The raw log and FRD preserve their original whitespace and recorded hashes.
