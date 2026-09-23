# Repository working agreements

## Selected authority

The selected candidate is `compact-floor-flush-development`. Machine authority
is [`current-candidate.json`](current-candidate.json). The shop packet is the
[assembly guide](docs/floor-flush-assembly-guide.md),
[shop checklist](docs/floor-flush-shop-checklist.md) and
[construction sheets](docs/floor-flush-construction/). Bought 4×4 plywood uses
that folder. 4×8 rips use
[kerf sheets](docs/floor-flush-construction-kerf-right/)
([which plywood packet](docs/floor-flush-width-option.md)). Same candidate, not
a second load study. Evidence and gates are
in the [MVP master plan](docs/floor-runner-mvp-master-plan.md) and
[completion ledger](docs/floor-runner-mvp-completion-ledger.md).

This is engineer-unreviewed conditional DIY documentation under recorded
loads, DF-L No. 2, catalog hardware and an explicit no-slip floor assumption.
It is not a fabrication release, manufacturer qualification, inspected build,
verified floor or climber rating.

Do not transfer acceptance from a preserved candidate, historical six-case
pass, or a document that still calls itself “current.” Resolve history through
the selected authority. Chronological constraints live in
[docs/history/decision-log.md](docs/history/decision-log.md).

## Claim boundary

- Six authenticated no-slip cases pass 36 frozen adopted checks. That does not
  qualify every failure mode.
- Listed ML24Z force interactions and catalog-unlisted separation / independent
  flange couples remain distinct. Do not invent capacities.
- 66 purchased Hillman 42605 panel/kicker screws are separate from 144
  specified SDS25112 screws in 24 ML24Z angles. Do not transfer SPAX
  resistance, stiffness, pilots or installation rules to Hillman. The owner
  selected a lead-hole pilot plus face countersink; bit sizes are recorded on
  the shop checklist, not published by Hillman and not CAD occupancy.
- Partially threaded bolts are the basis. Full-thread-root sensitivity is
  non-adopted and exceeds 1.0. Nominal bolt length is not delivered shank.
- No-slip floor support is an unverified analytical assumption. Do not add a
  floor-friction test or claim an anchor.
- Do not claim actual wood, cuts, holes, hardware, pads or floor were
  inspected. Checklist Actual/Disposition cells stay blank until observed.
- Do not run native solves, enlarge members, redesign the frame, or add
  external sign-off as a blanket new prerequisite. A failed adopted criterion,
  missing load path, contradictory instruction or incompatible delivered part
  still stops the affected operation.

## Geometry and hardware constraints

Keep solid 4×6 legs/rims, compact single 2×6 base members, two outboard 2×6
runners, whole kickers, the 1:12 rear recess, twelve outward-facing bolt
stacks, 24 ML24Z angles and 66 panel/kicker axes. Do not double-stack vertical
2×6s or introduce built-up vertical substitutes. No custom fabricated steel
shoes. Inserts are not installed, qualified or build-ready. Later conversion
of the 66 Hillman and 144 SDS axes is a geometric option on the current
stations ([screw-repair-inserts](docs/screw-repair-inserts.md)); do not drill
insert pilots at build. The twelve frame bolts stay bolts.

Preserve older candidates and their evidence as history. Occupied CAD
diameters and `connection-axes.csv` modeled lengths are analysis envelopes,
not bit or purchased-length instructions; use the shop columns and checklist.

## Communication

Keep chat concise. Documentation, website text, code and commits use normal
prose. Preserve changes belonging to other agents, including untracked files.

## Working set

Builder docs start at [docs/README.md](docs/README.md). Older studies are in
[docs/history/](docs/history/). See
[docs/selected-working-set.md](docs/selected-working-set.md).

## Structural-only bolted candidate lane

The candidate `compact-floor-flush-bolted-development` is a separate
development lane. It may replace the 144 structural SDS attachments at 24
ML24Z stations only after its own geometry, mechanics, and evidence gates
pass. Preserve `compact-floor-flush-development`, its evidence, its twelve
existing frame-bolt arrangements as the starting layout, and its 66
Hillman panel/kicker screws. For the owner-directed two-vertical-bolt
principal/header layout, panel/kicker screw axes may move where necessary to
keep supported receivers after hidden-frame changes. Record every moved axis,
retain the 66-screw count and purchased screw policy, and recheck backing,
edge support, installation, and load transfer. This relaxation applies only
to the separate bolted candidate; the selected angle-frame axes stay fixed.
On 2026-09-20 the owner approved changes to hidden
frame members in this separate lane;
the earlier center-support-only limit no longer governs it. Preserve the
climbing surface, panel outlines, and panel/kicker screw count, and verify
kerf-right kicker edge support. Changed frame bolts must be rechecked, not
silently assumed preserved. Panel through-bolts, inserts, new panel fasteners,
and custom steel remain outside this lane. The owner's earlier
"just brackets, no lap joints" instruction is historical for this candidate:
the later V4 scope allows plain full-section, face-to-face timber overlaps
and bolted solid-timber corner cleats. Factory brackets are optional.
Half-laps, housed/interlocking joinery, and routine structural wood-thread
removal remain excluded. Use through bolts with metal nuts and washers;
preserve individual-member transport and check complete joints and costs.
This scope approval does not select a connector or authorize cutting or
drilling. See
`docs/bolted-candidate-plan.md` and the task ledger for the bounded sequence.
For this separate lane, the owner selected direct cross-dowel/barrel-nut
connections as the current development approach; the
[simple-joints V4 plan](docs/bolted-candidate-simple-joints-v4.md) and
rated-hardware focus are retained as history.
The selected-candidate stock/geometry constraints above remain binding only
for selected-baseline changes. The bolted candidate must keep the panel/screw
hardware policy and prove any new receiver/backer connections rather
than inheriting the old member identities or case passes.
