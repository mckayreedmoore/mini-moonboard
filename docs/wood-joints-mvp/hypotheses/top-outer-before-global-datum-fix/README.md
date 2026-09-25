# Preserved top-outer report datum defect

Parent ran this producer against retained WJ16 in 25.72 seconds on
2026-09-24. Thirteen implemented local geometry/provenance screens passed;
five readiness/acceptance fields remained false. Review then found that
`stock_and_frame.cleat_local_frame.right_rail_row_global_X_mm` repeated the
local coordinate 2211.975 mm. The source-frame X origin is −1130.3 mm, so
the correct global X is 1081.675 mm. The modeled stack world axes already
used the source transform; this is a report datum defect.

Preserve this [report](geometry.json), [producer](producer.py.snapshot), and
[hash manifest](sha256.json) as superseded evidence. Do not use its mislabeled
global field as a cutting, drilling, or placement dimension.
