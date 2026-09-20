# Corrected HL/B66 load-axis mapping for the center concept

**Status: source-backed direction screen, not a joint resistance verdict.**
The [Simpson C-C-2026 HL drawing, p. 315][hl-source] shows F1 along the
supported beam **and horizontal-flange reach**, perpendicular to the angle's
bend line; uplift is vertical. In the figure's right-hand bracket, the upright
flange is on the post's right X-normal face, the horizontal flange reaches
toward +X, and its bend runs front-to-back along Y. The table lists F1 and
uplift only. The [MiTek ESR-3455 B66 Figure 3 and Table 3, p. 9][b66-source]
show F1 along the reach and F2 across it for a comparable brace, but its B66
values apply only to the stated `C_D = 1.6` duration.

The CAD uses global X across the board/header, Y front-to-back, and Z up.
For a horizontal-seat-up HL angle, define local `e1` as the signed horizontal
flange reach (F1), `e2 = Z × e1` as the bend line (unlisted transverse), and
`e3 = +Z` as uplift. The upright-flange outward normal is parallel to `e1`
in these poses. A side's sign is geometry bookkeeping, not proof that one
connector resists both signs.

| Pose | Upright normal / leg bolt axis | Bend `e2` | F1 / reach `e1` | Uplift `e3` |
| --- | --- | --- | --- | --- |
| Figure's right-side beam/post angle | +X | +Y | +X | +Z |
| Upper right, outward-X principal face | +X | +Y | +X | +Z |
| Upper left, outward-X principal face | −X | −Y | −X | +Z |
| Lower, rearward-Y core face | −Y | +X | −Y | +Z |

The prior audit mapped outward-X HL33 F1 to global Y, a 90-degree error.
It maps to global **X**; the unlisted horizontal transverse axis is **Y**.
Rotating the bracket about Z rotates both axes; mirroring it reverses the
signed reach while uplift remains up. The machine-readable
[`hl_load_axes.py`](../../scripts/hl_load_axes.py) fixture and tests preserve
this physical registration and project signed force and moment. They assign
no allowable to either sign, moment, or combined action.

For a corresponding outward-X MiTek B66 pose, its F1 and F2 axes would be X
and Y, respectively, subject to the actual Figure 3 installation. Its
published numbers cannot be used at the board's ordinary load duration.

Simpson says connectors are required on both sides to obtain F1 lateral
resistance in both directions, and lateral loads may not be doubled for a
pair. MiTek requires B66 braces on both sides for F1 in both directions.
Those pairing rules refer to the *local rated direction* in each typical
installation; they do not provide HL's unlisted transverse resistance.
Earlier same-Y and rear-shifted inner HL33 CAD rejections remain geometry
observations, but their claim to cover *global Y* with paired F1 needs
reassessment. A collision-free upper pair still needs a separate route for
any global-Y transverse demand, moments, separation, contact and interaction.

The old-connector and partial-topology reactions are diagnostic only. For
example, archived A1-rear old-proxy left principal/header total includes
X = 70.8 N and a large X-axis moment; that total is **not** the bracket's
X force or a new-topology envelope. A current-geometry simultaneous local
wrench, contact state and load-direction classification remain necessary.
No load is transferred between catalog axes, no B66 duration conversion is
made, and no member or bracket is accepted for cutting or drilling. This
correction changes an audit and dependent ranking text, not an accepted
capacity calculation.

[hl-source]: https://dhcsupplies.s3.us-east-2.amazonaws.com/Documents/simpson-strong-tie/hl-angles.pdf
[b66-source]: https://www.mitek-us.com/wp-content/uploads/files/pdf/Code%20Evaluation%20Reports/esrESR-3455.pdf
