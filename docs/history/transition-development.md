# Perimeter-transition inspection variation

[Open the separate 3D model](https://mckayreedmoore.github.io/mini-moonboard/?model=lower-transition-development)
or choose **Perimeter transitions · unselected hardware** in the Design selector.
The default plywood reference and all earlier candidates remain available.

This is a nominal CAD inspection, **not a selected construction detail or
FEA-qualified design**. It builds on the [mid-batten clip variation](mid-batten-clip-study.md)
without changing its climbing grid, front-panel screw axes or leg geometry.

## What changes

- Twelve perimeter/kicker end screws are removed and their old bores refilled
  in the new-stock model. Existing physical stock would require separate review.
- Ten custom 6 mm steel angle envelopes span the two lower panel transitions,
  two upper kicker transitions, two horizontal seam ends, two panel-top ends
  and two lower kicker ends.
- Forty replacement fasteners comprise twenty through-bolts and twenty
  side-grain rail screws. They are generic, unselected envelopes, not an
  approved A21 installation or a transfer of thin-connector screw ratings.
- Two existing splice profiles gain material and become four separately
  selectable 19.05 mm plywood plies. No glue, friction or composite-action
  credit is assumed; original splice screw paths remain accessible.

The resulting viewer has **365 selectable entries: 87 bodies and 278 frame
connections** (164 screws and 114 bolt assemblies). Bolts are red, screws blue
and custom angles grey. Click an entry for dimensions and qualification limits.

## Inspection artifacts

- [STEP assembly](../exports/lower-transition-development/lower-transition-development.step)
- [Front view](../exports/lower-transition-development/lower-transition-development_front.png)
- [Rear view](../exports/lower-transition-development/lower-transition-development_rear.png)
- [Metric/imperial stock schedule](../exports/lower-transition-development/lower-transition-development_parts.csv)
- [Connection schedule](../exports/lower-transition-development/lower-transition-development_connections.csv)
- [Source/artifact hash manifest](../exports/lower-transition-development/manifest.json)

The STEP profiles govern shaped plies and angles; bounding dimensions are not
flat-pattern fabrication drawings. The model preserves old splice bores and
adds supplemental through-bores. The steel bends, holes, actual fastener heads,
thread engagement, installation sequence and material resistance remain unresolved.

## Checked geometry and remaining limits

The candidate tests check complete solid/head/hardware intersections, nominal
receiving members and pilot paths, LED/tool envelopes, original splice-screw
access, new side-grain screw penetration, nominal washer bearing rings and the
connection graph. Existing floor positions and independent ply thicknesses
are retained. These checks do not model joint slip or prove load sharing.

Top packaging leaves only **0.5 mm beyond the nominal washer edge and 0.9 mm
between the nominal socket and angle return**. These are measured CAD gaps,
not approved manufacturing tolerances, product edge distances or demonstrated
installation access. Resolve the actual product geometry before adopting them.

The eight earlier mid-batten clips and their 32 unselected screw envelopes
remain provisional too. No FEA has been run on this transition variation.
Next resolve connector/fastener products and tolerances, then evaluate joint
demands with qualified extraction and independent-ply behavior.
