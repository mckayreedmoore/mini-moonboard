# V11 shorter-bolt shopping and readiness note

This is a corrected projection of the frozen V1 current-stack schedule, not a new hardware selection. The V2 machine record is `fea/generated/v11-shorter-bolts-v1/build-package/hardware/shopping-schedule-v2.json` (SHA-256 `bb557b511ea908af73d72f3eaa792a693e3a0009986f9eb2a4f36855b15f2658`); it derives from V1 `fea/generated/v11-shorter-bolts-v1/build-package/hardware/shopping-schedule-v1.json` (SHA-256 `996a64b0614df23284a76c606ebc7edc3c049652588d4273f9d4265b7fcb45bc`). The grouped shopping CSV and axis crosswalk remain byte-identical to V1 (SHA-256 `d709c04c20475fa4567fba9cbdd54c3bd482338c674b0faae308ca73757809db` and `9bc09b70875b39769b1b6ee4d79934bc300e351372e0805074e2ce5a9ea37fc5`).

## Current modeled quantities

| Item | Quantity | Current SKU grouping |
|---|---:|---|
| 3/8-in bolts | 110 | 363 × 48; 365 × 8; 368 × 2; 372 × 4; G0341148 × 32; 8092 × 4; 8093 × 12 |
| 1/2-in bolts | 2 | G0340956 × 2 |
| Nuts | 112 | 2571 × 90; 2573 × 2; 2584 × 20 |
| Washers | 224 | 15023 × 220; 15025 × 4 |
| Sleeves | 4 | 13731 × 4, retained at the four lower cleat-post stacks |

The current model requires 24 ZX128-B-T4 angle bodies. The owner reports their identity and ownership, but no observed or reported delivered count is recorded; they are not included in the 452 modeled bolt-stack fastener pieces. The 66 Hillman panel/kicker screws are also outside this schedule. Historical catalog links are in `shopping-list-v1.csv`; prices, current stock and delivery were not checked.

## Readiness

The 16 outer-top G0341148 axes remain held for the unresolved 3/8-in spacing/end/oblique design review. The 16 A574 axes (8092 × 4 and 8093 × 12) remain held for the applicable yield-property/method basis. These are the two named holds represented in the 80-axis planning partition; those other axes have not thereby passed all remaining checks.

The cleat basis remains the V9 pair of two nominal 19.05-mm plywood leaves per cleat (38.1 mm nominal, 36.5 mm strength-allowance scenario), with perfect bond/no slip only as a modeling assumption. No current cleat adhesive/process is selected. The 112-axis fit crosswalk preserves blank `Actual` and `Disposition` fields. Bolts and nuts are reported not purchased. Purchase, drilling, fabrication and climbing are not released; geometry bore envelopes are not drill-bit instructions.
