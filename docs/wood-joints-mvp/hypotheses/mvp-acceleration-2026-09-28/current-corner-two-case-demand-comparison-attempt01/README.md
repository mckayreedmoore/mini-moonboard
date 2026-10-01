# Two conditional corner-demand cases

The independent parent export audits authenticate all seven increments of
the current a12-rear and a1-rear corner reports. Both cover the complete left
outer BG001/BG003/BG045 chain, including contacts, washer seats and onward
transfers. `comparison.json` preserves each of its eight lateral-plane and
six axial-tie vectors separately, with per-case maxima across the increments.

| Group | Maximum lateral-plane resultant, a12-rear | Maximum lateral-plane resultant, a1-rear |
| --- | ---: | ---: |
| BG001 post/spine | 335.061 N | 146.049 N |
| BG003 spine/side/inner block | 483.948 N | 137.900 N |
| BG045 inner block/header | 90.116 N | 87.077 N |

These are demands, not capacities. A12-rear has the larger group maximum in
each row of this table, but that does not permit transferring a direction,
loaded-end selection, bearing or splitting check to A1. Individual signed
actions can reverse. In particular, BG003 side_1's spine-plane Y/Z vector
changes from approximately (-292.424, +385.608) N in a12-rear to
(+93.920, -100.972) N in a1-rear. Each case must retain its own action vector.

The same comparison records all seven increments of the sixteen modeled
contact cells at the four primary timber interfaces. Their engagement differs
between these cases. At full load, all four post/spine contact actions in A1
have zero-containing force intervals; a12 instead resolves compression there.
All four inner-block/header contact actions in a12 have zero-containing force
intervals; A1 resolves compression there. A zero-force interval alone does not
prove finite separation, but supplies no resolved compression to credit.
The exported bolt forces and ties retain the load transfer for that modeled
state. Neither case can inherit the other's face-bearing contribution.

Peak modeled cell-average pressures at full load are:

| Interface | a12-rear | a1-rear |
| --- | ---: | ---: |
| Post / exterior spine | 0.03737 MPa | 0 MPa |
| Exterior spine / side | 0.02188 MPa | 0.02116 MPa |
| Side / inner block | 0.01376 MPa | 0.00620 MPa |
| Inner block / header | 0 MPa | 0.02615 MPa |

These are normal force divided by the source modeled contact-cell area,
independently checked by the producer. They are not continuous contact
pressures, actual timber stresses or resistance comparisons. They remain
dependent on the source contact penalty and geometry assumptions.

Only two of six registered cases supply usable corner demands, at the
recorded zero-gap and proxy-stiffness scenario with an unverified no-slip
floor. This comparison is not the requested six-case envelope or engagement
and stiffness sensitivity. It establishes no complete corner resistance or
joint acceptance and does not reopen the twelve original LEG/FLOOR-RUNNER
resistance arrangements. The 92 new block axes remain a separate inventory.

Reproduce from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-two-case-demand-comparison-attempt01/produce.py
```

The producer authenticates exact report hashes against their parent audits.
It never launches a solver or combines independently maximized components
into an invented load case.
