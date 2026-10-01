# Olander CAD-link access check — attempt04

**Outcome:** Olander's public search-index result for the listing
`05073287001` displays a “View 3D CAD Model” label alongside the Wera wrench
SKU and description. Direct retrieval of the listing returned a browser-tool
cache miss, so the actual model-link destination and its access requirements
could not be inspected. No model bytes, download link, CAD viewer metadata, or
source provenance were exposed by the available public result. Public,
account-free model access is therefore **not verified**; it is not established
that the link is gated or that a model is absent.

The indexed listing binds the retailer's product row to SKU `05073287001` and
alternate code `JOKER SW 3/4 SB`. It does not bind any model to Wera authorship
or authorization, an exact revision, units, datum/orientation, or complete
profile geometry. The underlying page's CAD control could not be opened, so no
assertion is made about its target or content. No account, login, signup,
purchase/cart action, or vendor contact was attempted.

No geometry, model, or operation screen was run. The four retained `#407`
axes remain `NOT_RUN_SOURCE_GAP`. The search strings, retrieval outcomes, and
source boundary are recorded in [`source-audit.json`](source-audit.json); the
reviewed result text is summarized in
[`source-observations.md`](source-observations.md). No original Olander HTML or
CAD bytes were available to hash; terminal hashes apply to this local packet
only.

Run the read-only integrity check from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/retained-3-4-tool-geometry-source-gap-attempt04/verify_source_access.py
```
