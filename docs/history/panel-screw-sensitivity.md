# Panel screw count sensitivity

The 75-screw candidate removes 12 of the 87 panel/kicker screws, retains every
original screw axis, and selects existing infill axes to keep center-principal
spacing at most 300 mm. This is a test candidate, not an approved drilling change.

Nine new native solves provide six matched comparisons: F10, C6 and C10 against
the preserved full-87 baseline, plus new full-87/reduced-75 controls for each
synthetically mirrored load. All numerical equilibrium, interpolation and
compression-only bearing checks passed. The pattern has a small effect on
maximum displacement but a material effect on the critical F10 screw demand.

| Load probe | Maximum panel displacement, 87 → 75 screws (mm) | Maximum screw withdrawal, 87 → 75 (N) | Maximum screw lateral demand, 87 → 75 (N) |
| --- | --- | --- | --- |
| F10 | 21.811 → 22.162 | 1,064 → 1,277 | 537 → 628 |
| Mirrored F10 | 21.516 → 21.700 | 767 → 887 | 432 → 483 |
| C6 | 14.030 → 14.110 | 962 → 963 | 439 → 462 |
| Mirrored C6 | 13.762 → 13.833 | 976 → 978 | 441 → 465 |
| C10 | 16.273 → 16.331 | 418 → 418 | 510 → 511 |
| Mirrored C10 | 16.190 → 16.235 | 413 → 412 | 511 → 511 |

The maxima in different columns need not belong to the same screw. F10's peak
withdrawal remains at `timber_panel_upper_left_8`: 1,064.4 → 1,277.2 N, a 20.0%
increase while maximum panel movement increases 1.61%. Thus low displacement
sensitivity does not establish that the removed screws were redundant. The
[existing signed fastener screen](../fea/results/horizontal-panel-fastener-screen-v1.json) already
leaves withdrawal, head pull-through and combined action unresolved.

These probes do not establish that 87 screws, 75 screws, or more than 12 screws
per face panel are required. The practical next step is a direct comparison of
the proposed 12-per-panel layout and a review of the load and contact assumptions.
Retaining 87 does not establish adequacy either. A recommendation to add hardware
requires connection evidence beyond these provisional spring demands.

## Method and evidence

[Runner](../fea/panel_screw_sensitivity.py) reconstructs the frozen parent input.
Before any modification, its complete native deck must exactly reproduce the
parent deck. Reduction deletes only the named three-direction panel screw spring
triplets. Physical elements, mesh, loads, constraints, interpolation equations
and all retained spring properties stay identical. Bearing active sets are solved
afresh. [Comparison](../fea/panel_screw_comparison.py) checks those invariants,
replays native DAT forces and gates, authenticates input artifacts and matches
connection axes against the published export manifest and parent geometry sources.

Mirrored probes reflect the load point, force and moment onto the opposite panel;
self-weight remains unchanged. Exact subcell integration supplies consistent S8
tractions on the unchanged opposite-panel mesh. These coordinates need not
coincide with named hold holes. They address unilateral sampling bias, not all
right-side load positions; local patch stresses are not a mesh convergence study.

There is no distributed panel-to-timber compression contact: both compressive
and tensile panel support acts through discrete screw springs. That omission
can change local prying and load sharing; it is not a demonstrated conservative
bound on every screw demand.

Assumptions remain E=7,000 MPa, ν=.3, equal 1,000 N/mm directional connector
springs, rigid bracket bodies, clamped feet, 250-lb user load with the existing
dynamic multiplier, and the original 20-mm patch/standoff wrench. No new
material, joint, whole-frame or floor acceptance follows. The later round-service
bore geometry has a different retained section and requires its own analysis.

Raw new cases and comparisons are archived in
[panel-screw-sensitivity-v1.tar.xz](../fea/results/panel-screw-sensitivity-v1.tar.xz).
Original full-87 parents remain in
[horizontal-frame-batch-v2.tar.xz](../fea/results/horizontal-frame-batch-v2.tar.xz).
All result qualification and removal-approval flags remain false.

Light verification covers exact spring-only deletion, signed partial-cell loads,
mirrored wrench and gravity preservation, native deck reproduction, unchanged
load/spring rejection, and the difference between small movement changes and
increased fastener demand.

The authoritative aggregate is `comparisons/summary.json` in the new archive;
its six `comparisons/*.json` files contain every screw's signed demands. After
extracting both archives, replay one comparison with:

```sh
uv run python -m fea.panel_screw_comparison \
  --full /path/to/original-batch/f10-k1000 \
  --reduced /path/to/sensitivity/f10-reduced \
  --connections /path/to/sensitivity/comparison_sources/exports/horizontal-service-development/connections.csv \
  --output /tmp/f10-screw-comparison.json
uv run pytest tests/test_panel_screw_sensitivity.py tests/test_panel_screw_comparison.py -q
```

The tests using expanded local evidence skip when those generated directories
are absent; the analytical partial-cell test still runs. Archive replay therefore
provides the explicit numerical-evidence check after extraction.
