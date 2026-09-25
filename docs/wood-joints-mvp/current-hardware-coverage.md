# Current WJ24 hardware coverage and count reconciliation

**Prepared:** 2026-09-25. **Status:** source-bound inventory reconciliation
for the current development axes. This note and its machine-readable
[coverage index](current-hardware-coverage.json) reconcile the 92 current
candidate bolt axes with the 12 retained starting frame arrangements. They
select no SKU, establish no delivered fit or resistance, and authorize no
purchase or physical work.

## Quantity authority

The candidate rows are bound to [grip-screen attempt 02](hypotheses/evaluation-resume-2026-09-24/grip-screen-attempt02.json),
SHA-256 `9f84a15ed05ca9832f594c4a0b2c8d1322b90e74e462aa7c725b031bad69643a`.
The current screen contains 92 axes; the [retained frame review](current-frame-bolt-review.md)
and [retained audit](wj24-retained-frame-bolt-audit.md) reconcile 12 separate
starting stacks. Current piece-count arithmetic is:

| Scope | Axes | Bolts | Nuts | Separate washers | Disposition |
| --- | ---: | ---: | ---: | ---: | --- |
| WJ24 candidate axes | 92 | 92 | 92 | 184 | Each current axis has one bolt, one nut, and two washer roles. |
| Retained starting frame | 12 | 12 | 12 | 24 | Three source groups below; identity is preserved, current WJ24 fit/mechanics are not established. |
| **Structural stacks represented** | **104** | **104** | **104** | **208** | Quantity reconciliation only. |
| Separate Hillman panel/kicker policy | 66 screw axes | 66 screws | — | — | Excluded from the structural bolt total. |
| Removed SDS25112 hardware | 144 former axes | 0 current WJ24 | — | — | Excluded from this current coverage. |

The earlier inventory's 104 candidate axes / 216 candidate washer equivalents
are historical and do not match the current attempt02 source; its 12 retained
frame stacks were separate. It included four special backer stacks with
additional washer roles. The current candidate has two washer roles per
axis, and the current 12 retained stacks add their separate two washer roles
each, giving 92 candidate stacks plus 12 retained stacks: 104 total stacks
and 208 washers.

The 6.35 mm candidate shaft and the retained 9.525 mm and 12.7 mm bolt
envelopes are model geometry. Their modeled lengths are not purchase lengths,
delivered shank dimensions, or actual thread boundaries. The JSON lists the
exact attempt02 axis IDs by family so the counts can be checked without
reconstructing them from the abbreviated family names below.

## Candidate-family coverage

The supplier identities and size classes below are leads documented in the
linked source notes. “Axial screen” means the listed overall-length, `LG`,
`LB`, stack, or member-thread comparison only. None proves full functional
engagement of the matched nut, received dimensions, capacity, or assembly fit.

| Current family | Count and modeled grip / length | Existing candidate route or shortest screened class | Axial and engagement status |
| --- | --- | --- | --- |
| Ordinary 6 in, 127 mm-grip axes | 48; 127 / 152.4 mm; 6.35 mm shaft envelope | K.L. Jack `25C600HCS5Z`, 1/4-20 × 6 in Grade 5 cap screw, is a US-catalogue candidate; `25CNFH5Z` is the nut lead. Würth `072.14.6` is an alternate but its product page’s 1 in thread-length field conflicts with its catalogue’s 0.750 in value. | Six-inch minimum length clears the 140.9794 mm tip target by 8.8806 mm and `LB,min` clears the stated 120.382 mm nominal-D wood-thread threshold. `LG,max` is 4.7592 mm beyond the earliest nut-bearing plane, so catalog dimensions do not establish full-height nut fit. The 6.096–6.604 mm two-spacer layout is only a geometry proposal; it is not adopted. See [ordinary basis](current-ordinary-hardware-basis.md), [sourcing follow-up](current-ordinary-hardware-sourcing-followup.md), and [spacer option](current-ordinary-hardware-spacer-option.md). |
| Side 8 in, 177.8 mm-grip axes | 16; 177.8 / 203.2 mm | Lawson/FalconGrip `FA21103`, 1/4-20 × 8 in Grade 5 partial-thread cap screw; K.L. Jack `25CNFH5Z` nut and `25NWUS` Type A Wide washer candidates. | Conditional eight-inch length screen clears the minimum physical-tip target; `LG` margin is +2.5908 mm. Minimum delivered standard length may be 4.572 mm shorter than the modeled endpoint. Actual transition and full nut engagement, finish compatibility, washer support, and delivered endpoint remain unresolved. See [side option](current-side-hardware-option.md). |
| Outer-post 4 in, 76.2 mm-grip axes | 4; 76.2 / 101.6 mm | K.L. Jack `25C400HCS5Z` 1/4-20 × 4 in Grade 5 cap-screw listing; `25CNFH5Z` nut and `25NWUS` washer candidates. | The standard minimum-length screen clears the physical-tip target by 10.8966 mm. `LG,max` is 2.286–3.7592 mm beyond the modeled nut-bearing interval; this does not by itself show failure, but the matched functional nut fit is unresolved. The exact bolt product page was not fully retrievable and displayed prices conflict. See [outer-post option](current-outer-post-hardware-option.md). |
| Center post, 127 mm grip | 4; 127 / 139.217 mm | 5.75 in is the shortest screened quarter-inch class; no exact SKU or price was verified. | Minimum-length margin to the physical-tip target is +3.5306 mm; `LG` margin is +2.5908 mm. The worst final-receiver thread interval allowed by `LB,min` is inside the quarter-length screen by 1.143 mm. Product identity and functional nut fit remain open. |
| Center principal, 122 mm grip | 4; 122 / 139.217 mm | K.L. Jack `25C550HCS5Z`, listed as 1/4-20 × 5.5 in Grade 5, is a catalog lead; the product detail timed out. | Minimum-length margin to the physical-tip target is +2.1806 mm; `LG` margin is +3.9408 mm. The nominal-D NDS quarter-thread screen exceeds its limit by 0.207 mm at `LB,min`; use part-specific dimensions or `Dr`/a detailed method if that nominal-D check is needed. No matched nut/washer set is assigned. |
| Center post header, 167 mm grip | 4; 167 / 179.217 mm | 7.5 in is the shortest screened class; no exact SKU or price was verified. | Minimum-length tip margin is +5.9486 mm and `LG` margin is +4.4908 mm; the receiver quarter-thread screen is inside by 21.943 mm. Product identity and functional engagement remain open. |
| Center principal header, 172.8 mm grip | 4; 172.8 / 190.017 mm | 7.5 in is the shortest screened class; no exact SKU or price was verified. | Minimum-length tip margin is only +0.1486 mm; minimum permitted length is 4.089 mm shorter than the modeled endpoint. The nominal-D NDS screen would require measured `LB` ≥165.307 mm, 0.207 mm above `LG,max` 165.100 mm. Table limits alone do not establish that exception; use a part-specific interval or `Dr`/detailed method if needed. |
| Knee outer inner-header, 177.1 mm grip | 4; 177.1 / 202.5 mm | 7.75 in is the shortest screened class but has no SKU. Lawson `FA21103` 8 in is a separate candidate alternative shared with the 16 side axes. | The 7.75 in screen meets the physical-tip target; for the 38.1 mm header receiver its nominal-D quarter-thread screen exceeds by 4.507 mm at `LB,min`. The 8 in alternative clears both far-receiver quarter-length screens and the physical-tip target, but minimum delivered length may be 3.872 mm shorter than the current endpoint. Full nut fit remains open. See [center/knee options](current-center-sandwich-hardware-options.md). |
| Knee outer side, 215.9 mm grip | 4; 215.9 / 241.3 mm | 9.25 in is the shortest screened quarter-inch class; no exact SKU or price was verified. | Minimum-length tip margin is +1.4986 mm; minimum delivered length may be 10.922 mm shorter than the modeled endpoint. `LG` margin is +8.9408 mm and the receiver quarter-thread screen is inside by 7.493 mm. Product identity and functional fit remain open. |

The current center/knee dimensional note uses a provisional 1/4-20 nut and
Type A Wide washer range to compare axial stacks. That is not a universal
1/4-20 selection across the 92 candidate roles. Exact nut/washer identity,
thread class, actual fit, steel support, and capacity remain family-specific
open items. The 1/4-20 fixed-rotation thread-class comparator in
[current thread-fit travel](current-thread-fit-travel.md) is an idealized
geometry interval, not installed WJ24 travel or evidence of full-height nut
engagement.

Across the 92 candidate axes, 76 have a named bolt SKU or supplier-specific
catalog lead in the source notes: the 48 ordinary six-inch axes, 16 side
axes, 4 outer-post axes, 4 center-principal axes, and the 4 knee inner-header
axes under the separate eight-inch option. The remaining 16 axes—center post,
both center-header groups, and knee outer side—have only screened nominal
length classes, with no exact supplier bolt SKU verified. This count measures
catalog lead coverage, not fit qualification: no candidate axis has a
delivered matched bolt/nut fit established by this inventory.

## Retained 12 starting frame arrangements

These named Bolt Depot parts remain catalog references from the selected
baseline research. The current frame review records every retained station as
requiring a new WJ24 structural recheck; none is stock-verified or accepted
for the changed WJ24 load path.

| Retained family | Count and modeled size / grip | Existing catalog references | Current WJ24 fit disposition |
| --- | --- | --- | --- |
| Lumber-leg upper bolts | 4; 1/2 in × 8 in; 177.8 mm grip | Bolt Depot `#407` Grade 5 bolt, `#2573` nut, `#15025` USS washers | Product references only. Verify actual grade, body/thread transition, nut engagement, washer support and fresh actions. The modeled nut envelope is 0.1524 mm taller than the cited #2573 maximum; the source audit reports 2.7432 mm beyond the modeled nut at minimum bolt length / maximum washer stack. |
| Front rail/post bolts | 4; 3/8 in × 4 in; 76.2 mm grip | Bolt Depot `#367` Grade 5 bolt, `#2571` nut, `#15023` USS washers | Product references only. Full-body-to-thread screening threshold is 69.3166 mm; no delivered transition or matched nut fit is established. Current wrench/access, washer support and mechanics are open. |
| Rear rail/leg bolts | 4; 3/8 in × 4.5 in; 88.9 mm grip | Bolt Depot `#368` Grade 5 bolt, `#2571` nut, `#15023` USS washers | Product references only. Full-body-to-thread screening threshold is 78.8416 mm; verify the 50.8 mm remaining leg bearing section, delivered transition, nut fit, support, access and fresh mechanics. |

The exact twelve axis IDs and retained-source dimensions are in the JSON and
[frame-bolt audit](wj24-retained-frame-bolt-audit.md). Keep these stacks
separate from the 92 candidate stacks; do not import former angle-frame bolt
forces or acceptances.

## Shared packages and cost coverage

The eight-inch Lawson route appears in separate 16-axis and four-axis notes.
If those options are assessed as one 20-axis sourcing scenario, use one
package set: 20 bolts, 20 nuts and 40 washers require one 25-piece Lawson
bolt pack and one 100-piece box each of K.L. Jack `25CNFH5Z` nuts and `25NWUS`
washers, leaving 5 bolts, 80 nuts and 60 washers. The nut and washer boxes
displayed $4.71 and $3.47, respectively, on 2026-09-25; no public Lawson bolt
price was found. Do not add a second bolt pack by summing the isolated
16-axis and four-axis package rows.

Other bounded package context is recorded in the JSON: the K.L. Jack
ordinary 6-inch candidate uses 100-piece bolt and nut boxes for 48 axes; the
Würth ordinary route is an alternate with two 25-bolt packs, one 200-nut
pack and one 100-washer pack; the 5.5-inch center-principal lead displays a
100-piece box at $30.59, with 4 needed; and the 4-inch outer-post route lists
100-piece packages without a reliable price. These are alternatives and
listing contexts, not a cost subtotal. Shipping, tax, current availability,
delivered identity, and WJ24 item fit are not priced or established.

## Source pins and limits

The machine-readable index embeds SHA-256 pins for the attempt02 axis JSON,
this coverage’s source schedule and all current ordinary, outer-post, side,
center, thread-fit, and retained-frame notes. The bolt-length tables cite
ASME B18.2.1-2012 (R2021); the 6 in / 1/4 in transcription caveat is recorded
in [the source-attribution correction](bolt-dimension-source-correction.md).
K.L. Jack, Lawson, Würth, and Bolt Depot identities and public listing
attributes are reproduced only from the linked, dated source notes; no new
vendor search, contact, account action, purchase, or delivery is represented
here.

This inventory does not assign bolt/nut/washer capacities, transfer any
prior analysis pass, approve a stack movement, or replace source-specific
thread, receiver, access, fit, and mechanics checks. No purchase length
should be taken from a modeled cylinder.
