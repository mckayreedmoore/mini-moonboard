# Physical orientation convention

Use these physical directions everywhere a view, drawing, or build discussion
needs words rather than raw CAD coordinates:

| Term | Meaning |
| --- | --- |
| **Front** | The hold-bearing climbing face: the underside of the sloped main panel and the face of the kicker. A climber stands here. |
| **Back** | The opposite board-normal support side. Rails, bearing blocks, LED wiring, and the leg/frame bracing belong here. |
| **Left** | Climber-left while facing the holds: the A-column side, where the scale figure stands in the viewer. |
| **Right** | Climber-right while facing the holds: the K-column side. |

The board slopes 40 degrees from vertical. Consequently, world `+Y`/`-Y`
coordinates alone do **not** define front/back: the meaningful normal is local
to the panel. CAD schedules retain their numeric global datum for fabrication;
this convention controls plain-language labels and the interactive view.

The initial viewer camera is a front/hold-facing view. McKay is positioned at
the front-left floor location. The viewer mirrors the raw CAD X coordinate so
the A column remains visible at climber-left; this display transformation does
not change any drill or fabrication datum.
