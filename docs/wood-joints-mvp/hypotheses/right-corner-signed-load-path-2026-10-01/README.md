# Right outer-knee simultaneous bolt and receiver actions

**Checked:** October 1, 2026. **Disposition:** source join and internal
force/couple bookkeeping pass. Complete right-corner resistance, all-body
boundary transfer and six-case acceptance remain open.

## Coverage and source boundary

This packet fills the right-side counterpart of the left corner signed
register (local `current-corner-complete-resistance-register-attempt01/`,
pending its owner's publication). The published
[left corner demand export](../mvp-acceleration-2026-09-28/current-corner-native-demand-export-attempt03/README.md)
summarizes that source recovery.
It uses the right assembly's actual existing response records rather than
reflecting left-side forces or transferring a left-side pass. The candidate
is `compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`. It preserves the reviewed model,
all 92 new bolt axes, twelve retained frame stacks and 66 Hillman screws.

Six `knee_outer_right` post/side/header axes and eight lateral planes cover
the post/spine, spine/side/inner-block and inner-block/header bolt families.
Their receivers are `base_post_outer_right`, `knee_outer_right_spine`,
`base_side_right`, `knee_outer_right_inner_frame_block` and the shared
`base_header`. The eight upper blocks/32 upper axes are excluded.
No right-side BG identifiers are invented. The
[source trace](source-trace.md) records exact source rows, plane numbers,
receiver order, endpoint coordinates and case hashes.

The existing A1-rear, A12-rear and K12-rear all-body response freezes supply
seven states each, at load factors 0.1, 0.2, 0.3, 0.45, 0.675, 0.925 and 1.0.
They are authenticated conditional response histories, not a complete
six-case envelope or established gravity/event-history solution. No response
or native solver is produced here.

## What the checker reconstructs

[The producer](produce.py) authenticates the reused source checker, complete
three-case freeze, acceptance register, all-body audits, source decks/DATs,
case/revision identities and geometry input pins. It requires the original
increment response gates and body raw/interval balance gates. It joins
every selected axis to the actual ordered wood receivers and outer head/nut
seats, then verifies each lateral plane lies at the matching wood interface.

For each plane, the two saved SPRING2 local RF components are independently
recombined through the source force-basis rows. Endpoint RF signs,
equal/opposite actions, source element/inventory identities, local DOFs,
bilateral law gates and propagated force-rounding radii must agree with the
exported global vector. The separate end-to-end SPRINGA tie is checked
against its tension-only source binding and physical outer-seat endpoints.
The producer does not independently parse the native DAT tokens; it pins
those files and checks their already recovered component records.

The side bolts each have three receivers, two lateral planes and one
end-to-end tie. These remain one physical bolt per axis. The side receiver's
two opposite-interface actions are summed simultaneously; the tie is added
once at each physical outer seat, with no invented middle washer or nut.

Every bolt's fixed wrench reference is its source **head-seat point**. For
each receiver, the producer retains `F = sum(F_i)` and
`M = sum((p_i − reference) × F_i)`, together with the contributing endpoint
actions and coordinate-component rounding radii. This is transport of point
forces to a common datum. It does not create an endpoint free couple or
identify an internal steel bending moment. Radii account for the saved RF
precision at fixed source coordinates, not fabrication or physical tolerance.

## Three-case results

Coverage is **126 physical-bolt states, 168 lateral-plane states and 294
receiver wrenches**. Internal equal/opposite actions cancel over each bolt's
receivers: maximum component discrepancy is `2.264855e-14 N` and
`9.094947e-13 Nmm`. These are arithmetic reconstruction checks, not widened
physical equilibrium tolerances.

Each plane peak below is at K12-rear full load. The vectors act on the first
receiver named in the source trace. Tiny numerical components are omitted.
The axial tie belongs to that same bolt and state; it is not combined with
an independently governing tie peak.

| Axis suffix / plane | Force on first receiver `(Fx,Fy,Fz)` N | Lateral resultant N | Same-state axial tie N |
| --- | --- | ---: | ---: |
| `inner_header_1` / 41 | `(+90.915,-13.359,0)` | 91.891 | 118.446 |
| `inner_header_2` / 42 | `(-22.706,+5.063,0)` | 23.264 | 19.341 |
| `post_1` / 43 | `(0,-149.740,-255.678)` | 296.299 | 60.318 |
| `post_2` / 44 | `(0,+208.352,-253.298)` | 327.980 | 19.190 |
| `side_1` / 45 | `(0,-284.861,+380.620)` | 475.413 | 98.179 |
| `side_1` / 46 | `(0,-3.405,-63.648)` | 63.739 | 98.179 |
| `side_2` / 47 | `(0,+226.249,-59.327)` | 233.898 | 47.093 |
| `side_2` / 48 | `(0,+21.827,-85.301)` | 88.050 | 47.093 |

The largest source tie is **118.4459 N**, `inner_header_1` at K12 full load.
The largest selected per-bolt receiver force and transported couple occur
simultaneously on `base_side_right`, `side_1`, at K12 full load:
`F = (0,+281.455314,−444.268160) N`, magnitude **525.919473 N**;
`M = (0,−22584.938320,−10420.708648) Nmm`, magnitude **24873.090030 Nmm**.
These values are about that bolt's head-seat datum and include both lateral
interfaces. They are not a whole-member section demand, local bearing peak,
splitting demand or bolt internal-bending bound.

## Reproduction and independent review

From the repository root in the existing environment:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/right-corner-signed-load-path-2026-10-01/produce.py --check > /tmp/right-corner-signed-actions.json
.venv/bin/python docs/wood-joints-mvp/hypotheses/right-corner-signed-load-path-2026-10-01/produce.py --check --rejection-checks
```

The parent run returned exit zero. Independent force/couple and datum-shift
known answers pass; five deliberately corrupted plane records are rejected,
covering first-force sign, reaction sign, nonfinite force, source row and
rounding radius. Ruff passes. The
[independent review](independent-review.md) checks the source reconstruction
and scope. Raw output remains local; publication includes code and summaries.

| Record | SHA-256 |
| --- | --- |
| Producer | `13989f42845210caadb15c1cf3903a47c2634b866195dc0c5f2156ea9605f2ea` |
| Parent raw output | `48b68ab78d24febd79cb2e12bbec761209c6c1ac6fffa24075c22bbbcac12cbf` |
| Reused signed-tie source checker | `0c58a7dc6c82ccc2624ee9d3355e2840f738be01961ddaf3f64486700e89e6c9` |
| Existing three-case freeze | `d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73` |

## Remaining joint work

This packet supplies right-side simultaneous bolt/receiver actions for
applicable resistance and transfer calculations. It does not include every
surrounding timber contact, panel/retained-frame port or external load;
therefore it is not the complete five-body boundary or a member-section
equilibrium calculation. Complete joints still require applicable bearing,
continuous three-receiver bolt response, steel/shank/thread interaction,
washer contact and resistance, shared timber/group behavior, detailing,
splitting/tear-out and onward transfers under the full case envelope.

Missing right-side results cannot be replaced by the left-side register's
capacity or demand. The original LEG/runner work is preserved for applicable
reuse. No criterion, hardware fit, physical inspection, fabrication or
climbing release is established here.
