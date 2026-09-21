# PB-02 combined cleats: one inherited upright-bolt relocation

**Nominal geometry rejected.** This candidate retains both solids and all four
new through-bolts from the committed
[combined-cleat probe](simple-center-combined-cleats-probe.md). It removes the
old inherited upright X bore at Y=−147.3, Z=350 mm from this candidate only,
and rebuilds that bore from X=50.95 to 177.95 mm at **Y=−129, Z=400 mm**.
Both ends, inward washer bearing disks, outward washer face disks, hardware
cylinders, and straight tool cylinders move with it. No panel, panel/kicker
screw, wood solid, or other bolt moves.

The station is near the upright side cleat's forward Y edge. Its Z=400 center
is nominally tangent to the header/principal cleat's Z=380 top for the
20-mm-radius straight left tool. This tests one higher station, not a search
or an accepted drilling coordinate.

| Screen | Nominal result |
| --- | --- |
| Eight complete bore envelopes | Seven fully received by intended wood; relocated upright only 0.70000000 total. Principal contribution **0**; side cleat contribution 0.70000000. |
| Sixteen inward washer bearing disks | Fifteen full; relocated principal-left disk **0.12270522**. |
| Cleat/wood and cleat/cleat overlaps | None. |
| Bore against unintended wood, all other bores, and 66 fixed screws | None. |
| New/inherited hardware and face disks against wood and screws | None. |
| Straight tool against wood | Relocated right end clips `base_rail_bottom_right` by **78.63629 mm³**. Other tool/wood hits: none. |
| Cross-end bore, washer, hardware, and tool occupancy | No additional intersecting envelopes in the modeled screen. |
| Fixed panels and kickers | 48 panel plus 18 kicker axes; all 66 exposed shafts have 1.0 fraction in their named frame receiver, with the shifted right-center kicker screws mapped to the backer. Both inner kicker edges remain supported. |

The full 7.30-mm modeled upright bore at Z400 misses the principal entirely.
Its left washer has only partial bearing, so there is no through-wood joint
at this coordinate even though the left nominal tool clears the new cleat.
The right straight tool also fails access. The prior ten `kicker_header_*`
whole-shaft fractions in the unchanged header remain 0.7125; the table's
1.0 receiver result measures only each shaft's segment exposed after the
first member. The 66 screw axes and their wood are unchanged.

For the relocated bolt, the side cleat has 46.7 / **10.1 mm** to its two Y
transverse edges. The near edge is below the conditional reversible 4D
loaded-edge marker of 25.4 mm for a nominal 6.35-mm bolt. Its Z grain-end
distances are 123 / 60 mm; these are not transverse edges. The principal's
rear Y offset is 53.7 mm, but its inclined top/section has no wood at this
station, so an end-distance pass cannot be claimed. The link bolt and moved
upright differ by 30 mm in Z and 18.3 mm in Y at the side cleat; actual NDS
row classification and required spacing still depend on signed actions.
These numbers are conditional geometry diagnostics, not NDS capacity results.

The nominal envelopes use a 10-mm washer radius, 10-mm hardware radius with
5-mm outward length, and a 20-mm tool radius with 20-mm outward length. They
do not select a purchased bolt, nut, washer, or wrench. The manufacturer
lists [GEARWRENCH 80112](https://www.gearwrench.com/all-tools/ratchets-sockets/chrome-sockets/80112-14-drive-6-point-standard-sae-socket-716)
with 0.618-in A/B dimensions (7.8486-mm nominal radius) and 0.965-in overall
length. That could inform a later smaller-socket occupancy study; this probe
does not substitute it for the 20-mm straight tool, and the socket dimensions
do not establish ratchet, extension, hand, or installation sweep.

Remaining gates include a fully received alternative joint, conditional NDS
edge/end and directional spacing assessment, signed combined load paths and
moment/contact retention, wood bearing and splitting, bolt yield and group
action, washer pressure, delivered bolt length/threads/shank and complete
head/nut/washer stacks, tolerance and real installation access, and all-case
structural response. The earlier header/post 7-in versus 8-in vertical-bolt
stack issue also remains open. No fabrication, drilling, or rating release.

Reproduce with
`.venv/bin/python scripts/simple_center_combined_upright_relocation_probe.py`
and `.venv/bin/python -m pytest -q
tests/test_simple_center_combined_upright_relocation_probe.py`.
