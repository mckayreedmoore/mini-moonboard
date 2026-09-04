# V1 exterior-leg cutting

The two exterior hockey-stick legs use four lower and four upper 18 mm
laminations. Laminate each matched pair to form one 36 mm leg member; mirror
the finished lower profile for the left and right legs.

## Lower member

Start each of the four lower laminations as a `1495.2 x 180.0 x 18.0 mm`
rectangle. On the face of each blank, use a local coordinate system with the
long end as `(0, 0)` and the width increasing toward `(0, 180)`. Retain the
five-point profile emitted by
[`mini_moonboard_v1_leg_cut_schedule.csv`](../exports/mini_moonboard_v1_leg_cut_schedule.csv):

```text
(32.757, 0.000) → (0.000, 90.000) → (0.000, 180.000)
→ (1495.198, 180.000) → (1495.198, 0.000) → close
```

The small omitted triangle creates the CAD's 95.776 mm wide horizontal floor
bearing face when the member is set 20 degrees from vertical (60 degrees from
the descending board). Do not merely cut a square lower end: that would put a
corner, rather than the modeled bearing face, on the floor.

## Upper member and knee

Cut four `400.0 x 180.0 x 18.0 mm` square-ended upper laminations. Pair them
into two 36 mm members. At the row-8 bend, place the upper/lower members and
the exterior 450 x 450 mm knee plate exactly as the STEP assembly and generated
connection schedule show. The knee plate—not an unfastened butt—is the
provisional connection between the two segments.

The full floor interface, structural bolt stack, glue system, and unanchored
stability remain human-review items. This file only makes the CAD's plywood
geometry transferable to a blank.
