# WJ-03 through-bolt procurement source note

**Snapshot date:** 2026-09-23. **Status:** sourced candidates only; no hardware selected, geometry released, or strength/capacity claim made.

This note reads the current WJ-03 `hardware.json` and `interfaces.json`. The exact CAD wood grips are 127.0 mm (5.000 in) for the eight post/header bolts and 177.8 mm (7.000 in) for the twelve side/bridge bolts. These are modeled dimensions, not measurements or manufacturing tolerances of delivered wood. `hardware.json` counts 20 bolts total: 8 × 6 in and 12 × 8 in. Each interface stack has a head washer, wood grip, nut-side washer, and one nut; the removal sequence lists the same components.

## Listed bolt candidates

| WJ-03 count | Direct product | Published product data | Listed price at snapshot |
|---:|---|---|---:|
| 8 × 6 in | [Bolt Depot #10, 1/4-20 × 6 in zinc-plated hex bolt](https://boltdepot.com/Product-Details?product=10) | Low-carbon steel (vendor says Grade 2 or A307A); ASME B18.2.1; partial thread; 7/16 in across flats; head height 0.150–0.163 in; under-head length tolerance +0.06/−0.10 in; minimum thread length 3/4 in. | $0.39 each; $26.12/100; $209/1,000 |
| 12 × 8 in | [Bolt Depot #14, 1/4-20 × 8 in zinc-plated hex bolt](https://boltdepot.com/Product-Details?product=14) | Low-carbon steel (vendor says Grade 2 or A307A); ASME B18.2.1; partial thread; 7/16 in across flats; head height 0.150–0.163 in; under-head length tolerance +0.10/−0.18 in; minimum thread length 1 in. | $0.90 each; $59.92/100; $479/1,000 |

The vendor pages offer piece and pack pricing but do not publish a live on-hand count. Their note says actual thread length may exceed the minimum and invites customers to ask them to measure current stock if thread length matters ([minimum-thread table and note](https://boltdepot.com/Fastener-Information/Bolts/US-Thread-Length)). Neither product page publishes an under-head thread-start range or maximum thread length.

## Nut and washer candidates

| Per WJ-03 | Direct product | Published dimensions/specification | Listed price at snapshot |
|---|---|---|---:|
| 1 × nut (20 total) | [Bolt Depot #2569, 1/4-20 zinc-plated Grade 5 steel hex nut](https://boltdepot.com/Product-Details?product=2569) | ASME B18.2.2; 7/16 in across flats (0.428–0.438 in); height 7/32 in (0.212–0.226 in). | $0.07 each; $4.86/100; $38.80/1,000 |
| 2 × washer (40 total) | [Bolt Depot #15021, 1/4 in zinc-plated Grade 5 steel USS washer](https://boltdepot.com/Product-Details?product=15021) | ASME B18.21.1; ID 5/16 in (0.307–0.327 in); OD 47/64 in (0.727–0.749 in); thickness 0.051–0.080 in. | $0.09 each; $6.19/100; $54.40/1,000 |

The USS washer envelope corresponds to the WJ-03 modeled washer envelope (18.6436 mm OD and 8.0 mm ID); its published tolerance range contains those nominal values. The nut listing gives the 7/16 in wrench flats and thickness used for the fit arithmetic. These are dimensional matches for evaluation only, not selections.

## Stack-length arithmetic and remaining thread-location gate

For a conservative three-thread projection at 1/4-20 (3 × 0.050 in = 0.150 in), the product maximum washer and nut dimensions give:

| Wood grip | Maximum washers (2 × 0.080 in) | Maximum nut height | Required under-head length with 3-thread projection | Candidate minimum under-head length | Length-only margin |
|---:|---:|---:|---:|---:|---:|
| 5.000 in | 0.160 in | 0.226 in | 5.536 in | 5.900 in (6 in less 0.100) | 0.364 in |
| 7.000 in | 0.160 in | 0.226 in | 7.536 in | 7.820 in (8 in less 0.180) | 0.284 in |

The stack has sufficient **total under-head length** for a full-height listed nut and 3 threads of projection at the bolt-length tolerance minimum, assuming actual washer/nut dimensions stay within their published ranges. The 2-thread projection alternative reduces each requirement by 0.050 in. This arithmetic does not establish that the nut is on thread.

To leave the entire modeled wood grip on smooth shank and have complete threads begin no later than the nut, the first complete thread would need to fall in a very narrow under-head interval based on the washer tolerances:

- 5 in grip: after the wood plus a maximum head-side washer, but by the earliest nut face: **5.080–5.102 in**.
- 7 in grip: same stack with the 7 in grip: **7.080–7.102 in**.

The product listings state only minimum thread lengths (3/4 in and 1 in), not thread-start locations or maximum thread lengths. Those minimums cannot establish either interval. An item that fits the overall length arithmetic may still place thread runout in the wood or leave some nut thickness short of complete thread. Do not treat either bolt as passing the WJ-03 smooth-shank/nut-engagement gate without vendor-confirmed dimensional limits for the delivered lot and the corresponding tolerance stack. No bolt strength or capacity is evaluated here.

## 20-bolt quantity estimate

At the displayed per-piece rates, the listed quantities total **$18.92** before freight and tax: 8 × #10 = $3.12; 12 × #14 = $10.80; 20 × #2569 nuts = $1.40; 40 × #15021 washers = $3.60. Vendor pack-tier prices are listed above; this estimate does not assume the 100-piece pack tiers or confirm a stock count.
