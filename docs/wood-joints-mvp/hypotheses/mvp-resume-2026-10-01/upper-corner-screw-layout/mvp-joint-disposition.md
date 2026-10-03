# Joint MVP working disposition

## Working scenario

Use the [current analytical packet](../README.md#current-analytical-working-model-for-the-mvp-goal): six nominal cases, **250 lb × 2 downward, signed 300 N horizontal, original 100 mm hold lever**, recorded gravity and separate 25 kg accessory allowance. The complete zero/nominal source is retained; the 50 mm comparison is non-adopted.

The [working force register](working-joint-register.md) covers **24 blocks, 104 structural bolts and 66 purchased Hillman 42605 screws**: 624 bolt-axis states, 648 bolt-interface states and 396 screw states. Twenty corrected axes use their local allocations; 84 retain source-frame records. Local result counts below overlap this inventory and must not be added to it.

Working assumptions: dry DF-L No. 2, stated wood/steel properties, partially threaded smooth-shank bolt envelopes, first-order local geometry, rigid timber, K20 compression-only contacts, concentric washer lands, unqualified Hillman stiffness/plywood properties and no-slip floor. Local reallocations do not feed back into the frame. Nonunique seating supplies no motion/stability acceptance.

## Completed finite checks and explicit exceptions

Indices compare demands with each method's own declared reference; different maxima are not combined. A component index below one establishes that comparison only.

| Scope | Finite result under stated assumptions | Evidence / working disposition |
| --- | --- | --- |
| Top outer corners | Both groups balance together: **12 block / 24 host / 48 bolt states**. Maximum lateral/path/mean-seat/smooth-steel indices **0.814 / 0.160 / 0.769 / 0.319**. | [Transfer](corner-first-order.md), [references](corner-first-order-components.md). Finite transfer and component comparisons complete. |
| Bottom outer corners | Transfer and **all 48 fresh component records complete**. Maximum 45/92 ksi lateral **0.398 / 0.278**, concurrent steel reserve **0.280**, path **0.0366**, mean-seat **0.229**, smooth-steel **0.112**. | [Transfer](bottom-corner-transfer.md), [references](bottom-corner-components.md). All reported comparisons below their declared references; left governs these maxima. |
| Four continuous knee shafts | **All 24 loaded states** close three receiver wrenches; 96 placements retained. Smooth steel **192.479 MPa**, index **0.303** against the 92 ksi hypothesis. | [Loaded-shaft completion](knee-contact-entry.md). Isolated force boundaries; no shared-group/body-pose envelope. |
| Six header duties | **72 bolt states / 36 interfaces**; six supported-boundary maps preserve signed wrenches. Twelve supported seats; 116 contact centroids on wood. Peak tie **239.705 N**, mean **1.122 MPa**. | [References](header-replay.md), [boundary map](header-traction-map.md). Opposite-wall/ligament-sharing hypotheses retained; full A1-rear torque **−12.768 N·m** remains despite zero knee contact samples. |
| Central partial nut seat | Six ties admit the centered supported-ring route: peak **22.952 N**, trial **0.942 MPa**, mean wood index **0.219**. Signed coupon/integrals complete. | [Static route](central-seat-transfer.md). Unsupported crescent unloaded; centering, rigid nut land and ductile plastic interpretation explicit. |
| Panels / 66 screws | Head demand **1871.251 N**, simultaneous lateral **726.611 N**, A12-rear upper-left `edge_2`; favorable nominal-head references **930.222–984.128 N** remain exceeded. All twelve ties/contact actions balance in this state. | [Head worksheet](head-reference-basis.md), [complete saved path](panel-path-reconciliation.md), [panel material](panel-material-fidelity.md). **Declared reference exception**; actual Hillman resistance/stiffness unverified. |
| Members / top rail | Under the declared C_D = 1.25 rated-peak hypothesis, normal/face/component-bound peaks **0.519 / 0.817 / 0.951**. Permanent C_D = 0.9 peaks **0.174 / 0.133 / 0.182**. Original C_D = 1 rail face remains **1.021524**. | [Duration basis](member-duration.md), [permanent calculation](dead-load-check.md), [original replay](member-replay.md). Finite conditional duration comparisons complete; original exceedance and method limits preserved. |
| Other duties / retained pairs | Existing exclusions retained; row-factor sensitivity **0.963**, ideal washer wood indices **0.208 / 0.264**. | [Register](joint-register.md), [24-block duties](remaining-block-duties.md), [methods](bolted-replay.md). Applicable component evidence reused. |

The [top-corner nominal net-section comparison](corner-net-section.md) covers eight deciding signed cuts and 24 actual ligaments. Tension/compression/bending indices are **0.0781 / 0.0286 / 0.0430**; the same-state regional shear/torsion bound is **0.2420**. Exact regional offsets recover all six wrench components. Common longitudinal strain, end-bridge continuity, area-shared transverse force and equal-modulus twist remain explicit MVP assumptions; no notch or splitting capacity is assigned.

The completed [four-corner static group assessment](corner-group-finish.md) covers **24 states / 101,276 finite signed cuts** using physical wall/seat/contact forces and weight once. Grain shear/torsion, normal diagnostic, single-channel and two-rail-row longitudinal references peak at **0.3349 / 0.0538 / 0.1699 / 0.0991**. Transverse opening stress reaches **0.1700 MPa** with no adopted perpendicular-tension or whole crossed-group capacity; local cracking remains the explicit working assumption.

The [remaining twelve blocks](remaining-net-sections.md) complete **2,304 recorded opening-section limits** across all six cases under the same assumptions. The normal diagnostic sum and same-state shear/torsion bound peak at **0.00180 / 0.03221**. These are finite nominal section comparisons; continuous-station maxima and notch/splitting capacity are outside the method.

The [six header paired-bore sections](header-net-section.md) complete **72 signed limits / 216 regional comparisons** using all 394 source actions per case. Tension/compression/bending indices are **0.2557 / 0.1281 / 0.1632**; the same-state shear/torsion bound is **0.3486**. Full A1-rear torque is retained. This completes the finite nominal comparison under the same sharing assumptions, without new strength or qualification.

The [six header cleat bodies](header-cleat-net-sections.md) complete another **1,968 signed traces / 36 body-case comparisons** using a documented retained-rectangle subset around longitudinal holes. Normal diagnostic/shear bound peaks are **0.02093 / 0.13814**. Omitted sound wood and nominal sharing assumptions are explicit; no local stress bound or splitting capacity is inferred.

The [two knee spines](knee-spine-net-sections.md) complete **600 existing opening-section limits** across all six cases. Normal diagnostic/shear bound peaks are **0.09635 / 0.38258**. Their asymmetric net centroids, full signed torque and original global-force scope are retained; local shaft fields and splitting capacity are not transferred.

The [retail thick-washer option](retail-washer.md) completes two resolutions at the current **707.884 N / 2.432 N·m** witness. Declared **25.4/8.3058/2.5 mm OD/ID/thickness** gives finer stress **207.205 MPa**, index **0.829** against assumed 250 MPa yield, with saved nominal timber support. This changes no inventory and qualifies no actual retail material.

## Practical disposition

The finite checks provide a reproducible conditional working model. Complete joint qualification and the panel reference exception remain open. Rail duration comparisons complete under the stated cumulative-peak assumption; the original normal-duration exceedance remains recorded.

Bottom left's governing record is A1-rear `side_1`: simultaneous **T=203.598 N, V=243.435 N**, smooth steel **71.254 MPa**. Right lateral/steel governs at K12-rear `side_1`: **T=5.283 N, V=4.842 N**; its path and mean-seat peaks are separate A12-left records.

The coordinator sets MVP disposition with the panel deficit and original rail finding visible. Neither is an observed physical failure. This sheet commissions no further models, research, tests or external sign-off.

Actual hardware/washer capacity, full splitting/group/torque resistance and delivered fit remain unqualified where stated. Equilibrium and small component indices supply no missing capacity. **47-criterion authority, complete-joint HOLD and fabrication/physical-release flags remain unchanged**.

## Conditional shop references

Use the [shop guide](../assembly-package/shop-guide.md), [joint addendum](../assembly-package/current-joint-addendum.md), [length fit](../assembly-package/hardware-length-fit.md), [costs](../assembly-package/catalog-costs.md) and [66-axis overlay](shop-addendum.md): 62 axes unchanged, four moved, two center receivers now `base_rail_top`. Historical STEP holes are not extra drill instructions.

BOM: 20 frame timber bodies, 24 blocks, 44 timber blanks, six plywood bodies, 104 bolt stacks/nuts, 208 washers, 66 panel/kicker screws. Owner-reported assembly/movement acceptability remains a working assumption. No build or floor inspection is claimed; Actual/Disposition cells stay blank until observed. No physical work is authorized.

## Frozen receipt index

Paths below are relative to this folder; linked notes contain complete source/output receipts.

| Saved result | SHA-256 |
| --- | --- |
| `frame-250-attempt02/comparison.json` | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| Same frame, `response.npz` | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| `rawlocal/working-joint-register/attempt03/register.json` | `c34745395481038e32c7474de1798882263de7e54a7cc494949948b4a5e3464c` |
| `rawlocal/dead-load-check/parent-attempt06/comparison.json` | `20802196776a89ea8b041832b413ef8d8613493b1bf36f89a3810807c5166e75` |
| `rawlocal/header-cleat-net-sections/attempt01/checks.json` | `b70fd818654a4d6509186a2718a81fa0b564cfc7ad808be52946f0eddfead1a2` |
| `rawlocal/knee-spine-net-sections/attempt02/checks.json` | `6b6c8df94f1ccab859ee980dd1835ba19286718f44e8a36ce6b9d0014064fc85` |
| `rawlocal/corner-group-finish/attempt03/checks.json` | `2ae3a84f273823dc6ca751e6fdddab8e0d70425ee7b34e1e38ebc79d5b672f23` |
| `rawlocal/corner-first-order-components/attempt01/checks.json` | `f220673994b6a6c5b6bc0afd104becd61b5bb68f5e22bc700ed07b901b94525c` |
| `rawlocal/bottom-corner-transfer/first-order-attempt01/checks.json` | `4d255ba5ebd8f1f93fb41ef90511eb3da49906f4729f33f5f63766e0a0bd78ed` |
| `rawlocal/bottom-corner-components/attempt01/checks.json` | `39e698d7ffec6646e2295f5ce96be0764ea8fbe6654ed3b0e881040b410bcc95` |
| Same component packet, `receipt.json` | `7a241d0e035167c2d920277d9c9f33ac12a919531d2b37c74c6819a0fd58e2ff` |
| `rawlocal/knee-contact-entry/suite-attempt01/suite.json` | `b707952e5ad740ad2ebc0306bce17a37e4718e88c1164cba568d9a39a6e8b79a` |
| `rawlocal/header-traction-map/attempt01/result.json` | `39d63b41dc495659b02cb4ff4fb638a19a491bc09e6ea3fd76a70314db08a837` |
| `rawlocal/central-seat-transfer/coupon-attempt01/coupon.json` | `bdc35b60ca03039f6e5acad8c5c81784086368a3472183ae7515f66335fe41bb` |

Parent authenticated the current result/source/output bindings and local links before publication. Each linked calculation retains its stated method scope. Original source vectors and formal flags remain unchanged; no software tests or agent review loop ran.
