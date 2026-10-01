# Current pair-output contract source review, September 27

This read-only review establishes the meaning of the proposed contact-force
outputs and their current bore-pair identities. It does not qualify native
output, freeze a new joint path, or establish an ordinary-joint response.

## Decision and source evidence

A current-joint path needs observable bearing before its post-bearing states
can be interpreted. The frozen attempt09 motion deck requests CF, CFN and CFS
for all 35 pairs. The pinned contact adapter, manifest and actual fragment
identify pairs `WJCP_020` through `WJCP_027` as the eight shaft-to-wood bore
pairs: two receiver pairs for each of four physical bolts. Washer-bore pairs
28–35 and seat pairs are separate and cannot substitute for these eight.
The [machine record](source-review.json) carries all eight complete pair IDs,
slave/master owners and source hashes. The adapter hash matches the manifest;
its sequential pair construction and summary order were checked against the
actual contact and output cards.

Pinned CalculiX 2.23 `contactprints.f:155–169` resolves the requested slave and
master names to a tie. `printoutcontact.f:72–95` selects that tie's contact
slave faces. Lines 181–205 sum normal or shear force vectors and their moments
about global origin. Lines 219–243 print the named pair, time and six resultant
components. Thus CFN is a net vector, not the integral of local pressure
magnitude. Opposing forces on a curved bore can cancel in this resultant.

The later scalar “normal force” statistic is the net force dotted with the
area-averaged normal (`printoutcontact.f:271–280`). It is also not an integrated
positive-pressure quantity, especially on a nonplanar surface. The source
calculates centroid and mean normal by dividing by area without a zero-area
guard (248–255); open-pair statistics may therefore be nonfinite. A verifier
must distinguish those undefined diagnostics from its required finite force
and moment channels. It must never replace a missing/nonfinite force with zero.

## Proposed conservative bearing witness

For the declared unilateral, frictionless contact law, an accepted state with
a resolved nonzero normal resultant on a named wood-bore pair is sufficient
evidence that some bearing is occurring. The candidate gate can therefore use
the first accepted state whose pair CFN vector norm exceeds an explicitly
frozen numerical threshold, followed by two later accepted states. This records
a first *observed resolved resultant*, not the first local contact point or
exact physical onset. Local bearing could have started earlier. A zero or
sub-threshold net vector cannot establish absence of local contact.

This policy avoids inventing an exact-onset prerequisite for a requirement to
observe post-bearing states. It also avoids using an unqualified scalar or
global contact count as proof. The actual threshold, output completeness and
accepted-state identity contract are not frozen by this review. If resolved
bearing is not observable by the path's predeclared stopping point, that path
cannot pass its post-bearing gate. Do not extend the path or relax the threshold
after seeing that result.

## Next executable method checks

Before a heavy joint retry, the small penalty touch/work fixture will request
CF/CFN/CFS at open, touch, compression and reopening states to test pair identity,
force sign and zero-state output. The shared-edge motion fixture will test two
full six-component cap projections with off-contact dependent DOFs, active
contact pairs and independent force/energy references. Both are in preparation;
neither is frozen or run at the time of this review. These tests must report
their actual results and limits before any joint output contract is accepted.
A flat-pair pass alone will not establish cancellation-free curved-bore output.

## Source binding

The machine record SHA-256 is
`73ed00e9a2e0643bfbbc8bc764249ef0dd3e1a35b1d23cdccf987fb3534c4eac`.
It binds the preserved attempt09 motion deck and contact records, the unchanged
contact producer, and the pinned 2.23 source archive. The contact fragment's
2.21 header remains historical; version-specific print behavior here comes
from the 2.23 archive, not that header. `printoutcontact.f` SHA-256 is
`4e1f5452d5fd268d7e4f1ab702de4804bb8f34a429b5e2c14ff9af3df9a9a055`.
No geometry, solver source, prior freeze, criterion or acceptance flag changed.

Run `python3 verify.py` from this directory to recheck the record, all source
hashes, both source members, 35 output requests and exact eight-pair crosswalk.
This verification does not execute CalculiX or qualify native output.
