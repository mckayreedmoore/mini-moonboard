# Public stock-source screen — 2026-10-01

This is a bounded public-offer screen for the 44 proposed original timber
blanks in [`cut-scenarios.md`](../current-stock-envelope-reconciliation-2026-10-01/cut-scenarios.md).
It records seller line prices and spec evidence separately. No listing below
passes the full material screen, so there is no lumber package total or
candidate price range.

The checked stock basis is untreated Douglas Fir-Larch No. 2 under the
candidate's recorded dry-service assumption, with original sections 2×6
38.1×139.7 mm, 4×6 88.9×139.7 mm, and 4×4 88.9×88.9 mm. Current seller
records must also establish the matching length, actual section, species
group, grade, treatment, and seasoning/condition. Prices are listing
observations, not quotes, selected products, availability guarantees, or
received-material evidence.

## Public lumber lines

Big Creek Lumber's direct product-detail pages showed the following current
rates when opened on 2026-10-01. The catalog identifies the count unit as
`piece`, while each numeric rate is **USD per MBF**. Those are different units;
the displayed rate is not a per-stick price. No per-piece conversion is made
here. Each link below is the direct seller detail page, and the observed
product/rate phrase is retained in the local excerpt record.

| Original stock | Direct length line | SKU | Public rate | Listing description |
| --- | ---: | --- | ---: | --- |
| 2×6 | 8 ft | [1321020608](https://bigcreekportal.epicoranywhere.com/ProductDetail.aspx?pg=59&pid=18426&pl1=1) | $880.00/MBF | Douglas Fir #2 or Better S4S |
| 2×6 | 10 ft | [1321020610](https://bigcreekportal.epicoranywhere.com/ProductDetail.aspx?pg=59&pid=18427&pl1=1) | $880.00/MBF | Douglas Fir #2 or Better S4S |
| 2×6 | 12 ft | [1321020612](https://bigcreekportal.epicoranywhere.com/ProductDetail.aspx?pg=59&pid=18428&pl1=1) | $880.00/MBF | Douglas Fir #2 or Better S4S |
| 4×4 | 8 ft | [1321040408](https://bigcreekportal.epicoranywhere.com/ProductDetail.aspx?pg=14&pid=18472&pl1=1) | $1,484.00/MBF | Doug Fir Std or Btr S4S |
| 4×4 | 10 ft | [1321040410](https://bigcreekportal.epicoranywhere.com/ProductDetail.aspx?pg=14&pid=18473&pl1=1) | $1,484.00/MBF | Doug Fir Std or Btr S4S |
| 4×4 | 12 ft | [1321040412](https://bigcreekportal.epicoranywhere.com/ProductDetail.aspx?pg=14&pid=18474&pl1=1) | $1,484.00/MBF | Doug Fir Std or Btr S4S |
| 4×4 | 16 ft | [1321040416](https://bigcreekportal.epicoranywhere.com/ProductDetail.aspx?pg=14&pid=18476&pl1=1) | $1,484.00/MBF | Doug Fir Std or Btr S4S |
| 4×6 | 8 ft | [1321040608](https://bigcreekportal.epicoranywhere.com/ProductDetail.aspx?pg=14&pid=18500&pl1=1) | $1,527.00/MBF | Douglas Fir #2 or Better S4S |
| 4×6 | 10 ft | [1321040610](https://bigcreekportal.epicoranywhere.com/ProductDetail.aspx?pg=14&pid=18501&pl1=1) | $1,527.00/MBF | Douglas Fir #2 or Better S4S |
| 4×6 | 12 ft | [1321040612](https://bigcreekportal.epicoranywhere.com/ProductDetail.aspx?pg=14&pid=18502&pl1=1) | $1,527.00/MBF | Douglas Fir #2 or Better S4S |
| 4×6 | 16 ft | [1321040616](https://bigcreekportal.epicoranywhere.com/ProductDetail.aspx?pg=14&pid=18504&pl1=1) | $1,527.00/MBF | Douglas Fir #2 or Better S4S |

The older indexed Big Creek category-page snapshot separately displayed
2×6×10 SKU 1321020610 at **$902.00/MBF**. Its search result said the page had
been crawled about two weeks before the 2026-10-01 observation and did not
show a price-validity date. The same-day direct product-detail line is
$880.00/MBF. Both observations remain visible in
`rawlocal/public-offer-excerpts.json`
and are not mixed; the direct detail line is the current rate used in the
screen, while $902.00 is retained only as an older listing variance.

No direct current 2×6×16 rate was verified. Do not substitute its 12-ft rate.
The product-detail lines do not publish actual section dimensions, the DF-L
species group, untreated status, or dry/moisture condition. Their 2×6 and 4×6
`#2 or Better` descriptions provide a public grade phrase, but do not resolve
the unproven species-group/material fields. The 4×4 `Std or Btr` label does not
demonstrate the No. 2 structural grade. All listed lumber lines therefore
have `price_known=true` and `specification_eligible=false` in the screen.

Big Creek's official [locations page](https://bigcreeklumber.com/locations/)
describes yards on California's Central Coast, Bay Area, and Central Valley;
its [contractor service page](https://bigcreeklumber.com/contractors/)
describes delivery throughout central and northern California. These pages
do not establish Denver service, local fulfillment, or any user's location.
No branch stock quantity, delivery charge, tax, or quote was observed.

## Scenario line coverage

These counts come directly from the reviewed cut-scenario document. They are
heuristic full-stick inputs for all 44 blanks, not optimized purchase
quantities. The 8-ft-only case places only 39/44 and is excluded from a full
44-piece price scenario.

| Scenario | 2×6 demand | 4×6 demand | 4×4 demand | Public line gap / limitation |
| --- | --- | --- | --- | --- |
| 10 ft | 8 × 10 ft | 4 × 10 ft | 1 × 10 ft | Lines exist for every length; all fail one or more material-spec checks. |
| 12 ft | 6 × 12 ft | 4 × 12 ft | 1 × 12 ft | Lines exist for every length; all fail one or more material-spec checks. |
| 16 ft | 5 × 16 ft | 3 × 16 ft | 1 × 16 ft | 2×6×16 has no verified direct price; no shorter-line substitution. |
| Mixed | 6 × 8 ft + 3 × 10 ft | 2 × 8 ft + 2 × 10 ft | 1 × 8 ft | Numeric lines exist for all lengths; all fail one or more material-spec checks. |

The four later section-ripped blocks remain priced, if ever, from original
4×6 stock before the proposed rips. The current source line cannot establish
post-rip grade or design values. No original-stock grade is transferred to
the two 83.9×139.7 mm or two 88.9×133.35 mm proposed sections.

## Plywood evidence

The current wood-lane source inventory identifies six modeled panel bodies as
`23/32 CAT-face plywood source geometry` and `plywood_layup: unverified`.
Those bodies do not imply six newly purchased sheets or a source item. The
four main panel bodies are about 1217.6125×1219.2×18.25625 mm and the two
kickers are 1217.6125×277×18.25625 mm. No exact sheet item, layup, panel-item
crosswalk, sheet nesting, or required quantity is established.

The Home Depot public listing showed Plytanium Model 605189 / Internet
#100003769 / Store SKU #724084, a 23/32-in × 4-ft × 8-ft Southern Pine
tongue-and-groove plywood sheathing sheet at **$49.00 each**, with a separate
**$44.10 each at 48+** tier. The direct [product page](https://www.homedepot.com/p/100003769)
establishes item identity; its public
[listing page](https://www.homedepot.com/b/Lumber-Composites-Plywood-Sheathing-Plywood/Plytanium/23-32/4/N-5yc1vZc7q5Z4ajZ1z0mcphZ1z0mcq1)
displays price and quantity tier. This is a comparable sheet-price
observation only. Its product/layout does not crosswalk to the current
CAT-face model identity or prove its layup, so neither a quantity nor a
candidate plywood total is assigned. The 48+ tier is not assumed to apply.
The page notes that local store prices may vary and inventory is not
guaranteed; no store or user location is inferred.

Sutherlands item 2552586 is described as 4×4-ft × 23/32-in APA CDX Yellow Pine
plywood, but its public [item page](https://sutherlands.com/products/item/2552586/sutherlands-4-x-4-foot-x-23-32-inch-apa-cdx-yellow-pine-plywood)
displayed no numeric price. Its matching item identity and layup against the
current wood-lane panel geometry are unresolved. This remains
`price_known=false`, with the currency context USD and per-sheet basis known.

The selected baseline's bought-4×4 packet and kerf-right 4×8 packet remain
distinct from this wood-lane panel source. This screen does not transfer a
packet, sheet count, or source qualification across those candidates.

## Machine screen and replay

[`source_screen.py`](source_screen.py) stores the observed listings and
provides a pure price-unit parser plus a strict spec-eligibility result.
`price_minimum_satisfied` tests only whether a row's stated quantity minimum
is met; it does not choose an exclusive tier or select a payable price. The
base row has no stated minimum, so that predicate remains true at 48 while
the discounted row's minimum is also met. No seller upper boundary is inferred.
`price_known`, `specification_eligible`, and `evidence_missing` are separate
fields. The tests cover explicit MBF and sheet units, unit conflicts and
ambiguity, cross-species/section/length/grade/treatment/condition rejection,
the older quantity tier, and the current observed source rows.

The local excerpt JSON is ignored raw evidence, not a full HTML capture. Its
SHA-256 is `e07576391def85f8e74e0b337ef8a7fa19625943df3c0b447663f87cc7a282c7`;
its entries preserve displayed snippets, direct source URLs, source observation
date, price amount/currency/unit, and the older $902.00 variance.
The exact source-page open clock time was not retained; the file records the
transcription time and preserves that limitation. No unit-rate-to-stick
conversion is recorded.

The scenario table was manually reconciled to the published
[cut-scenario counts](../current-stock-envelope-reconciliation-2026-10-01/cut-scenarios.md).
Their local `cut-scenarios.json` result hashes to
`9a450e0b6bca73cf62b95f5759bfcacffd9d682b3c465df3fbc27327723d6978`.
The current [source inventory](../../source-inventory.json) hashes to
`07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78`.
The pure offer screen uses independent nominal stock-class/length requests
keyed to each recorded seller and SKU, plus declared section and material
requirements. The lumber screen rejects incomplete comparison requirements;
all seven stock, section and material fields must be supplied. The public-book
wrapper screens only its recorded rows; callers can compare other listings
with the separate pure `screen_offer` helper. It does not load or replay the
stock-cut result. The amount
parser is bounded to this USD source book; foreign or absent currency codes
do not become known prices. The local result hash above belongs to JSON,
not to the Python stock-cut producer.

Run the focused check from the repository root:

```sh
.venv/bin/python -m pytest -q docs/wood-joints-mvp/hypotheses/current-stock-package-cost-2026-10-01
.venv/bin/ruff check docs/wood-joints-mvp/hypotheses/current-stock-package-cost-2026-10-01/source_screen.py docs/wood-joints-mvp/hypotheses/current-stock-package-cost-2026-10-01/test_source_screen.py
.venv/bin/ruff format --check docs/wood-joints-mvp/hypotheses/current-stock-package-cost-2026-10-01/source_screen.py docs/wood-joints-mvp/hypotheses/current-stock-package-cost-2026-10-01/test_source_screen.py
```

This is a source screen, not order selection, purchase, receiving, cutting,
design-value assignment, joint acceptance, or climbing release.

## Maintained source bindings

| Artifact | SHA-256 |
| --- | --- |
| `source_screen.py` | `ff333f5020caa4998fe800e92c81f4447f59eaf28ff5c99dcd457992fabe495f` |
| `test_source_screen.py` | `806ea1e404f1bbbeacc8dd91cf3133742acfc61155db805fe06bbe46ec1ff35e` |
