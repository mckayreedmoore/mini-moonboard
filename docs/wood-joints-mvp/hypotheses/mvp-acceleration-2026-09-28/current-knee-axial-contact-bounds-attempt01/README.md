# BG001 axial and contact equilibrium bounds

This packet maps the axial part of the current BG001 wrench using the two
modeled bolt tensions and compression-only normal resultants on the existing
post/spine face. It is an equilibrium envelope, not an accepted demand,
predicted bolt split, contact-pressure solution, resistance check, or joint
acceptance.

The inputs are pinned to
[`current-knee-post-conditional-bolt-screen-attempt01`](../current-knee-post-conditional-bolt-screen-attempt01/)
and
[`reduced-static-attempt01/contact-geometry.json`](../reduced-static-attempt01/contact-geometry.json).
The BG001 force acts on `knee_outer_left_spine` from `base_post_outer_left`.
Bolt tension on the spine is taken as global +X; contact compression on it is
global −X. The source contact face lies at x = −1219.2 mm, while the bolt-group
centroid is x = −1208.151 mm. At the projected contact datum
`(−1219.2, −137.6, 192.475) mm`, translate the signed wrench by

```text
Mx_contact = Mx_shaft
My_contact = My_shaft − 11.049 Vz
Mz_contact = Mz_shaft + 11.049 Vy
```

The JSON records a synthetic transform round-trip check and direct force and
moment closure for six unit-wrench witnesses. The source face is a rectangle
with two interior circular bolt-hole voids. The four real outer corners bound
its convex hull; the two extra serialized points are on circular hole
boundaries and are excluded from pressure support. Nonnegative corner
resultants describe ideal equilibrium/closure only. They do not claim a
finite-pressure traction realization, actual contact state, or installed
unilateral-contact law.

For tensions `T1,T2 ≥ 0` and outer-corner compression resultants `Ri ≥ 0`, the
axial/contact map at the face datum is

```text
Fx = T1 + T2 − ΣRi
My = z1 T1 + z2 T2 − Σ(dzi Ri)
Mz = Σ(dyi Ri)
```

This retains the face's moment arms when checking `My` and `Mz`. With zero
`Fx`, the normalized pure-couple moment arms span `My/R = −67.45…+73.8 mm`
and `Mz/R = −38.1…+95.25 mm`, where total bolt tension equals total contact
compression `R`. For a 1 N·m pure couple, the minimum total tie tension in this
ideal envelope is 13.550 N for `+My`, 14.826 N for `−My`, 10.499 N for `+Mz`,
and 26.247 N for `−Mz`. These are geometric equilibrium bounds, not allowable
loads. By comparison, with contact omitted the tension-only bolt pair has
`Fx=T1+T2`, `My=21.025(T2−T1)`, and `Mz=0`; it cannot carry a nonzero pure
couple when `Fx=0`. A hypothetical signed axial pair could form a `My` couple
over the 42.05 mm pitch, but would require a compression mechanism not
established for these bolts. Face contact also provides a route for `Mz`, so
the bolt-only `Mz=0` conclusion does not apply to the coupled system.

There is no unique tension allocation from equilibrium alone. The packet
records a self-equilibrated mode with equal added tension at both bolts and
opposing contact compression at the datum; adding any nonnegative multiple
preserves the wrench and makes each bolt's upper action unbounded in this
model. No pressure/stiffness law is available to select a physical split.

The accepted signed BG001 cut wrench is still missing for all six cases:
`a12-rear`, `a12-forward`, `a12-left`, `k12-right`, `k12-rear`, and `a1-rear`.
Each needs `[Fx,Vy,Vz,Mx,My,Mz]` at the shaft-group centroid, with cut side and
sign convention. The upstream panel wrenches are not BG001 joint actions.
Bolt tensile resistance, washer/head/nut seating, wood anchorage and splitting,
finite contact pressure and interface compatibility, and the separate lateral
transfer/capacity remain unqualified.

Reproduce the pinned packet with the Python standard library:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-knee-axial-contact-bounds-attempt01/produce.py --write
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-knee-axial-contact-bounds-attempt01/produce.py --verify
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-knee-axial-contact-bounds-attempt01/check_closure.py
```

The separate closure checker reconstructs each unit witness both from the
scalar equilibrium equations and from global force vectors and `r × F`; its
maximum observed force/moment residual was `5.33e−15` in the mixed N/N·mm units.
No solver, mesh, or CAD geometry is used or changed.
