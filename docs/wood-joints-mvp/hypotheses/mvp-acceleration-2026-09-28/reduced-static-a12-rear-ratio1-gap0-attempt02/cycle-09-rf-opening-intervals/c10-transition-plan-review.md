# c09 to c10 transition plan review

This is a read-only review of the predicted next active set. It does not prepare, freeze, or solve c10.

## Evidence binding and c09 result

- c09 `freeze.json` SHA-256: `9af8d36214b108d5d928cfca6e2bb3d853ef70ae8170584939157a5f5a962874`.
- c09 `response.json` SHA-256: `caa2f520636a0a227c425416ca88fc503f7d4f1fc8b06e2fafac832bac9aaf90`; its `input_freeze_sha256` matches the freeze above.
- The response records a verified native execution and passing isolated-spring RF action/reaction and KDU intervals, raw and interval equilibrium, and MPC checks. All 50 body-equilibrium checks pass. There are no native warnings.
- Contact complementarity still fails with nine compression-contact sign exceptions; tension-tie complementarity passes with zero exceptions. `numerical_checks_passed`, `mechanical_acceptance`, and `qualified_for_design` are false.

## The nine c09 contact exceptions

Seven active normals have negative compression force and positive opening; the predicted transition deactivates them. Two inactive normals show penetration with zero compression force; the predicted transition activates them.

| c09 contact | c09 state | Opening (mm) | Compression force (N) | Predicted c10 state |
| --- | --- | ---: | ---: | --- |
| `contact_20_1` | active | 0.000001700 | -0.3033 | inactive |
| `contact_21_1` | active | 0.000004270 | -0.7619 | inactive |
| `contact_32_0` | active | 0.000004730 | -0.7144 | inactive |
| `contact_36_1` | active | 0.000045000 | -5.9879 | inactive |
| `contact_48_1` | active | 0.000016550 | -2.2022 | inactive |
| `floor_base_floor_left_11` | active | 0.001499225 | -272.9226 | inactive |
| `floor_base_floor_right_14` | active | 0.000001547 | -0.2816 | inactive |
| `contact_40_2` | inactive | -0.000586400 | 0 | active |
| `contact_95_17` | inactive | -0.000352100 | 0 | active |

Deactivating the two floor normals also removes their paired tangent groups, `floor_base_floor_left_11_friction` and `floor_base_floor_right_14_friction`.

## Predicted c10 branch

The read-only `dat-displacement-rounding-intervals/v1` transition predicts 514 active groups: 318 normal contacts, 166 axial ties, and 30 floor tangents. Relative to c09's 521 groups, seven normals turn off, two normals turn on, and the two paired floor tangents turn off: 11 group changes total. The c09 displacement intervals yield zero threshold ambiguities for this transition. The candidate set does not repeat any of the ten consumed branches c00–c09.

These counts and state changes are a deterministic prediction from c09's recorded response and DAT output. They are **predicted, not solved**: no c10 native response exists, and c09's own contact complementarity remains failed.

## Bounded continuation recommendation

Budget one separately reviewed c10 run as a zero-gap closure diagnostic. If c10 passes the numerical checks and all contact/tie complementarity checks, stop zero-gap iteration there and proceed to the separately budgeted source-clearance method fixture and six-case matrix. If c10 retains sign exceptions, yields an ambiguous or repeated state, or fails another numerical gate, stop this branch and diagnose the method/model before proposing any further zero-gap solve. The c00–c09 run allowance is already consumed; this report does not authorize or launch c10.
