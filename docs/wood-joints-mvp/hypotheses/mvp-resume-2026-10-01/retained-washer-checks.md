# Retained frame washers: current dimensional binding

## Result and decision

The twelve retained bolts now have separate 3/8-inch and 1/2-inch washer
geometry bound to all six current nominal force states. This supplies
**24 exterior washer roles and 144 seat-state records**, using the same
72 signed bolt ties as the current remaining-joint screen. Quarter-inch
washer dimensions are not transferred to these stacks.

| Conditional washer family | Roles / seat states | Minimum OD, mm | Maximum ID, mm | Saved bore diameter, mm | Ideal full-support area, mm² | Peak ideal pressure / Fc-perp |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| [Bolt Depot 15023](https://boltdepot.com/Product-Details?product=15023), retained 3/8-inch front/rear bolts | 16 / 96 | 25.2222 | 11.5062 | 11.1125 | 395.657468 | **0.208291** |
| [Bolt Depot 15025](https://boltdepot.com/Product-Details?product=15025), retained 1/2-inch upper-leg bolts | 8 / 48 | 34.7472 | 14.6558 | 14.2875 | 779.566923 | **0.287806** |

The 3/8-inch peak is `rail_front_bolt_right_2`, K12-right: simultaneous tie
355.131153 N and ideal pressure 0.897572 MPa. The 1/2-inch peak is
`lumber_leg_bolt_right_2`, K12-right: tie 966.833771 N and ideal pressure
1.240219 MPa. Head and nut roles carry the same saved tie; each role retains
its own receiver identity and saved bore. The wood reference is the existing
conditional DF-L No.2 base perpendicular bearing, **4.309223 MPa**.

The dimensional part of the previous `RETAINED_WASHER` gap is addressed.
**Full-seat support is unknown for all 24 roles. Actual pressure, wood
bearing acceptance and washer metal acceptance remain null in every state.**
The ideal comparisons do not select hardware, establish the full annulus
on sound wood, or accept the joints. Numeric washer yield, head/nut bearing
faces, eccentricity, tilt, bridging and preload remain separate conditions.
There is no new larger-washer decision from this ideal comparison.

## Calculation and source scope

[retained_washer_checks.py](retained_washer_checks.py) uses
`A=π(ODmin²−max(IDmax, Dbore)²)/4` and `p=T/A`. Catalog ID governs the
unsupported central opening in both families. Minimum thicknesses 1.6256
and 2.1844 mm are retained as dimensional inputs; no metal resistance is
assigned from those thicknesses or the catalog Grade 5 washer label.

The washer ranges reuse the unchanged [hardware engagement specification](assembly-package/hardware-engagement.md)
and its source `assembly-package/hardware_engagement.py`, SHA-256
`d8e2a08e46fd9507a89d8e7ecb238ddf229490f4909345cbb641374ee8133295`.
The producer reads the literal dimensional table without executing that
older worksheet or consuming its historical forces. Saved bore diameters
come from `../current-finished-feature-register-2026-10-01/axis-features.json`,
SHA-256 `bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19`.
The retained geometry register supplies receiver identities and unchanged
retained bore bindings. These are modeled dimensions, not delivered stock,
cut-hole measurements or drill-bit instructions.

Current forces come only from
`remaining-joint-screen-attempt04/all-two-receiver-92ksi/screen.json`, SHA-256
`5b85139b2acaefd8ff74df916229766438c0caf3bc9c3a1a7b5080f8f393033a`,
and its hash-bound `bolt-states.csv`. The underlying frame is
`two-receiver-frame-attempt03/`. Its bounded, nonunique nominal seating
permits saved-force comparison but establishes neither unique pose nor a
motion envelope or strict tangent stability. No historical three-rear-case
force record was reused as current demand.

All **14 input bindings**, including eight distinct retained receiver
STEP files, matched before and after calculation. The source file retains
the original geometry pins; neither binding a bore radius nor reusing a
retained receiver proves an exterior washer footprint. No CAD regeneration,
fresh seat-support query, frame/native solve, software test or review agent
was used. Ruff passes.

Current local result: `retained-washer-attempt01/checks.json`, SHA-256
`55ad4689489bc965cde1d182a68c5171723a835180966f2b0e9fed2229faa2e1`.
Its exact producer snapshot and raw output are ignored/local. Replay requires
the preserved source files and `/tmp` geometry register; the published
source is not a complete raw-evidence backup.

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/retained_washer_checks.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/retained-washer-attempt02
```

Use a fresh output directory. All 47 criteria remain pending, all eight
release flags remain false and Actual/Disposition cells stay blank.
Reviewed geometry, hardware policy, existing frozen outputs, the panel
deficit and top-rail proxy exception are unchanged.
