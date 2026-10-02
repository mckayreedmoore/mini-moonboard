# Panel screw force direction and recorded load basis

The owner questioned the withdrawal result on October 2, 2026, using the
[linked Mini MoonBoard assembly video at 1:39](https://www.youtube.com/watch?v=wDB6Lg4x_lM&t=99s)
and describing four screws per panel edge with shared corner screws.
The next comparison is mounting and load-sharing fidelity before selection
of a hardware correction. This record does not change the reviewed axes.

## What withdrawal means

Withdrawal is axial loading that tends to separate the panel from its timber
backing, in the direction from the screw tip toward the head. The thread can
withdraw from the timber, or the head can pull through the panel; those are
different resistance checks. Lateral loading acts along the panel face.

The modeled panel tangent is `(0, cos(50 degrees), sin(50 degrees))`.
Its outward normal is `(0, sin(50 degrees), -cos(50 degrees))`, approximately
`(0, 0.7660444431, -0.6427876097)`. Downward gravity therefore has a positive
outward component on this overhanging face. The screw reaction restrains the
panel inward; ordinary compression contact between the panel and backing
cannot provide that inward restraint.

## Recorded load arithmetic

The frozen input is
[`model-inputs.json`](../../mvp-acceleration-2026-09-28/reduced-static-attempt01/model-inputs.json),
SHA-256 `178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9`.
Each `cases[].source_applied_load` records a 250 lb climber, dynamic factor
2.0, downward force 2224.11080763025 N and a separate 300 N horizontal force.
Its application point is 100 mm outward from the hold patch center.

Dotting each recorded applied force with the outward normal gives:

| Case | Horizontal force, global XYZ, N | Climber-force outward projection, N |
| --- | --- | ---: |
| A12-rear | `(0, 300, 0)` | 1659.444203 |
| A12-forward | `(0, -300, 0)` | 1199.817537 |
| A12-left | `(-300, 0, 0)` | 1429.630870 |
| K12-right | `(300, 0, 0)` | 1429.630870 |
| K12-rear | `(0, 300, 0)` | 1659.444203 |
| A1-rear | `(0, 300, 0)` | 1659.444203 |

These are projections of the climber force alone, before panel dead load and
the contact/screw force allocation. They are not individual screw demands or
a resistance result. The current frame producer combines its dead-load
column times 1.1111358300342407 with one recorded climber-load column. It
does not apply another 2x multiplier to that climber column. Earlier worker
studies with additional proportional scaling retain their separate scope.

## What the current numerical result establishes

The current comparison is
[`two-receiver-frame-attempt03/comparison.json`](../two-receiver-frame-attempt03/comparison.json),
SHA-256 `0ff0dfc00c112a906910641141fd242f4a58295aa3324ca569132a3fa2d388a5`;
its response SHA-256 is
`774c3bbddf8061f6b9d1cfdd5f22efbeb1025bd57431a249912ae8e60a731f52`.
It explicitly records `product_laws_measured: false`: all 66 axial and 132
lateral screw components use the same assumed 2689.678816784642 N/mm law.

The saved screw demands exceed the worksheet's declared generic references.
That is a conditional model/reference exceedance. There has been no physical
panel test, measured Hillman failure load or demonstrated unsafe verdict.
An individual force can exceed the free-load normal projection because local
compression and screw tension can form a prying couple. Whether the model
represents that sharing accurately remains a question about the mounting,
backing, contact, panel compliance and screw laws.

The [mounting-pattern comparison](official-pattern-comparison.md) therefore
comes before treating a keeper or replacement screw as necessary. Moon's
[written build guide](https://us.moonclimbing.com/blogs/guides/how-to-build-your-moonboard)
also specifies horizontal bracing across panel joints; screw count alone
does not describe the backing/load path. The video fetch did not return
playback, so the shared-corner pattern here remains the owner's observation.
