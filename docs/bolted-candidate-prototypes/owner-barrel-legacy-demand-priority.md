# Historical angle actions: barrel-study priority only

The [reproducible extraction](../../scripts/owner_barrel_legacy_demand_priority.py)
maps all 24 selected-baseline ML24Z stations and six audited no-slip cases to
the twelve current barrel-viewer duty families. It checks all 144 station-case
and 288 flange-case records, reconstructs each reported vector norm, and
retains the source hash. Its input is the **old bracket model**, not a barrel
joint-force solve. No action or capacity here is adopted for construction.

| Family | Largest old flange force | Largest old flange moment |
| --- | ---: | ---: |
| top outer | 1,186.59 N | 15,242.05 N·mm |
| outer base/side | 733.26 N | 19,818.08 N·mm |
| outer header/post | 598.66 N | 12,017.53 N·mm |
| bottom outer | 595.43 N | 18,805.16 N·mm |
| upper outer | 70.16 N | 15,742.57 N·mm |

The force and moment maxima in a row may come from **different** cases or
flanges. In particular, low old force does not mean the upper-outer moment
can be ignored. This comparison favors early *changed-topology* analysis of
the top-outer and outer-base duties, while keeping bottom/upper-outer moment
transfer and the conditional recessed outer-header detail in view. It does
not prescribe a barrel proof load or let the original angle's stiffness,
contact, forces, or pass flags migrate to the new frame.

The next structural step, after viable geometry and identified hardware,
is a barrel-only whole-frame force solve under the required cases. That solve
must report simultaneous force and moment transfer at each actual interface,
including wood contact, bolt axial/lateral action, barrel reaction, and
backer/retained-bolt actions. Separate bolt, barrel, thread, wood bearing,
tear-out/splitting, washer-seat, group, member and frame checks must then use
those same-case actions. The current viewer and this priority table release
no drilling, fabrication, or climbing.
