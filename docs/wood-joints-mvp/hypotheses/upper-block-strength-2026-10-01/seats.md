# Upper-block washer seats and axial references

This check covers the 16 uppermost and 16 service upper-block bolts. For each
of the 32 axes it binds the head and nut washer seats to the two exterior wood
faces, tests three annulus sizes on the saved finished STEP solids, and carries
the source axial tie through both seats for all 672 response states. The
local-only machine-readable replay is `seats.json`; it retains all 1,344
seat-state records and the three support scenarios for each.

## Seat ownership and CAD support

Head and nut owners come from the signed `head_to_nut_axis_xyz` and exact
per-member bolt-line midpoints and bearing lengths. Each endpoint must match a
unique member face within 1e-5 mm. The block is not presumed to carry the head:
16 heads map to blocks and 16 to hosts; the same split applies to nuts. The
seat normal points from each saved exterior face into its owning wood member.

The checker imported 15 unique saved finished-member STEP solids. It matched
their paths and SHA-256 values to the pinned bundle manifest, then matched
solid validity, solid and face counts, volume, bounds, and surface areas to its
STEP readbacks. Each of 64 nominal seat locations was checked against the full
BREP under three fixed-center annuli. All 192 seat/scenario combinations had
inward support fraction 1.0, outward overlap fraction 0.0, and a matching
coplanar planar datum face at probe depths 0.01, 0.05, and 0.1 mm. Maximum
datum-plane offset was 1.01e-9 mm; minimum absolute normal alignment was 1.0.
The replay records 1,152 inward/outward volume probes.

| Annulus scenario | OD (mm) | ID (mm) | Area (mm²) | Inward support | Outward overlap |
| --- | ---: | ---: | ---: | ---: | ---: |
| CAD modeled | 18.6436 | 8.0000 | 222.7262 | 1.0 at every seat | 0.0 at every seat |
| Catalog minimum area | 18.4658 | 8.3058 | 213.6279 | 1.0 at every seat | 0.0 at every seat |
| Catalog maximum envelope | 19.0246 | 7.7978 | 236.5067 | 1.0 at every seat | 0.0 at every seat |

Catalog dimensions are Type A Wide bounds from the pinned fastener input. The
minimum-area case pairs the smallest OD with the largest ID; the maximum
envelope case pairs the largest OD with the smallest ID. These are separate
conditional bounds, not a selected or received washer. All 64 conditional
grain axes are perpendicular to their bolt axes, so the Fc-perp route below
applies under its stated assumptions. The code also leaves parallel and
oblique grain routes explicitly unresolved.

## Signed axial seat reference

The script checks each frozen `axial_force_on_block_n` vector against the
signed bolt axis and the source `axial_tension_n` scalar. All 672 source
scalars are exactly nonnegative, and every two-seat pair retains the same
physical sign. In this source set all 1,344 seats carry positive axial tension;
the source has no zero or compression state. The calculation keeps the signed
projection per seat. If a future source contains compression, the record stays
negative and washer pressure demand is zero; it is not converted to pressure
with an absolute value.

The largest axial force is 535.389 N at the uppermost right outer block's
`rail_1`, K12-rear at increment 6. The service-level maximum is 57.210 N at
the left outer upper block's `upper_side_1`, K12-rear at increment 6. Each
state stays separate from the lateral peak and from every group total.

For positive tension, the conditional pressure reference is the force divided
by the fully supported annulus area, compared with 625 psi Fc-perp from the
pinned upper-review source and the directly pinned
[material specification](../hardware-material-specification-2026-09-30/materials.md).
The primary [2024 NDS Supplement Chapter 4](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024-Supplement_20240719_Chapter-4-Reference-Design-Values_Website-1.pdf),
Table 4A at printed page 34 (PDF page 4), supplies DF-L No. 2 `Fc-perp=625 psi`.
Its SHA-256 is `1f65975633f111c308944c470b6cc10e9207b6c45e8a0804b8bdec3378bbc71b`;
`seats.py` verifies both the material record and this local PDF. It
assumes uniform compression over the whole washer/wood annulus and no preload
or bearing-area-factor increase.

| Annulus scenario | Ideal Fc-perp reference force (N) | Peak average pressure (MPa) | Peak Fc-perp ratio |
| --- | ---: | ---: | ---: |
| CAD modeled | 959.78 | 2.404 | 0.5578 |
| Catalog minimum area | 920.57 | 2.506 | 0.5816 |
| Catalog maximum envelope | 1,019.16 | 2.263 | 0.5253 |

These values are conditional ideal-annulus references, not bolt or joint
capacities, acceptance criteria, or release evidence. They do not resolve
washer bending or spreading, cap-head/nut bearing-face geometry, eccentricity,
wood-face flatness, splitting, adjustments, local load transfer, or actual
contact. No physical part or cut was inspected.

## Pinned inputs and replay

The uppermost and service action packets are SHA-256 pinned to
`0fc5f9ce9c92effcb01d3213c38b33282c281539dab9d48cb06f33e15c1994a6` and
`f4c92d874dcb0f40e5e900971deaff9580e99063b453e1984e9b1ba660a2be9f`,
respectively. The catalog input, CAD annulus constants, support implementation,
geometry module, and finished-member bundle manifest are also hash-checked.
The ignored `seats.json` records those hashes, every STEP hash and readback,
CAD/OCP versions, datum/probe tolerances, and all signed state identities.

Run from the repository root:

```sh
uv run --no-sync pytest -q docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/test_seats.py
uv run --no-sync python docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/seats.py
uv run --no-sync python docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/seats.py --verify
```

The generator only reads frozen source and finished-solid evidence. It runs no
native solve and changes no candidate geometry. It leaves `joint_accepted`,
`six_case_envelope_established`, `fabrication_released`, and `drilling_released`
false.
