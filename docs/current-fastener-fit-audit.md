# Current through-bolt fit audit

Scope: `wide-principal-development`, checked on 2026-09-08. This supplements
the [selected dimensional hardware family](selected-bolt-hardware.md), whose
historical quantity table belongs to an earlier variant. The current exported
connection schedule remains the source of installation coordinates.

## Current stacks

| Family | Quantity | Nominal under-head length | Nominal wood grip | Minimum calculated tip projection |
| --- | ---: | --- | ---: | ---: |
| Leg to rim | 8 | 95.25 mm / 3¾ in | 76.2 mm | 4.9022 mm |
| Leg-ply stitches | 6 | 63.5 mm / 2½ in | 38.1 mm | 11.7602 mm |
| Base gussets | 8 | 76.2 mm / 3 in | 57.15 mm | 4.9022 mm |
| Lower backing | 2 | 152.4 mm / 6 in | 127.668 mm | 9.5682 mm |

All 24 use the selected 3/8-16 dimensional family, one nut and two SAE washers.
Projection subtracts the documented bolt underlength allowance, two maximum
2.032 mm washer thicknesses, maximum 8.5598 mm nut thickness and **nominal**
wood grip. Every calculated value exceeds two pitches (3.175 mm). This is not
a guarantee of two complete usable exposed threads: actual grip, tip chamfer,
thread runout and delivered dimensions remain inspection items. No tightening
torque or clamp-friction credit is established.

Using the published reference thread length and the minimum washer stack also
places each nut's modeled start beyond the nominal unthreaded shank. This does
not resolve the unknown manufactured thread runout or authorize a substitute
bolt with a different thread length. The stitch bolts have appreciably more
projection; shortening them is a possible later fit optimization, not an
unannounced change to the current purchasing/CAD schedule.

## Washer support in actual machined CAD

All **48 washer bearing planes** have a complete nominal wood-support annulus
in the current machined bodies, including the two recessed backing-head seats.
The check probes 0.1 mm into the declared first/last wood member at each actual
washer contact plane. It excludes the 11.1125 mm bore and uses the selected
minimum 20.447 mm washer OD, yielding approximately 231.372 mm² supported area.
Negative-control tests confirm that an air gap or an edge-clipped seat would
not pass the full-annulus check.

This resolves the geometric full-support prerequisite for the
[conditional wood-bearing calculation](backing-bearing-envelope.md). It does
not prove uniform pressure, washer rigidity, sound wood, acceptable compression,
local ligament strength or adequate joint resistance. Physical gaps, oversized
holes, wood damage and machining tolerances can invalidate the nominal result.

```bash
uv run pytest -q tests/test_washer_seating.py
```

The 56 removable panel insert/machine-screw pairs and 108 manufacturer bracket
screws are separate attachment families. They are not included in the 24-bolt
stack or 48-washer counts, and no bolt result transfers to their resistance.
