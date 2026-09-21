# PB-02 current center placement inventory

The [placement-table script](../../scripts/simple_center_current_placement_table.py)
prints the complete per-bolt/per-member table for this trial. It reads the
maintained tolerance-pose geometry, then applies
`simple_center_post_header_two_bolt_probe.VARIANTS["shorter_8in_trial"]`.
That is the newer 143.9 mm high post/header block with **two post-to-block
and two block-to-header bolts**. The remaining six bores keep the tolerance
pose. There are ten bores in this inventory. The earlier eight-bore tolerance
pose and its five-family 5.075 mm subset margin are historical comparators,
not the whole-center result for this revision.

Each row names a bolt, receiving wood member, face or neighboring bore,
nominal centerline distance, conditional marker, one project fabrication
allowance, and arithmetic reserve. The script emits JSON or Markdown. Run:

`.venv/bin/python -m scripts.simple_center_current_placement_table --format markdown`

The nominal diameter is 6.35 mm. The project comparators are 4D = 25.4 mm
for a potentially loaded transverse edge or a parallel neighboring pair,
and 7D = 44.45 mm for a possible tension grain end. Those are **conditional
markers**, not a completed NDS classification or adopted capacity check.
The marker definitions and grain/edge distinction follow the repository's
[NDS geometry basis](simple-rail-nds-geometry-basis.md) and earlier
[center member screens](simple-center-wide-post-probe.md). The current
post/header dimensions and axes are from the
[two-bolt block probe](simple-center-post-header-two-bolt-probe.md).
The project fabrication allowance is **5.0 mm once per classified marker**:
`reserve = nominal centerline distance − conditional marker − 5.0 mm`.
For example, the new post/block bolt has 30.7 mm to the post rear Y edge,
so its conditional reserve is 30.7 − 25.4 − 5 = **0.3 mm**. The prior
small-tool and tolerance-pose arithmetic effectively applied 5 mm twice to
transverse edges; this table does not. A negative reserve means only that
this chosen conditional marker plus project allowance is unmet.

| Bolt / member and feature | Nominal mm | Conditional marker mm | Allowance mm | Reserve mm |
| --- | ---: | ---: | ---: | ---: |
| `post_cleat_1` / shifted post rear Y edge | 30.7 | 25.4 | 5 | +0.3 |
| `post_high` / shifted post top grain end | 36.9 | 44.45 | 5 | −12.55 |
| `upright` / side block front Y edge, inherited | 16.1 | 25.4 | 5 | −14.3 |
| `cleat_header_1` / `cleat_header_2` parallel pair, header | 27.5 | 25.4 | 5 | −2.9 |
| `upright` / inclined principal, Y lower box boundary | source-derived | unknown | none | unknown |

The table includes all ten bolts in each intended receiving member and every
pair of bores sharing a member. Parallel pairs receive only a conditional 4D
pitch comparator. Orthogonal pairs list the shortest finite-centerline gap as a
geometry observation with **unknown** placement classification. The inclined
principal's rectangular-box distances are also shown with **unknown** marker
and reserve; its oblique grain, end and loaded-edge treatment needs a separate
member-specific check. Force direction, edge sign, loading mode, group
spacing, stock and drilling variation, and physical hardware are not resolved.
Unknown rows are retained in JSON and Markdown and excluded only from the
explicitly named *conditional subset minimum*. The subset minimum here is
−14.3 mm after the single allowance; there is **no whole-center minimum**
or claim of complete classification.

Two orthogonal neighboring-bore pairs warrant a local wood check before
selection. `post_high`/`post_cleat_2` in the shifted post has a **26.0 mm
finite-centerline gap**, leaving **18.7 mm nominal wood between bore surfaces**.
`upright`/`cleat_link` in the side block now has a **27.5 mm centerline gap**
and **20.2 mm nominal wood** after moving only `cleat_link` to Z328.5. Its
lower grain-end distance is 51.5 mm, 2.05 mm beyond the separate 7D+5 project
comparator. These values use the model's 3.65 mm bore radius. This is
not a measured ligament or a strength rating; drill variation, splitting,
combined local stress and applicability of any spacing rule remain open.

The older post/block single-bolt Y=−150 mm position has 25.7 mm to the rear
Y face: just **0.3 mm above 4D before allowance**. The regression test keeps
that position visible as a historical warning. The current post/block pair
has moved to Y=−145 mm, while inherited positions and the new bolt pitch
still require review. This inventory neither changes the model nor releases
cutting, drilling, fabrication or a structural rating.

Focused check:
`.venv/bin/python -m pytest -q tests/test_simple_center_current_placement_table.py`.
