# Saved frame rank and clearance seating assessment

The current proposal has a supported result for the recorded rank criterion and
for finite seating freedom at fixed forces. All six zero-clearance states have
rank 300. All six nominal-clearance states fail that strict criterion, with rank
296 or 297, but their fixed-force seating sets remain bounded under the recorded
no-slip floor and circular clearance laws. Rank failure alone therefore does
not establish physical instability or a required geometry change.

This assessment uses the fresh proposal gravity operators and the saved six-case
response. It preserves the 250 lb × 2 climber force, signed 300 N horizontal
force, original 100 mm hold lever, frame gravity and 25 kg equipment allowance.
The global operator still has 104 bolt axes; the four proposed internal knee
ties have their separate static allocation. They do not acquire global elastic
stiffness from this postprocessing.

## Numerical results

The translation values below are conservative norm bounds on each body's rigid
translation coordinates, reported at the model's representative body datum.
They include the saved representative rigid pose and the certified seating
increments. They are not total elastic panel/member deflections, measured build
movement, or a comparison against an adopted serviceability limit.

| Case | Zero-clearance rank | Nominal-clearance rank | Largest zero-clearance rigid translation, mm | Nominal rigid translation outer bound, mm |
| --- | ---: | ---: | ---: | ---: |
| A12 rear | 300 | 296 | 3.841708 | 6.908433 |
| A12 forward | 300 | 296 | 2.934116 | 5.699697 |
| A12 left | 300 | 297 | 4.096779 | 7.197814 |
| K12 right | 300 | 297 | 4.290616 | 7.321272 |
| K12 rear | 300 | 296 | 4.129908 | 7.180716 |
| A1 rear | 300 | 296 | 1.740138 | 3.980563 |

The largest nominal bound occurs at `top_center_left_cleat` in K12 right.
Each component is bounded over an enclosing box in the certified null
coordinates. Box vertices need not be compatible points in the original
circular clearance disks, so the tabulated norm is an outer bound, not an
attainable maximum. The raw record also includes all 50 bodies' translation
and rotation component intervals for each of the 12 states.

## Method and scope

[frame-stability.py](frame-stability.py) reuses the pinned
`bounded_clearance.finite_clearance_certificate` method. It recovers the 1,612
lumped force coordinates from the 1,888 raw rows, checks the full signed body
wrenches and saved pose/compliance identity, retains all eight floor footprints
and 88 clearance planes, and reproduces the saved active-tangent rank/nullity.
No frame forces, floor/contact branch, geometry, stiffness or acceptance
threshold is changed. The zero-clearance results preserve their original
rank-300 classification and have no extra seating increment.

The first-order force model has no inertia, geometric stiffness or dynamic
history. A doubled force envelope does not establish those omitted behaviors.
The bounded seating result does not close simultaneous local joint elastic
compatibility, actual changed-hole stiffness, or complete joint resistance.
Those remain distinct numerical obligations in the whole-model assessment.

## Frozen result and provenance

Parent executed `rawlocal/frame-stability/attempt01` in the shared serialized
analysis slot, with the recorded single-thread numerical runtime. The result is
`COMPLETE_SAVED_RANK_AND_FIXED_FORCE_RIGID_SEATING_ASSESSMENT`: 12 states,
six strict rank-300 failures, and six bounded nominal seating certificates.
All 392 source pins and three receipt-bound outputs match.

- Receipt SHA256: `08389aeb240e3b8cba7f140689c1e056fb8b132a535fdc242b0d408844975873`.
- Gravity assessment SHA256: `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95`.
- Frame comparison SHA256: `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729`.
- Response SHA256: `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90`.

A later accidental overwrite of an upstream washer receipt was preserved and
recovered byte-for-byte from the verified external evidence archive. Its
original SHA256 `041067657335395f4b1723a237e11574a0ed0b3efcba4e95f32e25db77d3630f`
and the complete stability source/output closure were rechecked after recovery.
No numerical result or source pin was regenerated to accommodate that overwrite.

The 108-axis proposal remains unadopted. Formal authority, fabrication and
climbing release remain unchanged.
