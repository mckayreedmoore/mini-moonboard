# Bolted candidate: active V4 simple-timber-joint plan

Status: **development only; G1 open; no cutting or drilling release.** This
plan implements the owner's V4 direction for the separate
`compact-floor-flush-bolted-development` lane. It supersedes the prior
[rated-HL bracket focus](bolted-candidate-rated-hardware-focus.md) as the
active design sequence, without erasing its test results or the selected
`compact-floor-flush-development` baseline.

## Fixed scope and design order

The physical board is kerf-right, cut from two 4×8 panels. Preserve its
climbing surface, panel outlines, holds/T-nuts/LED requirements, all 48
main-panel and 18 kicker screw axes, and the existing panel-screw policy.
Verify actual receiving timber and both inner kicker edge supports after
any hidden-frame change. Keep the selected baseline and authentic six-case
archives separate. The twelve old frame-bolt arrangements are starting
references, not automatically valid after changing frame geometry.

Use ordinary through bolts, metal nuts and suitable bearing washers for
structural move interfaces. A plain full-section face overlap is permitted;
it retains both member thicknesses and has a real centerline offset. A
rectangular solid-timber corner cleat with separate through-bolt groups is
permitted where it simplifies a butt corner. A small cleat may remain
bolted to one transport member. Factory metal brackets are optional when
their **complete installed** cost or engineering value is better. No
half-lap, housed/interlocking joinery, custom steel, panel through-bolts,
new panel fasteners, unqualified inserts, structural wood-thread removal
per move, manufacturer contact, or glued structural assembly is authorized.
Do not inherit HL bracket timber minima for ordinary timber joints.

Keep floor support and landing-space assumptions explicit. Do not claim
that nominal CAD fit, a single wood-bearing mode, bolt-shaft strength, or
one old proxy load is a complete structural joint. Evaluate actual
simultaneous actions, contact-only bearing, slip/rotation, load-to-grain
directions, bolt group and eccentricity, wood/washer/bolt resistance,
access, stock, disassembly and cost before selection. No member has been
physically inspected, cut or drilled.

## Bounded sequence

| Task | Required outcome | Gate |
| --- | --- | --- |
| PB-00 | Reconcile candidate authority and tests; archive bracket-only decision without changing baseline rules. | Scope only |
| PB-01 | Compare full-section overlap and rectangular cleat at one actual rail duty; complete bolt/wood geometry, preliminary action path, access and purchased-cost comparison. | Representative joint |
| PB-02 | Connect the center/base assembly, backing and adjoining rail ends; map all original duties and select a costed mixed-or-single architecture. | G1 concept |
| PB-03 | Build one coherent kerf-right CAD assembly with full stacks, receivers, no unintended SDS path and individual-member transport sequence. | Physical geometry |
| PB-04 | Complete 2024 NDS-applicable local checks, contact/stiffness inputs and map all 36 criteria without waiving their safety questions. | G2 analysis inputs |
| PB-05 | Run all six required cases on one frozen candidate, including the forward case; reconcile convergence and resistance. | Candidate evidence |
| PB-06 | Deliver costed stock/cut/drill/hardware and assembly packet plus independent review, with remaining physical receiving checks explicit. | Owner decision packet |

PB-01 compares *both* simple joint types at the same rail duty, but does
not force both to be selected. A 2×2 cleat is a screening suggestion, not
an approved section; size it from actual edge/end, group and action checks.
The cleat's two bolt groups are serial load-transfer interfaces, not
capacities to add. Orthogonal bores must not collide and both ends of each
bolt need washer/nut and tool access. Avoid precision joinery or a new
generic optimization framework. PB-02 follows only after a credible rail
detail or an exact limiting condition with one concrete adjustment.

Purchased cost includes full bolt/nut/washer stacks, changed timber,
retained brackets if any, tooling/consumables, and known delivery/tax;
unknown prices stay unknown. Keep owner-owned stock, sunk hardware,
fabrication effort and move operations separate. The historical $122.70
ML24Z/SDS subtotal is not a complete frame budget or a price ceiling.

## Claim and evidence boundary

Use the existing [2024 NDS component helpers](../mini_moonboard/bolted_timber_checks.py)
only within their documented scope. A two-member lateral-yield result
does not cover cleat integrity, splitting, axial separation, group
effects, formed steel, or an entire frame. Same-case loads must be
recomputed for the selected topology, including the earlier difficult
forward contact state. Preserve failed and nonconverged diagnostics as
history; never substitute them for accepted forces. No selected-candidate
hash may be edited merely to silence the existing stale-snapshot CI gate.

Source scope: [AWC TR12](https://awc.org/wp-content/uploads/2021/12/AWC-TR12-1510.pdf)
describes dowel-yield lateral methods and exclusions; the
[USDA Wood Handbook, Chapter 8](https://research.fs.usda.gov/download/treesearch/62253.pdf)
provides illustrative loaded-edge guidance, not a complete 2024 NDS
joint verdict. The task-supplied V4 plan is the scope handoff; current
model, authenticated sources and fresh candidate evidence govern numbers.
