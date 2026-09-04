# V1 assembly placement layout

[`mini_moonboard_v1_assembly_layout.csv`](../exports/mini_moonboard_v1_assembly_layout.csv)
is generated directly from every physical solid in the CadQuery assembly. It
lets a builder locate the rear rails, bearing blocks, ties, splices, legs, and
gussets without reverse-engineering their placement from a rendered view.

Its datum **O** is the board centerline at the kicker's climbing-face plane and
finished-floor plane. Positive X is right when facing the climbing surface,
positive Y is toward the support side, and positive Z is up. Each row records:

- the exact CAD part name used by the cut, fastener, and STEP documents;
- its mass-center X/Y/Z location from O;
- a stable world direction for its longest edge; and
- its world-axis bounding dimensions for dry-fit identification only.

Use the cut list for blank sizes, the leg profile schedule for the non-rectangular
leg cut, this layout to place parts, and the primary/secondary connection
schedules to fasten them. A world AABB is not a cut dimension for a rotated
part; the viewer and cut list provide those separately.
