# Retained-wire obstacle lower bound, attempt01

Status: completed analytic subset derived from the frozen current retained
access report. The [source report](../retained-access-attempt03/access.json)
SHA-256 is
`fffa0027926a57583cc13ffbcef552fc8e5f8da96964d50c64ef63ffd4ce4c97`; the
derived [report](report.json) SHA-256 is
`5f59dcd1400cdf00f2b5ff0f1960b8598706707572766bf1d50c148b85380620`. Producer
and source-script pins are recorded in the report.

The producer selects the four lumber-leg bolts from attempt03 and removes only
the obstacle IDs `protected/wires/wire_010_A10_A11` and
`protected/wires/wire_130_K10_K11` from the completed collision maps. This
reduces the obstacle count from 1,041 to 1,039; no other obstacle ID is
excluded. It makes no new shape, route, or geometry.

The source `_collision_report` loop visits every non-excluded obstacle for
each candidate envelope, with no early exit or hit truncation. The derived
rows preserve the source hit threshold, zero terminal allowance, target-role
exclusions, and original hit volumes. All 24 component-direction checks—four
axes × three moving components × withdrawal/reverse insertion—have no
remaining hit; reverse insertion reuses the identical swept occupancy. The
subset result therefore says only that the two named wire
solids account for all intersections recorded on those paths in the original
attempt03 maps.

No live CAD or native run occurred; approved geometry is unchanged. The
report sets `harness_removability_established`,
`complete_assembly_or_transport_established`, and
`physical_service_path_established` to false. Connector separation, PWR1,
actual strand staging, cable anchors/slack/bend limits, panel handling,
support, tools, capture, and physical fit remain open. See the parent
[retained-wire sequence note](../../../current-retained-wire-sequence.md) for
the proposed topology-realistic next screen.
