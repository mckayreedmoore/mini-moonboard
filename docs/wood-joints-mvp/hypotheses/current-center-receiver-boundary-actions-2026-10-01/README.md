# Current center receiver boundary actions

This source-only packet reconstructs the complete modeled boundary of the
two center posts, their two cleats and the kicker header for three frozen
rear cases at seven saved increments. It preserves every signed interface
endpoint, application point, source rounding bound and physical body load.
The direct post/header seats remain separate from the post/cleat/header
routes. No screw force is allocated between those routes.

The saved inventory contains 212 interface groups and 250 scalar rows per
state: 40 internal groups and 172 external boundary groups. Across all
21 states it retains 5,292 target-body endpoints, 6,636 physical nodal loads
and 105 body balances. The 235 incident geometric pairs comprise 22 finite
opposed contacts and 213 AABB-separated pairs; all finite pairs and all
16 candidate-bolt and 14 panel-screw axis memberships have modeled ports.
AABB separation is not an exact BRep contact evaluation.

The maximum reconstructed body residuals are 0.000130995 N and
0.159621032 Nmm, within the unchanged source gates of 0.1 N and 2 Nmm.
The floor selected/released masks differ by case and remain explicit. All
endpoint coordinates and source rounding bounds are retained, including
the distinct outer-seat points of axial bolt ties. These results reproduce
the saved source audit; they do not validate a physical joint.

The [plan](plan.md) records the scope and source census. Exact metadata
production and verification use the pinned local source closure:

```bash
python3 docs/wood-joints-mvp/hypotheses/current-center-receiver-boundary-actions-2026-10-01/produce.py --write
python3 docs/wood-joints-mvp/hypotheses/current-center-receiver-boundary-actions-2026-10-01/produce.py --verify
python3 docs/wood-joints-mvp/hypotheses/current-center-receiver-boundary-actions-2026-10-01/raw_dat_oracle.py --check docs/wood-joints-mvp/hypotheses/current-center-receiver-boundary-actions-2026-10-01/boundary-actions.json
```

The output is conditional source-action accounting. Non-qualifying screw
withdrawal proxies, the unverified floor assumption, A12 source/recovery
discrepancies and wider six-case gaps remain open. Body equilibrium and
complete modeled port coverage establish no contact activity, stiffness,
resistance, complete physical joint path or release. All 47 criteria remain
pending. No CAD/native run, geometry change or physical work is performed.

The independent [raw-DAT oracle](raw_dat_oracle.py) imports no producer,
boundary accounting or frozen export helper. It authenticates the frozen
sources, reads emitted deck connectivity and loads, and reconstructs all
5,250 scalar records directly from printed native RF tokens and carrier
bindings. Across 21 states, all 5,292 endpoints, 6,636 nodal loads and 105
body balances match. It checks 182 selected and 154 released floor-tangent
channels, retaining token-derived bounds and source-load corrections.
Application points match exactly. Endpoint-force differences are at most
3.95e-31 N; body-moment differences are at most 1.83e-10 Nmm.

Focused tests cover source refusal, candidate/revision and pending authority,
complete point-action accounting, scalar-index spaces, moment transport,
common and distinct endpoint coordinates, raw-token intervals, floor recovery
and continued C3D20 deck connectivity. They run without saved CAD/native
artifacts:

```bash
python3 -m pytest -q -c /dev/null --rootdir docs/wood-joints-mvp/hypotheses/current-center-receiver-boundary-actions-2026-10-01 docs/wood-joints-mvp/hypotheses/current-center-receiver-boundary-actions-2026-10-01
```

All 74 focused tests and Ruff pass. Three fresh independent Luna reviews at
maximum effort close with no confirmed defects in the [review record](review.md).
The oracle uses floor source corrections from the pinned model; it does not
derive them again from deck equations. The correctness review independently
checked floor inventory/correction identities and active/inactive reference
node participation in the frozen equations. This remains a source-method
validation boundary, not floor or complete-joint qualification.

The primary owns final validation, shared integration and Git.
