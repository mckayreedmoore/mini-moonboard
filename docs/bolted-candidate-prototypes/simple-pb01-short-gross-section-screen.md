# PB-01 six-inch corner block: gross section actions in two retained cases

Status: **source-bound diagnostic components, not net-section resistance,
joint utilization or drilling release.** The rectangular part is a bolted
solid-wood corner block; `cleat` remains the historical machine name. This
screen uses the same 152.4-mm `quarter_short` block and the separately
archived, tension-only A12-left and K12-right hybrid runs. Each still has
23 old ML24Z/SDS proxy stations and is not a full V4 configuration.

The [reproduction script](../../scripts/simple_pb01_short_gross_section_screen.py)
calls the retained-archive verifier and reads all 20 reported section cut
sides in each case. It confirms the modeled 139.7 × 57.15 mm **gross unbored**
rectangle and 152.4-mm grain length. It reuses the existing elastic
component arithmetic: signed `N/A`, `M_u/S_u`, `M_v/S_v`, rectangular
`3V/(2A)` peaks, same-cut corner axial-plus-biaxial-bending magnitude,
and same-cut orthogonal transverse-shear magnitude. Values are N/mm² = MPa.
The native report also gives torsional moment, but the script does **not**
convert it to torsional stress. Each maximum below is taken over cut sides;
maxima from different cuts or cases must not be added together.

| Maximum isolated component | A12-left | K12-right |
| --- | ---: | ---: |
| Same-cut corner normal tension, MPa | 0.008700 | 0.014946 |
| Same-cut corner normal compression, MPa | 0.007885 | 0.013469 |
| Same-cut center transverse shear, MPa | 0.004318 | 0.008152 |
| Absolute torsional **moment**, N·mm | 1,231.950 | 1,967.171 |

The right-side case is higher for each listed component, so the old left
case alone was not a useful envelope for this block. These small gross
elastic stresses are **not** evidence of a safe bored block. At bolt cuts,
the effective area and second moments differ from this rectangle; local
wood embedment, splitting, tear-out, washer bearing, torsion, combined
stress, group action and all-six full-V4 demands remain open. Actual wood
grade and adjustment factors are also unverified. The separate
[bored-section geometry screen](simple-pb01-short-bored-section-probe.md)
quantifies removed area, but it cannot by itself supply local fracture
resistance or final demand.

Reproduce with `.venv/bin/python -m
scripts.simple_pb01_short_gross_section_screen` and
`.venv/bin/python -m pytest -q
tests/test_simple_pb01_short_gross_section_screen.py`.
