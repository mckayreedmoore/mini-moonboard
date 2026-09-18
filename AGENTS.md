# Repository working agreements

## Selected authority

The selected candidate is `compact-floor-flush-development`. Machine authority
is [`current-candidate.json`](current-candidate.json). The shop packet is the
[assembly guide](docs/floor-flush-assembly-guide.md),
[shop checklist](docs/floor-flush-shop-checklist.md) and
[construction sheets](docs/floor-flush-construction/). Evidence and gates are
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
shoes. Inserts are not installed, qualified or build-ready.

Preserve older candidates and their evidence as history. Occupied CAD
diameters and `connection-axes.csv` modeled lengths are analysis envelopes,
not bit or purchased-length instructions; use the shop columns and checklist.

## Communication

Keep chat concise. Documentation, website text, code and commits use normal
prose. Preserve changes belonging to other agents, including untracked files.

## Working set

See [docs/selected-working-set.md](docs/selected-working-set.md). Do not treat
historical `current-*` documents, `exports/` of other candidates, or
`fea/generated/` as the selected shop packet.
