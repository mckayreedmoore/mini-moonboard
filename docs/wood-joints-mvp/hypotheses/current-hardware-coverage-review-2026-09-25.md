# Independent review: current WJ24 hardware coverage

**Reviewed:** 2026-09-25. **Disposition:** no remaining material count,
source-binding, or conditionality defect found after the historical-count
wording was clarified.

Reviewed [current-hardware-coverage.md](../current-hardware-coverage.md),
SHA-256 `40aadf989a3d6d797f1ff1958aeba94389b72ea36d33ad36bcc39c9c424b1e60`,
and [current-hardware-coverage.json](../current-hardware-coverage.json),
SHA-256 `8e1a5325d99aa83a82cfd7dba1e6767ea2e2ba484be38e5fb12df39b227afdea`.
The JSON pins the current source notes and the axis source
`grip-screen-attempt02.json` (SHA-256
`9f84a15ed05ca9832f594c4a0b2c8d1322b90e74e462aa7c725b031bad69643a`). That
source identifies revision `led-clearance-2x6-runner-seated-blocks-v1`,
reviewed commit `b1e8707d`, and 92 candidate axes. All ten pinned hardware
source-note hashes were recomputed and match.

The nine candidate-family lists have counts summing to 92 and form an exact,
duplicate-free partition of the 92 source axis IDs. Every family records one
bolt, one nut, and two washer roles per axis. The retained lists contain the
12 distinct IDs in the kerf-right bolt schedule: four lumber-leg upper bolts,
four front-rail bolts, and four rear-rail bolts. Their recorded diameter,
length, and grip groups match that schedule (12.7 × 203.2 / 177.8 mm,
9.525 × 101.6 / 76.2 mm, and 9.525 × 114.3 / 88.9 mm respectively).
Together this supports 104 represented structural stacks: 104 bolts, 104
nuts, and 208 separate washers. The current hardware schedule defines the
candidate CAD roles as an integral-head bolt (head plus shaft geometry), two
washers, and a nut; it does not count those five geometry roles as five
purchased components. The retained geometry review separately records 12
retained arrangements and five modeled components per stack.

The count boundary is clear after the author’s edit: the historical inventory
was 104 **candidate** axes / 216 candidate washer equivalents, with the 12
retained frame stacks separate; its four special backer stacks had additional
washer roles. Current coverage is 92 candidate plus 12 retained stacks, or
104 total stacks / 208 washers. The older source
[`wj24-hardware-inventory/README.md`](wj24-hardware-inventory/README.md),
SHA-256 `60602de76db370bf4e0dc73ad93aef1feeb4e6debdfbf424692577c95ee49ccc`,
confirms the candidate-versus-retained distinction. The current coverage
keeps the 66 Hillman 42605 panel/kicker screws separate and excludes the 144
removed SDS25112 axes.

The shared Lawson option is aggregated once: its `candidate_side_16` and
`candidate_knee_inner_header_4` families have 20 distinct axes total. One
25-piece bolt pack and one 100-piece box each of the nut and washer leads
cover 20 bolts, 20 nuts, and 40 washers, leaving 5, 80, and 60 pieces. The
coverage explicitly says not to add another bolt pack from the isolated
16-axis and four-axis rows.

Product language remains conditional throughout. Supplier SKUs are called
catalog leads or candidates; model lengths, `LG`/`LB`, and thread intervals
are described as screens, not delivered dimensions or functional nut
engagement. The note does not select a universal 1/4-20 stack, transfer
retained baseline acceptance, assign strength or capacity, or represent
purchase, receipt, stock ownership, or physical fit. The cited retained
Bolt Depot items remain historical product references and are explicitly
subject to WJ24 recheck. The note reports 76 axes with a named supplier bolt
lead and 16 without an exact supplier SKU; the family arithmetic supports
those totals.

All 13 relative Markdown links in the coverage note resolve. The new coverage
Markdown and JSON were not yet in Git’s tracked-file list at review time, and
no existing `docs/README.md` or evaluation-resume index link to the coverage
note was found; treat that as a publication/handoff check if these artifacts
are intended to be retained or linked for downstream readers, not as a count
or sourcing defect.

Validation was read-only: compared family and package records to the pinned
attempt02 source, retained IDs to the 12-row kerf-right bolt schedule and
retained review, recomputed all embedded source hashes, and checked local
Markdown links. No vendor search, CAD operation, native solve, or source edit
was made as part of this review.
