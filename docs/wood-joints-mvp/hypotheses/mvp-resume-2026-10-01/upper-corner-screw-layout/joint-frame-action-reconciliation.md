# Coupled-frame action reconciliation

The [adapter](joint-frame-action-reconciliation.py) exports physical body actions
from an authenticated coupled response's actually accepted states. It performs saved-array
postprocessing only. It does not run a source pipeline, solve an equilibrium
system, rebuild CAD, compute resistance or select a candidate. The response
remains a separate **reviewed104 coupled-knee sensitivity** until its force
joins and affected resistance comparisons are complete.

The consumed preparation and reduction preserve 104 structural axes, the 66
Hillman axes, the reviewed original gravity/accessory factor, and the six
250 lb × 2 / signed 300 N / 100 mm-lever cases. Two `dead-only` states use
the original gravity column zero, scaled by the same accessory/dead factor,
with no live column. Their downstream strength duration factor is 0.9;
elastic actions retain the source factor 1.0. Four continuous knee shafts
replace their twenty old lumped spring rows; the other 100 axes retain their
existing conditional laws. No proposed internal-v tie is included. Existing
reviewed and proposal-gravity comparisons retain their original scope.

## Mapping and guards

The adapter uses `simple_frame.lump_floor`'s exact transformation `T`, followed
by the consumed `old_kept_lumped_rows`. For kept coupled forces `f_old`, the
canonical source force is `T_keep.T @ f_old`. This preserves the original
stiffness-weighted floor cell expansion; it does not recover local floor
pressure or alter the no-slip assumption. The twenty removed canonical rows
have explicit unavailable flags. Their zero placeholders are never zero-demand
comparisons for the replaced knee connectors.
Every body-action record also marks `source_force_available` and
`replaced_source_row_placeholder`; source nodal loads and new port actions are
available, while the twenty replaced canonical rows remain guarded.

Each new wood term contributes `-f_port * direction_global_xyz` at its exact
`point_mm` to its named member. Bore and wood-seat points retain the consumed
quadrature layout. Metal-only head-seat ports have empty wood-term lists and
add no direct wood action. The applied force has no independent free couple;
the saved location supplies its moment. Every retained canonical row keeps its
signed force, point and independently recovered free couple through
`top_corner_actions.physical_actions`.

Source nodal loads come from the original `F` map and DOF labels. Each of the
50 bodies must reproduce its consumed `W` load wrench within `1e-6` in N/Nmm.
Its complete point-action wrench must close within the existing **0.1 N /
2 Nmm** body bounds and reproduce `-Dwood_body.T @ f` within `1e-5` in N/Nmm.
The separate external-load/floor-support check uses **5 N / 100 Nmm** bounds
over the whole frame. These are numerical reconciliation guards, not adopted
strength criteria. Source and output hashes are checked before and after
publication. A failed guard leaves incomplete output and a CLI STOP record;
it cannot be indexed as a completed comparison.

The six panel bodies use their recorded APA direction-1 chart solely for
action-station metadata. They receive no timber beam section interpretation.
All 44 timber bodies reuse the exact frozen geometry and original station
inventory. Existing station indices and finished-section recipes remain
matchable. Separate event-cut arrays include the complete current point-action
and footprint station inventory, including the new distributed knee actions.
These cuts use the same `member_screen.cut_vectors` sign and before/after
partition; no new force sharing or rectangular fallback is introduced.

## Parent execution and outputs

The parent completed `attempt03` from the authenticated `frame-attempt08`
disposition packet. It exports twelve accepted states and retains two failed
zero-gap states as explicit force-free exclusions. A smaller accepted-state
packet remains a subset; it cannot imply its missing counterparts completed.
All six live cases at zero and nominal gaps set `all12_live_states=true`.
Both `dead-only` states set `both_permanent_states=true`; all fourteen set
`all14_required_states=true`. Each action object and state summary records
`state_tag`, `case_id` and `gap_scale`. Permanent tags are `dead-only_zero`
and `dead-only_gap`, matching the preserved original permanent response.

The following command reproduces the final refined disposition packet export.
A declared failed state contributes no action or section arrays.
Use a new immediate output child and retain every earlier attempt:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/joint-frame-action-reconciliation.py build \
  --preparation docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-compatibility-completion/prepare-attempt03 \
  --wood-reduction docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-port-reduction/attempt01 \
  --response docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-compatibility-completion/frame-attempt08 \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-action-reconciliation/attempt03
```

The equivalent API is `build(output, preparation, reduction, response)`.
`prepare(output, preparation, reduction)` authenticates and writes source-only
plans without opening numerical arrays. No import executes either function.

| Output | Scope |
| --- | --- |
| `body-actions.jsonl.gz` | All 50 bodies in every completed state; exact point forces/free couples and source identities |
| `source-row-response.npz`, `source-row-map.json` | Canonical retained-row forces, kept relative motions, coupled forces, exact floor expansion and replaced-row guards |
| `nominal-gap/action-section-arrays.npz`, `zero-gap/action-section-arrays.npz` | Existing member-screen point/cut array naming for 44 timber bodies; extra `__event__internal_*` arrays and `body__event_stations_mm` |
| `permanent-nominal-gap/`, `permanent-zero-gap/` | Same section/geometry schema for `dead-only`, explicitly separated from live duration factors |
| Each branch's `geometry.json` | Original timber stations/section identities, updated point inventories and supplemental event stations |
| Each branch's `member-actions.json` | Case/member/array identities and action counts; no resistance ratios |
| `summary.json`, `receipt.json` | All 50 body balances per state, source/load closure, actual state coverage, old-force identity comparison, complete source/output bindings |

The adapter reports both bitwise force identity and the actual peak retained
force change. A numerical tolerance does not silently promote changed forces
to historical capacity acceptance. Output remains
`COMPLETE_SAVED_COUPLED_ACTION_RECONCILIATION_NOT_RESISTANCE_QUALIFICATION`;
`strength_comparisons_complete`, `numerical_goal_complete`, joint acceptance
and physical release remain false.

The source packet may use
`PARTIAL_CONDITIONAL_COUPLED_FRAME_STATES_WITH_DECLARED_STOPS`. Its
`comparison.json` must identify only audit-passed states, and its
`response.npz` must contain exactly those states' five field families. A raw
STOP packet, rejected fixed-mask diagnostic, missing accepted array or extra
rejected state array is refused. Every accepted state must have
`audit.all_passed=true` and every individual audit gate true. Its source JSON
path, hash and `/states/i` pointer travel with each exported body and case.

`required_state_inventory` in the summary and receipt records all fourteen
case/gap keys. It preserves the source case dispositions and their exact JSON
provenance. Accepted records match actual fields one-to-one. Finite floor-search
exclusions bind the original packet receipt and exception trace, retain all
256 distinct masks and their actual solver/audit counts, and set
`physical_equilibrium_nonexistence_proven=false`. An unassessed key remains
`UNASSESSED_REQUIRED_STATE`, with no source pointer or force field. Other
numerical stops remain unresolved rather than completed finite dispositions.

The current adapter also accepts an external partial source receipt solely for
an exact excluded floor-search disposition. Its receipt-bound comparison must
contain one matching case/gap with no accepted field, identical original
packet/trace path/hash/pointer and the same complete search summary. The trace
and unchanged preparation, reduction and gravity inputs are then authenticated
as before. Arbitrary partial packets are not stop evidence. This supports the
refined response's reuse of `k12-right_zero` from `frame-attempt06` while
preserving the older adapter snapshot and action outputs.

`counts` separates accepted states, finite floor-search dispositions,
unassessed states and unresolved numerical stops. Only a completely assessed
fourteen-key inventory sets `finite_state_disposition_inventory_complete`.
That flag does not set `all14_required_states`, which requires fourteen actual
accepted fields. `action_exports_complete_for_accepted_states` can be true for
a subset; its `action_state_scope` remains `accepted_state_subset`. Component
consumers must count only that accepted subset and retain all exclusions.

The preserved `a12-left_zero` finite search tried 256 unique masks: 102 had
original-law audits and 154 stopped numerically (151 `PrimalInfeasible`, two
`InsufficientProgress`, one `AlmostSolved`). None passed. The separate rejected
diagnostic records `base_floor_right` normal force about `1.7154e-8 N`, normal
motion `-0.0184618 mm`, and tangential resultant `339.4605 N`. Its held no-slip
footprint fails the unchanged positive-bearing gate. This is a completed
finite method disposition with a specific support-model limit; it supplies no
accepted forces and proves no physical-frame failure or absence of all possible
equilibria. The original source STOP remains a STOP.

`canonical_raw_row_available` and
`canonical_raw_row_to_kept_lumped_position` provide the signed canonical
1888-row availability and kept-motion join. The latter is `-1` for replaced
rows. Each `<state_tag>_raw_force_n` preserves the source `D` sign;
`<state_tag>_kept_lumped_relative_motion_mm` follows the consumed kept order.
The 66 screw triples remain available identity rows. Panel-local consumers
may recover original nodal footprints through the bound original `B.T` and
`F`, then cross-check their wrenches against the six-panel body-action census;
the point-action export is not a substituted nodal footprint.

## Smallest affected-reference continuations

Reuse pure functions with a new, explicitly bound action source. Existing
`build()` workflows have literal historical pins and must not be pointed at
this response by rewriting those pins or replaying their source pipelines.

| Comparison | Existing reusable method | Required new join |
| --- | --- | --- |
| Ordinary shafts and steel | `bolt-reference-completion.geometry_for`, the pinned `upper-right-combined-transfer.solve_state`, existing field/endpoint recovery | Extract new T and signed V from available canonical axial/lateral rows for the unchanged axes; retain source geometry, material and each own end. Four replaced continuous shafts use their coupled fields instead. A changed T/V requires its own applicable field calculation. |
| Panel/screw gross references | `panel-reference-completion.screw_references` and `panel_sections` | Join the 66 preserved screw row triples, kept relative motions, complete panel actions and same-case receiver actions. Preserve the existing contact/profile/material limits. |
| Panel local/net references | `panel-local-net-completion.local_screw`, `net_rows` and the saved geometry/layer recipes | Supply the newly joined screw and panel-cut actions. Hold-applied-load-only comparisons are reusable only with identical applied load/geometry definitions. |
| Base, contact and floor bearing | `contact-bearing-completion.ratios` and its saved contact/footprint inventory; `receiver-bearing-completion.scalar_comparison` | Recompute compression, active-area and mean comparisons from current signed canonical rows. Retain ripped-stock unsupported binding labels and distinguish floor cell allocations from actual local pressure. |
| Timber normal/shear/torsion | Existing `member_screen` pure reference methods, `member-opening-general-completion.normal_stress/elastic_stress` and saved section fields | Match original station/section identities to the exported before/after cuts. Join supplemental event cuts separately. Reuse solved unit section fields with changed wrenches; preserve component/domain limits. |

The export does not yet provide nodal connector forces or individual absolute
elastic fields. A consumer that needs them must use the already bound `Bwood`
and original `F` rather than treating point actions or rigid coordinates as
those fields. Washer metal, splitting, actual restraint/stability, permanent
strength comparisons and loaded clearance retain their separately defined duties. This
adapter supplies their action inputs where applicable; it supplies no capacity.

The separate [saved-force mean worksheet](joint-frame-bearing-reference.py)
reuses the existing contact and NDS scalar helpers within this packet. Per
accepted state it covers 108 timber-contact faces, eight uniform floor means,
198 receiver sides and 208 washer own ends. The current geometry has 34
possible parallel/oblique receiver interfaces; the older addendum's 30 counted
only historically active interfaces. Zero active area remains an explicit
null comparison. Ripped-stock references remain hypothetical, with no grade
inheritance. Permanent states use `C_D=0.9`; live states use `C_D=1.0`.

For the 100 scalar connectors, washer own-end moments remain unknown and are
never filled with zero. The four continuous connectors retain each wood-seat
resultant, sampled pressure and moment from their consumed point ports. Saved
support areas are usable only with the exact reviewed finished STEP, positive
supported area and the applicable source profile. Ideal-annulus diagnostics,
partial support and the four source-quarter-inch/shop-5/16 rail-axis mismatches
remain separate. Neither route supplies washer metal stress or a physical
pressure patch. The inherited `1e-4 N` contact-law gate is reported separately
from the compatible source's `0.1 N` gate; the worksheet repairs no forces and
changes no tolerance.

Source-only `mean-preparation02` authenticated 325 source and four output
bindings without reading array values. Its receipt hash is
`d7818b5fce6e30b6c90c35729dab2f5dfcb246566377fa8cc654a4fc13150b9d`.
The prepared worksheet producer hash is
`aa44d9840be4baf1002ed62446ce8219ed9e8d0f0fe3c0ea4be4426ff41b7d17`.
It binds the caller's exact action receipt and resolves an older live producer
path only to that receipt's byte-identical producer snapshot. Preparation took
1.60 seconds; parent-only saved-force arithmetic is estimated at 5–20 seconds
and under 100 MB. The parent authorized the saved-force arithmetic against the
final refined `attempt03` action receipt. The resulting
`mean-reference-attempt01` completed in 2.17 seconds, with receipt hash
`67e98ce04e58aab46659207295d8d200ace179b59809852b1fb8e549f6e6f890`.
Its recorded command was:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/joint-frame-bearing-reference.py build \
  --actions docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-action-reconciliation/attempt03 \
  --receipt-sha256 370dafc75a90967cc45e9888bdbd5610fa2df6930a5821d4cd52d01bae70904e \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-action-reconciliation/mean-reference-attempt01
```

Reproduction must use a fresh output child; existing attempts cannot be
overwritten. The mean worksheet is supporting accepted-subset evidence under
the action packet's complete finite disposition inventory, not fourteen
accepted force comparisons.
`mean-preparation01` and its earlier source snapshot remain preserved. The
second preparation includes the exact aggregate floor-resultant law residual
and separate cell-projection residual, so a small projected cell error cannot
hide a failed inherited footprint-law gate.

The independent mean-result audit checked all 332 source and eight output
bindings, 1,296 timber-face means, 96 floor means, 2,376 receiver means and
2,496 washer own ends. The timber-face reference peak is `0.0578245` and the
floor mean peak is `0.0927669`. Applicable supported-area washer reference
peaks are `0.396701` for conditional stock and `0.228608` for hypothetical
ripped stock; neither exceeds one. The ideal-area peak `0.812440` belongs to a
shop/source profile mismatch and is retained only as a diagnostic.

Sixty-three contact groups fail the inherited strict law report, and five
force/motion activity rows exceed its inherited disagreement bounds. They are
recorded explicitly, without changing the accepted source's `0.1 N` domain.
There are 348 unavailable supported-area joins: 288 end-state rows have a
different saved finished STEP, 48 further rows have the shop/source profile
mismatch, and twelve rows retain the unsupported right-center principal seat.
The total profile-mismatch inventory is 96 end-state rows, overlapping some
STEP mismatches. All 2,400 scalar own-end moments remain null; the 96 continuous
own ends have saved pressure-resultant moments. All 2,496 washer metal stresses
remain null. The two excluded zero-gap states contribute no mean rows.

## Retention and validation

These owned adapter and worksheet leaves and ignored `rawlocal/joint-frame-action-reconciliation`
stay active. Original source outputs and all other workers' files remain
unchanged; nothing is pruned or selected for archive. `attempt01` retains its
failed producer snapshot and exports: a member-loop variable shadowed the
required disposition inventory before final publication. The corrected
`attempt02` producer hash is
`ebbd987e9cd2f105c89631677f292b9cc8a2939e300b2cd4bdd4c8de16dc89e9`.
It passed AST/Ruff and a focused check that the disposition inventory has one
assignment. The source-only review authenticated 85 bindings and the complete
fourteen-key inventory before parent execution.

The narrow reused-partial-stop update's producer hash is
`8eaf209dc594be9468b9bea60ddd02974e1a05f2bc915fd2dc41dcf2b11eaf8c`.
The earlier `attempt02` snapshot and outputs remain unchanged. The final
`attempt03` receipt is
`370dafc75a90967cc45e9888bdbd5610fa2df6930a5821d4cd52d01bae70904e`,
and its summary hash is
`353ce1316bbd005be0e3f286e416eab7bd549c465a99c629d6f34ce11d8c7330`.
Its independent audit checked 92 source and nineteen output bindings, all
600 body records, the exact accepted-tag/mask inventory, all 44 original
station/rectangle recipes and 1,056 original plus 1,056 event cut arrays.
The body closure peaks remain `9.5661e-12 N` and `1.8795e-9 Nmm`; external
closure peaks are `2.0827e-10 N` and `6.4820e-7 Nmm`. Ten source states reuse
their exact earlier fields; only `a1-rear_gap` and `k12-rear_zero` were refined
for the unchanged panel-screw law gate. Their final residuals are
`2.78114e-6 N` and `6.86623e-6 N`. Both frozen floor exclusions remain intact.

The preserved `attempt02` receipt hash is
`d79abda0dd3df21c84b65b83f95d1f2e0d4c00e5139fd356533b5b0ec0d60f18`;
the summary hash is
`705841d25f9af5261f80e997ef199e5a80870d09bbe31b996b331cd7838eb8c4`.
The independent read-only audit checked all 85 source and 19 output hashes,
600 unique state/body records, all 44 original station/rectangle recipes,
the 1888-row mask and exact accepted-tag array census. Body closure peaks are
`9.5661e-12 N` and `1.8795e-9 Nmm`. Six nominal live, four zero-gap live, and
both permanent branches were exported. `a12-left_zero` and `k12-right_zero`
remain unavailable in every force, action and section array.

These results complete action reconciliation for the accepted subset and
retain a complete finite disposition inventory. They do not complete fourteen
accepted frame states or resistance comparisons. The worker performed no
mechanics, CAD, native/frame solve, software test suite, staging or commit.
