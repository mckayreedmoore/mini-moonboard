# Denver-region timber price lookup, attempt 02

**Accessed:** 2026-09-27. **Status:** incremental public-listing evidence only;
no candidate product, local quote, purchase quantity, or release.

This lookup is for `compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`. The source is the current
[attempt01 timber source/yield schedule][schedule] (SHA-256
`2c710708d5e775d742375e28fadd323ecfe7f8e81c186c6028704c903a65266c`). That
schedule pins the reviewed [attempt02 full-frame manifest][manifest] at SHA-256
`21073d852474d4443f61f2172cd9eabc3ce49ee86414facb105773822e3c60f3`.

## Required stock classes and schedule quantities

The source schedule contains 20 preserved frame records: four nominal 4×6
records with 9,198.378 mm of recorded source length and sixteen nominal 2×6
records with 20,582.770 mm. Sixteen frame hosts are rebuilt in the reviewed
manifest. Those old source lengths do not measure current material removal or
define a purchase list.

The same schedule groups 24 current proposed blocks as follows:

| Stock class | Frame source records | Block blanks | Combined length |
| --- | ---: | ---: | ---: |
| 4×4 | 0 | 18 / 2,140.2 mm | 2,140.2 mm |
| 4×6 | 4 / 9,198.378 mm | 4 / 547.4 mm | 9,745.778 mm |
| 2×6 | 16 / 20,582.770 mm | 2 / 552.6 mm | 21,135.370 mm |

The proposed block length groups are:

- 4×4: 15 × 119.7 mm, 1 × 86.9 mm, and 2 × 128.9 mm.
- 4×6: 2 × 134.7 mm from proposed 88.9 × 139.7 mm stock, ripped to
  83.9 × 139.7 mm; and 2 × 139.0 mm ripped to 88.9 × 133.35 mm.
- 2×6: 2 × 276.3 mm.

The two 4×6 rip groups propose 5 mm and 6.35 mm section reductions,
respectively.

These are source/proposed blank records, not purchased-stick counts. There is no
cut nesting, kerf/end-trim, defect, surfacing, or receiving-loss allowance.
Actual stock yield and quantities remain unresolved.

## Public supplier observations

Front Range Lumber is the confirmed local yard in this screen. Its Denver-region
pages list Douglas-fir 4×4 in 8, 10, 12, 16, and 20 ft; 4×6 in 8, 10, 12, and
16 ft; and 2×6 framing lumber in 8 through 20 ft lengths. The pages publish no
item prices and say listed products and lengths may not be available at either
location. This is size guidance, not a live inventory result.

Denver Fence Supply publishes these unit-price listings. Its product pages
also return structured seller offers marked `InStock`, priced in USD, with
`priceValidUntil` / `validThrough` of 2027-12-31:

| Seller listing | Public price | Structured availability |
| --- | ---: | --- |
| 4×4×8 Grade A (SKU 5363) | $22.50 each | `InStock` |
| 4×6×8 WRC (SKU 5366) | $41.45 each | `InStock` |
| 2×6×8 WRC (SKU 5360) | $16.88 each | `InStock` |

The 4×4 page calls its item “Grade A” and categorizes it as a post; it gives
no species, grading rule, actual section, treatment, or store quantity. The
4×6 and 2×6 titles say “WRC”; neither page gives actual section, grade,
treatment, or store quantity.

Denver Fence Supply's official [homepage][dfs-home] identifies it as a locally
owned business located in Commerce City, Colorado. The reviewed product pages
still provide no branch-level quantity: `InStock` is the seller's online offer
status, not an on-hand count for Commerce City. The public page metadata does
not give a price-change date; the validity date is listing metadata, not a
supplier quote.

Cedar Fence Direct, with a published Wheat Ridge / Denver location, lists
4×4×8 Western Red Cedar STD at $24.99 each and labels its Western Red Cedar
fencing “in stock.” Its site describes the product as fencing stock and does
not give a location-specific quantity or an actual section for this item.
This is a local public price observation, not a DF-L lumber match.

Lowe's and Home Depot product pages were reopened on the access date. Their
2×6×8, 4×4×8, and 4×6×8 Douglas-fir / fir pages are listing leads only. Lowe's
asks for a ZIP or city to return pricing and availability; Home Depot shows
“Select store.” No amount or Denver store inventory was visible without those
inputs, which were not supplied. Lowe's listing specifications include:

- 2×6×8 #2 Prime Douglas-fir, kiln-dried, actual 1.5 × 5.5 in; page lists
  anti-stain treatment without identifying its chemistry.
- [4×4×8 #2 Premium Douglas-fir listing][lowes-4x4], green. Its overview gives
  actual 3.563 × 3.563 in; its detailed specification table lists 3.562 ×
  3.562 in. The page also lists contact type “Above ground” and “Meets AWPA
  Standards: Yes”; neither identifies treatment or confirms compatibility
  with the candidate's material scenario.
- 4×6×8 #2 & Better Douglas-fir, green, S4S, actual 3.562 × 5.625 in; page
  lists anti-stain treatment without identifying its chemistry.

These retailer descriptions do not establish a delivered DF-L species-group
mark, final grade, treatment compatibility, moisture, or connection-zone
condition. The 4×6 listings also do not establish an inspection/regrade route
after the two proposed section rips.

## What remains unresolved

No public price found here is for the source schedule's candidate material
basis of DF-L No. 2 stock with verified treatment, seasoning, dimensions, and
receiving condition. The 4×4 “Grade A” and 4×4 cedar prices lack that timber
identity; the listed 2×6 and 4×6 WRC items are different seller-labeled stock.
Do not total these amounts into a candidate lumber cost or substitute them for
a quote.

The exact order quantity, usable yield, matching Douglas-fir unit prices,
delivered stock, tax, and delivery cost remain open. The four proposed 4×6
section-ripped blocks still lack a documented post-rip grade/inspection basis;
the original source grade does not transfer across those rips. No lumber was
selected, measured, inspected, ordered, cut, or delivered.

## Reproducible method

On 2026-09-27, opened the linked supplier, retailer, and product pages and read
their publicly visible size, species/grade/treatment, location, price, and
availability fields. For Denver Fence Supply, fetched the three public product
pages over HTTPS and read their product offer metadata (`price`, `USD`,
`availability`, and validity date), without logging in or adding items to a
cart. No ZIP, city, or store was entered or selected; no vendor was contacted.
Prices and availability are observations of those pages on the access date,
not guaranteed offers or current physical stock.

Direct sources: [Front Range framing sizes][frl-framing], [Front Range timber
sizes and lengths][frl-timbers], [Front Range Lakewood yard][frl-lakewood];
[Denver Fence Supply 4×4×8][dfs-4x4], [4×6×8 WRC][dfs-4x6], and
[2×6×8 WRC][dfs-2x6]; [Cedar Fence Direct][cedar-home]. The same Lowe's and
Home Depot product URLs catalogued in the [attempt01 lookup][price01] were
reopened; that note carries their direct item URLs.

[schedule]: ../current-timber-source-yield-attempt01/current-timber-source-yield.json
[manifest]: ../current-full-frame-input-manifest-attempt02/current-full-frame-input-manifest.json
[price01]: ../current-timber-price-research-attempt01/README.md
[frl-framing]: https://www.frlco.com/product-info/framing-lumber/
[frl-timbers]: https://www.frlco.com/product-info/timbers/
[frl-lakewood]: https://www.frlco.com/locations/lakewood-colorado/
[dfs-4x4]: https://denverfencesupply.com/product/4x4x8-grade-a/
[dfs-4x6]: https://denverfencesupply.com/product/4x6x8-wrc/
[dfs-2x6]: https://denverfencesupply.com/product/2x6x8-wrc/
[dfs-home]: https://denverfencesupply.com/
[cedar-home]: https://cedarfencedirect.com/cfd-home-page/
[lowes-4x4]: https://www.lowes.com/pd/4-in-x-4-in-x-8-ft-Lumber/5002102005
