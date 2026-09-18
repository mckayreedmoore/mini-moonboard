# Insert attachment symmetry review

The current `round-insert-development` layout has exact left/right symmetry:
all 28 attachment pairs have mirrored horizontal coordinates and identical
heights. This review reads `attachment_datums()` in
[`round_insert_frame.py`](../mini_moonboard/round_insert_frame.py), including
its inherited rows and columns from
[`round_panel_layout.py`](../mini_moonboard/round_panel_layout.py).
It evaluates geometric regularity, not connection resistance or a mathematical
optimum. No geometry changes follow automatically from this review.

## Main panels

Each face has four evenly spaced horizontal attachment positions at absolute
coordinates 70, 446.7167, 823.4333 and 1200.15 mm: a 376.7167 mm pitch.
The four principal/rim rows have a uniform 358.3833 mm pitch within each panel,
with matching heights on both columns and both sides. Their bottom and top
panel-edge offsets are 59.05 and 85 mm respectively.

The lower bottom-rail and service-rail attachments align with their adjacent
principal rows. Moving the upper service rails to slope station 1278.25 mm
also aligns their attachments with the first upper-panel principal row.
The upper top-rail attachments remain at 2419.35 mm, 65.95 mm above the fixed
fourth upper principal/rim row at 2353.4 mm. Making that final row inline would
require reconsidering the top receiver/support geometry or moving the fixed
principal row; it is not an isolated attachment adjustment.

Across the horizontal panel seam, the nearest principal attachment rows are
144.05 mm apart, with 85 mm below and 59.05 mm above the seam. The moved service
rails have 105.95 mm between their nearest timber faces. Horizontal panel-edge
offsets of 19.05 mm at the outer rim and 70 mm at the center reflect the existing
receivers and open center service corridor. The nearest main attachment to a
hold/LED axis is 35.255 mm, between `round_panel_lower_left_service_2` and `B6`;
this planar distance alone does not establish assembled clearance or strength.

## Kicker panels

The 60 and 140 mm rows have an 80 mm pitch. On the 225 mm-high kicker they leave
60 mm below and 85 mm above, placing the pattern center 12.5 mm below the panel
center. All kicker columns still share the same two heights and mirror exactly
left/right. The upper row has 46.9 mm to the post end at 186.9 mm.

A possible comparison would retain the lower row at 60 mm and raise the upper
row to 165 mm. This would give equal 60 mm panel-edge offsets, but reduce the
upper attachment's post-end distance to 21.9 mm. Alternatively, moving both
rows to 72.5 and 152.5 mm would center the existing 80 mm pitch while leaving
34.4 mm to the post end. Neither option has been qualified or selected.

The current 140 mm upper row retains an end distance consistent with the
historical SPAX spacing screen. That screw-specific allowance does not establish
an acceptable end distance for the modeled inserts. Any kicker revision needs
insert-specific resistance and end-distance evidence, along with fresh receiver,
hardware and hold-clearance checks.

The current pattern is regular within the retained framing and fixed upper
principal row. Further visual symmetry is possible in the kicker, but its
tradeoff is reduced receiver end distance, not a demonstrated structural
improvement.
