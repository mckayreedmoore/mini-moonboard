# Complete right five-body source boundary

**Checked:** October 1, 2026. **Disposition:** reconstruction of the complete
modeled interface boundary passes for the three frozen conditional rear
responses. Resistance, local sections, gravity/event history and six-case
joint acceptance remain open.

## Scope and method

This extends the reviewed
[right bolt/receiver join](../right-corner-signed-load-path-2026-10-01/README.md)
beyond its six bolt axes. The five bodies are `base_header`,
`base_post_outer_right`, `base_side_right`, `knee_outer_right_spine` and
`knee_outer_right_inner_frame_block`. The shared header is included as a whole
body: its connections to the opposite side are boundary ports, not discarded
because they lie outside the right knee. This is the complete source boundary
of that five-body set, not the complete frame or a finished-section stress
solution.

[The producer](produce.py) authenticates the reviewed right-join method and
calls its source checks for all A1/A12/K12 model, deck, DAT, response,
all-body audit and terminal pins. It preserves the candidate
`compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`, without any new native run or
reviewed-model change. It reuses only the generic endpoint/floor adapter and
body-balance functions from the pinned
[existing demand exporter](../mvp-acceleration-2026-09-28/current-corner-native-demand-export-attempt03/produce.py).
It does not reuse the left corner's contract, body set, forces or capacities.
The [source-method trace](source-method-trace.md) records the independent
inventory and source-field check.

Every original carrier whose named endpoint is in the five-body set is
selected, then grouped by its physical source connection name. Two transverse
spring components become one plane force, and two floor tangent channels
become one floor interface; they are not separately added again. Normal
contacts, both outer bolt seats, retained frame bolts, panel screw actions
and adjoining members remain present. For floor tangents, the pinned adapter
requires exactly one selected or released state, both local channels, correct
source directions/points and the released-zero provenance checks.

The reporting datum for each body is independently calculated from its
source descriptor start/end midpoint and compared to the all-body audit's
reference. Endpoint actions and the source nodal loads are summed there.
Every newly calculated body residual and RF-rounding radius is compared to
the pinned all-body audit. The physical response limits remain **0.1 N and
2 Nmm**, including both raw and interval gates. Separate arithmetic matching
limits of `1e-8 N` and `1e-6 Nmm` do not replace or expand those gates.
DAT files are authenticated, but this packet does not independently parse
their RF tokens or establish a new response acceptance.

For assembly accounting, all point forces and nodal-load resultants are
transported to global origin. The sum of boundary actions and external loads
must reproduce the five source body residuals transported to that same
origin. Internal action pairs cancel in that sum, while their individual
receiver actions remain in the retained output for downstream checks. A
transported couple is not internal bolt bending or a local stress bound.

## Observed results

Each case has **392 original scalar carrier rows grouped into 338 physical
interfaces: 42 internal and 296 boundary**. There are **62 boundary port
groups** by member, external receiver and role. Seven states per case give
21 assembly states and 105 individually checked body states.

| Case | Selected floor tangent groups per state | Released groups per state | Interface/body checks |
| --- | ---: | ---: | --- |
| A1 rear | 2 | 2 | Pass at all seven states |
| A12 rear | 2 | 2 | Pass at all seven states |
| K12 rear | 0 | 4 | Pass at all seven states |

Across all 105 body states, the largest raw force residual component is
`0.000218 N`; the largest raw moment residual component is
`0.295190104 Nmm`. Their source rounding radii and interval checks are
retained. Internal force cancellation discrepancy is zero; internal couple
discrepancy is at most `3.63798e-12 Nmm`. Assembly reconstruction differs
from transported source body residuals by at most `1.39622e-12 N` and
`1.92954e-9 Nmm`. These discrepancies are arithmetic checks, not a new
assembly acceptance tolerance.

The boundary retains timber/panel contacts, candidate and retained bolt
planes, outer-seat ties, panel screw planes, conditional screw-withdrawal
carriers, floor normals and selected/released no-slip tangents. The source
withdrawal role remains `non_qualifying_parametric_screw_withdrawal`; retaining
its force does not establish Hillman capacity or stiffness. Likewise, the
floor state is the frozen conditional response's state, not a newly proved
gravity-settled/event-history solution.

The five-body group's full-load source nodal load is approximately
`(0,0,-296.838696) N` with moment about global origin
`(-117383.937729,+255220.213510,0) Nmm`. The boundary net balances this
resultant within the preserved body residuals. That net can hide large
opposing joint forces and cannot be substituted for individual port, bolt,
receiver or section actions.

## Validation and reproduction

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/right-corner-whole-boundary-2026-10-01/produce.py --check > /tmp/right-corner-whole-boundary.json
```

The parent run returned exit zero; the force/couple transport oracle and
all source joins/body comparisons pass. Ruff passes. The
[independent review](independent-review.md) records a separate source-endpoint
replay and its limits. Raw interface/action output stays local. Publication
contains code and summaries only.

| Record | SHA-256 |
| --- | --- |
| Producer | `c4547fd3186aff6a59bac032428c42bbbc2e8e8e6f8a144559ad7bc2ffa422b7` |
| Parent raw output | `56463f3c6a49a89cf937fe95eced068b4938de4cdf42d66ca487b63a67057f0f` |
| Reused right-join method | `13989f42845210caadb15c1cf3903a47c2634b866195dc0c5f2156ea9605f2ea` |
| Reused generic export helper | `0e6aa1b0ec50e3137d2f431f79365de899d109a5d5c61d37de344c9596681fe8` |

No strength, combined interaction, finished-section demand, criterion pass,
joint acceptance, physical inspection, fabrication permission or climbing
release follows from this boundary reconstruction.
