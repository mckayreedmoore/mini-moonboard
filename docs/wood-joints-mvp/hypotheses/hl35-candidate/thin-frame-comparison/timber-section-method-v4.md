The targeted finished-section method is ready for parent-owned selected
queries when the new common-shaft field identifies a stress concern. No
candidate BREP section was queried during method verification and the
existing 1,050-station inventory was not repeated.

The frozen [helper](../../../../../scripts/thin_bolted_timber_section_properties.py)
has SHA-256 `398e883849dfd83a34aeb60b5ac0b5d50f57ffa9b01f3f2427e341725749a80a`.
The [coupon receipt](timber-section-method-coupons-v4.json) has SHA-256
`44c8d26e88572cdae762d43496ecd81734693d1102e89ca09c2ac1d5696df110`.
Six analytic fixtures and Ruff passed with CadQuery 2.8.0,
cadquery-ocp 7.9.3.1.1 and NumPy 2.5.2. The independent reviewer checked the
cross-inertia mapping, signed wrench transport and actual material extrema.
All release flags remain false.

The method intersects one actual, unfilled finished solid with the existing
grain-normal plane. OpenCascade surface properties provide area, centroid
and central area moments, including the cross product. Rigid transformations
preserve analytic curves; integration and bounding use geometry rather than
tessellation. The installed APIs were inspected and their behavior verified
on analytic shapes. [BRepGProp](https://dev.opencascade.org/doc/refman/html/class_b_rep_g_prop.html),
[GProp_GProps](https://dev.opencascade.org/doc/refman/html/class_g_prop___g_props.html)
and [BRepBndLib](https://dev.opencascade.org/doc/refman/html/class_b_rep_bnd_lib.html)
describe these geometry operations.

| Fixture | Known answer being checked |
| --- | --- |
| 100 × 60 mm rectangle | A=6,000 mm²; centroid=(50,30); second moments 5,000,000 and 1,800,000 mm⁴ |
| Concentric radius-10 mm hole | Subtract π100 mm² and π10⁴/4 mm⁴; retain centroid |
| Eccentric radius-10 mm hole at (70,40) | Subtraction and parallel-axis centroid/cross-moment identities |
| 40 × 20 mm corner recess | Actual maximum U+V=140; absent bounding-box corner would incorrectly give160 |
| Centroidal axial force expressed at a different datum | Full force/couple transport removes the apparent eccentric moment |
| Incorrect saved area or different cut station | Fail closed |

For a simultaneous complete signed lower-grain cut wrench, the method
transports the full moment to the actual centroid. With U×V=grain,
Mu=∫σV dA and Mv=−∫σU dA. Solving the central two-by-two moment matrix gives
the linear normal-stress gradient. Directional geometric bounds along that
gradient find the actual extrema on the trimmed section; an absent corner
or a full rectangle is not substituted. These are linear section components,
without hole/notch stress concentration, local fracture or stability
qualification. Effective shear area, arbitrary-section maximum shear and
torsion resistance remain unavailable; 1.5V/A is not adopted.

`measure_section(shape, origin=..., grain=...,
expected_prior_area_mm2=..., wrench=...)` is the geometry API. The immutable
request CLI accepts 1–40 selected existing stations per batch. It verifies
the unit/cache/detail source pins, selected finished BREP bytes and volume,
grain and saved same-station area within 0.001 mm². The new 132-body demand
consumer must supply authenticated simultaneous cut witnesses and retain
each capture's actual host support datum. This geometry helper explicitly
does not independently recover a supplied wrench from its force field.

A request JSON uses this structure; the optional wrench is the complete
signed tuple, not independently located component maxima:

```json
{
  "candidate": "compact-floor-flush-thin-bolted-development",
  "unit_packet_sha256": "5e78ac49a2db2050caf7ee7d2002d0ebf4f9a92496e857a0e2d652629bd0d848",
  "geometry_cache_sha256": "cafdd983a41f2eee15647b28e60e5b2704354a4c5518d120e4c4342001994bb9",
  "state_id": "source-bound common-shaft state ID",
  "source_sha256": {"path-to-compatible-source": "source SHA-256"},
  "requests": [{
    "member": "existing member ID",
    "station_global_grain_projection_mm": 0.0,
    "state_id": "same source-bound state ID",
    "signed_same_cut_wrench": {
      "cut_point_xyz_mm": [0.0,0.0,0.0],
      "force_on_lower_portion_xyz_n": [0.0,0.0,0.0],
      "moment_on_lower_portion_about_cut_xyz_nmm": [0.0,0.0,0.0]
    }
  }]
}
```

The example is schema documentation, not a valid candidate query or load
case. Parent execution binds actual requests and writes distinct evidence:

```sh
UV_CACHE_DIR=/tmp/thin-timber-uv-cache uv run python -m scripts.thin_bolted_timber_section_properties \
  --requests PATH --requests-sha256 SHA256 --out DISTINCT_OUTPUT
UV_CACHE_DIR=/tmp/thin-timber-uv-cache uv run pytest -q \
  tests/test_thin_bolted_timber_section_properties.py
```

The frozen method and coupon remain active inputs. Production selected
queries, complete timber resistance and the common-shaft force consumer are
separate remaining work; no source or raw run was pruned.
