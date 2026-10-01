# Panel screw-group total withdrawal lower bound — attempt01

## Engineering result and stop condition

The current model maps each loaded main panel to twelve Hillman screw axes,
all parallel to the panel's inward normal. Under a normal-only contact screen,
five of the six frozen climber-load cases give a conditional lower bound of
**1,199.82–1,659.44 N** on the *sum* of the twelve screw axial tensions,
before panel and hardware gravity. The sixth case, `a1-rear`, stays unresolved:
the pinned geometry contains a finite `kicker_left` / `main_lower_left` face
whose normal can provide an inward compression reaction. No contact state or
force share is assigned to that patch. No force is divided among individual
screws.

Stop a case-specific deduction if a loaded panel lacks the twelve mapped
axes, an axis is not aligned with the inward panel normal, or any finite
contact face can supply an opposing normal reaction. This screen also assumes
zero tangential contact traction; frictional transfer has no assigned law.
Even for the five bounded cases, do not use the result as a per-screw action
or resistance check: exact-product withdrawal/stiffness, installed
engagement, head/panel limits, group distribution, and downstream receiver
transfer remain open.

## Reproduction

From the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/panel-screw-group-total-withdrawal-attempt01/verify_panel_group.py --verify
```

The verifier reconstructs each outward force component as the dot product of
the frozen applied force and its source-recorded outward panel normal. It
cross-checks the case-to-panel map and applied force in the reviewed
reduced-static inputs, checks the current receiver map has twelve screw axes
per loaded panel, verifies each axis is unit length and points along the
inward panel normal, and checks all finite contact-patch normals in the
pinned contact-geometry record. For `a1-rear`, it finds the opposing-normal
kicker patch and returns no group lower bound. For the other five cases, the
bound applies only under a normal-only unilateral contact interpretation:
backing reactions push outward, and no enumerated finite contact normal points
in the opposing direction. Friction or other tangential restraint remains
unassigned. These geometry checks do not establish that the screw group is the
only physical inward restraint; the current model keeps its screw attachment
laws undefined. The script writes only with `--write` after exact source
hashes pass.

## Results

| Case | Loaded panel | Axes | Climber-load outward normal force | Conditional minimum total group tension |
|---|---|---:|---:|---:|
| `a12-rear` | `main_upper_left` | 12 | 1,659.44 N | 1,659.44 N |
| `a12-forward` | `main_upper_left` | 12 | 1,199.82 N | 1,199.82 N |
| `a12-left` | `main_upper_left` | 12 | 1,429.63 N | 1,429.63 N |
| `k12-right` | `main_upper_right` | 12 | 1,429.63 N | 1,429.63 N |
| `k12-rear` | `main_upper_right` | 12 | 1,659.44 N | 1,659.44 N |
| `a1-rear` | `main_lower_left` | 12 | 1,659.44 N | **Not established** — opposing-normal kicker contact is unresolved |

The source case moments remain relevant to distribution and peak actions
within each group; this force-only equilibrium bound does not recover those
actions. The `a1-rear` opposing-normal candidate is a finite 113.5635 mm²
`kicker_left` / `main_lower_left` patch; its geometry does not establish
active contact, bearing, stiffness, or capacity. Panel, T-nut, hold, and
accessory gravity are excluded, as are installation effects and the path
beyond the receiving timber. The source load contract applies the climber
wrench directly to each panel and does not model hold/T-nut attachment
mechanics.

## Limits and disposition

This result provides conditional necessary group actions for five cases in
the Option B panel-withdrawal screen and isolates one unresolved alternate
contact in the sixth. It does not establish that the current screws have an
applicable structural rating, prove actual contact behavior, assign load
among the twelve axes, establish load-slip stiffness, or check transfer into
the receivers and frame. The current model marks every panel-screw
`mechanical_attachment_defined=false`, and the geometry inventory cannot prove
that no other physical inward restraint exists. The panel-withdrawal and
receiver/hardware gates remain **BLOCKED**. Missing product or installation
evidence is not a physical failure finding. No geometry, native solver input,
mesh, or physical installation was changed or evaluated.

## Source pins

| Source | SHA-256 |
|---|---|
| [Six-case load contract](../../../../../docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-load-cases.json) | `9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a` |
| [Current receiver screen](../../../../../docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/receiver-screen-attempt04.json) | `851495f2ccc80f286a7eae97fc54bcf602a478bb7d4e13eb28e2ae44cfb87991` |
| [Reduced-static source/input record](../reduced-static-attempt01/model-inputs.json) | `178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9` |
| [Reduced-static contact geometry](../reduced-static-attempt01/contact-geometry.json) | `034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151` |

The local files are listed in [`SHA256SUMS`](SHA256SUMS).
