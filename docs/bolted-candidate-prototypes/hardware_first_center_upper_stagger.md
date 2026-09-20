# Center-tongue rear-staggered upper HL33 screen

**Status: rejected sampled installed poses.** The outer upper HL33s stay at
Y = -100..-36.5 mm. One inward-facing factory HL33 is placed on each
principal at three rearward shifts: 63.5, 66, and 70 mm. These are discrete
samples from the current `hardware_first_center_tongue` one-piece principal
and header solids, not a continuous optimization or a new member design.
Regenerate the paired JSON with `uv run python -m
scripts.hardware_first_center_upper_stagger --output
docs/bolted-candidate-prototypes/hardware_first_center_upper_stagger.json`.

The [Simpson 2026–2027 connector catalog](https://www.strongtie.com/resources/literature/wood-construction-connectors-catalog)
(HL33 row, PDF p. 315) gives 82.55 mm equal legs, 63.5 mm bend length,
31.75 mm along-bend hole offset, and 50.8 mm vertical-leg hole offset. The
horizontal-leg hole inset is undimensioned; this screen assumes 50.8 mm.
Ideal plate thickness is 4.55 mm and ideal wood-bore diameter is 14.2875 mm.
They are diagnostic envelopes, not delivered dimensions or drill sizes.

| Rearward shift | Inward plate Y range | Principal bolt Y | Missing wood per principal bore |
| ---: | ---: | ---: | ---: |
| 63.5 mm | -163.5..-100 mm | -131.75 mm | 1,115.537 mm³ |
| 66 mm | -166..-102.5 mm | -134.25 mm | 3,044.079 mm³ |
| 70 mm | -170..-106.5 mm | -138.25 mm | 6,776.071 mm³ |

At 63.5 mm, the inward and outward plate bands merely touch at Y = -100 mm;
the larger shifts leave a Y gap. None collides with an existing outer plate.
The new bore center at the minimum shift is only **5.2552 mm** from the
principal's near transverse boundary in its sloping broad face, less than
the **7.14375 mm** ideal bore radius. Full solid intersection confirms the
missing receiver wood above. At 66 and 70 mm the center boundary distance
shrinks to 3.3401 and 0.2759 mm. This is an oblique-cut geometry screen,
not a formal code end-distance classification.

The two inward seats remain at the *same* Y station as each other. Each
sample therefore retains 14,764.068 mm³ of seat-to-seat overlap and two
1,314.609 mm³ vertical-leg/seat overlaps. Each seat also intrudes
9,086.691 mm³ into the opposite principal. Rearward translation of both
brackets does not cure those occupied-volume conflicts over the sampled
range. The report gives every plate and bore bound and intersection.

Each inward principal bolt has a **separate axis** from its
outer mate, with a 63.5, 66, or 70 mm Y-direction center separation.
Because the principal grain slopes in Y/Z, those are not same-row
along-grain pitches. At 63.5 mm the components are about 40.8 mm along
grain and 48.6 mm across grain. The report gives the center-separation
3D and 4D comparators for nominal 12.7 mm bolts, plus exact modeled
centerline boundary rays for all existing and new fastener axes. At the
minimum shift, the principal's positive grain ray to its oblique end is
66.3147 mm, a -22.5853 mm margin to 7D; the negative transverse ray is
5.2552 mm, a -45.5448 mm margin to 4D. The header's apparent ±230 mm
grain boundaries are raised-profile shoulders, not free ends. All new
header axes remain independent of the original header axes and have at
least 27.4241 mm ideal bore-surface gap at the minimum shift. These are
measurement and search filters only. Load direction, formal end/edge
category, bolt grouping, delivered tolerances, and strength remain open.

Both panel outlines, all 66 panel/kicker screw axes and receiving wood, and
all twelve existing frame axes remain fixed. No sampled new hardware has a
positive-volume clash with panel solids, protected 50.8 mm screw envelopes,
conditional 63.5 mm overall screw envelopes, frame-axis envelopes, or
independent bore axes. The original tongue baseline has no failures.
This rejection applies to the three specified paired inward poses. It
provides no connector capacity, drilling coordinates, installation approval,
or reversible F1 qualification. No lap joint or custom steel is modeled.
