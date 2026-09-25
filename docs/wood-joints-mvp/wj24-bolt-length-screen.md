# WJ24 center-axis bolt-length screen

**Status: conditional dimensional screen.** For the sixteen WJ24 center axes
whose catalog lengths were unassigned, this screen carries forward explicit
nominal length classes of 4 × 4.75 in, 8 × 5.75 in, and 4 × 7.5 in. These
values are dimensional candidates for further review. They do not identify a
supplier or SKU and are not an approved hardware schedule, purchase list,
capacity result, or release for drilling, fabrication, or assembly.

The source [WJ24 hardware inventory](hypotheses/wj24-hardware-inventory/README.md)
records 16 `wj05_center_x190` bolt axes with modeled wood grips of 100.915644,
127, and 167 mm. It also records the same historical under-head stack screens
as the WJ05 center-node model. This report leaves that producer and inventory
unchanged; it adds a separate length screen against those axes.

| Axes | Count | Modeled wood grip | Historical WJ05 under-head screen | Screened nominal length | Minimum delivered length under standard tolerance | Far nut face max + 3.175 mm thread projection | Remaining length margin | Conditional receiving window for measured body end / first full-form thread |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `center_principal_header_{left,right}_{1,2}` | 4 | 100.915644 mm | 113.133044 mm | 4.75 in (120.65 mm) | 118.11 mm | 114.895044 mm | 3.214956 mm | 95.25–101.6 mm |
| `center_post_{left,right}_{1,2}` and `center_principal_{left,right}_{1,2}` | 8 | 127 mm | 139.2174 mm | 5.75 in (146.05 mm) | 143.51 mm | 140.9794 mm | 2.5306 mm | 120.65–127 mm |
| `center_post_header_{left,right}_{1,2}` | 4 | 167 mm | 179.2174 mm | 7.5 in (190.5 mm) | 185.928 mm | 180.9794 mm | 4.9486 mm | 160.382–165.1 mm |

The “historical WJ05 under-head screen” uses the center-node model's nominal
1.651 mm washer thickness, the 5.7404 mm maximum finished-nut thickness, and
3.175 mm past the nut. The new candidate lengths use a wider stack screen:
two Type A narrow washers at their 2.032 mm maximum thickness, the nut at its
5.7404 mm maximum thickness, plus 0.5 mm allowance on each of the two modeled
wood members and the same 3.175 mm full-form thread projection. That wood
allowance is only a screen input. It is not a stock tolerance or a receiving
acceptance rule.

The modeled stack order is bolt head, one 1/4-in washer, the ordered pair of
wood receivers, one 1/4-in washer, and one 1/4-20 finished hex nut. No
counterbore is included on these sixteen center axes. The modeled washer
thickness is 1.651 mm nominal, with a 1.2954–2.032 mm dimensional range; the
nut maximum thickness is 5.7404 mm. The 3.175 mm thread projection preserves
the WJ05 center-node model input. It is not a published minimum engagement
rule and does not establish connection strength. The dimensional inputs and
their limits are recorded in the [WJ05 center-node source](../../scripts/wood_joint_wj05_center_node_probe.py),
[preserved WJ05 center-node report](hypotheses/wj05-center-node-relieved.md),
[WJ05 backer hardware basis](wj05-center-backer-transfer.json), and
[ordinary hardware basis](ordinary-hardware-basis.md).

The length arithmetic follows the 1/4-in partially threaded hex-screw
envelope in ASME B18.2.1-2012, Tables 12 and 13. Nominal length is measured
from the under-head bearing surface to the extreme end of the point, including
the point; it is not the length of delivered smooth shank. For the relevant
size and length ranges, this screen uses a −0.10 in lower tolerance through
6 in and −0.18 in above 6 in. Its table-based `Lg,max` / `Lb,min` pairs are
101.6/95.25 mm at 4.75 in, 127/120.65 mm at 5.75 in, and 165.1/158.75 mm at
7.5 in. `Lb` is a minimum body length to the last thread scratch; `Lg` is a
maximum grip-gaging length. Neither value gives the actual first full-form
thread on a delivered bolt. See the [ASME B18.2.1 standard record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws),
K.L. Jack's [fastener technical catalog](https://www.kljack.com/docs/default-source/technical-information/kl_jack_fasteners-technical_data_and_charts.pdf),
and the repository's [source correction for the six-inch dimensions](bolt-dimension-source-correction.md).

At each proposed nominal length, the minimum delivered length still exceeds
the largest assumed far-nut face plus 3.175 mm. A positive stack margin only
shows there is room for the assumed nut and projection. Receiving must measure
each actual bolt and washer stack together and confirm a functional,
full-height nut engagement. Measure the last thread scratch, first full-form
thread, full-form thread end, and delivered under-head length. The measured
body end must meet the table `Lb,min` and, if a later lateral method uses
nominal bolt diameter, leave no more than one-quarter of the nut-side wood
member carrying thread. The first full-form thread must begin no later than
the earliest nut bearing face; full-form thread must pass the complete nut
and continue at least 3.175 mm beyond its far face, while ending no farther
than the measured bolt tip. If a later method's threaded-bearing condition is
not met, use the measured root diameter in that method. These are receiving
conditions for a dimensional candidate, not strength acceptance.

For the 167 mm group, an 8 in nominal bolt has ample overall length but fails
the standard-envelope transition screen: its `Lb,min` is 171.45 mm, while the
earliest nut bearing face is 168.5908 mm. It therefore cannot provide the
assumed full-height nut engagement within this partial-thread envelope. The
7.5 in option is the shortest candidate in the quarter-inch increment screen
that has enough total length and a positive measured transition interval. The
shorter 7.25 in option misses the total-length requirement by 1.4014 mm and
has a −1.632 mm transition interval. For the other groups, the next shorter
4.5 in and 5.5 in options miss the worst-case total-length stack by 3.135044
and 3.8194 mm, respectively.

All sixteen proposed nominal assignments and the source inventory hash are
reproduced by [`wood_joint_wj24_bolt_length_screen.py`](../../scripts/wood_joint_wj24_bolt_length_screen.py).
At report generation, the inventory SHA-256 is
`cb11b4f14d9c6cb02bb1ecb5789579d096b6ae436171f91eabea9891f1927624`; the
sorted axis identity SHA-256 is
`08b356ce03fc524627ee864feb053e1e99c2a923207a6ce3b1898ed8830f02c7`.

No supplier availability or SKU has been verified for the 4.75, 5.75, or
7.5 in candidate lengths. Any catalog substitute, full-thread bolt, or part
with a different transition requires its own complete stack and receiving
screen. Nominal clearance, installation access, actual timber, delivered
hardware, structural behavior, cost, and complete joint acceptance remain
outside this length-only report. No candidate pass, historic center-node
diagnostic, or unrelated WJ24 group transfers acceptance here.
