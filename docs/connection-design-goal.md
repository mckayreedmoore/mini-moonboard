# Connection-design completion goal

## Target

Produce one coherent, auditable timber-frame connection candidate, not a climbing
approval. Preserve published predecessor models and their source-bound analysis.
No broad frame redesign unless the connection evidence requires one.

## Work sequence

1. Select and model removable-panel inserts and machine screws. Preserve existing
   through-bolts and manufacturer-specified bracket screws. Record purchased
   dimensions separately from modeling envelopes and unverified resistance.
2. Recover six-component aggregate leg/base forces from authenticated current
   results; extend the load cases to asymmetric single-hold loading. Distinguish
   fixed-floor/bonded-frame conditional forces from actual unanchored demands.
3. Resolve the lower-backing bolt edge-distance issue with a checked purchased
   connector or another evidence-supported detail; assess other actual joints
   against their applicable resistance data without equal-share assumptions.
4. Publish a consistent model, metric/imperial hardware and cut schedules,
   drilling/access information, assembly sequence and qualification ledger.
5. Independently review geometry, evidence and documentation; retain explicit
   human material, installation, floor-contact and physical validation gates.

## Completion boundary

An auditable candidate can contain clearly identified unresolved qualification
items, but must not silently substitute assumptions for supplier ratings or
claim that an optimistic model validates the physical joints. Missing structural
evidence remains visible and prevents construction/climbing approval.

Local work and commits continue during Denver quiet hours. Publication follows
the repository Git agreement. Another agent's untracked design notes are outside
this task's edit/staging scope.

## Current implementation status

- Panel-insert geometry and inspection package implemented as
  `panel-insert-development`; 56 replacements, existing transport/bracket
  fasteners retained. Geometry/export checks pass; resistance remains open.
- Supplier research identifies usable nominal dimensions but not a qualified
  insert engagement/withdrawal rating in the actual stock.
- Current leg-resultant recovery identifies an ideal-bonded panel-edge path as
  well as rim contact. [Aggregate leg-to-board actions](timber-joint-demand.md)
  are recovered; isolated bolt-group demand remains unresolved.
- The A21 backing-angle trial is not selected: available rating/installation
  restrictions do not establish suitability. The original backing edge-distance
  concern remains open, not silently accepted.
- Nine asymmetric basis cases and 216 linear-combination scenarios are complete
  on the preserved timber mesh; [results and limitations](timber-asymmetric-results.md)
  include aggregate leg actions. These are not actual isolated bolt demands.
- Wider solid-lumber principals and matched short base blocks are being developed
  to resolve the backing-bolt edge geometry without an unsuitable angle rating.
- Final joint resistance checks and human/physical validation remain outstanding.
  The overall goal is not complete.
