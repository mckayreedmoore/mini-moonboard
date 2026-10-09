# Intermediate bolt-length proposal

This follows the [issued hardware worksheet](../hardware.md) and reuses its
scalar dimension-window helper. The complete 100 axis records in the
[aligned-wire geometry](../../occupied-aligned-wire-v1.json) exactly match the
raised-rail records. This establishes reuse of their nominal stack dimensions;
it transfers no force, strength, installed-hardware or tool-access pass.

The previous shop-window study already checks the next listed 5-, 7- and
9-inch bolts. Those improve tip projection but cannot guarantee conservative
nut seating within the recorded dimension boxes. This study checks the
intermediate 4¾-, 6½- and 8½-inch lengths against the same nominal receiver
stacks and catalog washer/nut bounds.

| Quantity | Existing → proposed length | Minimum two-pitch margin | Minimum nut-near minus Lg | Added nominal tip/withdrawal length |
| ---: | --- | ---: | ---: | ---: |
| 16 | 3/8 × 4½ → 4¾ in | 5.842 mm | 3.2512 mm | 6.35 mm |
| 4 | 3/8 × 6 → 6½ in | 10.160 mm | 3.2512 mm | 12.7 mm |
| 4 | 1/2 × 8 → 8½ in | 11.535508 mm | 4.3688 mm | 12.7 mm |

All three conditional length/gage comparisons are positive. The calculation
checks all 24 identified axes, verifies 879 source pins before and after, and
independently enumerates 96 comparison-box corners. The other 76 shafts retain
their issued nominal proposals. [Inputs](inputs.json), [helper](analyze.py)
and [result](result.json) preserve the exact source and axis joins.

These products remain unadopted. Their tips and withdrawal lengths would
change the occupied model. The proposal does not add spacers, change washers,
cut bolts, relocate axes or substitute fully threaded bolts.

## Procurement leads and standard limits

Primary listings identify partially threaded Grade 5 hex cap screws:

- [Zoro G0341148 / N01200.037.0475](https://www.zoro.com/zoro-select-grade-5-38-16-hex-head-cap-screw-zinc-plated-steel-4-34-in-l-10-pk-n012000370475/i/G0341148/): 3/8-16 × 4¾ in, $9.15 per ten.
- [Grainger 38WP04 / N01200.037.0650](https://www.grainger.com/product/Hex-Head-Cap-Screw-Steel-38WP04): 3/8-16 × 6½ in, $22.49 per ten.
- [Zoro G0340956 / N01200.050.0850](https://www.zoro.com/zoro-select-grade-5-12-13-hex-head-cap-screw-zinc-plated-steel-8-12-in-l-5-pk-n012000500850/i/G0340956/): 1/2-13 × 8½ in, $15.15 per five.

Buying two, one and one packs respectively would cost **$55.94** for these
replacement-bolt proposals, including eleven spares, before shipping/tax.
These October 8 MDT / October 9 UTC 2026 listing observations are not an
inventory confirmation, delivered-part selection or complete hardware quote.
The original full basket and its cost remain unchanged.

The numerical comparison uses the existing
[ASME B18.2.1-2012 PDF](https://www.wanhong-fastener.com/wp-content/uploads/2025/04/ASME-B18.2.1-2012.pdf),
SHA `c3b36b05e45149816941ae0d3e3e17c808831ce4d93f9f082424d9ecebaaa0a6`.
Table 12 gives Lg/Lb values of 3.75/3.44, 5.25/4.94 and 7.00/6.62 inches;
Table 13 gives minus length tolerances of 0.10, 0.18 and 0.18 inches.
The listed standards do not name an edition. Applying this table requires
the applicable full-body cap-screw definition and finished-part dimensional
agreement: the standard dimensions concern uncoated parts. Lg is a grip-gaging
coordinate; it is not an observed first full-form thread. Nominal thread
length is a calculation reference, and the tabulated values govern.

## Remaining fit and mechanics questions

The comparison does not establish full smooth bearing. Against the saved
farthest-bearing body targets, minimum bodies remain short by **10.5156 mm**
for both 3/8-inch groups and **12.827 mm** for the 1/2-inch group. Even the Lg
maxima are headward of those targets by the modeled head-washer thicknesses.
These are profile diagnostics, not failed or accepted joint resistances.

Resolve actual thread/runout and nut active-thread intervals, applicable
thread-bearing resistance, finished coating dimensions, washer/fillet seating
and the new tip/tool/removal envelopes before adopting the proposals. The
merchant drawings add nominal dimensions without tighter transition bounds.
Actual observations remain blank. All hardware-adoption, fit, strength,
fabrication and climbing release flags remain false.

## Reproduction and retention

Run from the repository root with a fresh output path:

```sh
uv run python -B docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/bolt-window-followup-v1/analyze.py --out /tmp/eoere-intermediate-bolt-reproduced.json
```

The standard-library helper reuses the frozen hardware preparation and
dimension functions. It performs no CAD, solver, force-field or physical work.
Keep this small proposal and its existing source consumers active. Do not
overwrite the issued shop tables, old long-bolt result or frozen geometry.
