# Conditional base reaction recovery

The [source-bound report](../fea/results/timber-base-demand.json) recovers
aggregate base-on-board forces and moments from the accepted
`timber-base-development` mesh. It includes all six original cases and 216
asymmetric scenarios reconstructed from nine independently audited linear basis
solutions. No new solver run or connection-capacity calculation was performed.

The base free body contains the header, four posts, both kicker panels and both
plywood gussets. It excludes the inclined frame and legs. Its common moment
reference is the header center: approximately `(0, −178.875, 205.95)` mm.
With no gravity or external climbing load applied directly to this free body,
its summed floor reaction equals its aggregate action on the remaining board.
Original undeformed coordinates are used for these linear calculations.

## Important floor-support finding

The existing fixed-floor model constrains the **kicker bottom as well as the
posts**. There are 911 unique base floor nodes. Per-body membership is 281 nodes
on the left kicker, 313 on the right kicker, and 83 on each of four posts.
These counts overlap at shared boundaries; the resultant uses each node once.
Some kicker nodes lie well outside the post footprints. The recovered action
therefore cannot be described as post-only support or transferred to a base with
a floating kicker. Actual contact, friction, separation and structural credit
for the kicker require a separate model and physical design decision.

For the original 2.4 kN downward case, the aggregate base-on-board result is:

| Board-local component | Value |
| --- | ---: |
| X force | −0.7225 N |
| S force | 236.3300 N |
| N force | −575.3395 N |
| Moment about X | 164,469.0949 Nmm |
| Moment about S | −40,314.5795 Nmm |
| Moment about N | −4,802.5860 Nmm |

S follows the inclined board upward; N points toward its backing. The report
also provides world components and the equal-and-opposite board-on-base action.
These values are **not individual gusset, backing, clip or bolt demands**.
Internal force distribution among the base members is not recovered here.

## Evidence boundary and next use

Archived input/output hashes, mesh identity, basis equilibrium and scenario
replay are authenticated before recovery. CAD contact membership must exhaust
the non-leg floor nodes without overlapping either leg footprint. The selected
load nodes must lie outside the base group. Tests independently sum scalar
forces and moments, compare all reported cases, and reconstruct physical contact
membership. Missing evidence fails rather than being skipped.

The mesh remains isotropic, fixed-floor and ideally bonded, including unintended
leg-to-panel-edge load transfer. This result does not qualify the newer wide
variant, real unanchored behavior, any joint resistance or a climber rating.
Use it to identify the lower load path and support assumptions before deriving
local demands described in the [connection qualification ledger](connection-qualification-ledger.md).

```bash
uv run pytest -q tests/test_timber_base_demand.py tests/test_timber_base_evidence.py
```

The recovery command is `uv run python -m fea.timber_base_demand`. It refuses to
overwrite its existing report; reproduction requires a fresh output location.
