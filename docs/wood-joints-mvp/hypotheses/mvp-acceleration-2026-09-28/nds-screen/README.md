# Preliminary individual-bolt reference scenarios

These calculations establish a reusable numerical route, not the resistance
of a current joint. They reuse `fea/dowel_yield.py`, which implements the TR12
single-shear equations with explicit bearing intensities, bolt yield moments
and reduction terms. No native solve or candidate geometry change is involved.

## Explicit assumptions and results

The scenario uses a 1/4-inch full-body bolt, 3.5-inch and 1.5-inch effective
wood bearing lengths, zero interface gap, wood specific gravity 0.50, and
bolt bending yield strength 45,000 psi. The assumed bolt axis is perpendicular
to both members' grain. The 0/90-degree angles below concern the **lateral
load direction relative to grain**, not the bolt axis. Bearing strengths are
the explicit rounded values 5,600 psi parallel and 4,450 psi perpendicular.
All six yield modes are evaluated for each scenario.

| Main load/grain angle | Side load/grain angle | Reference Z, lbf | Reference Z, N | Governing mode |
|---|---|---:|---:|---|
| 0 degrees | 0 degrees | 179.007 | 796.262 | IV |
| 0 degrees | 90 degrees | 134.763 | 599.457 | IV |
| 90 degrees | 0 degrees | 134.763 | 599.457 | IV |
| 90 degrees | 90 degrees | 127.657 | 567.848 | IV |

These are unadjusted **individual-fastener reference values**. They cannot
be multiplied by the number of bolts to produce a corner-block capacity.
The calculation omits group action, geometry and service adjustments, threads
in bearing, axial/combined loading, splitting, tear-out, washer behavior and
all current structural demands. Actual receiver lengths and conformity to the
specified bolt basis remain to be checked. No candidate criterion passes here.

## Source and end-grain finding

The official [NDS-2024 Chapter 12](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
was downloaded and its text inspected. Its PDF SHA-256 is
`5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`.
Table 12A uses the full-body 45,000 psi bending-yield basis. That supports an
explicit design scenario; it does not establish the properties or shank
occupancy of a particular purchased quarter-inch bolt from a grade label.
The custom member lengths here are calculated with the equations, not taken
as a direct lookup from that table.

Sections 12.3.3.4 and 12.5.2.2 provide an important separate route: for the
covered main-member end-grain lateral connection, use perpendicular-grain
bearing strength for the main member and apply the 0.67 end-grain factor to
the reference lateral value. The former provision covers dowels at least
1/4 inch in diameter. Member roles and applicability must be established for
each actual stack. This is distinct from the adjacent lag-screw withdrawal
rule. The four numerical scenarios above do **not** cover these end-grain-axis
cases or apply that factor. An existing helper's exclusion of end-grain axes
does not mean the standard forbids all such lateral connections.

## Verification and reproduction

The producer checks all six rounded reference values from the existing
TR12 Example 3.1 benchmark (900, 900, 414, 550, 550 and 663 lbf, within
0.6 lbf) and the governing mode. It separately evaluates the NDS closed-form
mode IV expression for all four scenarios, without using the TR12 quadratic
helper for that check. Outputs include the helper's SHA-256, assumptions and
explicit exclusions. Reproduction needs only Python's standard library:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/nds-screen/produce.py --verify
```

Use `--write` to regenerate the JSON after reviewing any changed input or helper.

An independent Luna/max source reviewer checked the producer's equations,
reduction terms, bearing inputs and scope and found no material error.
