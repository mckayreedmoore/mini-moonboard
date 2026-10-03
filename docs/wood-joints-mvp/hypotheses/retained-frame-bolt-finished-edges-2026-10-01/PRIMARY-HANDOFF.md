# Primary handoff: retained frame-bolt finished boundaries

Status: this assigned nominal geometry packet is complete. Numerical validation
and four independent review passes are complete; [final review disposition](review-final.md)
and [final file pins](final-pins.json) accompany the handoff. Primary integration
remains its responsibility. Do not treat this as joint acceptance.

I am sending these numbers because the preceding retained-bolt resistance
packet left finished end/edge geometry unresolved. This packet supplies the
current nominal directional geometry and signed receiver joins while keeping
NDS detailing applicability and complete-joint resistance unresolved. The
numbers come from authenticated saved geometry and load evidence, not an
online surrogate or a stock bounding box.

The report covers twelve retained bolts, 24 receiver memberships and eight
finished members. All 288 queries resolve at three named interior depths and
four modeled grain/cross-grain directions. All 252 signed bolt states join to
504 receiver rows and 1,008 resolved signed component choices. Physical force
points remain separate from the interior geometry query origins.

| Number | Value | Why it matters |
| --- | --- | --- |
| Finished distances different from the stock box | 96 of 288 queries | Stock envelopes cannot replace finished surfaces. |
| Other bore is first material loss | 28 of 288 queries | A nearby cut and the exterior member boundary are distinct. All 28 retain exit/re-entry/exterior traces. |
| Largest finished/stock difference | 637.4226611176605 mm | `lumber_leg_bolt_left_2/second/near_head/g-`: stock 1854.9133046511552 mm, finished 1217.4906435334947 mm at 0.01 mm inward of the receiver head-side bearing end. |
| Example other-bore first exit | 36.03275892843429 mm | `rail_front_bolt_left_2/first/midpoint/g-`; its exterior exit is separately 98.10285892843432 mm. |
| Minimum sampled exterior distance, g+ | 71.95185978252302 mm | `rail_rear_bolt_left_1/first/midpoint/g+`. |
| Minimum sampled exterior distance, g- | 70.17214107156568 mm | `rail_front_bolt_left_1/second/midpoint/g-`. |
| Minimum sampled exterior distance, q+ | 41.59714107156567 mm | `rail_front_bolt_left_2/second/midpoint/q+`. |
| Minimum sampled exterior distance, q- | 43.63845902187154 mm | `rail_rear_bolt_left_2/second/midpoint/q-`. |

These are centerline distances at named sampled depths. They are not observed
cuts, a through-depth minimum, a bore-radius-subtracted ligament, or an NDS
loaded-edge/square-cut-end classification. A sloped recess, other bore or blind
cap does not automatically become an NDS square-cut end.

## Reproducible artifacts

| Artifact | SHA-256 |
| --- | --- |
| `/tmp/mini-moonboard-retained-frame-bolt-finished-edges-2026-10-01.json` | `75db902ab8ebb64985592e8f1552333db763facb35d9be1630ec521202fe2332` |
| Same prefix, `-raw-oracle.json` | `faa735bc0c386373c4639e7d7e9dcf88dbc97e28552ddc1719a66075f8efc028` |
| Receipt self-check digest | `92b360f31a45791fe73415443461f07a239585973ff8ed35d464c50188d5d1f1` |
| Producer | `55240f4dda242078be0179e43a4032b67b681a17522ee6844c00895280793ea1` |
| Pure method | `3aabafb6c1ce25545ae00050dc213ba82a749a9c6ef5a8c0d4819f47c2532aa4` |
| Independent oracle | `1faaaa293ff51ec9b42967c6ab646911929719f1197660caf49d1deeae077961` |
| Source manifest, 165 pins | `2d7050f533e315fb28a635b93546e1e5d2036011eddfb77e966dcd73c947f9c9` |

The 39 focused tests and whole-packet Ruff pass. Producer replays with two
hash seeds are byte-identical. An independent checker reconstructs all
288 profiles, 504 receiver rows and 1,008 signed projections, rechecks the
165 source pins and original 143 load pins, and refuses six semantic mutations.
It imports neither the producer nor the method. A root replay reproduces the
same receipt, and its self-check passes. The CLI output guards protect all
existing packet files and authenticated inputs, including inode aliases.
Both checker modes require the externally recorded oracle digest, and the
documented upstream replay sequence reproduces all three frozen prerequisites.

## Remaining assumptions and source limits

The official 2024 AWC NDS Chapter 12 PDF is pinned in
[source-evidence.json](source-evidence.json): SHA-256
`53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f`.
Sections 12.1.2.1–12.1.2.4 define grain-relative edge distance, square-cut end
distance, spacing and a row aligned with load. These definitions can be
obtained reliably from the primary online source. They do not supply this
candidate's finished geometry, delivered grain, hole quality or mixed-load
applicability. Placement table factors and historical interpolation are not
adopted here.

Through-depth minima, NDS loaded-end/edge classification, Cdelta, Cg, splitting
acceptance and complete-joint resistance remain NULL. All 47 criteria remain
pending and all release flags remain false. No CAD/native execution, geometry
mutation, shared-input mutation, inspection, fabrication or Git operation was
performed by this lane.

## Communication and next assignment

At the initial handoff, tmux/TUI messaging and the direct tmux socket were
inaccessible. The shared repository supplied the results during that interval.
On October 1, after the owner restored full access, the TUI send tool accepted
the handoff message to the primary thread
`01a0f821-5e03-7781-bb0e-0d15efebcbe2`. It supplied the verified numbers,
explained their purpose, preserved the applicability limits, and requested
another bounded assignment. Messaging access is now verified.
The primary has independently replayed the report and revised checker receipt
byte-identically and reported all 39 tests passing. Its commentary preserved
the three-depth sampling and unresolved NDS applicability limits. This verifies
receipt of the numerical evidence through the shared repository.

Primary: with the final review disposition and pins now present, please
validate and integrate this packet with its sampling and acceptance limits
intact, then give this secondary agent another bounded parallel assignment.
Continue using included usage only; the owner explicitly forbids credits or
paid fallback if included usage runs out.
