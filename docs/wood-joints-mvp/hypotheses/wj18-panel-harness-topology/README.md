# Panel and harness transport connectivity

Status: bounded topology investigation, 2026-09-24. The retained WJ18 lighting
layout connects all four main panels. Unplugging only the two factory string
connections does not isolate those panels for individual transport.

The [report](topology.json) projects every retained LED solid's centroid into
the canonical main-panel local X/T outlines and requires exactly one owner.
It then follows the exact 132-position order in the
[routing reference](../../../led-wiring-reference.md).

| Panel | Installed LED count |
|---|---:|
| Lower left | 42 |
| Upper left | 30 |
| Lower right | 35 |
| Upper right | 25 |

Twelve modeled wire segments cross panel boundaries: six between the left
lower/upper panels, five between the right lower/upper panels, and F1–G1
between the lower panels. None is a factory string connection. The two
factory boundaries, E2–E3 and I4–I5, each remain within a lower panel.
The five right vertical crossings are exactly the five wires hit by the
[earlier rail-removal samples](../wj12-right-rail-motion/README.md).

The manufacturer [V5 guide](https://moonclimbing.com/media/moonboard-pdf/MB_LED_Installation_V5%2050%20LED%20Nov%202025.pdf)
describes insertion from the rear and connection between supplied strings.
The parent retrieved the same PDF bytes as the routing reference and read
its installation text. Its damaged-LED repair procedure cuts wires; that
procedure is not an individual-panel transport instruction.

The owner-selected [round-passage basis](../../../round-service-wiring-reference.json)
already intends feeding the complete strand through enclosed passages and
installing lights after the panels. A reverse feeding/removal sequence is
therefore a relevant next investigation. It needs explicit bulb handling,
factory connector handling, pass-through envelopes, bend/slack bounds, and
support of panels and loose harness. This report does not prove that sequence
or require electrical modification. Removing one boundary bulb alone also
does not disconnect its continuous wire from the next bulb.

Preserve the fixed lighting and panel geometry while checking that sequence.
Do not substitute the unwired initial-build state for the wired transport
requirement or infer physical impossibility from this connectivity result.
No native solve, physical observation, or release is claimed. The
[execution record](execution.json) and [manifest](sha256.json) bind this probe.
