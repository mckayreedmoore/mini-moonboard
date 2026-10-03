# Proposed knee bridge: order and transport reconciliation

This is an **unadopted four-stack addition** to the frozen current order.
The existing 104 bolts, 104 nuts, 208 washers and 66 Hillman screws remain
current. [Force/geometry proposal](../upper-corner-screw-layout/knee-spine-reinforcement.md)
and [completed fit](knee-bridge-fit.md) supply the separate engineering basis.

| Proposed order change | Quantity / consequence |
| --- | --- |
| New 1/4-20 × 6.5-in partial-thread Grade 5 bolt lead, K.L. Jack `25C650HCS5Z` | 4; one additional stock family |
| Existing matched K.L. Jack `25CNFH5Z` metal nuts | Pool grows 84 → 88 |
| Declared thick-washer lead Hillman `885522`, Lowe's `755754` | Pool grows 8 → 16; four listed four-packs instead of two |
| Existing Lawson `FA21103` 8-in pool | Still 24 from one 25-pack, one spare |
| Total bolt / nut / washer needs if adopted | **108 / 108 / 216** |
| Hillman panel/kicker screws | **66**, unchanged |

All other order lines and family allocations are copied exactly from the
current `working-order/attempt03` export. No new price, delivery conformity,
package term for the bolt lead or complete order total is established. The
[stock profile](../upper-corner-screw-layout/knee-bridge-hardware.md) retains the
required nut/thread coordinates and declared washer geometry.

The geometric planning convention adds **0.262771 kg** of hardware and removes
**0.014812 kg** of wood, net **0.247959 kg**. Adding that delta arithmetically to
the frozen modeled frame gives **225.197914 kg**; the 25-kg equipment allowance
stays separate. These are planning weights, not measured parts or a new gravity
solve. Nominal solid shafts, full regular-hex heads, nominally bored hex nuts
and annular washers use 7,850 kg/m³; removed wood uses its original 600 kg/m³.
Threads, fillets and chamfers are omitted. Existing frame mass conventions
remain explicit; no added gravity is silently credited in the old force packet.

There are still **44 timber blanks / 50 timber-and-plywood bodies**. Reinforcement
bolts connect only the two faces of their own spine; they join no transport
members. They can remain in each spine during individual-member transport or
be removed using metal nuts. This introduces no routine wood-thread removal.
The [fit report](knee-bridge-fit.md) covers the installed and straight axial
envelopes; actual wrench turning/handling remains unobserved. This note does
not change the published shop sequence or authorize drilling.

## Frozen arithmetic receipt

The parent ran [knee_bridge_order.py](knee_bridge_order.py) once, with five
authenticated input/source pins and no software test or review loop.

| Artifact under `rawlocal/knee-bridge-order/attempt01/` | SHA-256 |
| --- | --- |
| `proposal-order.json` | `028542c6127320ce51410ed9f0910896a1ee1b13c5737fcdc68895b500e2ffe1` |
| `receipt.json` | `9dfd84b938fe7be0f7917c1bfef57f451cb26a53da94295c2accae91ac9b4774` |

Counts and receipt artifacts match. Current source order, model geometry,
authority, Actual/Disposition cells and physical-release flags are unchanged.
