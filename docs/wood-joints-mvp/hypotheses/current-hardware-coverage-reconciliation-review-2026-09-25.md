# Independent review: current hardware coverage reconciliation

**Reviewed:** 2026-09-25. **Disposition:** the revised coverage reconciliation
matches its pinned attempt02 axis source and its new unmatched-length lead
screen. The category totals, source pins, and hardware-count boundaries are
consistent. No candidate stack is presented as fit-qualified.

## Frozen inputs

| Artifact | SHA-256 |
| --- | --- |
| [`current-hardware-coverage.md`](../current-hardware-coverage.md) | `6bda5d032d52c8da38e069548153dbfe93c6bdfeea6f8ded1ba4f650cf75dd8c` |
| [`current-hardware-coverage.json`](../current-hardware-coverage.json) | `011dcf33c8a99d5072623db06388ffc0e409c8824be15015e68b454c31e7305d` |
| [`current-unmatched-length-hardware-options.md`](../current-unmatched-length-hardware-options.md) | `25f4ec31fb84d32cdf70bdbddd8c67f86d020c60851e7d4ae29dbd39fffeab03` |
| Prior independent [`current-hardware-coverage-review-2026-09-25.md`](current-hardware-coverage-review-2026-09-25.md) | `b3ce06b7d69a9b07bb48649c3f0859cad20baf1dbddcd5cad7046e1d97228c3c` |
| Independent [`current-unmatched-length-hardware-options-review-2026-09-25.md`](current-unmatched-length-hardware-options-review-2026-09-25.md) | `dcfe094d7524fb84a411a72ed679d8e039556c9d921dbe5ef262f69caf8f7011` |
| Frozen axis source, grip-screen attempt02 | `9f84a15ed05ca9832f594c4a0b2c8d1322b90e74e462aa7c725b031bad69643a` |

The earlier coverage review remains unchanged and retains its original pins
to coverage Markdown SHA-256
`40aadf989a3d6d797f1ff1958aeba94389b72ea36d33ad36bcc39c9c424b1e60` and
coverage JSON SHA-256
`8e1a5325d99aa83a82cfd7dba1e6767ea2e2ba484be38e5fb12df39b227afdea`.
The unmatched-length review also explicitly binds its scope to that earlier
coverage JSON; it is not represented as a review of the later reconciliation.

## Axis and listing reconciliation

I parsed all 92 IDs from grip-screen attempt02 and compared them with the
candidate-family lists in the revised coverage JSON. The lists are a
duplicate-free, exact partition of the source IDs. The mutually exclusive
listing categories cover all 92 axes:

| Listing category | Families | Axes |
| --- | --- | ---: |
| Named supplier/SKU lead at the screened nominal length | Ordinary 48, side 16, outer-post 4, center-principal 4, center-post-header 4, center-principal-header 4 | 80 |
| Named bolt lead only at a longer length class | Knee inner-header 4 (8-in Lawson lead for the 7.75-in screen), center-post 4 (6-in HiStrength lead for the 5.75-in screen) | 8 |
| Unresolved supplier listing beyond the screened class | Knee outer side 4 (9.5-in Ro-Brand HC5127 listing against the 9.25-in screen) | 4 |
| **Total candidate axes** |  | **92** |

The distinctions are appropriate: nominal classes are not treated as SKUs;
longer-length alternatives remain separate from those classes; and HC5127 is
kept as a source-conflicted listing lead. Ro-Brand's 105 ksi statement is
attributed to its Grade 5 category description, while the HiStrength SAE
J429 Grade 5 cut sheet states 120 ksi minimum. That published discrepancy
does not establish failure, defect, or unsuitability of a delivered part.
The JSON and Markdown both state zero fit-qualified delivered stacks and
leave the actual thread transition, matched-nut engagement, delivered fit,
and capacity unresolved.

## Source pins and component counts

All eleven records in `source_document_pins` of the revised coverage JSON
recompute to their listed SHA-256 values. Its unmatched-length source pin
matches the frozen note above. The related-review record matches the
independent unmatched-length review hash above and preserves the earlier
coverage JSON hash in the recorded scope. The prior coverage review file was
also rehashed and remains at the exact original SHA shown above. All relative
Markdown links in the revised coverage note resolve.

The revised piece counts reconcile as:

- 92 candidate axes: 92 bolts, 92 nuts, 184 separate washer roles.
- 12 retained frame arrangements: 12 bolts, 12 nuts, 24 separate washers.
- 104 represented structural stacks total: 104 bolts, 104 nuts, 208 washers.
- The 66 Hillman panel/kicker screws remain separate; the 144 removed
  SDS25112 axes remain excluded.

The reported package context remains conditional and arithmetically
consistent: the shared 20-axis Lawson scenario uses one 25-bolt pack and one
100-piece box each of nuts and washers, leaving 5, 80, and 60 pieces. The
eight 7.5-in HiStrength listing units extend to `$20.32` at the displayed
`$2.54` each before freight and tax; package quantity is 1. The 6-in
HiStrength alternative shows `$1.23` each with package quantity 50 and
quantity breaks, so the minimum order remains unclear. HC5127 has no stated
price or package quantity. These are dated listing contexts, not selected
purchase scenarios.

Validation was read-only: source hashes, IDs, partition counts, quantities,
and local links were checked. No vendor contact, purchase, CAD, native solve,
or edit to either prior review was made.
