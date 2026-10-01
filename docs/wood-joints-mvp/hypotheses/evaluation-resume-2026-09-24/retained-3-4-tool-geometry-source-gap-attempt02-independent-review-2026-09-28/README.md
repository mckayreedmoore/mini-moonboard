# Independent review — retained 3/4-in tool source gap, attempt02

Reviewed 2026-09-28. Verdict: **SUPPORTED_WITH_QUALIFICATION**. The attempt02
disposition is supported as a bounded source finding: the checked public Wera
routes provide exact-part identity and discrete dimensions for Joker
`05073287001`, but the review found no Wera-issued complete external-profile
model or dimensioned drawing usable to bind the wrench outline. The four
matching-size #407 axes therefore remain `NOT_RUN_SOURCE_GAP`; the eight axes
with different #367/#368 bolt references remain outside this 3/4-in comparator
screen.

The reproduced `verify_source_gap.py` exited successfully. It confirmed 23
repository input pins and all four packet artifact hashes. The pinned T07/T08
parent reviews support identity, register, option-crosswalk, and nominal
envelope work only; they explicitly leave physical fit, access, service,
installation/removal, capture/support, transport, and product selection open.
The 12 retained identities reconcile to four T08 #407 lumber-leg axes and
eight front/rear #367/#368 axes. No operation or geometry screen was run in
this review.

One wording qualification is material. Wera's product page download does
resolve to a manufacturer-hosted datasheet headed for part `05073280001` (5/16
in), not target part `05073287001`. However, that file includes a “Further
versions in this product family” table with an explicit `05073287001` row and
the target's 3/4-in, 246 mm, 42 mm, 9.5 mm, 34.8 mm and 11 mm data. It can
corroborate those discrete family dimensions; it is not a target-part-specific
datasheet and it does not define the full contour. Thus the source-gap
conclusion remains sound, while “not accepted as exact-part geometry evidence”
should mean “not accepted as complete exact-part profile geometry,” rather
than implying that the file contains no target-specific dimensional row.

Wera's official Digital Support PDF also describes virtual product images
that can be viewed in 360 degrees or as 3D objects in augmented reality. The
packet's Data Cockpit/public-source review accurately says that no exact CAD
geometry was retrieved and that internal-sales access remains unresolved, but
it does not list the visual 3D route as a separate checked route. The booklet
does not establish that a downloadable, dimensioned, datum-bound model for
this exact wrench is publicly available. Keep the conclusion bounded to the
reviewed source artifacts and routes; do not convert this gap into a claim
that Wera has no CAD or 3D asset.

The Wera product family page confirms `05073287001` is the 3/4-in variant and
publishes the dimensions above, its 30-degree open-end return angle and
80-tooth ring. The user manual explains its jaw holding plate and integrated
stop but is not a dimensioned drawing. The exact-part PDF short-link and
candidate Wera media-PDF route were not accessible through the browser
retriever; this is an access limit, not evidence those files do not exist. The
Data Cockpit material describes product-data and image exports with access via
Wera internal sales, so that access route remains unverified. An Olander
“View 3D CAD Model” listing is still only a discovery lead without bound
Wera-authored/authorized bytes, exact revision, datum, units, or hash.

The separate review packet is hash-bound by `terminal-hashes.json`. The
attempt02 directory, candidate geometry, operation records, selected tool,
and criteria were not changed.

## Reviewed source trail

- [Wera 6000 Joker Imperial product page](https://www.wera.de/en/tools/6000-joker-ratcheting-combination-wrenches-imperial)
- [Wera-hosted family datasheet reached from that page](https://hybris-media.wera.de/download/pdfgenerator-datasheets/en/05073280001.pdf)
- [Wera user manual](https://www.wera.de/fileadmin/pdf/manuals/11670984-00000177-09_screen.pdf)
- [Wera catalogs](https://www.wera.de/en/downloads/catalogs)
- [Wera Digital Support PDF](https://www.wera.de/sh/Wera-Digital-World.pdf)
- [Bolt Depot #407 product page](https://boltdepot.com/Product-Details?product=407)
- [Olander distributor listing](https://www.olander.com/items/05073287001), excluded as non-primary CAD evidence

`review-record.json` records the independent hashes, parent-review identities,
axis dispositions, source limits, and packet terminal values. External source
responses were inspected through browser-extracted text; no external file
bytes were saved into this review packet.
