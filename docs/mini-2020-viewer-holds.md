# Mini MoonBoard 2020 viewer holds

The viewer includes 130 generic visual placeholders for the Mini MoonBoard
2020 setup: 120 on the main face and ten on the kicker. Select **2020** in the
hold setup control to preview them. The 2020 and 2025 layouts share the viewer's
visibility, front-view, and hold-selection controls.

Use [Problem highlights](viewer-problem-highlights.md) to mark start, hand,
foot, and finish holds and share the selection through a link.

## Sources and observed layout

The [official 2020 bundle page](https://us.moonclimbing.com/products/mini-moonboard-2020-hold-set)
lists 130 holds from Original School Holds and Wood Sets A, B, and C. Its public
[front-view setup image](https://us.moonclimbing.com/cdn/shop/files/mbsetup-mini.jpg?v=1770821237&width=665)
provides the positions, visible color families, and broad visual directions
transcribed in [`site/mini-2020-holds.json`](../site/mini-2020-holds.json).
Rows 3–12 are full. Row 2 is occupied except G2. Every position in row 1 is empty.
The face contains 40 yellow Original holds and 80 wooden holds.

The [Original School inventory](https://eu.moonclimbing.com/original-school-holds.html)
contains 40 hand holds and ten footholds. The wood inventory comprises
[32 Set A holds](https://us.moonclimbing.com/products/moonboard-wood-holds-set-a),
[24 Set B holds](https://moonclimbing.com/wood-holds-set-b.html), and
[24 Set C holds](https://us.moonclimbing.com/products/moonboard-wood-holds-set-c).
References were checked on September 11, 2026. No source photographs or artwork
are included in the repository or downloaded by the viewer.

## Approximation and orientation

The holds reuse the viewer's original generic edge, pinch, sloper, jug, wedge,
triangle, and crescent profiles. Shape categories, rounded millimeter dimensions, and visual
rotations are estimates from the setup image. No individual silhouette is
traced, and no physical dimensions or grip details have been measured.

A rotation is clockwise as viewed from the front of the board. The generic
mesh has local +X right and +Y up before that rotation. A wide edge starts with
its long axis horizontal; a tall pinch starts with its long axis vertical.
The wedge narrows toward local +Y. Rotation values align these generic shapes
with broad visible directions in the source image. They are not Moon's
manufacturer orientation marks, and symmetric envelopes cannot reproduce an
individual hold's gripping direction or distinguish every 180-degree turn.

The directional refinement uses two additional reusable mathematical envelopes:
a rounded triangle whose tip faces local +Y and a crescent whose opening faces
local +Y. These were independently compared with the official image:

| Position | Generic profile | Clockwise rotation | Visible direction |
| --- | --- | ---: | --- |
| C12 | Triangle | 180° | Tip down |
| E11 | Crescent | −10° | Opening up, slightly left |
| K7 | Crescent | 45° | Opening upper-right |

These broad directions replace symmetric placeholders; they do not establish
the actual gripping surface. Other uncertain shapes retain their earlier
envelopes. An independent implementation review confirmed the additional forms
are reusable analytic categories, not individual hold traces or replacements.

Wooden holds share the `wood` family because the reference image does not
establish individual A/B/C membership. Grid labels identify positions, not
manufacturer hold numbers. The ten `KICK` labels identify viewer slots only.
The source setup image does not show the kicker: those ten generic upright
footholds use the viewer's existing kicker positions, and their arrangement
and orientation remain illustrative.

These placeholders support visual preview, not physical installation,
replacement-hold fabrication, or engineering checks. Use Moon's app and actual
hold references to install holds. The preview does not establish grip geometry,
clearance, fastener length, connection resistance, or frame, panel, and floor
adequacy. Holds remain excluded from the structural model and CAD exports.
Faithful scans and reproductions remain governed by the project's
[hold scanning and publication policy](hold-scanning-and-ip.md).
