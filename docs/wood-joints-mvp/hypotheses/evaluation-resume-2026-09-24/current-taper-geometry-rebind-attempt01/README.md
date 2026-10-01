# Current leg-taper geometry rebind — attempt01

This read-only audit measures the two leg solids in the current exact 50-member
STEP bundle for `led-clearance-2x6-runner-seated-blocks-v1`. It does not rebuild
CAD, export or mesh geometry, run a solver, edit the criteria register, inspect
physical stock, or transfer a selected-baseline structural result.

The current STEP bindings are identical in full-frame input manifest attempts
03 and 04. Their current hashes are:

| Member | STEP SHA-256 | Size |
| --- | --- | ---: |
| `lumber_leg_left` | `1416e3aec21eea2993542f8266649ebe0aec50b3ec6444f445f18f88cbffa065` | 46,074 bytes |
| `lumber_leg_right` | `e346646efb8bdf9c03d45dfa024900622abcd65fe0d58bf11c6dcd3735bedff4` | 41,836 bytes |

The audit read those existing STEP BReps and measured the unique four-vertex
sloping planar face. It projects each vertex onto the leg axis `g` and section
axis `N` recorded by the taper geometry reference; the taper run is the
endpoint-edge station difference in `g`, and the recess depth is the endpoint
edge displacement in global `x`. Both members measure a 457.2 mm run, 38.1 mm
maximum recess, a 12:1 run/depth ratio, and a modeled stock section of
88.9 × 139.7 mm. The existing one-in-ten predicate requires 381.0 mm, leaving
76.2 mm geometric margin. The measured face coordinates, normals, projections,
and source pins are recorded in [`taper-geometry-rebind.json`](taper-geometry-rebind.json).

Thus the current candidate's static geometry predicates pass for
`taper_taper_at_least_one_in_ten` and `taper_intended_stock_and_runout`. The
source criteria table assigns both rows to “FR-3 and fresh case.” Since this
candidate has no fresh native case, this report leaves their full frozen-row
disposition pending; it establishes only the complete current-geometry
predicates. The modeled stock dimensions do not establish delivered lumber or
cut quality.

The right leg STEP is translated −3.175 mm in global `x` relative to the older
kerf-right taper artifact. Its current local stock spans, taper stations and
runout dimensions still match; the current STEP is authoritative for this
rebind. This does not establish native-to-CAD identity or any fit/load
consequence.

Reproduce with the repository virtual environment:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-taper-geometry-rebind-attempt01/audit.py --verify
```

The full-frame attempt03 source manifest's read-only `--verify` passed before
this audit and checked all 50 STEP member hashes and identities. Parent
independently checked that attempt04 preserves the same member geometry and
STEP hashes. No criteria or coverage register was changed.
