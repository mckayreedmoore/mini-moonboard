# Mini MoonBoard LED routing reference

The selected routing hypothesis uses three 50-LED strings. The manufacturer’s
[current V5 guide](https://moonclimbing.com/media/moonboard-pdf/MB_LED_Installation_V5%2050%20LED%20Nov%202025.pdf)
shows a rear-view Mini diagram on printed page 4. Both that diagram and the
[requested older guide](https://moonclimbing.com/media/moonboard-pdf/MB_LED_Installation.pdf)
were visually inspected. A1 is at the lower right from behind; routing climbs
column A, descends B, and alternates through K12 at the upper left.

The resulting 132-position index gives these derived string boundaries:

| String | Installed indices | First–last position |
| --- | --- | --- |
| 1 | 1–50 | A1–E2 |
| 2 | 51–100 | E3–I4 |
| 3 | 101–132 | I5–K12 |

The V5 guide lists 150 bulbs and 16 spares. The diagram’s 132 installed positions
instead leave 18 unused bulbs arithmetically. This discrepancy remains unresolved;
18 is a model inference, not a corrected manufacturer specification.

For the 50-LED kit, LED1 feeds the first string. PWR1 connects to the supplementary
feed at the end of the second string, using the supplied two-wire extension.
Keep the rear controller’s controls and connectors accessible; use the supplied
5 V power supply. These instructions also appear in the
[online build guide](https://moonclimbing.com/build-your-moonboard).
The older two-string Mini kit contains 134 LEDs and has different boost guidance;
do not mix the two kit instructions.

The guides specify nominal 13 mm / half-inch panel holes and flush LED faces.
They do not establish cable diameter, inter-LED cable length, usable slack,
minimum bend radius, connector size, rear LED projection, controller dimensions,
or extension lengths. Hole spacing does not establish cable length. Measure the
purchased kit before approving routing or timber cutouts.

On September 11, 2026, the owner reported approximately **12 inches (304.8 mm)
from bulb base to bulb base** on the purchased kit. Use that as the provisional
available path length between adjacent bulbs, including bends, rather than as
straight-line spacing. The shortest segment, measurement tolerance and remaining
installation slack still need checking. This measurement does not establish the
cable diameter, connector size or minimum bend radius.

Any CAD wire envelope
and green display color are project visualization choices. Timber removal needs
separate structural checks.

[Machine-readable reference](led-wiring-reference.json) records the full derived
order, kit distinction, source hashes and unresolved dimensions. This reference
does not qualify wiring fit, electrical modifications or the frame for construction.
