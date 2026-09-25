# Current hypothetical midpoint clearance map — attempt 01

This static map visualizes only the frozen site rows in
[`current-midpoint-clearance-attempt03/report.json`](../current-midpoint-clearance-attempt03/report.json).
It does not load or build CAD. The source report SHA-256 is
`a7f7b15200421ad2f6527cf2248f70e7f424164a357a2e69afdf48ad538582e4`; its 491
site centers and 904-obstacle scope match the attempt03 report. The plotted
artifacts are [`current-midpoint-clearance-map.png`](current-midpoint-clearance-map.png)
and [`current-midpoint-clearance-map.svg`](current-midpoint-clearance-map.svg).

Marker shape identifies the five site groups: LED horizontal (120), LED
vertical (121), T-nut horizontal (120), T-nut vertical (121), and kicker
T-nut horizontal (9). Main-panel and kicker-local coordinates are plotted in
separate axes; all nine kicker sites share `s = -75 mm` in the reported local
coordinate. The map draws site centers only and infers no panel boundary.

Color gives the primary result class: 44 timber-flange-hit sites, 7 timber
rear-projection-only sites, 220 sites with only an existing T-nut/LED overlap,
and 220 sites with no screened hit. A blue ring marks a site with both timber
and existing T-nut/LED hits (22 sites). A black marker edge marks more than one
reported BRep hit record at that site (266 sites); records may be separate
probe-envelope intersections at one site. The full record remains authoritative
for individual members, envelopes, and first occupied depths.

The plotted colors refer to provisional hypothetical probes: a 25.4 mm full
disk flange, 1.86 mm thick, and an 11.1125 mm diameter, 50.8 mm rear
projection. The screen omits plywood-panel bodies, all 131 modeled wire spans,
and service operations; it excludes the same display and access proxies as
the source report. A colored site does not establish real-tool blockage or
future-product incompatibility, and a no-hit site does not approve a future
layout.

Regenerate with `uv run python
docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-midpoint-clearance-map-attempt01/plot_current_midpoint_clearance.py`.
[`source-hashes.json`](source-hashes.json) records the frozen report,
producer, and output hashes. Both exports include the scope footer: “Provisional
probes; wires, panels and service access excluded. No future-layout approval.”
