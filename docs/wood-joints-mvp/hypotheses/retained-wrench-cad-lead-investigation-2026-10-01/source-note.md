# Retained 3/4-inch wrench CAD lead: direct investigation

Checked October 1, 2026 UTC. This supersedes the retrieval uncertainty in the
[preserved Olander attempt04](../evaluation-resume-2026-09-24/retained-3-4-tool-geometry-source-gap-attempt04/README.md)
for this one public lead. It supplies no wrench geometry, fit result, tool
selection, joint resistance or release.

## Observed outcome

The [Olander listing for Wera 05073287001](https://www.olander.com/items/05073287001)
is reachable by a direct anonymous HTTPS request: HTTP 200, 126,833 bytes in
the recorded retrieval. Its HTML contains the text “View 3D CAD Model,” but
the button is disabled. The text alone was not evidence of a working model
link.

An anonymous Playwright browser loaded the page, allowed its client code to
run, and observed the button still disabled. The page's CAD availability
response reports `cadAvailable=false`, `cadDownloadAvailable=false`,
`cad3DViewAvailable=false` and `cad2DViewAvailable=false`, with the error
`Invalid product ID 05073287001`. No enabled CAD control was clicked.

The page's advertised JavaScript identifies the public Catalog Data Solutions
service, domain `olander.cad`, and the item number as its product key. A direct
read of that exact
[availability endpoint](https://www.product-config.net/catalog3/cad?d=olander.cad&id=05073287001)
returned HTTP 200 and the same negative flags and product-key error. This was
a source-derived request, not a guessed model download URL. The 256-byte
availability response SHA-256 is
`cd7377b3cbbec4f553bdf06890f8d6951480b0c1f209822d27cb41c54cbd4712`.

Thus this observed public route supplies no viewer or downloadable model for
the wrench. A browser retrieval cache miss was not a sufficient diagnosis of
the underlying route. The new result does not show that Wera has no model
elsewhere, that the retailer can never add one, or that access is gated by an
account. No authentication, order or vendor-contact action was taken.

## Source provenance

Raw public source bytes remain local, under `/tmp/mini-moonboard-*`;
they are not committed result data. Hashes identify the observed bytes and
are not assertions that mutable pages will reproduce identically later.

| Source | Observed SHA-256 |
| --- | --- |
| Exact Olander item HTML | `22a1f178a510474813793deec522b615bde875b15cd624317bf56647c45cbb3b` |
| [Advertised item-page JavaScript](https://www.olander.com/_next/static/chunks/app/items/%5BitemId%5D/page-b499c04919b148a8.js) | `b1b722165b5f77cb9410a906d96a4ef36b423dcb979dde0c2847c8ff22d787f5` |
| [Advertised Olander CAD dialog script](https://www.product-config.net/catalog3/d/olander/cds2.js) | `bbfd01ad8d505a0c0600afe51619eb832b7870e0c408175ec303d21b3f505e61` |
| [Advertised CAD service script](https://www.product-config.net/catalog3/js/cds-catalog.js) | `ee9997f5f25c6140eb984206875c203a15f76e73d96b73bbe87d71b705e2b88f` |

The retailer identifies its item as Wera 05073287001 / JOKER SW 3/4 SB. No
model bytes, source authorization, revision, units, datum or complete contour
were exposed; those properties cannot be assigned from the listing label.

## Engineering consequence

The four retained leg-bolt tool checks remain `NOT_RUN_SOURCE_GAP`. Preserve
their original bolt resistance and modeled wire-path findings. The earlier
7/16-inch tool proxy cannot establish access for a 3/4-inch head or nut.

Do not repeat the failed public CAD lead as an access study. Advance this
dependency with another traceable, size-matched full tool profile or a
source-supported enclosing model with explicit dimensional and engagement
limits. A conditional fit model may be evaluated before physical receiving;
this source investigation adds no inspection prerequisite. Tool approach,
turning, counterhold, cable service, capture, support and reverse sequence
remain separate requirements.
