# Larger bolts and wider four-bolt patterns: completed investigation

**No passing candidate was found in the tested four-bolt pattern family while
retaining the existing single 2×6 leg and rim.** This completes the requested
larger-bolt/wider-pattern investigation. It does not establish that every
possible connection using these members is impossible.

The search assessed 801,905 combinations using the previously selected load
assumptions and actual wood boundaries. Every geometrically acceptable candidate
still exceeded the lateral connection reference. Consequently none advanced
to a construction model or purchase specification.

## Results

A demand/reference ratio at or below 1 passes the individual lateral check.
Pitches below are measured along the leg and rim grain directions; the four
centers form a parallelogram, with two grain-parallel rows in each member.

| Bolt diameter | Placement-passing trials | Best lateral ratio | Best leg/rim pitches | Minimum nominal placement margin |
| --- | ---: | ---: | --- | ---: |
| ⅜ inch | 13,142 | 1.282 | 102 / 44 mm | 0.359 mm |
| 7⁄16 inch | 1,696 | 1.198 | 92 / 46 mm | 0.014 mm |
| M12 | 225 | 1.193 | 86 / 52 mm | 0.193 mm |
| ½ inch | 0 | — | — | — |
| ⅝ inch | 0 | — | — | — |

The best ⅜- and 7⁄16-inch groups shift their centroid −16 mm along the leg and
+4 mm along the rim. The best M12 group shifts −20 mm along the leg. These are
analytical trial coordinates, not drilling instructions. The very small nominal
placement margins do not include machining tolerance and are insufficient to
claim a robust fabrication detail. Even at nominal geometry the lateral checks
fail.

## Why diameter alone did not solve it

Larger bolts need more wood around each hole and more space between rows.
Under the two bending cases, individual leg bolts load toward both edges.
The conservative directional application of NDS loaded-edge and row-spacing
rules requires 141.29 mm depth for two rows of ½-inch bolts, or 170.66 mm for
⅝-inch bolts. Available depth is 139.7 mm. The [directional spacing review](leg-directional-spacing.md)
distinguishes the actual table rules from the conservative per-bolt application
to a combined force/moment group.

**Correction to the earlier rough diameter table:** that sensitivity held wood
bearing strength constant while increasing bolt diameter. The NDS perpendicular
bearing expression depends on diameter:

`Fe_perpendicular = 6100 × G^1.45 / sqrt(D_inches)`.

The corrected search uses `G = 0.50`, diameter-dependent bearing and
Hankinson interpolation for each bolt force, and diameter-dependent group
stiffness. Thus the earlier 0.91 ratio for a ⅝-inch bolt was an optimistic
incomplete comparison, not evidence of an acceptable replacement. Primary
provisions are in [NDS 2024 Chapter 12](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf),
section 12.3.3 and the placement tables in section 12.5.1.

## Search scope and assumptions

- Actual member thickness/depth: 38.1 × 139.7 mm; original grain axes and wood
  boundaries retained.
- Four bolt centers: all combinations of 38–110 mm pitches in 2 mm increments,
  with centroid shifts of −24–24 mm in 4 mm increments along each grain axis.
- Both full-contact pressure cases from the [completed leg assessment](leg-completion-decision.md).
  The joint moment is recalculated about each moved group centroid.
- Forces on the leg oppose those on the rim. Loaded-edge distances follow each
  bolt's force direction; between-row spacing, 4D full-value along-row spacing,
  conservative 7D end clearance, and maximum cross-grain spread are checked.
- Fully smooth shanks in both wood members; bending yield at least 45 ksi;
  dry-service, normal-duration factors and conservative yield reductions.
- Four-fastener/max-pitch group-action factor is retained as a conservative
  screen. No tightening friction is credited.

This is a bounded grid, not a continuous global optimization or a search of
all bolt counts and connection topologies. Reduced-value along-row spacing was
not credited. End, edge and capacity calculations are necessary checks; they
do not establish net-section, splitting, prying or complete installed behavior.
Since all candidates fail a necessary lateral or placement check, those later
checks cannot turn these trial results into a passing design.

The analysis assumes fresh stock. Moving holes in previously drilled stock
would require a separate repair detail; no plugging or re-drilling approval is
implied.

## Resulting design direction

A purpose-designed steel bracket or splice that attaches over a longer length
of each member is the next connection approach to investigate if the single
2×6 legs are retained. It can place its two sets of fasteners independently,
without requiring every bolt to fit inside the present wood-to-wood overlap.
That concept is not yet modeled or qualified. A physical hinge remains another
option if reducing transferred moment is preferred.

## Reproduction and validation

- [Search code](../fea/leg_bolt_pattern_search.py)
- [Results, exact coordinates and input hashes](../fea/results/leg-bolt-pattern-search-v1.json)
- [Focused tests](../tests/test_leg_bolt_pattern_search.py)

```sh
uv run python -m fea.leg_bolt_pattern_search --output /tmp/leg-pattern-search.json
uv run pytest -q tests/test_leg_bolt_pattern_search.py
```

Independent review checked loaded-edge signs, moved-group equilibrium, fixed
wood boundaries, diameter-dependent group action, and placement formulas. It
identified and corrected the bearing-diameter issue before the final search.
Six focused tests passed, including a regression check for that error. Source
hashes were verified against the current calculation files and archived input
geometry.
