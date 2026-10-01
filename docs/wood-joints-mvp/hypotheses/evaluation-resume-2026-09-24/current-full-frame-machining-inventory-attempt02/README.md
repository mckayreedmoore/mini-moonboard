# Current full-frame machining coverage — attempt02

Attempt02 carries the owner-selected Hillman 42605 #10 preparation policy onto
all 66 panel/kicker screw axes in the reviewed
`led-clearance-2x6-runner-seated-blocks-v1` attempt04 manifest. It binds each
current axis ID, full source row, global origin, direction, panel, and receiver
to that manifest. The current axis-row canonical SHA-256 is
`464841ff6760a78e55f98d5b655672b4d8d962c8cbf50cfe61e47a2d541db4ed`.
The mapping preserves 58 source stations and all eight owner-directed moves.

The selected-baseline [shop checklist](../../../../floor-flush-shop-checklist.md)
is the policy source for a 1/8 in (3.175 mm) lead-hole pilot and 3/8 in
(9.525 mm) face countersink. The repository [working agreements](../../../../../AGENTS.md)
retain that purchased-screw policy for this candidate. The checklist does not
define the current WJ coordinate datums, receiver sections, operation depths,
tolerances, or setup sequence. Attempt02 therefore keeps that policy source
separate from the attempt04 coordinate/receiver source; the two sets of facts
are associated by current axis ID, not treated as one shop drawing.

The six panel identities are the exact finished STEP artifacts recorded in
attempt01. Their files are byte-hash checked here, but a finished BRep hash is
geometric identity evidence only; it does not decompose the final solid into
blanking, edge/profile, hole, or other machining operations.

| Current member | Finished STEP path | SHA-256 |
| --- | --- | --- |
| `kicker_left` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/kicker_left.step` | `4740a18f46b8e8ecc2c01c80f7966228c498e35a09f10d7ccb32b08ea3cd8691` |
| `kicker_right` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/kicker_right.step` | `d70c1fedf1c18304818a0f3adefdef0f64204f055a18d941ecd2b91a8dfe32b5` |
| `main_lower_left` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/main_lower_left.step` | `78e2bd7b3a3f4cb6f70a1a2156ae3143cb936b29e5560dd6fd0cf6142aac6270` |
| `main_lower_right` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/main_lower_right.step` | `408d8ed97edf27954fa63221096af25da56a5aab02d53f77ecccbcfafb5b5d90` |
| `main_upper_left` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/main_upper_left.step` | `4be26c61e59ca3c74f370989097f4bff9edf337fa4de1a30d7e5de9eb7ef52f7` |
| `main_upper_right` | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/main_upper_right.step` | `2791dca8f42b86a49b9e685f0f85d896642cbe9975a89bf1524bed89eddfea8f` |

The pinned attempt01 inventory has no prior cut-inventory rows for these six
panels. The attempt04 manifest and these finished-shape identities do not
provide a source-authoritative, complete panel operation decomposition, so
`MACH-GAP-01` remains open. The owner-selected policy supplies only the two
diameters. Pilot depth, countersink depth and included angle, location
tolerances, datums/setups, offcut result, physical receiver material/section,
and interactions with hold/LED cuts and local net section remain unresolved
for every axis. No physical receiver or shop operation has been verified.

`MACH-GAP-03` also remains open: operation definitions for all 92 candidate
bolt axes and 12 retained frame-bolt axes are unresolved. Timber/block
decomposition and critical-section gaps remain open as recorded in
`inventory.json`. `all_machining_represented` remains **false** and pending;
cutting/drilling and fabrication are not released. This packet makes no claim
that an actual part, cut, hole, receiver, or offcut was inspected. It does not
infer a tool dimension from occupancy or BRep geometry, and it runs no CAD or
native solver.

## Pinned sources

The producer fails closed if any listed source bytes change:

| Source | SHA-256 |
| --- | --- |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json` | `9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-machining-inventory-attempt01/inventory.json` | `6a36c53f40f552dc36f214fda0fb3b0f193b9c9918f99b04af637eb4a0adf77f` |
| `scripts/build_current_full_frame_machining_inventory_attempt01.py` | `10a194415df37d423b11d4a587ad1a013c2ac5ae5d1d81aa58b162dc617e188c` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-machining-inventory-attempt01/README.md` | `ef536d2196446cb1469421d30bfe9b55211948738e63b4258534030328381a3c` |
| `AGENTS.md` | `672203b929d51d340d39d770e71dd43b019794ea33172bc9f4f7be469fc20536` |
| `docs/floor-flush-shop-checklist.md` | `c88463f7b3d861014e6aecd7af8c087ed8fce155389d08faf67b1e11f0659599` |

## Reproduction

Run these commands from the repository root:

```sh
.venv/bin/python -B scripts/build_current_full_frame_machining_inventory_attempt02.py --verify
.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_current_full_frame_machining_inventory_attempt02.py
sha256sum -c docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-machining-inventory-attempt02/SHA256SUMS
```

The static producer verifies source hashes and axis/member identity, then
rebuilds the JSON record for comparison. It does not launch CAD, inspect BRep
faces, run a native solve, or generate a shop ticket. `--write` creates the
inventory once and refuses to overwrite an existing file. Attempt01 and all
source evidence remain unchanged.
