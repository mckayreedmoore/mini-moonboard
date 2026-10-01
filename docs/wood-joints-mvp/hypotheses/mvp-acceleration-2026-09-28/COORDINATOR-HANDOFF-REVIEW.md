# Independent coordinator-handoff review

Read-only review of [`COORDINATOR-HANDOFF.md`](COORDINATOR-HANDOFF.md), its
source-preparation records, and the current owner constraints. No model or
candidate geometry was changed, and no native solve was run.

## Consequential preflight finding

The proposed first reduced-frame law gives the 66 Hillman 42605 panel/kicker
screws lateral resistance only and no axial withdrawal credit. The six frozen
climber loads all have positive outward components along the source panel
normal `[-0.0, 0.7660444431189781, -0.6427876096865394]`. Direct dot products
with the forces in [`current-load-cases.json`](../evaluation-resume-2026-09-24/current-load-cases.json)
are:

| Case | Outward component (N) |
| --- | ---: |
| A12 rear | 1,659.44 |
| A12 forward | 1,199.82 |
| A12 left | 1,429.63 |
| K12 right | 1,429.63 |
| K12 rear | 1,659.44 |
| A1 rear | 1,659.44 |

The dynamic factor is already in those frozen forces. With no tension path,
compression-only panel-to-frame contact cannot react these outward loads. Treat
Hillman withdrawal stiffness and resistance as a primary integration gate:
use a source-supported law or an explicitly conditional sensitivity, or report
that the reduced model lacks this load path. Do not publish a complete
six-case demand table until the path is represented.

A resulting solver mechanism would establish only that the chosen analytical
model is incomplete or lacks equilibrium. Before calling the *physical design*
mechanistic or failed, audit all contact and fastener paths for verified
alternative restraint. The current preparation extracts 117 opposed planar
patches across 115 pairs; six pairs remain zero-area or unresolved, and the
center-kicker receiver paths are still open. No physical-failure conclusion
follows from omitting a presently unqualified screw-withdrawal law.

## Other review notes

- The handoff correctly calls the gravity/load compilation and global tipping
  screen preparation only, retains all 47 MVP-E criteria as open, and explicitly
  retires the old patched contact-instrumentation coupon as a route prerequisite.
  Its staged static fixtures remain appropriate for methods actually used by
  the reduced model.
- The main integration risks are disclosed: 586 hardware gravity rows still
  need defensible mechanical carriers; member self-weight must be distributed
  to recover internal bending; panels/screws, retained bolts, connector
  engagement, contact, floor support, and alternate center-kicker paths need
  explicit mappings and equilibrium checks. The 1,022 internal and 100 floor
  contact cells preserve area and first moment but do not establish active
  contact or stiffness.
- The route remains conditional on material, grain, panel, hardware and
  resistance applicability. Neither static convergence nor the gross tipping
  screen is a criterion pass or frame-stability acceptance.

## Sources checked

- [`reduced-static-attempt01/README.md`](reduced-static-attempt01/README.md)
- [`reduced-static-attempt01/prepare.py`](reduced-static-attempt01/prepare.py)
- [`fea/wood_joint_reduced_contacts.py`](../../../../fea/wood_joint_reduced_contacts.py)
- [`fea/wood_joint_reduced_loads.py`](../../../../fea/wood_joint_reduced_loads.py)
- [`fea/wood_joint_reduced_members.py`](../../../../fea/wood_joint_reduced_members.py)
- [`fea/wood_joint_reduced_panels.py`](../../../../fea/wood_joint_reduced_panels.py)
- [Owner mechanics-architecture guidance](../../next-mvp-plan.md#owner-mechanics-architecture-guidance-september-27)
- [`AGENTS.md`](../../../../AGENTS.md)
