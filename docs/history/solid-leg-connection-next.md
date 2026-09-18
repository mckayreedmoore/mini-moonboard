# Solid-leg connection: resolve bolt body length before enlarging holes

The next development choice is **verified full-body 3/8-inch hardware**, retaining
the extended 2×6 geometry for now. This is not a hardware selection or a joint
qualification. The [spread-joint native results](spread-leg-response.md) remain
unchanged, including their uncalibrated springs and fixed-floor assumptions.

The subsequent [standard-hardware CAD trial](leg-hardware-trial.md) uses a
4¼-inch bolt and four thick hardened washers to improve the tolerance basis
without larger bores. Its structural and receiving gates remain open.

## A material change affects the thread calculation

The earlier plywood leg consisted of two adjacent 3/4-inch plies. Each current
sawn-lumber leg is one continuous 1.5-inch member. The code now inventories the
actual raw CAD bearing intervals for all eight bolts: rim 2.032–40.132 mm,
solid leg 40.132–78.232 mm, measured from the under-head origin.

[NDS 2024 §12.3.7.2, page 95](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
permits full-body diameter in the lateral reference equations when threaded
penetration is at most one-quarter of the bearing length in the threaded
member. The solid leg's quarter length is 9.525 mm. At a nominal 3¾-inch bolt
length and 1-inch threaded tail, penetration is 8.382 mm: only 1.143 mm margin.
This nominal observation does not verify the actual fastener exception.

| Arithmetic scenario | Threaded bearing, mm | Quarter-condition margin, mm |
| --- | ---: | ---: |
| 3¾-inch bolt, nominal length and thread | 8.382 | 1.143 |
| Same, 1.524 mm overall shortfall; thread held fixed | 9.906 | −0.381 |
| 4-inch bolt, nominal length and thread | 2.032 | 7.493 |
| Same, 1.524 mm overall shortfall; thread held fixed | 3.556 | 5.969 |

These scenarios exclude thread runout. The required minimum full-body length
for the modeled stack is **68.707 mm (2.705 inches)** from under the head.
It must be recomputed for actual stock and washer dimensions.

Nominal length minus nominal thread length is not the guaranteed full body.
[Nickel Systems' dimensional guidance](https://www.nickel-systems.com/blog/what-are-max-grip-gaging-min-body-lengths)
distinguishes the last thread scratch from grip gaging and allows a five-pitch
transition. Its generic formula gives minimum body lengths of 61.9125 mm for
3¾-inch and 68.2625 mm for 4-inch 3/8-16 cap screws. Neither guarantees the
68.707 mm condition. These are a separate generic dimensional screen, not
certification of the current supplier's bolt; do not subtract overall-length
tolerance again from that minimum-body result.

## Conditional benefit, with the same native forces

Reusing the existing yield kernel, bearing directions, 45 ksi assumed bending
yield and reduction terms, changing only effective diameter from 0.298 to
0.375 inch gives the following maximum same-case lateral-demand/reference
ratios at the stiffest assumed springs. The governing cases are retained in
the [machine-readable report](../fea/results/solid-leg-thread-screen.json).

| Climber, lb | Root-diameter reference | Conditional full-body reference |
| --- | ---: | ---: |
| 150 | 0.633 | 0.502 |
| 200 | 0.803 | 0.637 |
| 250 | 0.972 | 0.771 |
| 300 | 1.142 | 0.906 |

This is **not a new FE solve or an adequacy pass**. No spring stiffness changes,
axial interaction, washer resistance, group effects, splitting or physical
restraints have been qualified. The favorable column is conditional on verified
fastener geometry and all the original material/reference assumptions.

## Larger bolts are not a drop-in alternative

The current 100×50 mm pattern has 46.888 mm minimum rim edge distance,
47.256 mm leg edge distance and 50 mm minimum along-grain pitch. A nominal
7/16-inch bolt meets the existing conservative 4D comparisons, narrowly;
1/2-inch does not. With 4D retained at both edges, the two-row minimum width
for 1/2 inch would be 141.2875 mm, exceeding the 2×6's 139.7 mm. Changing the
pitch or extending the leg top alone cannot close that width condition. These
are geometric screening rules, not the complete direction-specific NDS check.

Also, the current hardware renderer is explicitly a 3/8-inch dimensional
family: changing its diameter field alone would not resize the head, nut or
washers. Any larger-bolt experiment needs its own verified hardware envelopes
and collision checks. No larger bores or hardware were added to the viewer.

## Next release work

1. Obtain a traceable standard bolt specification or actual dimensional evidence
   establishing full-body length, runout, thread engagement and nut seating for
   the actual stack. A longer bolt is not automatically a compliant substitute.
   Retain the existing procurement list until this is resolved; no custom steel
   fabrication is proposed.
2. Establish the bending-yield basis for that fastener and check same-case
   lateral/axial action, washers, group action and splitting. Do not reuse the
   screw-withdrawal interaction equation for through-bolts.
3. With that connection and physical anti-roll/sway restraints defined, assess
   full-member combined behavior and compliant unanchored floor contact. These
   remain open, not implicitly passed by the favorable lateral reference.

This checkpoint avoids enlarging the wood or holes before resolving the current
fastener's actual load-bearing geometry. It does not approve climbing or alter
the current default design.

```sh
uv run python -m fea.solid_leg_thread_screen
uv run pytest -q tests/test_solid_leg_thread_screen.py
```

Verification: 35 focused thread-inventory, resistance and yield-kernel checks
passed, including exact replay of the published report. Ruff and whitespace
checks passed. Independent correctness, testing and package reviews found no
substantial issues. This is analysis implementation review, not joint approval.
