# Candidate rigid-translation witness for the free-cleat N path

This note records a source-pinned candidate assignment for frozen A09
`n_plus`, not a solver result. The relative port coordinate is 1.0 mm along
local N. Using the columns of the frozen port producer's serialized 3×3 basis
matrix, global N is `[0, −0.7660444431, +0.6427876097]`. Assign rail
translation `+0.5 N`, principal translation `−0.5 N`, and cleat translation
zero, with all rotations zero. This gives rail displacement
`[0, −0.3830222216, +0.3213938048] mm` and the opposite principal
displacement. The deck prescribes generalized port controls `+0.5` and
`−0.5`; the independent audit reports zero port-transform and boundary-value
error, no cleat boundary, and no port-control/nut-dependent-DOF intersection.

Translate each of the four hardware stacks halfway between its two receivers:
rail-axis stacks `+0.25 N`, principal-axis stacks `−0.25 N`. Head and shaft
remain one physical bolt; each bolt, both washers, and its nut move together.
The source inventory assigns each bolt to the cleat and its rail or principal
receiver. The four nuts have 24 rigid-fit equations (six each); the source
audit passes affine rigid reproduction and unique dependent variables. This
translation therefore preserves the frozen equation representation when each
nut control follows its bolt. The four nut-bore contact pairs are intentionally
unmodeled.

The directly checked geometric relations are:

| Source interface | Projected outer domains after the assignment | Candidate overlap |
| --- | --- | --- |
| Cleat–rail | Cleat `X=89.05…177.95`, `N=219.841…339.541 mm`; shifted rail `N=210.341…350.041 mm` | The cleat's 88.9 × 119.7 mm outer envelope remains inside the rail domain; N edge margins are 9.5 and 10.5 mm. |
| Cleat–principal | Cleat `T=355.624…444.524`, `N=219.841…339.541 mm`; shifted principal `N=209.341…349.041 mm` | The cleat's 88.9 × 119.7 mm outer envelope remains inside the principal side domain; N edge margins are 10.5 and 9.5 mm. |
| Rail–principal | Shifted rail end `T=317.524…355.624`, `N=210.341…350.041 mm`; shifted principal `N=209.341…349.041 mm` | Outer projected overlap is 38.1 × 138.7 = 5,284.47 mm², down from 5,322.57 mm² before motion. |

The face domains were matched from the pinned source inventory and mesh report
by area, centroid and plane normal, then projected from their analytic
parameter bounds. The three wood-interface normals have max `|n·N|`
`1.05e−12`; the 32 source normals in the 16 planar-seat pairs have max
`5.79e−13`. The declared 35 contact roles are 3 wood interfaces, 16 planar
seat pairs, 8 shaft-to-wood-bore pairs and 8 shaft-to-washer-bore pairs. The
eight CAD wood-bore gaps are about `0.575 mm`; the midpoint stack assignment
has `0.25 mm` radial offset to each receiver and `0.325 mm` nominal remaining
radial gap. The separately reviewed [C3D10 radial-envelope result](../ordinary-n-motion-radial-envelope-attempt01/README.md)
gives positive floating-point Bernstein-hull margins after reserve for all
eight wood bores (`0.0931487349 mm` minimum) and all eight co-moving washer
bores (`0.6725849896 mm` minimum).

The calculation supports a candidate zero-strain rigid translation under
ideal geometry. It does not prove all contact constraints: projected domains
are outer analytic bounds, not shifted Boolean intersections of trimmed faces
with inner wires; washer-seat overlap and the 19 planar contact pairs are not
fully checked. The C3D10 overlay has finite approximation error (plane
residual up to about `2.2e−8 mm`), and the radial envelope is floating-point,
not outward-rounded interval arithmetic. These finite tolerances and the
projection/equation precision mean this is not an exact native zero-force
state or proof of exact nonlinear nullity. No contact-law evaluation,
solver state or equilibrium was computed here.

Accordingly, this is not proof that an actual joint follows the assignment or
that a 1 mm port path resolves wood-bore bearing. It does not establish exact
contact onset, failure, capacity or frame demand; historical `1.15 mm` and
`1.3 mm` onset claims remain withdrawn. Small method-fixture passes do not
cure A09's free-cleat nonlinear nonconvergence, so this audit selects no
heavy retry.

All source hashes below are relative to
`docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/`.
`P` = `ordinary-port-motion-attempt09-common-map/`, `C` =
`ordinary-patch-contact-classification-attempt01/`, `I` =
`ordinary-patch-inputs-attempt01/`, and `R` =
`ordinary-n-motion-radial-envelope-attempt01/`.

| Pinned source | SHA-256 |
| --- | --- |
| `P/port-motion_n_plus.json` | `a28c0ba399842f96801ce5ce982dc6b52d459c537c132d283de01298d63b31bc` |
| `P/port-motion_n_plus-audit.json` | `9f1135ed95c48c07d3e82f7c5dcc7a0bef1e1cc22fd8350ec4fc7cdd1b28fdf4` |
| `P/port_motion_n_plus.inp` | `e94220362d6a4925dc71089b855f84daa540eb477103628291b319b4a9728def` |
| `P/port-motion-controls.inp` | `08fae47b80ed812483ee036abfcd7b110f0ecfbbc42a4c45bfa52bc8e07b565e` |
| `P/port-motion-n_plus-lock.json` | `fcc72f0d627bfe233b7893c134a4a93c9c6a5038a366680de119a84ee497a6cb` |
| `P/external-ports.json` | `2e2e52fbab16a34f9d1faf50a362c4c9cde9013957098498a941ce02713e6e02` |
| `P/mesh.json` | `1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07` |
| `P/contact-manifest.json` | `50f7d8c9b85197f43732d49d13e75240fa6d5423673d28274e278829878a594d` |
| `P/nut-coupling.json` | `568ade2437181bc8e9398f64a2818bbf8bd3f46a64dae9639bf363cb68bec960` |
| `P/nut-coupling.inp` | `af5b36dce4e85b19a6a5b4805dd6b00259da88ccc1a849769642db2ecbf62903` |
| `C/classification.json` | `18bdf1b9736ce6ca2cf2b3dd0488a7651da05f35e531605fd465e7b502363f13` |
| `I/inventory.json` | `70b396e636175abcad7467dc145029d7126c1ea7dff1d053a61f8c5321e1c1d3` |
| `R/radial-envelope.json` | `e459e979e33d9deb85ae5064fa27b2d2a78280ec87986bc40fc0ab4335a3ae3f` |
| `R/independent-review.md` | `5303e7949deb91ef9518eb3d280418d6bc8f7d0954fa32daffebedfd2ccf69ed` |
