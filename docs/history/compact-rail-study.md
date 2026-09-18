# Rejected compact low-rail response trials

**Both low-rail trials are numerically rejected. Neither provides a usable
strength conclusion.** The preferred development candidate remains the
three-bolt `compact-thick-development` frame described in the
[compact study](compact-thick-study.md), including its recorded joint shortfall.
This experiment neither resolves that shortfall nor establishes that adding
rails is structurally ineffective.

The separate `compact-rail-development` experiment adds raised single-2×6
side rails with bolted laps at both ends. It moves the outer posts inward and
changes the kicker attachment holes and open-edge clearances. The modeled
rail top is 236.9 mm above the floor, with a nominal 2 mm gap below the
header. These are changed geometry and contact conditions, not an accessory
whose capacity can be inferred from the preceding frame.

Both runs apply the same A12 case: 2224.11 N downward and 300 N rearward,
with a 100 mm hold standoff and a 25 kg equipment allowance. The downward
force represents twice the weight of the modeled 250 lb climber; it is not
a climber weight rating.

| Native trial | Recorded contact iterations | Outcome |
| --- | ---: | --- |
| `compact-rail-a12` | 18 | Contact active set repeated without convergence. |
| `compact-rail-a12-contact` | 12 | Contact active set repeated without convergence using `one_per_floor_body` updates and an explicit initial contact set. |

Each report records `contact_active_set_converged: false` and
`numerically_accepted: false`. The reported final iterates pass global
and member equilibrium and the printed-precision interpolation audit, but
those checks do not establish a consistent set of open and closed contacts.
The second run also reports that its sampled unmodeled gaps remain open;
that limited gap check does not cure the contact convergence failure.

The archived forces, displacements and contact states are diagnostic output
from rejected iterations. They must not be used to qualify bolts, lumber,
base bearing or a maximum climber weight. This numerical outcome is not
proof of physical instability or construction failure.

The [archive manifest](../fea/results/compact-rail-study/manifest.json) identifies
both compressed native reports, authenticated launch-source ZIPs, the geometry
record and a compact summary. Each source snapshot was checked against the
corresponding report's source hashes before archiving. Reports preserve their
original bytes when decompressed. Large native solver cycle files remain in
the named `fea/generated/` directories; their hashes remain in the reports,
but those files are not bundled in this archive.
