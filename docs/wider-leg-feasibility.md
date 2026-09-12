# Wider dimensional-lumber legs: preliminary feasibility

**Historical preliminary screen.** The subsequent
[actual-CAD review package](wider-leg-review/README.md) implements a revised
group location, catalog hardware and local resistance checks. Its numerical
results and limitations supersede this document's unfinished-work list; the
original preliminary coordinates below remain preserved for traceability.

**Yes: a larger single piece of dimensional lumber is a credible route without
custom steel fabrication.** The strongest preliminary option checked here uses
single 2×8 legs and matching single 2×8 outer rims, with six ½-inch bolts per leg.
Its lateral connection ratio is **0.818**, where 1.0 is the reference limit.
The minimum checked nominal placement reserve is **2.51 mm** beyond the applied
edge, end and spacing criteria. This is a promising screening result, not a
construction release or a prediction of breaking strength.

The owner now permits larger single-stock support legs and prefers to avoid
custom fabrication. The older single-2×6 designs remain preserved. Neither a
larger member nor the proposed bolt pattern has been selected or installed in
the current CAD.

## What changes

The preliminary six-bolt pattern has three positions along the leg, spaced
66 mm apart, and two positions along the rim, spaced 84 mm apart. Its center
moves −20 mm along the leg and +4 mm along the rim from the previous group
center. That means twelve leg bolts total, replacing the previous eight in a
fresh-stock design. These trial coordinates are not released drilling dimensions.

Both sides of the joint need attention. With the current 2×6 outer rim retained,
the checked larger-leg/four-bolt options still miss the lateral criterion or
placement reserve. A wider leg alone does not enlarge the rim's available
fastener area.

Nominal 2×8 stock is 1½ × 7¼ inches, compared with 1½ × 5½ inches for 2×6.
Nominal 2×10 is 1½ × 9¼ inches. These are standard dimensional sizes; see
[AWC's lumber size table](https://web-media.awc.org/wp-content/uploads/2021/11/17210943/AWC_EPD_NorthAmericanSoftwoodLumber_20200605.pdf).
The preliminary option uses ordinary bolt diameters and wood machining. Final
catalog bolt, nut and washer selections are still required; the earlier custom
plate-washer trial is not silently included in this proposal.

## Comparison

All ratios below are preliminary lateral connection results with applicable
placement checks, not full member/connection qualifications.

| Leg and adjoining rim | Bolts per leg | Best checked ratio |
| --- | --- | ---: |
| 2×8 leg, existing 2×6 rim | Four ½-inch | 1.244 |
| 2×10 leg, existing 2×6 rim | Four ½-inch | 1.215 |
| 2×8 leg and 2×8 rim | Four ½-inch | 1.070 |
| 2×10 leg and 2×10 rim | Four ⅝-inch | 0.990 |
| 2×10 leg and 2×10 rim | Four ¾-inch | 0.956 |
| **2×8 leg and 2×8 rim** | **Six ½-inch** | **0.818** |

Six bolts give the proposed 2×8 connection a better calculated margin than the
four-bolt 2×10 options. The six-bolt calculation includes a conservative
six-fastener group factor of 0.9509, rather than multiplying a single-bolt
capacity by six without adjustment.

## Assumptions and limits

The load basis remains a 250 lb climber with twice body weight downward,
300 N rearward force, up to 100 mm hold projection, equipment/hardware
allowances and all rear-support compression assigned to one leg. Feet are
assumed not to slide. The full-contact pressure-resultant range widens with
larger leg stock, and additional wood mass is included approximately at the
previous centers of gravity. Thus the wider-leg comparison includes changed
loads; it does not assume the old moments stay fixed.

Both members remain 38.1 mm thick. Smooth bolt shanks through both wood members
and bending yield of at least 45 ksi are assumed. Diameter-dependent wood
bearing and force-direction-dependent loaded edges are retained. Existing
smaller-section group stiffness is used conservatively.

The calculation centers wider stock on the previous axes. Final CAD must locate
the wider rims compatibly with the panels and existing connections. The screen
has not established net-section strength, wood splitting, lap prying, bolt
combined actions, washer bearing, or actual hardware fit. User approval of this
feasibility result would not establish those unchecked properties.

## How close

There is now a preliminary passing connection layout with about 18% unused
reference capacity in the checked lateral calculation. That percentage is not
an overall project-completion percentage or a reserve to physical failure.

The finite remaining work for this candidate is:

1. Check the new wood sections and complete joint resistance, including splitting,
   prying, washer bearing and combined bolt actions.
2. Specify available bolt lengths, shank/thread requirements, nuts and washers
   that meet those checks without custom fabrication.
3. Update the local CAD, verify fit with adjoining parts, and issue the revised
   hole pattern and lumber/hardware schedule.

No panel/T-nut qualification, comparison frame or floor-friction test is added.

## Evidence

- [Six-bolt calculation](../fea/wider_leg_six_bolt_screen.py)
- [Six-bolt result, forces and source hashes](../fea/results/wider-leg-six-bolt-screen-v1.json)
- [Four-bolt larger-stock comparison](../fea/wider_leg_pattern_screen.py)

Independent review reproduced the six-bolt result and checked force/moment
balance, loaded-edge directions, row geometry and group action. Three focused
tests passed. The result remains a feasibility screen pending the listed work.
