# Current wide-candidate hardware purchase schedule

The [generated CSV](wide-purchase-bom.csv) consolidates the installed hardware in
`wide-principal-development`. Quantities come from the authenticated published
parts and connection schedules, not from older variant totals. They exclude
spares and package rounding. This is a procurement planning artifact, not an
instruction to purchase unqualified hardware or approval to build.

| Installed hardware | Quantity |
| --- | ---: |
| 3/8-16 × 2½ in (63.5 mm) stitch bolts | 6 |
| 3/8-16 × 3 in (76.2 mm) gusset bolts | 8 |
| 3/8-16 × 3¾ in (95.25 mm) leg/rim bolts | 8 |
| 3/8-16 × 6 in (152.4 mm) backing bolts | 2 |
| Finished 3/8-16 nuts | 24 |
| SAE 3/8 flat washers, two per bolt | 48 |
| E-Z LOK 801420-13 inserts | 56 |
| Dottie FMDD14114 1/4-20 × 1¼ in flat-head machine screws | 56 |
| Simpson ML24Z angles | 18 |
| Simpson SDS25112 screws, purchased separately | 108 |

Bolt lengths are measured under the head; flat-head machine-screw length includes
the head. The eight leg/rim bolts have the previously selected Conquest
HBA-38X334 identity. Other lengths remain the recorded Conquest-family candidates:
the specification sheet establishes dimensional family, not every exact orderable
SKU. Confirm supplier availability, finish compatibility, full nut engagement and
the actual stack before purchase. Do not import the 114-bolt historical totals
from [the original hardware study](selected-bolt-hardware.md).

The CSV preserves existing product references from that study,
[insert selection](panel-insert-selection.md) and
[ML24Z qualification](ml24z-qualification.md). It does not assign washer bending
resistance, insert anchorage, tightening torque, locking method, or connector
capacity. The [current fit audit](current-fastener-fit-audit.md) and
[qualification ledger](connection-qualification-ledger.md) remain applicable.

## Separate items

Wood stock stays in the [candidate cut schedule](../exports/wide-principal-development/wide-principal-development_parts.csv)
and [stock/assembly notes](wide-principal-development.md). Holds, hold bolts,
T-nuts and their flange screws, the purchased MoonBoard LED kit, wiring accessories,
finishes, adhesives, tools and the separate crash pad are **not counted in this
structural-hardware CSV**. Their omission does not mean they are unnecessary;
the user's existing hold/LED inventory must be reconciled separately. No spare
percentage or package size is assumed.

## Reproduction

```bash
uv run python scripts/wide_purchase_bom.py
uv run pytest -q tests/test_wide_purchase_bom.py
```

The script verifies published source and CSV hashes, rejects unclassified
connections, and regenerates only this new CSV. It performs no CAD operation and
does not change historical models or exports.
