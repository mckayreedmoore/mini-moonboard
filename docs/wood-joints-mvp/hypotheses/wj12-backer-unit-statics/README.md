# WJ12 backer unit-wrench statics witnesses

Status: capacity-independent diagnostic, 2026-09-24. The
[report](statics.json) uses the actual finished left/right backers, header,
four bores, and installed shafts in the
[twelve-duty composition](../wj12-integrated-static/README.md). It applies
signed unit forces of 1 N and unit moments of 1 Nmm about each bolt-group
centroid. These are twelve synthetic cases per backer, not actual demands
or substituted historical angle actions.

| Derived geometry | Left backer | Right backer |
|---|---:|---:|
| Bolt-group centroid X/Y/Z, mm | −35 / −80 / 238.9 | 33 / −87 / 238.9 |
| Bolt spacing, mm | 34.000000 | 27.202941 |
| Row direction, global X/Y/Z | 0 / 1 / 0 | −0.588172 / 0.808736 / 0 |
| Negative-transverse contact-patch lever, mm | 16.706250 | 33.578630 |
| Positive-transverse contact-patch lever, mm | 27.743750 | 21.383676 |

The baseline uses two ideal point fasteners. It balances forces and moments
perpendicular to their row, leaving the moment parallel to that row
unresolved. The separate finite-contact construction transfers compressive
axial resultants to annuli around the bores and supplies the remaining
row-axis couple through a compression patch and bolt tension. It represents
one possible equilibrium construction, not predicted load sharing.

Each annulus has 4.15 mm inner and 6.15 mm outer radius, giving 64.716809 mm²
area. The row-moment patches are 2 mm radius disks centered halfway from the
bolt-row centroid to the actual outer-face boundary in each transverse
direction. These are explicit witness parameters, not selected bearing
areas, pressure distributions, or design dimensions. The right diagonal
row uses actual ordered face boundaries; a projected rectangle is not used
as supported material.

Boolean checks confirm each annulus and disk lies in finished material on
both sides of the contact plane, using separate 0.25 mm inward prisms.
All twenty-four finite witnesses satisfy force and moment equilibrium with
valid tension-only bolt axial reactions and compression-only contact
reactions. Maximum residuals are 6.94 × 10⁻¹⁸ N and 5.56 × 10⁻¹⁷ Nmm.
Those numerical residuals establish only the stated statics construction.
Fastener transverse bearing remains an ideal point reaction. Its physical
support, bolt tension, washer and wood resistance, splitting, contact
behavior, actual demand distribution, and capacity remain unverified.

Parent ran the final report against retained composed geometry in 0.25 s
and checked the producer hash afterward. Source/family fingerprints,
actual shape hashes, and exact composition/static-report hashes are bound.
The [manifest](sha256.json) preserves the report and exact producer snapshot.
Seven focused tests include asymmetric geometry, independently recomputed
signed equilibrium, missing support that balances algebraically but fails
the finite witness, and irrelevant circular counterbore floors during face
selection. The initial actual run exposed that face-selection issue; it
produced no statics report before correction. No geometry rebuild or native
solve was required for the correction.

The [sampled section report](../wj12-sampled-sections/README.md) supplies
separate local cut geometry. Neither report closes backer/header joint
acceptance. Real backer demands remain absent, all capacity/release flags
remain false, and fresh native execution remains authorization-dependent.
