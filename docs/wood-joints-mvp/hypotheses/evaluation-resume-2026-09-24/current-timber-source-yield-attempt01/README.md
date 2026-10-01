# Current timber source and yield screen, attempt 01

**Lookup date:** 2026-09-27. **Status:** source-bound preliminary screen; no
selected timber product, quote, cut list, or release.

This schedule joins the 20 timber records in
[`source-inventory.json`](../../../source-inventory.json) to the exact
24 candidate block IDs in the [attempt02 full-frame manifest][manifest],
revision `led-clearance-2x6-runner-seated-blocks-v1`. The machine-readable schedule is
[`current-timber-source-yield.json`](current-timber-source-yield.json), built
and checked by [`produce.py`](produce.py).

The older 28-blank/104-axis WJ24 inventory and cost screen describe a prior
geometry. They are excluded here. This attempt uses 24 current blocks and 92
candidate axes; it imports none of the older blank allocations or fastener
quantities.

## Quantity and section screen

The 20 preserved frame records use four nominal 4×6 sections and sixteen
nominal 2×6 sections. Their source-inventory long-dimension totals are 9,198.378
mm and 20,582.770 mm, respectively. These are source blank records, not a
current purchase cut list: the reviewed manifest identifies 16 frame hosts as
rebuilt, and those source dimensions do not quantify stock removed or current
cut yield.

The reviewed candidate block IDs group into 18 proposed 4×4 blanks, four
proposed 4×6 blanks, and two proposed 2×6 blanks. The matching proposed blank
length totals are 2,140.2 mm, 547.4 mm, and 552.6 mm. The stock dimensions and
grain direction are conditional pattern proposals from the current stock and
material-scenario notes. Finished bounding-box dimensions in the manifest are
not source blank dimensions.

| Stock class | Frame source records | Current proposed blocks | Combined arithmetic length |
| --- | ---: | ---: | ---: |
| 4×4 | 0 | 18 / 2,140.2 mm | 2,140.2 mm |
| 4×6 | 4 / 9,198.378 mm | 4 / 547.4 mm | 9,745.778 mm |
| 2×6 | 16 / 20,582.770 mm | 2 / 552.6 mm | 21,135.370 mm |

These totals only sum recorded/proposed blank lengths by stock section. There is
no nesting plan, kerf/end-trim allowance, defect allowance, section cleanup,
stock-length count, receiving loss, or usable-yield estimate. Prices and total
material cost remain unknown.

## Denver-area sourcing screen

Front Range Lumber's [timber page](https://www.frlco.com/product-info/timbers/)
publishes Douglas-fir 4×4 stock lengths of 8, 10, 12, 16, and 20 ft and 4×6
lengths of 8, 10, 12, and 16 ft. Its [framing page][framing]
lists 2×6 and common length ranges. The [Lakewood yard][lakewood]
serves Metro Denver, but its pages say the listed sizes are not a guarantee of
current stock and direct customers to call. No live item count, candidate quote,
exact grade/species group, or receiving condition was available. The posted
[delivery policy](https://www.frlco.com/fast-delivery/) lists $99 delivery on
orders of $500 or more in its service area; applicability to a final candidate
order is unresolved.

Big-box pages provide comparison leads, not selections. Lowe's 4×4 and 4×6
Douglas-fir product URLs are recorded in the JSON source list. Those pages
prompt for a ZIP/city before showing price or
availability. The listed 4×6 actual section is 3.562 × 5.625 in, larger than
the 88.9 × 139.7 mm source section, and the listing says green and
anti-stain-treated. A Lowe's 2×6 #2 Prime Douglas-fir kiln-dried 8-ft product
lists 1.5 × 5.5 in actual dimensions, but also lists anti-stain treatment and
location-gated pricing. [Home Depot's 4×4×8 No. 2 Douglas-fir page][hd4x4]
lists 3.5 ×
3.5 in actual dimensions and says the product may vary by store; no Denver price
or inventory was returned. These pages do not identify the candidate's required
species group, treatment acceptability, receiving condition, or delivery.

## Four proposed 4×6 section rips

The two central principal/header blocks reduce a proposed 88.9 × 139.7 mm
section to 83.9 × 139.7 mm. The two inner-frame blocks reduce 88.9 × 139.7 mm
to 88.9 × 133.35 mm. All four are proposed cross-section remanufactures.

The [ALSC Lumber Enforcement Regulations, §5.10.1][alsc-regs]
require the original mark to be removed or obliterated when grade-stamped
lumber is remanufactured in a way that may alter grade, subject to listed
exceptions. The short-length exception is limited to lumber otherwise
unmodified in cross-section, so it does not cover these proposed rips. The
supplier, current mark, grade after ripping, accredited-agency inspection or
regrade route, and final acceptance record are unresolved. Do not carry a
4×6 grade claim onto a ripped block without a documented applicable
disposition.

## Source and claim limits

The producer pins source-inventory and attempt02 manifest identities, checks
the 20 frame and 24 block counts, and requires the block IDs to match the
reviewed manifest exactly. It records current supplier leads and the lookup
date. Its JSON keeps delivered species group, grade, treatment, moisture,
receiving condition, inspector basis, price, and actual delivery unknown unless
a primary source explicitly supports a limited statement.

No lumber was selected, priced, inspected, ordered, cut, or delivered. No CAD,
solver, or test was run. Candidate acceptance and all physical-work/release
flags remain false.

[manifest]: ../current-full-frame-input-manifest-attempt02/current-full-frame-input-manifest.json
[alsc-regs]: https://alsc.org/uploaded/2023%20Lumber%20Program_Enforcement%20Regs.pdf
[framing]: https://www.frlco.com/product-info/framing-lumber/
[lakewood]: https://www.frlco.com/locations/lakewood-colorado/
[hd4x4]: https://www.homedepot.com/p/300874740
