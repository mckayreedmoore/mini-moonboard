# PB-02 alternate: recessed rectangular header and rear-cleat through-bolt

Status: **rejected**. This is one nominal alternate to the blocked front nut
in the [rear-cleat Y-bolt trial](simple-center-header-post-probe.md). It
addresses only the displaced `clip_split_header_center_right` duty; no
header-to-shifted-post connection is selected. The separate
`clip_split_base_center_right` duty remains open.

## One bounded pose

Keep the right-only shifted solid post at X=88.75…177.65,
Y=−175.7…−86.8, Z=0…238.9 mm, its two rear-cleat bolts at X=140,
Z=110/190 mm, the continuous solid rear cleat at X=89.05…177.95,
Y=−213.8…−175.7, Z=0…460 mm, and the link/upright details of the
preceding pose. Change **only** the hidden header's full rectangular
section: rip its front Y face back from −36 to −61.4 mm for its entire
2438.4 mm length. Its new section is 114.3 mm Y × 38.1 mm Z, at
Z=238.9…277 mm. The 25.4 mm removed strip is solid timber, not a pocket
or half-lap. The kicker, panel, backer, post, cleats, and all 66 screw axes
stay fixed.

Try one nominal 1/4-in (6.35 mm) ordinary through-bolt along Y at X=140,
Z=251.6 mm, from rear face Y=−213.8 to new header front face Y=−61.4.
The illustrative 7.30 mm bore is 0.95 mm larger than the nominal bolt,
within the 2024 NDS §12.1.3.2 interval of 0.79375…1.5875 mm oversize.
The intended load route is header → metal-nut bolt → continuous rear cleat
→ two existing through-bolts → shifted post. Face contact is not counted as
a connection. The bolt, nut, washer, shank/thread split, and shop drill are
not selected.

## Measured nominal screen

The 152.4 mm bore is wholly in the intended timber: 38.1 mm cleat (0.25)
and 114.3 mm header (0.75). It has no positive-volume hit on other modeled
wood, the 66 fixed panel/kicker screw axes, or the prior post, link, and
upright bores. Both modeled 20 mm washer disks are fully borne. At both ends,
20 mm radius × 20 mm straight tool cylinders and 10 mm radius × 5 mm
external hardware cylinders clear modeled wood. The front tool stops at
Y=−41.4 mm, 5.4 mm behind the installed kicker's rear plane at Y=−36;
the hardware stops at Y=−56.4 mm. Thus this pose removes the prior
front-nut **nominal cylinder collision**. It does not prove real wrench
swing, nut installation/removal, bolt length, or clearance with tolerances.

The decisive failure is support: for the entire header-height strip
Z=238.9…277 mm, the new header front is 25.4 mm behind the fixed kicker
back. Both inner kicker edges lose their direct header support there. All
ten fixed `kicker_header_*` screws still cross the kicker and reach the
recessed header, but only 19.84375 mm of each modeled 63.5 mm shaft is in
the header (receiver fraction 0.3125), versus 45.24375 mm in the original
header. This is a separate loss of the original kicker-header screw
receiver depth; neither the unchanged screw axes nor the remaining short
penetration qualify those screws as supported. Screw reach also cannot
restore the missing edge bearing. The other 56 fixed axes were checked for
collision with the trial bore, not requalified for receiver or load capacity.

For the nominal D=6.35 mm bolt, [2024 NDS Tables 12.5.1A–C][nds]
remain conditional on actual load direction, member grain, and joint
design. In the header, the bolt center is 12.7 mm from its bottom Z edge
and 25.4 mm from its top edge. If Z-positive is the only loaded edge under
perpendicular-to-grain action, the top reaches 4D=25.4 mm and the bottom
exceeds unloaded 1.5D=9.525 mm. If the action reverses, the bottom is
12.7 mm short of 4D. The 38.1 mm header cannot give both edges 4D:
50.8 mm would be needed. No signed demand is established here.

The rear cleat's X edge distances are 50.95/37.95 mm, both above the
conditional 4D marker; its grain-Z end distances are 251.6/208.4 mm.
The header's grain-X ends are 1359.2/1079.2 mm from the trial center.
The new bolt is 61.6 mm above the nearest old post-bolt Z level; this is
a bore-clearance observation, not a complete NDS group or spacing
qualification. Actual load-to-grain angles, loaded-end classification,
row spacing, cross-grain tension, net sections, bearing lengths, and
member/joint capacities remain unproved.

**Reject the pose for three independent reasons:** both inner kicker edges
lose direct support; all ten kicker-header screws lose most of their
existing header receiver depth; and the 38.1 mm Z section fails the
conditional reversible 4D edge screen. Front occupation clears only in the
illustrative cylinder model; real nut/tool access is not qualified.
No fastening change, cut, drilling coordinate, rating, or
fabrication release follows. The source geometry is the existing PB-02
link-edge pose and fixed kerf-right axes; the prior clips at both displaced
center-right stations remain removed only in this candidate lane.

Reproduce with `.venv/bin/python scripts/simple_center_header_post_alternate_probe.py`,
`.venv/bin/python -m pytest -q tests/test_simple_center_header_post_alternate_probe.py`,
and `.venv/bin/ruff check scripts/simple_center_header_post_alternate_probe.py
tests/test_simple_center_header_post_alternate_probe.py`.

[nds]: https://awc.org/resources/2024-nds/
