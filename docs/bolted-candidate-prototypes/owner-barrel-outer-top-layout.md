# Eight outer/top barrel-nut viewer duties (kerf-right trial)

`scripts/owner_barrel_outer_top_layout.py` is a detached, provisional geometry
screen of the selected kerf-right wood. It does not alter the 66 panel/kicker
screw axes, 12 retained frame bolt axes, or any original timber. It maps exactly
eight legacy clip duties but places no legacy angle placeholder in its proposed
hardware. The original clips/SDS remain in the selected baseline history until
an integrated candidate actually replaces them.

`build_layout(wood)` supplies Leibniz's assembly contract: eight `direct` rows
with two actual bolt axes, barrel solids, shaft stacks, full nominal drilling
paths and provisional access volumes each. Every row is `REVISE`; the direct
mode describes only topology, not fit. The outer-base pair is still a held
exception in the diagnostic screen because its neighboring tools have not been
cleared. No fictitious compact block is supplied.

| Duties | Trial contact and grain | Disposition |
| --- | --- | --- |
| Top outer left/right (2) | 88.9 mm inclined side rim (N grain) to X-grain top rail; bolt along X, barrel across 38.1 mm rail T thickness; barrel 30 mm from rail end | Direct nominal bore path |
| Top center left/right (2) | X-grain top rail to N-grain center principal; bolt along T, barrel across principal X thickness; barrel 70 mm below rail | Direct nominal bore path |
| Outer header/post left/right (2) | X-grain header atop Z-grain outer post; bolt down Z, barrel across 38.1 mm post X thickness | Direct nominal bore path |
| Outer base/side left/right (2) | X-grain header beneath N-grain side rim; bolt up Z, barrel across 88.9 mm rim X thickness | **Exception, not integrated:** conflicts with the PB09 bottom-outer tool and outer-header family remain unscreened |

Each duty has two actual nominal intersecting 7.5 mm machine bores and 10.0076 mm
cross-bores, with full nominal 5 in bolt-tip reach rather than a shaft ending at
the thread axis. The focused geometry screen finds both bores wholly within the
listed source timber at these centerlines. That is **not** a clearance or fit
verdict. In particular, the lower outer pair remains two explicit exceptions,
even though its isolated timber bores are continuous. This is a compact direct
same-member exception lead, with no added block or specialty cut assumed.

Provisional part identity is [Hillman 880543 at Lowe's](https://www.lowes.com/pd/Hillman-20-x-5-8-in-Slotted-Drive-Zinc-plated-Barrel-Nut/3012559)
and [Home Depot](https://www.homedepot.com/p/202242356), plus the ordinary
[Everbilt 800676 1/4-20 × 5 in bolt](https://www.homedepot.com/p/204633308).
The nominal 16.002 mm length, 10.0076 mm OD, 6.35 mm major thread, 127 mm bolt,
and 1.651 mm washer sensitivity are imported from
`scripts/simple_cross_dowel_continuation.py`. The barrel thread axis is posed
at 8.001 mm solely for the viewer. Its 6–10 mm sensitivity is open: no SKU
drawing controls it. Nominal rail-end/row margins and physical barrel entries
have not been strength-qualified.

Open before a complete viewer assembly: finite T-nut/hold-hole/hold-bolt, LED
and wire, 66 panel screw, 12 frame bolt, neighboring candidate hardware and
tool clearance; real washer/head/tool volumes; 6–10 mm axis-offset sweep;
complete bolt/barrel thread engagement and tip clearance; accessible assembly;
and actual purchased-part measurements. The outer-base pair also needs PB09
bottom-outer access and header/post interaction resolved. No load capacity,
structural approval, purchase fit, fabrication or drilling release is claimed.
