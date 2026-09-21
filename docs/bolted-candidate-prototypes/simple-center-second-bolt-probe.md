# PB-02: bounded second-bolt spacing screen

This geometry-only screen tests second bolts beside the existing bolts in four
serial joints using bolted solid-wood corner blocks (the older machine term is
`cleat`). It uses the maintained revised small-tool pose, before
the newer tolerance-pose work. It keeps the 66 fixed panel/kicker axes (48 +
18) and tests four named tangential offsets at each of the four new serial
interfaces. It does not search a continuous placement region.

| Interface | Tested second-axis offsets, mm | Collision-only fit | Conditional placement result |
| --- | --- | --- | --- |
| Post–corner block | Y −35/+35; Z −45/+45 | Z +45 only | Block top grain-end distance 33.9 mm, **10.55 mm short** of the 7D trial marker. |
| Corner block–header | X −35/+35; Y −35/+35 | Y −35 only | Block rear Y edge distance 10.7 mm, **14.7 mm short** of the 4D trial marker. |
| Header–principal cleat | X −35/+35; Y −35/+35 | None | Bore reception, washer bearing, or neighboring body clearance blocks each offset. |
| Principal cleat–principal | Y −45/+45; Z −30/+30 | None | Washer bearing, unintended wood, bore, or neighboring body clearance blocks each offset; the principal's oblique grain/end remains unclassified. |

The collision-only test checks complete nominal bore reception in both intended
woods, full illustrative 10-mm-radius washer bearing, unintended wood, the
other seven bolt bores, all 66 fixed screw envelopes, outward 10-mm-radius by
5-mm hardware envelopes, and 7.8486-mm-radius by 24.511-mm socket bodies at
both new ends. It also checks the new bodies against inherited hardware and
socket bodies. These are nominal solid intersections, not tolerance or tool
sweep checks.

For each second axis, the machine output reports centerline distances to
both sides of every relevant rectangular member in the bolt's row plane.
Grain assumptions follow the existing producers: post and post-side block Z,
header X, principal side cleat Y. The principal's inclined grain and oblique
end are deliberately left unclassified. The **4D = 25.4 mm transverse-edge**
and **7D = 44.45 mm grain-end** comparisons for a 6.35-mm nominal bolt are
conditional trial markers only. The output also gives a conditional 4D pitch
comparison and a 7D distance comparator; neither determines an applicable
spacing rule. Loaded edge/end, load direction, end-grain dowel action, and
member roles are not classified here.

Within these 16 named offsets, **none passes both modeled collision fit and
the conservative conditional placement-marker screen**:
the two collision-only fits miss a measured conditional placement marker, and
the remaining offsets have nominal fit blockers. This is a bounded search
result, not a claim that all possible locations are impossible. No strength,
selected hardware, tolerance qualification, ratchet/extension sweep, or
drilling release follows.

Reproduce with `.venv/bin/python scripts/simple_center_second_bolt_probe.py`
and `.venv/bin/python -m pytest -q
tests/test_simple_center_second_bolt_probe.py`.
