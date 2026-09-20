# HL/B66 load-axis mapping for the current center trial

**Status: source-backed direction screen, not a joint resistance verdict.**
The [Simpson C-C-2026 HL drawing, p. 315][hl-source]
shows F1 along the supported beam and uplift vertically for its typical
beam-over-post installation. Its table lists those two directions only.
The [MiTek ESR-3455 B66 Figure 3 and Table 3, p. 9][b66-source]
show F1 along the beam and F2 transverse to it for a comparable corner
brace, but its B66 values are limited to the stated `C_D = 1.6` duration.

The current CAD uses global X across the board/header, Y front-to-back,
and Z vertical. The following is a **coordinate inference from the typical
installation drawings**, to be checked against each actual installed
member and joint wrench before using any catalog value:

| Pose | Leg bolt axis | Bend line | F1 axis | Transverse action |
| --- | --- | --- | --- | --- |
| Typical beam/post drawing, beam along X | Y | X | X | Y |
| Current outward-X center HL33, leg on principal/post X face | X | Y | Y | X |

Rotating the angle 90 degrees about Z rotates F1 with its bend line; it
does **not** make the tabulated HL33 F1 cover the global X action in the
current outward-X pose. The HL page has no F2 cell to map to that X action.
For MiTek B66, an X-facing pose would map its F2 to an X-direction action,
subject to the direction and installation shown in Figure 3; its published
F1/F2 numbers cannot be used at the board's ordinary load duration.

Simpson says connectors are required on both sides to obtain F1 lateral
resistance in both directions, and lateral loads may not be doubled for a
pair. MiTek requires B66 braces on both sides for F1 in both directions.
Those pairing rules refer to the *local rated direction* in each typical
installation; they do not provide the HL's unlisted transverse resistance.
Therefore the same-Y and rear-shifted inner HL33 CAD rejections address
only one possible attempt to cover reversible local F1. Even a
collision-free upper pair would still need a separate route for any
global-X transverse demand, moments, separation, contact and interaction.

The existing old-connector and partial-topology reactions are diagnostic
only. A current-geometry simultaneous local wrench, contact state and load
direction classification are still needed. No load is transferred between
catalog axes, no B66 duration conversion is made, and no member or bracket
is accepted for cutting or drilling here.

[hl-source]: https://dhcsupplies.s3.us-east-2.amazonaws.com/Documents/simpson-strong-tie/hl-angles.pdf
[b66-source]: https://www.mitek-us.com/wp-content/uploads/files/pdf/Code%20Evaluation%20Reports/esrESR-3455.pdf
