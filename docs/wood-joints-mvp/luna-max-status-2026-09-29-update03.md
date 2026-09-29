# Wood-joints MVP-E status report — 2026-09-29 update 03

**Snapshot:** 2026-09-29 01:30 UTC (2026-09-28 19:30 America/Denver)

**Candidate:** `compact-floor-flush-wood-joints-development`

**Reviewed revision:** `led-clearance-2x6-runner-seated-blocks-v1`

## Current state

The joint is **not close to engineering acceptance**. The current register has
47 criteria: **47 pending, 0 passing**. There is no response-validated ordinary
joint, no accepted six-case full-frame result, and no full-frame readiness,
engineering-completion, or release approval. The criteria register describes
the exact acceptance boundary in [`current-criteria-coverage.md`](current-criteria-coverage.md).

## What has moved forward

- Docker access is working. The attempt09 patched CalculiX 2.23 binary was
  built offline in the pinned image, and an independent 35-check build
  provenance review passed. Its 39 offline tests also pass.
- The attempt09 exact-touch capture coupon has a separate, frozen attempt02
  packet. This is a method fixture, not the wood joint. Its pre-run review is
  still open; no readiness record, run-specific authorization, ledger
  reservation, or attempt02 launch exists.
- Geometry and inventory work now reconciles the 50 current frame members,
  24 former connector duties, 92 candidate bolt axes, 12 retained frame-bolt
  arrangements, and 66 Hillman panel/kicker axes (58 retained and eight
  owner-directed moves). Independent checks have accepted several bounded
  geometry, machining-crosswalk, fit, and resistance-method artifacts.
- The resistance implementation now has a reviewed NDS group-action factor
  for one-to-three-member rows. It does not calculate capacities or bolt-force
  distribution, and it does not cover four-or-more-member rows.

These are meaningful preparation results. None establishes a joint load path,
structural response, capacity, or criterion pass.

## What is holding the work

1. **The next capture-method run is not ready to launch.** The independent
   pre-run reviewer is waiting for the runner to enforce output limits during
   execution, prevent duplicate invocation with a durable launch guard, and
   check that the frozen container name matches the runner. Until those
   controls are revised and reviewed, the parent will not authorize or reserve
   the one-shot method coupon. Docker availability is no longer the blocker.

2. **There is no source-supported ordinary-joint history or validated
   response.** The active-map crosswalk and prior small fixture clarify the
   solver mapping, but they do not supply an adopted load/time history or
   demonstrate current-joint behavior. A prior attempt timed out before an
   accepted increment. The proposed transient travel remains an unselected
   geometry target, not a service demand. Without a supported history and a
   response that passes the frozen force, energy, contact, and equilibrium
   checks, T03 cannot close.

3. **The full-frame input model is incomplete.** Available mesh coverage is
   3 of 50 members. Authenticated Gmsh 4.12.1 is still unavailable in a usable
   environment; that exact-version mesher is a separate issue from Docker.
   Exact plywood product identity and properties, complete member/material
   assignments, contact and attachment maps, supports, and receiver-to-frame
   load transfer also remain open. A complete frame mesh alone would not close
   those model inputs.

4. **Nominal geometry does not yet prove mechanical duties.** Current maps
   locate interfaces and axes, but do not establish physical face ownership,
   active bearing, bolt roles, engagement, stiffness, or complete load
   transfer. The eight moved panel/kicker axes need their backing, edge
   support, installation, and load paths checked in the revised frame.

5. **Several resistance methods still lack applicable source support or
   current demands.** The reviewed group-action factor is narrow. Four-or-more
   member behavior, timber bolt combined actions, splitting, washer/plate
   response, and other connection modes remain unresolved. Official AWC
   NDS-2024 references and Appendix E material have not been authenticated
   through the available document route. A method helper cannot produce a
   criterion result without applicable sources, exact product and member
   inputs, and fresh signed connection demands.

6. **Build and cost evidence is unfinished.** The 66 panel/kicker screw-axis
   crosswalk is preserved, but the six panel cut decompositions, 92 candidate
   bolt-hole operations, 12 retained frame-bolt operations, and several
   per-operation depths, tolerances, tool setups, and support conditions still
   need evidence. Product selection, exact material properties, receiving, and
   complete costs are also open. No physical receiving or inspection has been
   claimed.

## Why progress feels slow

The remaining work depends on inputs that cannot safely be inferred: actual
load histories, exact product/material identity, applicable connection
methods, and complete load paths. Historical candidate passes cannot be
transferred to this revision. Geometry-only results and solver convergence
cannot substitute for structural acceptance.

Native work also uses one parent-owned serialized slot. Each launch requires a
frozen input, independent review, explicit parent readiness, a one-run ledger
reservation, and post-run validation. That adds review time, but prevents an
unreviewed or mismatched run from being treated as evidence. The next capture
coupon, even if it passes, validates instrumentation and output invariance
only; it will not resolve the ordinary joint or any of the 47 criteria.

## Next steps

1. Complete and independently review the attempt09 coupon runner safeguards;
   then, if all frozen gates pass, reserve and run that one bounded method
   coupon.
2. Obtain a source-supported ordinary-joint load history and finish the current
   map, demand, and response checks.
3. Make authenticated Gmsh 4.12.1 available, extend mesh coverage to all 50
   members, and bind the missing material, attachment, support, and load maps.
4. Close the applicable resistance methods and duty paths, then prepare and
   independently check the six full-frame cases.
5. Reconcile all 47 criterion dispositions, fit/transport, build operations,
   and costs before final review.

There is no credible completion date yet. The timing depends on resolving the
source and model-input gaps above; finishing the capture coupon alone would
not make the joint close to acceptance.

This report is a self-contained public status snapshot. Supporting append-only
analysis packets remain separate records and are not all included in this
status-only publication.
