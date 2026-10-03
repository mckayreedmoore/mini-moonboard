# Complete washer-end sources without repeating mechanics

Status: **parent attempt02 completed with finite partial source coverage**.
This owner authenticated the returned packet and did not invoke its build.
The parent owns saved-state execution and subsequent land geometry queries.
The [consumer](washer-end-source-completion.py) reuses the completed
N09 worksheet and accepted common-knee response. It can additionally join the
full N10 endpoint export when that packet is available. It runs no shaft,
contact, plate, frame, CAD or native solver, and adds no tests or review loop.

The parent's first saved-arithmetic attempt stopped before output on the
unhandled `host_nut` end label. The corrected map recognizes `host_head`,
`host_nut`, `cleat_head` and `cleat_nut` separately. It binds the receiver to
the saved host/cleat identity and checks that identity and the saved physical
head-to-nut axis against the register. A nut is not assumed to belong to a
cleat. No source geometry or force changed; the failed attempt and consumed
producer remain recoverable. The parent then completed a fresh attempt02.

## Completed parent attempt02 and current continuation

`rawlocal/washer-end-source-completion/attempt02` returned
`FINITE_PARTIAL_END_SOURCE_COMPLETION`. It contains 1,056 outside-corner
end/state rows: 48 finite accepted common-knee end recoveries and 1,008 ordinary
rows explicitly pending because no N10 packet was supplied to that invocation.
The existing 48 retail plate states remain reused in their original packet.
The source receipt authenticates 222 input pins and five output artifacts.

| Completed artifact | SHA256 |
| --- | --- |
| `attempt02/receipt.json` | `d974544f39a670bde1d9a493754224b199fe10f5126fc266f9914101d5fcbe00` |
| `attempt02/washer-end-source-completion.json` | `dde08e37b195b0e416cf7d4316afd2c574e1460088e7476f97cac1773fae649e` |
| `attempt02/washer-end-states.jsonl` | `6ad344211dd4cdff6190bccb9ca34f2586117fb2078c992ca118c7c832a74ed0` |
| `attempt02/land-query-plan.json` | `a5bf7a49515766ed02b46af817e1795ef18e8ab259acdde83dee5185d5cd9c92` |
| Consumed producer | `dbf242d54ae501c0bf8d4241447837dcf08e7e4d2d108703f43a2fc0e1c078c9` |

The common-knee own-moment peak is `k12-right`,
`knee_outer_right_side_2`, head on `knee_outer_right_spine`:
M = 1179.093383 Nmm at the same-state T = 316.6720803 N. Its applicable
rigid wood-pressure/reference peak is 0.8187967191. These are saved first-order
model references, without a new washer capacity or frame-feedback claim.

Subsequent parent runs completed the
[120 generic land probes](washer-land-completion.md) and the
[eight actual top-side 5/16 washer rings](washer-land-reference-completion.md).
The latter has 48 finite probes and a maximum declared mean/reference ratio
of 0.3876062484; the generic quarter-inch clipping observation is not an actual
5/16 washer deficit.

The final N10 `two-recovery-attempt01` packet now has all 1,008 ordinary rows,
with 1,006 finite end sources and two explicit G7 null ends. The new
[final reference join](washer-end-reference-join.md) completed its parent
attempt01 with 1,054 finite sources in 1,056 rows, preserving the 48 common
rows unchanged and retaining the two nulls. It authenticated the exact
partial N10 result and its historical producer snapshots. This
attempt02 receipt, producer and output bytes remain unchanged. Its original
pending count records the earlier invocation, not the current N10 inventory.

## Finite question and inputs

The question is which authenticated own-seat demands can replace the old
unknown or isolated demands, and which of the 25 unresolved support bindings
actually require another geometry query. This is a source and applicability
continuation, not a new washer capacity method.

| Frozen input | Receipt or report SHA-256 |
| --- | --- |
| N09 `rawlocal/washer-reference-completion/attempt02/receipt.json` | `fceaeb1c3d2a2f4d6e23ec1beb19e48ad40e8ab1a2eac1d50b5d39b7af4acac2` |
| Common knee `rawlocal/knee-common-shafts/attempt01/receipt.json` | `7abd870ca5a3923937cc44ada389704f9977e0d3bb9ed0f546abb06ba283ffda` |
| Common knee `rawlocal/knee-common-shafts/attempt01/report.json` | `dd6228320aaeaef898e68b738c05ade574be9fa28e8c7473648e9f21b5c7b2b0` |

The corrected N09 producer stays frozen at
`8746aed9bba5c8a1a897bb1bbf60a14ecd3f0928a760803ca05a309231a3575a`.
Its [completed comparison](washer-reference-completion.md) contains 1,104
end/state rows, including 48 completed retail plate states with zero numerical
stops. The maximum sampled stress proxy is 207.203849 MPa, or 0.828815 of
hypothetical 250 MPa yield. That existing result is reused unchanged.

The [common knee packet](knee-common-shafts.md) accepted 12 conditional shared
receiver equilibria, containing 24 redistributed shaft records and 48 outer
washer ends. These replace the older isolated knee demands in the continuation.
The saved global frame response is not replaced.

Optional N10 must be a full `bolt_reference_completion_receipt/v2` packet with
`mode = full` and `washer-ends.jsonl`; an N01-only packet cannot provide it.
Its receipt hash must be supplied explicitly. All consumed packets bind the
same c3a8 comparison, 62bd response and ce69 gravity assessment used by N09.

## Original parent API

This preserves the API used for attempt02. The newer frozen N10 continuation
uses [washer-end-reference-join.py](washer-end-reference-join.py).

```python
result = consumer.build(output)

# Once the completed full N10 endpoint packet is frozen:
result = consumer.build(
    another_fresh_output,
    n10_directory=frozen_full_n10_directory,
    n10_receipt_sha256=frozen_full_n10_receipt_hash,
)
```

Use a fresh immediate child of `rawlocal/washer-end-source-completion/`.
Without N10, the ordinary 1,008 moment gaps remain null and explicitly pending;
the accepted 48 common-knee ends and land request plan can still be consumed.
With N10, exact keys must cover the same 1,008 ordinary end/state records.

The output is a separate 1,056-row outside-corner worksheet,
`washer-end-states.jsonl`, a finite summary
`washer-end-source-completion.json`, `land-query-plan.json`, producer snapshot
and receipt. The original 48 retail results remain referenced in their frozen
packet rather than copied or rerun. Thus the old 1,104-record coverage is not
silently expanded. Source pins are authenticated before and after the saved
arithmetic. Import is inert; AST/Ruff checks do not establish engineering
completion.

## Current common-knee demand replacement

The exact join is `(case_id, axis_id, end_role, receiver_member)`. For each
shaft, the current force is `redistributed_tension_n`, also checked against
`normal_transfer.single_physical_tie_n`. The old `source_tension_n` is kept as
comparison provenance, not substituted for the redistributed force. The
historical isolated T, M and source bindings remain in each replacement row.

The physical outer receivers are the first and last members in the pinned
shaft geometry. The middle base side has no exterior washer. The source says
`physical_head_to_nut_order_verified = false`; these are modeled role labels,
not an inspection of installed hardware.

Signed own-seat moments are recovered from the saved wood tractions:

```text
F = sum(point_force_on_receiver)
M_at_seat = sum((point - own_seat) cross point_force_on_receiver)
```

The seat comes from the pinned common input contract. The consumer checks the
recovered resultant against the saved common-datum wrench, the source's
numerical tolerances, the paired hardware/wood pressure balance, and the saved
scalar series moment. The common receiver or interface moment is never
relabeled as washer bending. Signed transverse components use the two saved
physical basis vectors. Updated means use the same-state redistributed force.

The worksheet reports separate same-state witnesses for force, moment,
eccentricity and applicable wood pressure/reference ratio. It does not combine
independent peaks. These shared receiver poses do not supply global frame
feedback, passive laws for the four internal V ties, elastic timber
qualification or complete joint acceptance.

## Ordinary N10 join and reused method limits

When supplied, N10 must identify the original tie row, current response hashes,
receiver, nominal seat and signed end force. For head-to-nut axis **n**, the
receiver force is **+T n** at the head and **−T n** at the nut. Its own pressure
moment is `own_end_M_signed_xyz_nmm`; the beam-end moment is opposite. The
consumer checks the independently saved pressure-resultant recovery. Null or
unsupported sources remain null.

| Route | Reused arithmetic or candidate | Limit retained |
| --- | --- | --- |
| Rigid annulus pressure | Evaluate `Kwood * max(closure + abs(tilt) * outer_radius, 0)` for the saved rigid law. Compare the peak only where the seat, annulus and full nominal support match. | Washer flexure and actual contact can change this pressure. |
| Ordinary/common quarter-inch washer | Identify the original fine plate family: ID 8.3058 mm, OD 18.4658 mm, head radius 5 mm and catalog-minimum thickness 1.2954 mm. | This is a method candidate; no plate calculation runs here. The wider 25.4 mm retail result is not transferred. |
| Central partial nut seat | Reuse the existing supported-ring static trial, optionally with the recovered N10 own-seat moment. | Concentric matching tractions and hypothetical ductile metal remain assumptions; no elastic compatibility or actual first yield. |
| Retained larger washers | Preserve their own annulus, support and recovered wrenches. | Existing quarter-inch or 5/16-inch plate families do not match them; no metal comparison is assigned. |

At zero T, the source contact law returns inactive zero-pressure contacts
regardless of stored tilt. The consumer preserves that rule rather than
using an unloaded, potentially nonunique stored tilt to invent a pressure
peak. This does not qualify physical unloaded seating or tilt uniqueness.

The central trial uses radii 4.1529–5 mm, area 24.3580923073 mm² and second
moment 257.2615141449 mm⁴. With recovered force **N** and transverse moment
magnitude **M**, its affine field is `q_min,max = N/A −/+ 5 M/I`. Only a
nonnegative field is compression admissible. For that explicit trial,
`q_max` is a required hypothetical ductile yield floor, not elastic first
yield or actual capacity. No unsupported crescent or full washer annulus is
credited. A negative trial minimum rejects that ansatz, not the assembly.

## Exact 25 support obligations and original geometry request

N09's original aggregate stays **208 physical lands, 183 applicable, 25
unproved or inapplicable**. The continuation does not rewrite that frozen
count. It partitions those 25 identities as follows:

| Existing obligation | Physical lands | Continuation |
| --- | ---: | --- |
| Central `center_principal_right_2` nut on `base_principal_center_right` | 1 | Reuse its known partial full-annulus failure and existing supported-ring alternative. Its effective STEP is unchanged. |
| Top outer `rail_1/rail_2` cleat nuts, left and right | 4 | Reuse current corrected retail land evidence at the current physical seats. The old generic support coordinates are not certified. |
| Left service and right wj06 upper/lower side heads on base sides | 8 | Query the effective STEP at the registered current head datums. |
| Bottom outer side heads, left and right | 4 | Query the effective STEP at current corner replay seat datums. |
| Top outer side heads and cleat nuts, left and right | 8 | Query the effective STEP at current corner replay seat datums. |

This leaves **20 new seat locations**, each using the original minimum-area
annulus, radii 4.1529/9.2329 mm. Retain the source depths 0.01/0.05/0.1 mm,
inward and outward: **120 intersections, 60 inward and 60 outward**. These
were prepared requests in this source packet. The parent subsequently executed
them in [washer-land-completion.md](washer-land-completion.md), preserving this
original plan. Outward results are recorded separately from inward support.
The actual top-side family was then checked in
[washer-land-reference-completion.md](washer-land-reference-completion.md).

Every request carries its physical axis/role/member key, old support source,
old STEP and point, effective STEP/path/hash, current point/normal source,
annulus and signed probe offsets. For corners, the current point comes from
the frozen fresh corner replay's own-seat recovery, checked unchanged across
all six cases. For the eight service/wj06 heads, the registered head point
must match the saved point. This avoids querying shifted corner geometry at
historical coordinates.

The four reused rail-cleat lands have separate N09 current support bindings
from `retail-washer-suite/attempt01-fine/checks.json` and
`corner-timber-sections/attempt02/checks.json`. Their corrected STEP matches
the effective member; the saved retail/current seat agrees within N09's
0.002 mm component tolerance. The consumer also requires the actual center
difference to fit inside the recorded own-bore, edge and other-bore margins.
The supported wider annulus has the same inner radius and outer radius
12.7 mm; those margins permit reuse for the nested minimum annulus at the
current seat. This replaces a stale nominal land datum; it does not prove
the old point or loaded washer shift/tilt.

## Preservation and next decision

The earlier unexecuted draft is recoverable under ignored
`rawlocal/washer-end-source-completion/preparation-end-transfer/`.
The first prepared source, before its zero-T law correction, is also preserved
under `rawlocal/washer-end-source-completion/preparation-58f1/`.
The b83e source consumed by the failed end-role attempt and its documentation
are also preserved under `preparation-b83e/`. Original
N09 source/raw outputs and the accepted common-knee packet stay frozen. No
geometry, hardware, source forces, authority or release flags are changed.
Actual washer stress, yield and capacity remain null.

The parent consumed the accepted common ends and completed the nominal land
queries. The [new finite join](washer-end-reference-join.md) adds the final
N10 export, retaining its two unresolved G7 ends. Any later plate/contact
calculation should select a matching existing method
and explicit material assumptions. This continuation claims no completed
washer resistance criterion, whole joint acceptance or fabrication release.
