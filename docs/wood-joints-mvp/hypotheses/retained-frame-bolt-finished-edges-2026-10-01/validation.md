# Retained finished-edge validation

The frozen nominal report covers all twelve retained bolts, 24 current receiver
memberships and eight finished members. All 288 sampled grain/cross-grain
queries resolve, and the 504 signed receiver states have 1,008 resolved
component signs. The source physical force point and interior geometry sample
remain separate. All 47 criteria remain pending and every release flag is false.

## Frozen artifacts

| Artifact | SHA-256 |
| --- | --- |
| Report in `/tmp/mini-moonboard-retained-frame-bolt-finished-edges-2026-10-01.json` | `75db902ab8ebb64985592e8f1552333db763facb35d9be1630ec521202fe2332` |
| Independent receipt, same prefix with `-raw-oracle.json` | `faa735bc0c386373c4639e7d7e9dcf88dbc97e28552ddc1719a66075f8efc028` |
| Receipt self-check digest | `92b360f31a45791fe73415443461f07a239585973ff8ed35d464c50188d5d1f1` |
| Source manifest | `2d7050f533e315fb28a635b93546e1e5d2036011eddfb77e966dcd73c947f9c9` |
| Producer | `55240f4dda242078be0179e43a4032b67b681a17522ee6844c00895280793ea1` |
| Pure ray method | `3aabafb6c1ce25545ae00050dc213ba82a749a9c6ef5a8c0d4819f47c2532aa4` |
| Independent oracle | `1faaaa293ff51ec9b42967c6ab646911929719f1197660caf49d1deeae077961` |
| Focused tests | `855c7dac3ee2cad341a14f83874a1fefba2229ce2082a41fe94bb88564444277` |

## Checks performed

The 39 focused pytest tests pass. Independent synthetic answers cover a box,
rotation, a nonconvex recessed profile, another through-bore, a blind circular
cap, matching own-hole filling, tangent/corner refusal, bore-origin validation
and unsupported trims, including a grouped finite-cylinder endpoint/rim event.
A U-shaped synthetic section has known 2/4/6 mm exit/entry/exit events; both
methods preserve the complete trace and the oracle refuses a truncated trace.
Further tests verify the current 24/288/504 census, signed RF interval
selection, output alias refusal and source-pin refusal. Both CLIs refuse
same-path, symlink and hard-link outputs that alias protected inputs or any
existing packet file; isolated entrypoint tests verify the original bytes
remain unchanged.
Two producer-path regressions inject ambiguous and unsupported method results
and require all finished and signed-candidate distances to remain NULL while
stock locators stay numeric. Four CLI regressions require the caller's
externally recorded checker digest before either report or receipt replay.
Whole-packet Ruff passes.

Producer replays under `PYTHONHASHSEED=71` and `983` are byte-identical to the
frozen report. A fresh root invocation of the independent oracle produces a
receipt byte-identical to the author's receipt, and its self-check passes.
The three frozen upstream artifacts also reproduce byte-identically through
their documented offline generation sequence; the integration fixture reports
missing prerequisites explicitly. No native or CAD process was run.

The oracle imports neither the producer nor the method. It separately parses
the authenticated face signatures, intersects finite plane/cylinder surfaces
and applies planar trim parity. It matches every one of the 288 profiles,
including 28 three-event other-bore exit/re-entry/exterior profiles, all 504
receiver force records and all 1,008 signed projections. It checks 165 packet
source pins and the original 143 load-source pins, plus the finished face/axis
source chains. Its numerical comparison tolerance is 2e-6 mm for geometry;
this is nominal signature verification, not kernel classification or observed
hole validation.
Both checker modes additionally require the caller-supplied reviewed oracle
hash shown above. The receipt self-hash proves internal consistency; it is not
a digital signature or independent code approval. The root's final file pins
and the primary's validation remain the external handoff boundary.

Six deliberate in-memory mutations are refused: a foreign feature, reversed
saved-face normal, substituting the exterior for the first material boundary,
mixing receiver stock frames, a forged report source pin and promoting release.

## Independent reviews

Four independent review passes are complete. The [final disposition](review-final.md)
records the last three fresh Luna/max reviewers. Correctness and architecture
returned no substantial findings. Testing independently replayed the complete
report successfully and suggested duplicating that mandatory oracle invocation
inside pytest; root explicitly deferred the duplicate check. All confirmed
earlier findings were corrected. No current result discrepancy remains.

The primary also reproduced the report and checker receipt byte-identically
and reported all 39 tests passing. Its current receipt is
`/tmp/mini-moonboard-parent-retained-finished-edges-raw-oracle-v2-2026-10-01.json`;
its hash matches the final receipt above. Direct TUI/tmux messaging was blocked
at the initial handoff. After the owner restored full access, the TUI send tool
accepted the numerical handoff and next-assignment request to the primary.
The [primary handoff](PRIMARY-HANDOFF.md) and final file pins record the
updated communication receipt. Code, reports and numerical results remain
unchanged. Primary integration remains its responsibility.

## Applicability boundary

Distances are centerline values at the named query depth. They neither subtract
bore radius nor bound all bearing depths. The first material-loss event remains
distinct from an exterior free-surface exit; stock-box distances are separate
locators. NDS loaded-edge/end classification, Cdelta, Cg, splitting acceptance
and complete-joint resistance remain NULL. No native or CAD execution,
geometry mutation, physical inspection, drilling or fabrication is claimed.
