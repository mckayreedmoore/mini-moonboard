# PB02 bore-aware net-section screen

This screen binds four timber cuts to the corrected Z202/link-Z328.5
`a12-forward` diagnostic report. It authenticates the report hash, candidate,
current geometry fingerprint, geometry-source hash, numerical acceptance, and
the report's explicit nonqualification and no-release state.

A later face audit found one active canonical spring outside the true
principal/cleat overlap and no tributary-area basis for the four equal face
springs. These section actions remain pre-contact-cell-correction numerical
history and require recomputation after the corrected model rerun.

The cuts are the inclined principal at the upright bolt, the upright-side cleat
at both bolts, and the rear cleat at the link bolt. The two side-cleat cuts are
27.5 mm apart. Every cut uses a 7.3 mm diagnostic bore as a centered rectangular
strip in its grain-normal section. This is not a drill instruction. The result
also exposes that the published stiffness basis uses 7.5 mm, a 0.2 mm mismatch.

For each side of each cut, the screen reports axial force, biaxial bending,
linear-elastic net-section corner normal stress, and transverse shear demand.
Torsion is retained as a separate demand and is not combined with normal stress
or transverse shear. No resistance or utilization is calculated.

Three cuts have exact `member_section_demands` rows at the bore center. The
inclined-principal bore center is 5.691 mm below the report's first validated
full-width recovery plane. Its two actions are therefore reconstructed from the
authenticated free body and same-station bolt load, then applied only to the
requested nominal 38.1 x 139.7 mm far-field section. The output marks this
result as extrapolated and outside the report-valid full-section interval.

Open items remain torsion/shear interaction, local interaction between the two
nearby orthogonal bores, near-hole stress concentrations, material resistance,
the principal's actual clipped local section, and the other five load cases.
The screen is not a capacity verdict, drilling release, or fabrication release.
