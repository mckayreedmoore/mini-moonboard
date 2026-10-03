# Lower-left panel contact and screw sharing

Completed saved-result accounting, 2026-10-02. This compares A1-rear at
modeled bolt clearances in the twelve-screw and hypothetical twenty-screw
**width-grain** packets. No new load allocation, solve, geometry or hardware
change is made. Both results retain conditional panel and screw properties.

**The increase is a change of peak screw and a larger local compression/tension
couple, not an increase in external load.** The original peak screw falls from
1213.615 to 448.541 N. A newly added bottom-rail screw becomes the peak at
2180.721 N. The saved equations balance, but this does not establish physical
Hillman stiffness, continuous contact pressure or assembly capacity.

## Same load, different local reactions

The six-component external panel wrench is identical in both packets. The
climber action is 2224.111 N downward plus 300 N rearward at hold A1, with the
same 100 mm outward hold lever. Including the panel's assigned dead load, the
global force is `[0, 300, -2404.641]` N. Its outward panel-normal component is
1775.487 N. It is applied at one hold; this accounting changes no load split.

| Quantity | Twelve screws | Twenty screws |
| --- | ---: | ---: |
| Peak screw axial tension, N | 1213.615 | 2180.721 |
| Original `round_panel_lower_left_edge_2` tension, N | 1213.615 | 448.541 |
| Peak screw X station, mm | -835.075 | -1017.6125 |
| Modeled separation at peak screw, mm | 0.451212 | 0.810774 |
| Sum of all panel screw tensions, N | 4036.845 | 5112.820 |
| **Signed net** outward normal reaction from all contacts, N | 2261.358 | 3337.334 |
| Bottom-rail compression scalar sum, N | 1317.279 | 2691.586 |

The new peak is `hyp20_main_lower_left_edge_gap_1`; hold A1 is at
X = -1019.2 mm, only 1.5875 mm away across width. The contact reactions may
increase both local tension and compression while preserving net balance:
`4036.845 - 2261.358 = 5112.820 - 3337.334 = 1775.487 N`.
This is not a force-per-screw equal-sharing calculation.

### Hold location relative to the bottom rail

The saved A1 patch center is **T=299.824134 mm** along the board slope. The
bottom-rail screw line is **T=336.574134 mm**, 36.75 mm above the hold.
The rail's front support band is **T=317.524134–355.624134 mm**. Thus the hold
center is 17.7 mm below that band; the entire modeled 20 mm patch is below it,
with its upper edge 7.7 mm short of the rail. The panel outline begins at
T=200.624134 mm. This is a local overhang below the bottom rail, not an applied
load centered over that horizontal backing.

The 100 mm front-face lever and dynamic single-hold force therefore act near
a short support offset as well as near the new screw's X station. The side
members, kicker contacts and other screws still participate; these distances
do not assign the whole hold force or moment to one bolt/contact couple.
They are specific saved load/backing features to compare with an intended
installation. No hidden framing location is inferred from the owner's video
or front screenshot, and no physical frame alteration is made here.

Contact sums must retain signs and directions. Summing only outward normal
contacts gives 2532.131/3549.907 N; those are not the signed totals above.
Kicker-edge contacts include other directions. Their complete contributions
are retained in the wrench accounting rather than silently discarded.

## Full signed panel wrench balance

All forces below act **on the panel**. Moments use the saved rigid datum
`[-675.761235, 328.792727, 704.093666]` mm. The table rounds forces to 0.001 N
and moments to 0.001 N m; raw output retains full N/N mm precision.

| Packet / action | Fx, N | Fy, N | Fz, N | Mx, N m | My, N m | Mz, N m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| External, either | 0 | 300.000 | -2404.641 | 576.480 | -751.763 | -103.032 |
| Twelve: screw lateral reactions | 0 | 933.312 | 1112.278 | -13.254 | 380.083 | -318.927 |
| Twelve: all panel contacts | 0 | 1859.090 | -1302.471 | 619.541 | -23.315 | -48.778 |
| Twelve: screw axial reactions | 0 | -3092.402 | 2594.834 | -1182.767 | 394.995 | 470.737 |
| Twenty: screw lateral reactions | 0 | 995.105 | 1185.920 | -14.131 | 414.146 | -347.510 |
| Twenty: all panel contacts | 0 | 2621.543 | -2067.736 | 1045.033 | -316.372 | -328.852 |
| Twenty: screw axial reactions | 0 | -3916.647 | 3286.457 | -1607.381 | 653.989 | 779.394 |

External plus all reactions balances within 4.84e-12 N and 2.80e-9 N mm.
Both panel-to-panel seams have zero compression in this case. Kicker-edge
contacts remain included. There is no hidden added external force or moment.
Shared source rows, ownership, locations and spring laws are byte-equivalent
as parsed records. The common H block differs by at most
3.403e-13 mm/N after the separate width-grain reprojections; a changed old-row
compliance is not the explanation for this peak shift.

## Local opposing contact and levers

For the original twelve-screw peak, the nearest active opposing bottom-rail
contact is `contact_59_14`: compression 440.193 N, offset from the screw
`[+36.471 X, +9.612 T]` mm, in-plane distance 37.716 mm. The strongest
bottom-rail contact is another cell, `contact_59_6`, at 473.921 N.

For the twenty-screw peak:

| Nearby bottom-rail cell | Compression, N | X/T offset from peak, mm | State |
| --- | ---: | --- | --- |
| `contact_59_18` | 0 | +29.301 / +9.525 | Open; modeled closure coordinate -0.442075 mm |
| `contact_59_19` | 0 | +29.301 / -9.525 | Open; modeled closure coordinate -0.638996 mm |
| `contact_59_20` | 1488.348 | -65.358 / +9.525 | Bearing; closure 0.008254 mm |
| `contact_59_21` | 0 | -65.358 / -9.525 | Open; modeled closure coordinate -0.125516 mm |

The closest **active** opposing cell is therefore `contact_59_20`, 66.048 mm
away in the panel plane. It is also the strongest bottom-rail cell. These are
geometric diagnostics; the 1488 N cell is not assigned as the sole balancing
partner for the 2181 N screw. The full panel's screws, contacts and moments
all participate. Physical contact may distribute within a cell differently
from this sampled representation.

## Exact response assumptions implicated

- **Sampled opposed-face contact:** bottom-rail patch 59 has source area
  39594.656 mm² and 22 cells, arranged at eleven X stations and two transverse
  stations. Regular X spacing is approximately 94.659 mm; transverse cell
  centroids lie approximately ±9.525 mm from the screw row. Forces are
  transferred at saved cell attachment points, not an independently solved
  continuous pressure field. Six cells bear in the twelve-screw result and
  eight in the twenty-screw result. The closest cells opening while a farther
  cell bears is a specific contact-distribution assumption to examine.
- **Compression-only numerical penalty:** saved source scenario uses
  100 N/mm³ times cell area, with no contact tension. `contact_59_20` has area
  1803.256 mm² and stiffness 180325.568 N/mm. Its 1488.348 N corresponds to
  0.008254 mm numerical closure and model cell-average pressure 0.825367 MPa.
  Those quantities do not establish physical indentation or bearing capacity.
- **Unmeasured axial screw law:** every modeled screw uses
  `T = 2689.678817 × max(opening, 0)` N. The source sets axial/lateral
  stiffness ratio to 1.0 and explicitly says physical Hillman bounds are
  unestablished. The new peak's 0.810774 mm opening produces 2180.721 N by
  that law; this is not a manufacturer screw test or a failure load.
- **Elastic compatibility and load lever:** width-grain equivalent-layer
  plywood and receiver timber remain flexible. The added station is almost
  horizontally aligned with A1 and changes compatibility there. Existing
  panel properties, transverse proxies, full single-hold action and 100 mm
  lever remain conditional inputs. High self-equilibrating local reactions
  are consistent with prying in those inputs; this accounting does not prove
  which assumption dominates the actual build.

The finite mechanics question is whether the existing contact sampling,
penalty and screw force-slip law represent this local attachment sufficiently
well to use its peak as a demand. Preserve these exact reactions while
answering that question. This result supplies no alternate force allocation,
rigid-panel substitution, required redesign or new release gate.

The subsequent [saved-displacement recovery](contact-gap-recovery.md)
reproduces all original patch59 closure coordinates within 1.42e-10 mm.
Additional half-spacing samples find maximum closures of 0.044593 mm
with twelve screws and 0.010851 mm with twenty. Their largest witnesses
are 266–361 mm in X from the added peak screw; the nearest half-spacing
samples remain open. This identifies contact-sampling sensitivity, but
does not explain the concentrated screw force or supply a corrected
allocation. Saved representative poses do not establish a gap envelope.

The [subsequent area-preserving refinement](patch-contact-refinement.md)
replaces patch59's 22 samples with 44 and resolves the same A1 nominal
state under unchanged laws. Peak screw T changes by -0.271% for twelve
screws and -1.245% for twenty; the governing axes stay the same. Additional
positive closure remains in the refined recovered fields. Thus this one
sampling change does not explain the full peak demand or establish a
continuous-contact solution. The complete source responses remain frozen.

## Source pins and reproducibility

| Saved packet | Comparison SHA-256 | Response SHA-256 |
| --- | --- | --- |
| `panel-width-frame-250-attempt05-conic` | `5a49b2076e0e32e5fbae90b1da41be6b77973da9057aee860acebaee9cef05f0` | `ff54c8f662bce93e03b46e47b088408c82471c5956b824e3320afb32b79919ef` |
| `count20-width-grain-frame-attempt01` | `0a8bcf1ac6679d970d72e11e652d31e3406607699230bcf9915bb009e34e9b88` | `8271a9e6c3ff15440703f78b704e6f601a545b538611c09009afdeb77393eb7c` |

Producer [panel-contact-sharing.py](panel-contact-sharing.py), SHA-256
`8fd353bb515ef4b453bb2dbf820e087c506a46f5356b5fbcf0ffb28053c3e62f`.
Completed output `rawlocal/panel-contact-sharing/attempt02/result.json`, SHA-256
`09f2d21a5407615bd620644d65095eb534401902677b481604d2718a155032f5`.
All signed scalar-row actions are in the neighboring `signed-panel-actions.csv`,
SHA-256 `2dad908a379b74bf8078930405c171b016646a0a9eb10e8d33238ffad823d3b1`.
The output also pins both operator assessments, H/D/e/W files, row identities,
model inputs, models, the source carrier/contact cells and source contact patches.
The first arithmetic output is preserved; attempt02 additionally records open
nearest cells and signed normal totals.

From the repository root, use a fresh ignored child:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/panel-contact-sharing.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/panel-contact-sharing/attempt03
```

This reads saved arrays and performs wrench/row arithmetic only. No CAD,
native/frame solve, software test, independent review, staging or commit was
performed by this worker. Parent owns model selection and publication.
