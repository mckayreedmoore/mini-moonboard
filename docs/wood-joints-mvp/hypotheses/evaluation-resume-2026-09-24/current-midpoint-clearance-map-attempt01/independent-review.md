# Independent review

The map is a faithful visualization of the frozen attempt03 midpoint report.
I inspected the PNG and reviewed the producer, README, and source-hash manifest
read-only. I did not load CAD or run native mechanics.

The input report hash matches
`a7f7b15200421ad2f6527cf2248f70e7f424164a357a2e69afdf48ad538582e4`, with the
expected revision ID and 904-obstacle count. `source-hashes.json` matches the
report, producer, README, PNG, and SVG bytes; its geometry-snapshot canonical
digest and current-revision report digest agree with the input report. The
producer rejects a changed report hash, checks the revision, 491 unique rows,
904 obstacle shapes, allowed family/direction/surface mapping, and status
category totals before plotting.

I independently recomputed the 491 rows and their color/status categories:

| Site group | Sites |
| --- | ---: |
| LED / horizontal | 120 |
| LED / vertical | 121 |
| T-nut / horizontal | 120 |
| T-nut / vertical | 121 |
| Kicker T-nut / horizontal | 9 |

| Primary plotted category | Sites |
| --- | ---: |
| Timber flange hit | 44 |
| Timber rear-projection-only hit | 7 |
| Existing T-nut/LED only | 220 |
| No screened hit | 220 |

The categories are mutually exclusive by the producer's precedence rule:
flange hit, then rear-projection hit, then existing T-nut/LED hit, then no
screened hit. I confirmed 22 sites have the blue ring for both timber and an
existing T-nut/LED hit, and 266 have multiple BRep hit records, which can
include separate probe-envelope intersections at one site. Every source row
has an empty structural-hardware hit list. All 482 main sites and 9 kicker
sites are within the plotted axes; kicker sites are separately labeled and
share local `S = -75 mm`. The map draws site centers without inventing a panel
boundary.

The PNG is legible at 3300 × 2200 pixels: marker shapes distinguish the five
site groups, colors and outlines have matching legend entries, and the footer
states “Provisional probes; wires, panels and service access excluded. No
future-layout approval.” The README explains that the colors represent only
provisional hypothetical probes against the source report's obstacle set.
Neither a colored overlap nor a no-hit site is presented as actual blockage,
future product compatibility, or layout approval. The panel/wire/access limits
remain visible in both the text and image. No correction is needed.
