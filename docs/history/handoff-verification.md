# Human-audit milestone: evidence register

Scope is the [saved goal](current-goal.md): an independently reviewed,
product-specific **inspection candidate**, not construction, machining or use
approval. “Recorded” means an explicit decision request exists; it does not
mean a physical, dimensional or structural check passed.

| Goal requirement | Evidence for this candidate | Deliberately unresolved before fabrication/use |
| --- | --- | --- |
| Purchased face stock; separate leg stock; reasonable lumber selection | [Material record](purchased-materials.md), [remaining stock selection](remaining-material-hardware-closure.md), 18.25625 mm nominal faces in `product_frame`; unchanged faces in top revision | Actual category-versus-delivered dimensions, plywood stamp/strength axis and directional properties; supplier item for separate marine plywood |
| Selected fastener families and explicit source/allowance distinction | `selected_hardware` maps all 278 frame positions; [hardware dispositions](hardware-fit-dispositions.md) account separately for holds, 426 insert screws and lighting | US A21 proxy, real head/driver seats, custom steel fabrication, hold-specific bolt schedule and delivered electrical/retainer fit |
| Complete inspectable joint layout, bores and service provisions | 87 bodies plus 278 connection envelopes; all connection cores/material witnesses, 142 hold/132 LED axes, reserved routing and 228 washer annuli checked | These are nominal solids and explicit reserves, not exact threads, full harness, tool engagement or certified head bearing |
| Correct orientation, feet, connectivity and collisions | Current-candidate signed climbing-side/backing-side test; current floor/orientation/graph gate; complete nominal top-candidate intersection screen | Floor substrate, friction, erected stability and temporary handling/support; 24 retained tool obstructions require the stated installation order |
| End/edge and engagement assessment without false passes | Revised top end distances; 60 exact plywood-profile positions; [278-position axial report](top-joint-engagement.json); [all-family boundary dispositions](joint-boundary-dispositions.md) | Unmeasured wood/steel boundaries, load/grain classification, short kicker/splice margin, steel prying, screw-tip exclusion and full threaded engagement |
| Matching CAD/viewer/cut lists/hardware/assembly notes | [Top-joint exports](top-joint-development.md), metric/imperial CSVs, seven-variant export checks, browser selection checks, [assembly dependencies](product-frame-integration.md) | A final manufacturing release must replace allowances and establish a safe erection procedure; bounding blanks are not optimized nesting |
| Publish and preserve prior variants | Current viewer's 367 files (index, manifest, 365 meshes) fetched and hash-matched after deployment; predecessor artifact bytes retained and tested | CI status is separate from targeted local checks; no claim that a queued/running workflow passed |
| Preserve one-climber load assumptions and honest FEA | [150/200/250/300 lb reference envelope](physical-footprint-results.md), [rejected native recovery](leg-section-response.md), archived evidence hash checked | 250 lb is intended maximum, not a rating. No anchoring, pad, ballast or unverified composite credit; unanchored contact and actual connection resistance remain open |
| Independent review and a clear retain/change handoff | Separate correctness, testing and architecture reviews; fixes tested; [review packet](candidate-review-packet.md) and two finite disposition inventories | Human/professional review is not replaced by software agents |

## Retain/change conclusion

Retain the overall 2×8-foot100-derived arrangement, purchased face assumption
and separately modeled leg plies as the inspection baseline. Do not order
deeper lumber on the strength of rejected force recovery. Put the short
kicker/splice bolt margin, extended top steel and US clip fit first in the
reviewer's queue. Change those local details only against a named product,
geometry or resistance decision; their current positive clearances do not
approve fabrication.

The all-family table is a **complete disposition inventory**, not an automated
proof of every structural edge distance. Product identification and qualified
connection/stability assessment are the next phase. Neither a new general CAD
audit engine nor another unconstrained FEA search is a handoff prerequisite.

## Reproducible local evidence

The candidate checks are the selected-hardware, product-connection/frame/screen/
service, top-joint frame/screen, seven-variant export, axial-geometry/report,
profile-geometry/report and handoff-inventory tests in `tests/`.
Final local verification passed **80 candidate cases**, followed by **five
new handoff/current-orientation cases** (the two runs are disjoint). Repository
Ruff and diff whitespace checks passed. This is targeted candidate coverage,
not a claim that every historical test or remote CI workflow has passed.

The final added cases are reproducible with:

```sh
uv run pytest tests/test_candidate_handoff.py tests/test_top_joint_frame.py -k 'goal_critical or handoff or each_exported or review_packet' -q
```

`scripts/check_development_viewer.cjs` exercises real pointer selection of 16
parts/connections including the revised leaf and bolt; it checks selector
navigation, plywood default, and narrow-screen horizontal fit. The status
header can overlap the upper scene on narrow screens; this was recorded rather
than called full mobile usability approval.

The rejected FEA archive is retained at
`fea/results/leg_section_response/evidence.tar.gz`, SHA-256
`a3ed8496a9a3e13303f69f931c184172d100c31bbfffb86a63d4cb8c7091d31a`.
Hash identity preserves the evidence; it does not turn failed force recovery
into valid design demands.
